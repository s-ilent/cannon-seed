#!/usr/bin/env python3
"""scan_functions.py - bootstrap the code/data map of a PS-X EXE payload.

Deterministic MIPS-I linear-sweep scanner. It does not replace the
compiler-idiom or matching work; it produces the first-pass subsegment
list so splat can split per-function and progress/ratchets have something
honest to count.

Method (v2, documented and re-runnable):

1. Anchors: the proven entry point (pc0) plus every `jal` target found in
   the payload. `jal` encodes an absolute image address, so its target is
   a function start unless the word is data that happens to decode as jal
   (filtered later by the plausibility walk).
2. Linear walk from every uncovered anchor: consume instructions while
   they are plausible MIPS-I; stop after a `jr`/`j` plus its delay slot
   (function return or tail jump), after a run of >= 3 zero words
   (padding), or after 4 consecutive implausible words (embedded data).
3. v2 flow-through: a `jr`+delay does NOT end the walk when (a) the
   boundary address is not a jal target and (b) plausible code follows.
   GCC 2.6.3 places mid-function epilogues (early `return`s) whose
   fall-through continues the same function; v1 stopped there and
   manufactured prologue-less fragments (104 of 253 subsegments on
   slps_00270, see tools/prologue_hunt.py).
4. v2 branch-target rescue: branch/jump targets that land in remaining
   data gaps seed additional walks. A rescued run is kept only when it
   connects to (reaches or overlaps) an existing or other rescued range —
   orphaned walks would create NEW mid-function fragments, the very
   disease being fixed.
5. Ranges are merged; every uncovered aligned gap is data.
6. Type preservation: subsegments the tree already carries as `c`
   (C-matched functions) keep their type across re-scans.

Outputs (regenerated wholesale):
  - config/splat.slps_00270.yaml  subsegments section (between markers)
  - config/symbols.slps_00270.txt function symbols (between markers)
  - stdout summary

Usage: python3 tools/scan_functions.py [TARGET]     (default slps_00270)
"""

import re
import struct
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASELINES = REPO / "baselines"
SHA1_DIR = REPO / "config" / "sha1"

BASE = 0x80020000
HDR = 0x800

SPECIAL_FUNCTS = {0x00, 0x02, 0x03, 0x04, 0x06, 0x07, 0x08, 0x09, 0x0C,
                  0x0D, 0x10, 0x11, 0x12, 0x13, 0x18, 0x19, 0x1A, 0x1B,
                  0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x2A, 0x2B}
REGIMM_RT = {0x00, 0x01, 0x10, 0x11, 0x12, 0x13}
VALID_OPS = ({0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09,
              0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x10, 0x11, 0x12, 0x13}
             | set(range(32, 39))          # lb..lwr
             | {40, 41, 42, 43, 46}        # sb..swr
             | {49, 53, 57, 61})           # lwc1, ldc1, swc1, sdc1

JR = (0 << 26) | 0x08          # opcode 0, funct 8 (any register)
J = 2 << 26
JAL = 3 << 26


def plausible(w: int) -> bool:
    if w == 0:
        return True
    op = w >> 26
    if op not in VALID_OPS:
        return False
    if op == 0x00 and (w & 0x3F) not in SPECIAL_FUNCTS:
        return False
    if op == 0x01 and (w & 0x1F) not in REGIMM_RT:
        return False
    return True


def scan(payload: bytes, entry_off: int, hard_stops=frozenset()):
    n = len(payload) // 4
    words = struct.unpack(f"<{n}I", payload[: n * 4])

    def v2o(v):  # vram -> offset (or None)
        return v - BASE if 0 <= v - BASE < len(payload) else None

    anchors = set()
    if 0 <= entry_off < len(payload):
        anchors.add(entry_off & ~3)
    for i, w in enumerate(words):
        if (w >> 26) == 3:  # jal
            tgt = ((w & 0x3FFFFFF) << 2) | (BASE & 0xF0000000)
            o = v2o(tgt)
            if o is not None:
                anchors.add(o & ~3)
    # jal targets inside data produce garbage anchors; the walk from an
    # implausible anchor dies immediately, so no special filtering needed.

    def branch_target(i, w):
        """vram address a branch/jump at word i targets, or None."""
        op = w >> 26
        pc = BASE + i * 4
        if op in (0x04, 0x05, 0x06, 0x07) or op == 0x01:
            simm = w & 0xFFFF
            if simm >= 0x8000:
                simm -= 0x10000
            return pc + 4 + (simm << 2)
        if op == 0x02:  # j (not jal — jal targets are anchors already)
            return ((w & 0x3FFFFFF) << 2) | (BASE & 0xF0000000)
        return None

    def walk(start_off):
        """Forward walk with v1 stop rules + v2 jr flow-through.
        Returns (start, end) with end exclusive, or None."""
        a = start_off
        end = a
        bad = 0
        zeros = 0
        i = a // 4
        while i < n:
            w = words[i]
            if w == 0:
                zeros += 1
                if zeros >= 3:
                    return (a, end)
            else:
                zeros = 0
            if not plausible(w):
                bad += 1
                if bad >= 4:
                    return (a, end)
            else:
                bad = 0
                if (w >> 26) == 0 and (w & 0x3F) == 0x08:  # jr (any reg)
                    nxt = words[i + 1] if i + 1 < n else 0
                    stop = ((i + 2) if (nxt == 0 or plausible(nxt)) else (i + 1)) * 4
                    end = stop
                    # v2: flow through the jr when the boundary is not a
                    # jal target (nor a preserved C-matched function entry)
                    # and real code follows — this is a mid-function
                    # epilogue, not a function end.
                    if (stop not in anchors
                            and stop not in hard_stops
                            and stop // 4 < n
                            and words[stop // 4] != 0
                            and plausible(words[stop // 4])):
                        i = stop // 4
                        zeros = 0
                        bad = 0
                        continue
                    return (a, end)
            i += 1
            end = i * 4
        if end > len(payload):
            end = len(payload)
        return (a, end) if end > a else None

    covered = {}  # start_off -> end_off (function ranges)
    for a in sorted(anchors):
        if any(s <= a < e for s, e in covered.items()):
            continue
        r = walk(a)
        if r and r[1] > r[0]:
            covered[r[0]] = r[1]

    # v2 branch-target rescue for the remaining gaps
    def in_covered(o):
        return any(s <= o < e for s, e in covered.items())

    seeds = set()
    for s, e in list(covered.items()):
        for i in range(s // 4, e // 4):
            t = branch_target(i, words[i])
            if t is None:
                continue
            o = v2o(t)
            if o is not None and not in_covered(o & ~3) and (o & ~3) not in hard_stops:
                seeds.add(o & ~3)
    for a in sorted(seeds):
        if in_covered(a):
            continue
        r = walk(a)
        if not r:
            continue
        s, e = r
        # keep the rescued run only when it CONNECTS to an existing range:
        # its end reaches/overlaps one, or another seed's walk does.
        if any(s < e2 and e > s2 for s2, e2 in covered.items()):
            covered[s] = max(e, covered.get(s, 0))
        elif any(e2 == s for s2, e2 in covered.items()) or any(
            s2 == e for s2, e2 in covered.items()
        ):
            covered[s] = e

    # merge overlapping ranges, then trim trailing all-zero runs (>= 2
    # words) out of code ranges into the data side so spimdisasm never gets
    # the chance to classify real file bytes as NOBITS .bss (the retail
    # payload carries those zeros as actual bytes).
    merged = []
    for s in sorted(covered):
        if merged and s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], covered[s])
        else:
            merged.append([s, covered[s]])
    trimmed = []
    for s, e in merged:
        z = e
        while z - 8 >= s and words[(z // 4) - 1] == 0 and words[(z // 4) - 2] == 0:
            z -= 4
        trimmed.append([s, z])
    return trimmed


def data_gaps(code_ranges, payload_len):
    gaps = []
    cur = 0
    for s, e in code_ranges:
        if s > cur:
            gaps.append((cur, s))
        cur = max(cur, e)
    if cur < payload_len:
        gaps.append((cur, payload_len))
    return gaps


def preserved_types(yaml_path: Path):
    """Offsets the tree already carries with a hand-set type ("c" for
    C-matched functions). Returns {offset: (type, name)} and the set of
    offsets as hard walk-stop boundaries."""
    kept = {}
    if not yaml_path.exists():
        return kept
    in_block = False
    for ln in yaml_path.read_text().splitlines():
        if "# BEGIN GENERATED SUBSEGMENTS" in ln:
            in_block = True
            continue
        if "# END GENERATED SUBSEGMENTS" in ln:
            break
        if not in_block:
            continue
        m = re.match(r"\s*- \[(0x[0-9A-Fa-f]+),\s*(\w+),\s*(\w+)\]", ln)
        if m and m.group(2) != "asm":
            kept[int(m.group(1), 16) - HDR] = (m.group(2), m.group(3))
    return kept


def main(argv):
    target = argv[1] if len(argv) > 1 else "slps_00270"
    binpath = BASELINES / f"{target}.bin"
    if not binpath.exists():
        raise SystemExit(f"missing baseline {binpath}")
    blob = binpath.read_bytes()
    payload = blob[HDR:]
    header_words = struct.unpack_from("<I", blob, 0x10)
    pc0 = header_words[0]
    entry_off = pc0 - BASE

    kept = preserved_types(yaml_path := REPO / "config" / f"splat.{target}.yaml")
    hard_stops = frozenset(kept)

    ranges = scan(payload, entry_off, hard_stops)
    gaps = data_gaps(ranges, len(payload))

    # Defensive: a preserved c-function must START its own subsegment. If a
    # v2 merged range swallowed it, split the range at that offset so the
    # C file stays wired into the build (and log loudly).
    for off in sorted(kept):
        for i, (s, e) in enumerate(ranges):
            if s < off < e:
                print(f"scan: WARNING: splitting range {s:#x}..{e:#x} at "
                      f"preserved c-function {off:#x}")
                ranges[i:i + 1] = [[s, off], [off, e]]
                break

    subsegs = []
    for s, e in ranges:
        typ, name = "asm", f"func_{BASE + s:08X}"
        if s in kept:
            typ, name = kept[s]
        subsegs.append((s, typ, name, e - s))
    for s, e in gaps:
        subsegs.append((s, "data", f"data_{BASE + s:08X}", e - s))
    subsegs.sort()

    code_bytes = sum(e - s for s, e in ranges)
    data_bytes = sum(e - s for s, e in gaps)
    print(f"scan {target}: {len(ranges)} code ranges "
          f"({code_bytes:,} B, {100.0 * code_bytes / len(payload):.1f}%), "
          f"{len(gaps)} data gaps ({data_bytes:,} B)")

    # --- rewrite the splat yaml subsegments (regenerate wholesale) --------
    # One code segment covering the payload, subsegments in payload order.
    # splat 0.50 refuses top-level asm segments (needs a code parent), so
    # the interleaved layout is restored at LINK time instead:
    # tools/gen_ld.py gives every subsegment its own output section at its
    # explicit vram/rom address, in order.
    # The PS-X EXE header is NOT a segment: tools/mkpsxexe.py regenerates it
    # from committed config, so the linked image is the payload only.
    # NOTE on the rewrite regex: the group pattern requires `]` directly
    # after the hex digits, so it only matches a bare `- [0xNNN]` segment
    # reference line AFTER the generated block — the generated entries
    # themselves (`- [0xNNN, type, name]`) can never match, which is what
    # makes the wholesale replace + idempotent re-runs work.
    ytext = yaml_path.read_text()
    gen = ["    # BEGIN GENERATED SUBSEGMENTS (tools/scan_functions.py - make scan)"]
    for off, typ, name, size in subsegs:
        gen.append(f"      - [0x{HDR + off:X}, {typ}, {name}]   # {size:#x}")
    gen.append("    # END GENERATED SUBSEGMENTS")
    block = "\n".join(gen)
    new_ytext, count = re.subn(
        r"segments:\n.*?\n(\s*- \[0x[0-9A-Fa-f]+\])",
        "segments:\n"
        "  - name: payload\n"
        "    type: code\n"
        "    start: 0x800\n"
        "    vram: 0x80020000\n"
        "    subsegments:\n"
        + block + "\n\\1",
        ytext, flags=re.S)
    if count != 1:
        raise SystemExit(f"could not locate segments/end-marker in {yaml_path}")
    yaml_path.write_text(new_ytext)

    # --- rewrite function symbols between markers -------------------------
    sym_path = REPO / "config" / f"symbols.{target}.txt"
    stext = sym_path.read_text() if sym_path.exists() else ""
    head = stext.split("// BEGIN GENERATED FUNCTION SYMBOLS")[0]
    head = head.split("# BEGIN GENERATED FUNCTION SYMBOLS")[0].rstrip("\n")
    gen_syms = ["// BEGIN GENERATED FUNCTION SYMBOLS (tools/scan_functions.py)"]
    for s, e in ranges:
        gen_syms.append(f"func_{BASE + s:08X} = 0x{BASE + s:08X}; // type:func")
    gen_syms.append("// END GENERATED FUNCTION SYMBOLS")
    sym_path.write_text(head + "\n" + "\n".join(gen_syms) + "\n")

    print(f"wrote subsegments into {yaml_path.relative_to(REPO)} "
          f"and symbols into {sym_path.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

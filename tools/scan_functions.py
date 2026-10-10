#!/usr/bin/env python3
"""scan_functions.py - bootstrap the code/data map of a PS-X EXE payload.

Deterministic MIPS-I linear-sweep scanner. It does not replace the
compiler-idiom or matching work; it produces the first-pass subsegment
list so splat can split per-function and progress/ratchets have something
honest to count.

Method (v1, documented and re-runnable):

1. Anchors: the proven entry point (pc0) plus every `jal` target found in
   the payload. `jal` encodes an absolute image address, so its target is
   a function start unless the word is data that happens to decode as jal
   (filtered later by the plausibility walk).
2. Linear walk from every uncovered anchor: consume instructions while
   they are plausible MIPS-I; stop after a `jr`/`j` plus its delay slot
   (function return or tail jump), after a run of >= 3 zero words
   (padding), or after 4 consecutive implausible words (embedded data).
3. Ranges are merged; every uncovered aligned gap is data.

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


def scan(payload: bytes, entry_off: int):
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

    covered = {}  # start_off -> end_off (function ranges)
    for a in sorted(anchors):
        if any(s <= a < e for s, e in covered.items()):
            continue
        end = a
        bad = 0
        zeros = 0
        i = a // 4
        while i < n:
            w = words[i]
            if w == 0:
                zeros += 1
                if zeros >= 3:
                    break
            else:
                zeros = 0
            if not plausible(w):
                bad += 1
                if bad >= 4:
                    break
            else:
                bad = 0
                if w == JR or (w >> 26) == 2:  # jr (any reg) or j: stop after delay slot
                    i += 1
                    end = (i + 1) * 4
                    break
            i += 1
            end = i * 4
        if end > len(payload):
            end = len(payload)
        if end > a:
            covered[a] = end

    # merge overlapping ranges
    merged = []
    for s in sorted(covered):
        if merged and s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], covered[s])
        else:
            merged.append([s, covered[s]])
    return merged


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

    ranges = scan(payload, entry_off)
    gaps = data_gaps(ranges, len(payload))

    subsegs = []
    for s, e in ranges:
        subsegs.append((s, "asm", f"func_{BASE + s:08X}", e - s))
    for s, e in gaps:
        subsegs.append((s, "data", f"data_{BASE + s:08X}", e - s))
    subsegs.sort()

    code_bytes = sum(e - s for s, e in ranges)
    data_bytes = sum(e - s for s, e in gaps)
    print(f"scan {target}: {len(ranges)} code ranges "
          f"({code_bytes:,} B, {100.0 * code_bytes / len(payload):.1f}%), "
          f"{len(gaps)} data gaps ({data_bytes:,} B)")

    # --- rewrite the splat yaml subsegments (regenerate wholesale) --------
    yaml_path = REPO / "config" / f"splat.{target}.yaml"
    ytext = yaml_path.read_text()
    gen = ["    # BEGIN GENERATED SUBSEGMENTS (tools/scan_functions.py - make scan)"]
    for off, typ, name, size in subsegs:
        gen.append(f"      - [0x{HDR + off:X}, {typ}, {name}]   # {size:#x}")
    gen.append("    # END GENERATED SUBSEGMENTS")
    block = "\n".join(gen)
    new_ytext, count = re.subn(
        r"  subsegments:\n.*?\n(\s*# rom end marker)",
        "  subsegments:\n" + block + "\n\n  \\1",
        ytext, flags=re.S)
    if count != 1:
        raise SystemExit(f"could not locate subsegments/end-marker in {yaml_path}")
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

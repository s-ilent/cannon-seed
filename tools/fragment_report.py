#!/usr/bin/env python3
"""fragment_report.py - evidence census for prologue-less code subsegments.

Read-only companion to tools/scan_functions.py. Parses the committed
yaml layout (ground truth), then for every `asm` subsegment that does
not START with a GCC prologue collects the evidence needed to classify:

  (a) CONT-OF-PREV   continuation of the preceding range - one function
                     split by an embedded literal pool / jump table /
                     barrier stop (prev branches into or over it);
  (b) SHARED-TAIL    entry reached from >= 2 distinct OTHER ranges
                     (GCC shared epilogue / tail block);
  (p) PTR-CALLED     a data word holds this range's address verbatim
                     (function pointer table);
  (c) ORPHAN         no entry refs from other code and no pointer refs
                     - suspect garbage seed, re-type-to-data candidate.

Usage: python3 tools/fragment_report.py [TARGET]   (default slps_00270)
"""
import re
import struct
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASE = 0x80020000
HDR = 0x800
BRANCH_OPS = {0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07}


def branch_target(words, i):
    w = words[i]
    op = w >> 26
    pc = BASE + i * 4
    if op in (0x04, 0x05, 0x06, 0x07) or op == 0x01:
        simm = w & 0xFFFF
        if simm >= 0x8000:
            simm -= 0x10000
        return pc + 4 + (simm << 2)
    if op in (0x02, 0x03):  # j / jal
        return ((w & 0x3FFFFFF) << 2) | (BASE & 0xF0000000)
    return None


def prologue_frame(words, i, n):
    """addiu $sp,$sp,-N + sw $ra,(N-4|N-8)(sp) within two insns -> frame."""
    if i >= n:
        return None
    w = words[i]
    if (w & 0xFFFF0000) != 0x27BD0000:
        return None
    imm = w & 0xFFFF
    if imm >= 0x8000:
        imm -= 0x10000
    if not (-0x7F00 <= imm <= -8):
        return None
    frame = -imm
    for j in (1, 2):
        if i + j >= n:
            break
        w2 = words[i + j]
        if (w2 & 0xFFFF0000) == 0xAFBF0000:
            k = w2 & 0xFFFF
            if k >= 0x8000:
                k -= 0x10000
            if k in (frame - 4, frame - 8):
                return frame
    return None


def end_shape(words, e, n):
    if e >= 8:
        a, b = words[e // 4 - 2], words[e // 4 - 1]
        if a == 0x03E00008:  # jr $ra
            if (b & 0xFFFF0000) == 0x27BD0000 and (b & 0xFFFF) != 0:
                return "teardown"
            return "jr_ra"
    last = words[e // 4 - 1]
    op = last >> 26
    if op == 0 and (last & 0x3F) == 0x08:
        return f"jr_r{((last >> 21) & 31)}"
    if op in (0x02, 0x03):
        return "j/jal_end"
    if op in (0x04, 0x05, 0x06, 0x07) or op == 0x01:
        return "branch_end"
    return "data_stop"


def main(argv):
    target = argv[1] if len(argv) > 1 else "slps_00270"
    blob = (REPO / "baselines" / f"{target}.bin").read_bytes()
    payload = blob[HDR:]
    n = len(payload) // 4
    words = struct.unpack(f"<{n}I", payload[: n * 4])

    subsegs = []
    for ln in (REPO / "config" / f"splat.{target}.yaml").read_text().splitlines():
        m = re.match(r"\s*-\s*\[(0x[0-9A-Fa-f]+),\s*(asm|c|data),\s*(\w+)\]"
                     r"\s*#\s*(0x[0-9A-Fa-f]+)", ln)
        if m:
            subsegs.append((int(m.group(1), 16) - HDR, m.group(2),
                            m.group(3), int(m.group(4), 16)))
    code = [(s, s + sz) for s, t, nm, sz in subsegs if t in ("asm", "c")]
    gaps = [(s, s + sz) for s, t, nm, sz in subsegs if t == "data"]

    def rng_of(off):
        for s, e in code:
            if s <= off < e:
                return s
        return None

    # branch/jump entry refs (offset -> [source offsets]) and pointer refs
    entry_refs, ptr_refs = {}, {}
    starts = {s for s, _ in code}
    for i in range(n):
        off = i * 4
        t = branch_target(words, i)
        if t is not None and (t - BASE) in starts and (t & 3) == 0:
            entry_refs.setdefault(t - BASE, []).append(off)
        if words[i] in starts and rng_of(off) is None:
            ptr_refs.setdefault(words[i] - BASE, []).append(off)

    rows = []
    prev_code = None
    for idx, (s, t, name, size) in enumerate(subsegs):
        if t in ("asm", "c"):
            this_code = (s, s + size)
        is_asm = t == "asm"
        if is_asm and prologue_frame(words, s // 4, n) is not None:
            prev_code = this_code
            continue
        if not is_asm:
            continue
        e = s + size
        refs = [src for src in entry_refs.get(s, []) if not (s <= src < e)]
        srcs = {rng_of(src) for src in refs}
        srcs.discard(None)
        ptrs = ptr_refs.get(s, [])
        prev = prev_code
        gap = (prev[1], s) if prev and prev[1] < s else None
        prev_into = prev_over = False
        if prev:
            for i in range(prev[0] // 4, prev[1] // 4):
                bt = branch_target(words, i)
                if bt is None:
                    continue
                o = bt - BASE
                if o == s:
                    prev_into = True
                elif s < o < e and (o & 3) == 0:
                    prev_over = True
        out = []
        for i in range(s // 4, e // 4):
            bt = branch_target(words, i)
            if bt is not None and not (s <= bt - BASE < e):
                out.append(bt - BASE)
        # jump-table evidence: data words anywhere holding addresses INSIDE
        # F (case labels) - the switch-dispatch signature
        ptrs_into = []
        for gs2, ge2 in gaps:
            for i in range(gs2 // 4, ge2 // 4):
                if s + 4 <= words[i] - BASE < e:
                    ptrs_into.append(i * 4)
        # interior refs: branches from CODE landing in F's interior
        interior = {}
        for i in range(n):
            off = i * 4
            if rng_of(off) is None:
                continue
            bt = branch_target(words, i)
            if bt is not None and s + 4 <= bt - BASE < e:
                interior.setdefault(rng_of(bt - BASE), []).append(off)
        if len(srcs) >= 2:
            cls = "SHARED-TAIL"
        elif ptrs:
            cls = "PTR-CALLED"
        elif srcs:
            cls = "REF'D"
        else:
            cls = "ORPHAN"
        rows.append(dict(s=s, e=e, size=size, cls=cls, srcs=srcs, refs=refs,
                         ptrs=ptrs, prev=prev, gap=gap, prev_into=prev_into,
                         prev_over=prev_over, out=out, ptrs_into=ptrs_into,
                         interior=interior, end=end_shape(words, e, n)))
        prev_code = this_code

    print(f"== {target}: {len(code)} code subsegs, {len(rows)} prologue-less ==")
    print("   classes:", dict(Counter(r["cls"] for r in rows)))
    print()
    for r in sorted(rows, key=lambda r: -r["size"]):
        gs, ge = r["gap"] if r["gap"] else (0, 0)
        if r["gap"]:
            w = [words[i] for i in range(gs // 4, ge // 4)]
            gaptxt = (f"{len(w)}w z={sum(1 for x in w if x == 0)} "
                      f"ptr={sum(1 for x in w if BASE <= x < BASE + len(payload))}")
        else:
            gaptxt = "-"
        prevtxt = (f"prev {r['prev'][0]:#x}({end_shape(words, r['prev'][1], n)})"
                   if r["prev"] else "prev -")
        intotxt = (" P->F" if r["prev_into"] else "") + \
                  (" P-over" if r["prev_over"] else "")
        refstxt = "; ".join(f"{src:#x}@{('R' + hex(rs)) if rs else 'gap'}"
                            for src, rs in list(
                                zip(r["refs"], [rng_of(x) for x in r["refs"]]))[:4])
        ptrtxt = "; ".join(f"{p:#x}" for p in r["ptrs"][:3])
        jitxt = (f" jt={len(r['ptrs_into'])}@{r['ptrs_into'][0]:#x}"
                 if r["ptrs_into"] else "")
        intxt = ""
        if r["interior"]:
            parts = [f"{rs:#x}:{len(srcs2)}" for rs, srcs2 in
                     sorted(r["interior"].items())[:5]]
            intxt = " int<" + ",".join(parts) + ">"
        print(f"{r['s']:#x}-{r['e']:#x} {r['size']:>6}B {r['cls']:<11} "
              f"end={r['end']:<9} gap[{gaptxt}] {prevtxt}{intotxt}")
        if jitxt or intxt:
            print(f"           {jitxt}{intxt}")
        if refstxt:
            print(f"           refs: {refstxt}")
        if ptrtxt:
            print(f"           ptrs: {ptrtxt}")
        if r["out"]:
            outs = "; ".join(f"{o:#x}@{'R' if rng_of(o) else 'gap'}"
                             for o in r["out"][:6])
            print(f"           out -> {outs}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

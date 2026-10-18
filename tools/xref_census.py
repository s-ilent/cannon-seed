#!/usr/bin/env python3
"""xref_census.py - census of encoded address references in a TRUE image.

  python3 tools/xref_census.py TARGET [--gp 0x8006632C]

Reads baselines/<TARGET>.bin as the TRUE (de-framed) image and counts, for
every referenced address:
  lui   - lui+lo compositions (lui %hi; addiu/lw/sw with the same register
          within 6 instructions): the absolute-data reference form
  word  - raw data words holding the address (pointers, jump tables)
  gp    - $gp-based load/store offsets, absoluted through --gp when given
          (boot targets address small data gp-relatively; no lui form exists)

Output: build/work/xref.<TARGET>.txt, one line per referenced address:
  0x<addr> <lui> <word> <gp>
The de-frame flip's static resolver reads this census: a curated static whose
woven offset sits in a framing interlude has no mechanical woven->true map,
and the true image's own references are the only evidence for where it lives.
"""
import struct
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASE = 0x80020000
HDR = 0x800
LOADSTORE = {0x20, 0x21, 0x23, 0x24, 0x25, 0x28, 0x29, 0x2B}


def sext16(v):
    return v - 0x10000 if v & 0x8000 else v


def main(argv):
    target = argv[1]
    gp = int(argv[argv.index("--gp") + 1], 16) if "--gp" in argv else None
    img = (REPO / "baselines" / f"{target}.bin").read_bytes()
    n = (len(img) - HDR) // 4
    words = struct.unpack_from(f"<{n}I", img, HDR)
    lui, raw, gpc = {}, {}, {}
    for i, w in enumerate(words):
        op = w >> 26
        if op == 0x0F:  # lui
            rt = (w >> 16) & 31
            base = (w & 0xFFFF) << 16
            for j in range(i + 1, min(i + 7, n)):
                w2 = words[j]
                op2 = w2 >> 26
                if op2 == 0x0F:
                    break  # a fresh lui reuses the register
                rs = (w2 >> 21) & 31
                if (op2 == 0x09 or op2 in LOADSTORE) and rs == rt:
                    a = (base + sext16(w2 & 0xFFFF)) & 0xFFFFFFFF
                    lui[a] = lui.get(a, 0) + 1
                    break
        elif op in (0x23, 0x2B) and ((w >> 21) & 31) == 28 and gp:
            a = (gp + sext16(w & 0xFFFF)) & 0xFFFFFFFF
            gpc[a] = gpc.get(a, 0) + 1
        if BASE <= w < BASE + 0x1000000:
            raw[w] = raw.get(w, 0) + 1
    out = REPO / "build" / "work" / f"xref.{target}.txt"
    with out.open("w") as f:
        for a in sorted(set(lui) | set(raw) | set(gpc)):
            f.write(f"0x{a:08X} {lui.get(a, 0)} {raw.get(a, 0)} {gpc.get(a, 0)}\n")
    print(f"xref {target}: {len(lui)} lui-refs, {len(raw)} word-refs, "
          f"{len(gpc)} gp-refs -> {out.relative_to(REPO)}")


if __name__ == "__main__":
    main(sys.argv)

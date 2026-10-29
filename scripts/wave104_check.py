#!/usr/bin/env python3
"""Pre-check the x7 size=0x104 own-row wave (seventeenth-return queue item 1).

Checks, per the e3dc method (scripts/e3dcv_check.py pattern):
1. byte-identity of the seven 0x104 retail rows (baselines/<t>.bin at the yaml offset),
2. the row's neighborhood in each yaml (predecessor/successor rows for judge extent pinning),
3. name-collision scan (symbols files + config/symbols.curated.txt),
4. listing files exist for the seven names,
5. quick word-level scan of the common body: count jals (call sites), %hi/%lo pairs,
   lw/sw gp-relative candidates.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MEMBERS = [
    ("slps_00270", 0x19A38, "func_80039238"),
    ("sces_00269", 0x195EC, "func_80038DEC"),
    ("mainmenu_eu", 0x55F44, "func_80075744"),
    ("g3_jp", 0x4048C, "func_8005FC8C"),
    ("g3_eu", 0x40BDC, "func_800603DC"),
    ("g3org_jp", 0x3D928, "func_8005D128"),
    ("g3org_eu", 0x3E030, "func_8005D830"),
]
SIZE = 0x104


def main() -> int:
    blobs = {}
    for t, off, fn in MEMBERS:
        p = REPO / "baselines" / f"{t}.bin"
        data = p.read_bytes()[off : off + SIZE]
        blobs[t] = data
        print(f"{t} {fn} @0x{off:X}: {len(data)} bytes, sha1-prefix {data[:8].hex()}..{data[-8:].hex()}")
    ref = blobs[MEMBERS[0][0]]
    identical = all(b == ref for b in blobs.values())
    print(f"\nBYTE-IDENTICAL x7: {identical}")
    if not identical:
        for t, _, _ in MEMBERS:
            if blobs[t] != ref:
                diffs = [i for i in range(SIZE) if blobs[t][i] != ref[i]]
                print(f"  {t} differs at word offsets: {[hex(d & ~3) for d in diffs]}")
    # neighborhood rows
    print("\nYAML NEIGHBORHOODS:")
    for t, off, fn in MEMBERS:
        yml = (REPO / "config" / f"splat.{t}.yaml").read_text().splitlines()
        needle = f"[0x{off:X}, asm, {fn}]"
        idx = next(i for i, l in enumerate(yml) if needle in l)
        print(f"== {t} L{idx+1}")
        for k in (idx - 1, idx, idx + 1):
            print(f"   {yml[k].strip()}")
    # name collisions
    print("\nNAME-COLLISION SCAN:")
    for t, off, fn in MEMBERS:
        sym = (REPO / "config" / f"symbols.{t}.txt").read_text()
        hits = [l for l in sym.splitlines() if fn in l]
        cur = (REPO / "config" / "symbols.curated.txt").read_text()
        chits = [l for l in cur.splitlines() if fn in l]
        listing = REPO / "asm" / t / "nonmatchings" / f"{fn}.s"
        print(f"  {t}: symbols={'YES' if hits else 'no'} curated={'YES' if chits else 'no'} "
              f"listing={'YES' if listing.exists() else 'MISSING'}")
    # word scan of the reference body
    import struct
    words = [struct.unpack(">I", ref[i : i + 4])[0] for i in range(0, SIZE, 4)]
    jals = [(i * 4, hex(w & 0x3FFFFFF)) for i, w in enumerate(words) if (w >> 26) == 3]
    lui = [(i * 4, hex((w >> 16) & 0xFFFF)) for i, w in enumerate(words) if (w >> 26) == 0xF]
    print(f"\nBODY WORD SCAN (ref): {len(words)} words; jals={jals}; lui_count={len(lui)}")
    gp = sum(1 for w in words if (w >> 26) in (0x23, 0x2B) and ((w >> 21) & 31) == 28)
    print(f"  gp-relative lw/sw candidates: {gp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

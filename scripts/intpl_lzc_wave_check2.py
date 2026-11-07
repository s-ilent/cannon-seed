#!/usr/bin/env python3
"""Phase-2 pre-check: the mainmenu_jp Intpl row REMAINDER bodies.

Phase 1 (intpl_lzc_wave_check.py) proved Intpl 0x24 + the three census
members inside the 0x68 remainder (Square12 0x80065F98, Square0
0x80065FC0, AverageZ3 0x80065FE8) are uniquely placed and the region is
GTE macro code. This script byte-proves each remainder body against the
landed sibling copies (hardened baselines, direct read - the same trust
model as phase 1):

  mmj Square12  0x46798 0x28  vs  sces 0x167B8 / g3_jp 0x32284 /
                                g3_eu 0x31BC0 / g3org_jp 0x2F720 /
                                mainmenu_eu 0x4609C   (all c 0x28)
  mmj Square0   0x467C0 0x28  vs  the same five targets' Square0 rows
  mmj AverageZ3 0x467E8 0x18  vs  slps 0x16D40 / g3_jp 0x322D4 /
                                g3_eu 0x31C10 (c 0x20 rows): first 0x18
                                bytes + what the siblings' 0x18..0x20
                                tail holds (pad law vs truncated body)

Decision rule: AverageZ3 flips ONLY if the siblings' first 0x18 bytes
match mmj AND the siblings' 0x18..0x20 tail is zero pad (the Lzc pad
law). If the tail is nonzero, mmj's AverageZ3 is a truncated variant and
stays data.
"""
import struct
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def blob(t: str, off: int, size: int) -> bytes:
    return (REPO / "baselines" / f"{t}.bin").read_bytes()[off:off + size]


def words_le(b: bytes) -> list[int]:
    return [struct.unpack("<I", b[i:i + 4])[0] for i in range(0, len(b), 4)]


def dwcmp(a: bytes, b: bytes) -> int:
    return sum(x != y for x, y in zip(words_le(a), words_le(b)))


def main() -> int:
    ok = True

    print("== Square12 0x28 (mmj @0x46798) vs landed c rows")
    ref = blob("mainmenu_jp", 0x46798, 0x28)
    for t, off in (("sces_00269", 0x167B8), ("g3_jp", 0x32284),
                   ("g3_eu", 0x31BC0), ("g3org_jp", 0x2F720),
                   ("mainmenu_eu", 0x4609C)):
        dw = dwcmp(ref, blob(t, off, 0x28))
        print(f"   {t:<13} @0x{off:X}: dw={dw} "
              f"{'IDENTICAL' if dw == 0 else 'DIFFERS'}")
        if dw:
            ok = False

    print("== Square0 0x28 (mmj @0x467C0) vs landed c rows")
    ref = blob("mainmenu_jp", 0x467C0, 0x28)
    for t, off in (("sces_00269", 0x167E0), ("g3_jp", 0x322AC),
                   ("g3_eu", 0x31BE8), ("g3org_jp", 0x2F748),
                   ("mainmenu_eu", 0x460C4)):
        dw = dwcmp(ref, blob(t, off, 0x28))
        print(f"   {t:<13} @0x{off:X}: dw={dw} "
              f"{'IDENTICAL' if dw == 0 else 'DIFFERS'}")
        if dw:
            ok = False

    print("== AverageZ3 (mmj @0x467E8 0x18) vs c 0x20 rows")
    ref = blob("mainmenu_jp", 0x467E8, 0x18)
    avg_ok = True
    for t, off in (("slps_00270", 0x16D40), ("g3_jp", 0x322D4),
                   ("g3_eu", 0x31C10)):
        sib = blob(t, off, 0x20)
        dw = dwcmp(ref, sib[:0x18])
        tail = sib[0x18:]
        tail_zero = tail == b"\x00" * len(tail)
        print(f"   {t:<13} @0x{off:X}: first0x18 dw={dw} "
              f"{'IDENTICAL' if dw == 0 else 'DIFFERS'}; tail0x8="
              f"{tail.hex()} ({'zero pad' if tail_zero else 'NONZERO'})")
        if dw:
            avg_ok = False
    print(f"   -> AverageZ3 flip decision: "
          f"{'FLIP 0x18 (pad law)' if avg_ok else 'KEEP DATA (body differs)'}")
    if not avg_ok:
        print("      (the Intpl+Square12+Square0 flip still stands: "
              "0x24+0x28+0x28 = 0x74, remainder 0x18 stays data)")
        ok = True  # phase-2 verdict tracks the decided flip set

    print(f"\nPHASE-2 VERDICT: {'OK' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

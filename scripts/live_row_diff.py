#!/usr/bin/env python3
"""live_row_diff.py - the per-index live diff map.

Compares the judge's final linked .bin (build/judge/<NAME>.bin, written by
tools/judge_unit.py) against the retail row bytes in baselines/<T>.bin at
the row's yaml offset, one 32-bit word per index. The judge's .bin is the
LINKED section - the pre-link .o dump is relocation-polluted (j/hi-lo
pairs read as fake diffs). The map's raw mismatch count == the judge's
DIFF exactly (validated cron-202611060231 on d62: 143/274).

Usage: python3 scripts/live_row_diff.py TARGET NAME [OFFSET_HEX] [EXTENT_HEX]
  TARGET defaults g3org_jp, NAME defaults SsVabOpenHeadWithMode,
  OFFSET/EXTENT default the g3org_jp func_80068064 row (0x48864 / 0x448).
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def load(path, off, n):
    data = Path(path).read_bytes()
    return data[off:off + n]


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "g3org_jp"
    name = sys.argv[2] if len(sys.argv) > 2 else "SsVabOpenHeadWithMode"
    off = int(sys.argv[3], 16) if len(sys.argv) > 3 else 0x48864
    ext = int(sys.argv[4], 16) if len(sys.argv) > 4 else 0x448

    retail = load(REPO / "baselines" / f"{target}.bin", off, ext)
    built = load(REPO / "build" / "judge" / f"{name}.bin", 0, ext)
    if len(built) != len(retail):
        print(f"SIZE built {len(built)} vs row {len(retail)} - NOT SIZE-EXACT; "
              f"index map below is prefix-aligned only")
    n = min(len(built), len(retail)) // 4
    rows = []
    for i in range(n):
        b = int.from_bytes(built[i*4:i*4+4], "little")
        r = int.from_bytes(retail[i*4:i*4+4], "little")
        if b != r:
            rows.append((i, b, r))
    print(f"live map {target}/{name}: {len(rows)}/{n} words differ "
          f"(built {len(built)} B, retail {len(retail)} B)")
    # contiguous runs
    runs = []
    for i, b, r in rows:
        if runs and i == runs[-1][1] + 1:
            runs[-1][1] = i
            runs[-1][2].append((i, b, r))
        else:
            runs.append([i, i, [(i, b, r)]])
    for a, b_, items in runs:
        print(f"  [{a}..{b_}] {len(items)} w")
        for i, bw, rw in items[:6]:
            print(f"    [{i}] built {bw:08X}  retail {rw:08X}")
        if len(items) > 6:
            print(f"    ... {len(items)-6} more")
    # tail shift detector: how far must built[i] move to match retail?
    if rows:
        a, b_, items = runs[-1]
        print(f"last run [{a}..{b_}]: built [{a}] {items[0][1]:08X} vs "
              f"retail [{a}] {items[0][2]:08X}; retail [{a-1}] "
              f"{int.from_bytes(retail[(a-1)*4:(a-1)*4+4], 'little'):08X} "
              f"(a -1 shift means built tail == retail tail minus one word)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""oracle_runs.py - the retail-bound wave enumerator.

Reads the differing bytes between the built image (build/<target>.bin)
and the true baseline (baselines/<target>.bin) and enumerates the
retail-bound work order: differing bytes grouped into runs (gap <= 4
merged), each run decoded as the overlapping little-endian words, built
vs retail.

The wave discipline (docs/TASKS.md, window cron-20261019-0549): the
oracle per wave is the enumerator, but READ THE RUNS EXHAUSTIVELY - a
22B run is two pairs, a 42B run three (wave 2 existed because wave 1
read one pair per run). This tool instruments that lesson: EVERY
overlapping word of EVERY run is decoded, so one pass yields the full
name set.

Word pairs are raw loads/stores; %hi/%lo pairs must be read with the
sign-extension carry in mind (lui 0x800A + lw 0x894C is 0x8009894C, not
0x800A894C) - the decode here prints the raw words, the reader applies
the carry.

Usage:
    python3 tools/oracle_runs.py <target> [target ...]

Run `make build TARGET=<t>` first.  Writes nothing; exit 0 with
"0 differing bytes" when the target is GREEN.
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HDR = 0x800  # PS-X EXE header


def words(buf: bytes, start: int, end: int):
    """Decode the 4-byte LE words overlapping [start, end)."""
    out = []
    lo = max(0, (start - 3) // 4 * 4)
    for w in range(lo, end, 4):
        wb = buf[w:w + 4]
        if len(wb) == 4:
            out.append((w, wb))
    return out


def run_for(target: str) -> int:
    built = (REPO / "build" / f"{target}.bin").read_bytes()
    base = (REPO / "baselines" / f"{target}.bin").read_bytes()
    if len(built) != len(base):
        print(f"[{target}] LENGTH MISMATCH built={len(built)} base={len(base)}")
        return 1

    diffs = [i for i in range(len(built)) if built[i] != base[i]]
    if not diffs:
        print(f"[{target}] 0 differing bytes")
        return 0

    # merge into runs with gap <= 4
    runs = []
    s = p = diffs[0]
    for d in diffs[1:]:
        if d - p <= 4:
            p = d
        else:
            runs.append((s, p + 1))
            s = p = d
    runs.append((s, p + 1))

    print(f"[{target}] {len(diffs)} differing bytes in {len(runs)} run(s)")
    for (a, b) in runs:
        pa = a - HDR
        print(f"  run [{a:#x}..{b - 1:#x}] {b - a}B  payload 0x{pa:X}")
        for off, wb in words(built, a, b):
            rb = base[off:off + 4]
            if wb == rb:
                continue
            print(f"    word 0x{off:06X} (payload 0x{off - HDR:06X}): "
                  f"built {wb.hex()} -> retail {rb.hex()}  "
                  f"(built 0x{int.from_bytes(wb, 'little'):08X} "
                  f"retail 0x{int.from_bytes(rb, 'little'):08X})")
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    rc = 0
    for target in sys.argv[1:]:
        rc |= run_for(target)
    return rc


if __name__ == "__main__":
    sys.exit(main())

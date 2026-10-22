#!/usr/bin/env python3
"""inventory_report.py - per-target unmatched function inventory by class.

Reads each target's generated symbols file, keeps every function symbol
the target's own yaml does not cover with a c row (the unmatched set -
the target-scoped is_matched rule pair_report landed in cron-20261022-
0658; the bare src/<name>.c existence test it replaced was shared across
all eight exes and false-matched cross-exe name collisions), and
classifies it with the same rules pair_report uses (veneer / fragment /
sdk / compiler). Prints a class table per target plus the totals, so the
matching lane picks from real remaining work rather than the cross-region
twin list, which is now library-dominated.

Usage: inventory_report.py [--delta] [target ...]
Gated (cron-20261022-0928): each target must pass pair_report.input_gates
(witnessed baseline + build ELF consistent with the committed yaml); the
classes read baseline bytes, and unwitnessed bytes classify garbage.
Exit: 0 report produced (possibly partial); 2 every requested target
refused.

PICK DELTA (cron-20261022-1158): every report run now prints, under the
class table, the instrument delta vs the RETIRED pre-0658 matched test
(pair_report.matched_delta): +gains = span-coverage matched members the
old file/lo-VA test under-counted (they left the pick lists when the
instrument changed - not progress), -dissolves = cross-exe name-collision
artifacts the old test over-counted (never real work). The gated path
prints the same numbers inventory_report --delta prints standalone:

  inventory_report.py --delta [target ...]

--delta runs WITHOUT the gates BY CONSTRUCTION, not by bypass: it reads
config/symbols.<t>.txt, the yaml, and src/ only - no baseline byte and
no build-ELF VA crosses the check - so it answers "what does the
instrument change alone do to the lists" on an unwitnessed tree (the
oracle-down windows), writing build/matched_delta_<t>.txt. Exit: 0.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pair_report import (REPO, elf_funcs, fn_class,  # noqa: E402
                         input_gates, is_matched, matched_delta,
                         sym_funcs)

TARGETS = ["slps_00270", "sces_00269", "mainmenu_jp", "mainmenu_eu",
           "g3_jp", "g3_eu", "g3org_jp", "g3org_eu"]


def delta_report(want):
    """The ungated instrument-delta run (see module docstring)."""
    have = [t for t in want
            if os.path.exists(os.path.join(REPO, f"config/symbols.{t}.txt"))]
    deltas = {t: matched_delta(t) for t in have}
    for t in want:
        if t not in deltas:
            print(f"{t}: no symbols file")
            continue
        gains, dissolves = deltas[t]
        print(f"{t:14s} delta  +{len(gains):3d} gains / -{len(dissolves):2d} "
              f"dissolves  (vs the retired pre-0658 file/lo-VA test; "
              f"instrument, not progress)")
        path = os.path.join(REPO, f"build/matched_delta_{t}.txt")
        with open(path, "w") as f:
            for name, va in sorted(gains, key=lambda g: g[1]):
                f.write(f"gain {name} {va:08X}\n")
            for name, va in sorted(dissolves, key=lambda g: g[1]):
                f.write(f"dissolve {name} {va:08X}\n")
    tot_g = sum(len(deltas[t][0]) for t in have)
    tot_d = sum(len(deltas[t][1]) for t in have)
    print(f"{'TOTAL':14s} delta  +{tot_g:3d} gains / -{tot_d:2d} dissolves")
    return 0


def main():
    argv = sys.argv[1:]
    delta_only = "--delta" in argv
    want = [a for a in argv if not a.startswith("--")] or TARGETS
    if delta_only:
        return delta_report(want)
    total = {}
    refused = 0
    for t in want:
        ok, problems = input_gates(t)
        if not ok:
            refused += 1
            print(f"{t}: REFUSED - {'; '.join(problems)}")
            continue
        if not os.path.exists(os.path.join(REPO, f"config/symbols.{t}.txt")):
            print(f"{t}: no symbols file")
            continue
        elf = os.path.join(REPO, f"build/{t}.elf")
        sizes = {va: sz for _, (va, sz) in elf_funcs(elf).items()} \
            if os.path.exists(elf) else {}
        counts = {}
        unmatched = []
        for name, va in sym_funcs(t):
            if is_matched(t, name, va):
                continue
            size = sizes.get(va)
            if size is None:
                continue
            c = fn_class(t, va, size, name)
            counts[c] = counts.get(c, 0) + 1
            total[c] = total.get(c, 0) + 1
            unmatched.append((c, name, va, size))
        line = "  ".join(f"{k}:{v}" for k, v in sorted(counts.items()))
        print(f"{t:14s} unmatched {sum(counts.values()):5d}  {line}")
        with open(os.path.join(REPO, f"build/inventory_{t}.txt"), "w") as f:
            for c, name, va, size in sorted(unmatched):
                f.write(f"{c} {name} {va:08X} {size}\n")
        g, d = matched_delta(t)
        print(f"{'':14s} pick delta: +{len(g)} gains / -{len(d)} dissolves "
              f"vs the retired pre-0658 test (instrument, not progress)")
    line = "  ".join(f"{k}:{v}" for k, v in sorted(total.items()))
    print(f"{'TOTAL':14s} unmatched {sum(total.values()):5d}  {line}")
    if refused and refused == len(want):
        print("\nall requested targets REFUSED - no inventory. Run the "
              "disc-return sequence first (witness 8/8 STRICT). The "
              "ungated `--delta` mode still answers what the instrument "
              "change alone did (it reads no baseline and no ELF).",
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

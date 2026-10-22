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

Usage: inventory_report.py [target ...]
Gated (cron-20261022-0928): each target must pass pair_report.input_gates
(witnessed baseline + build ELF consistent with the committed yaml); the
classes read baseline bytes, and unwitnessed bytes classify garbage.
Exit: 0 report produced (possibly partial); 2 every requested target
refused.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pair_report import (REPO, elf_funcs, fn_class,  # noqa: E402
                         input_gates, is_matched)

TARGETS = ["slps_00270", "sces_00269", "mainmenu_jp", "mainmenu_eu",
           "g3_jp", "g3_eu", "g3org_jp", "g3org_eu"]


def sym_funcs(target):
    """[(name, va)] for the target's function symbols."""
    out = []
    path = os.path.join(REPO, f"config/symbols.{target}.txt")
    for line in open(path):
        m = re.match(r"(\w+) = 0x([0-9A-Fa-f]+); // type:func", line)
        if m:
            out.append((m.group(1), int(m.group(2), 16)))
    return out


def main():
    want = sys.argv[1:] or TARGETS
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
    line = "  ".join(f"{k}:{v}" for k, v in sorted(total.items()))
    print(f"{'TOTAL':14s} unmatched {sum(total.values()):5d}  {line}")
    if refused and refused == len(want):
        print("\nall requested targets REFUSED - no inventory. Run the "
              "disc-return sequence first (witness 8/8 STRICT).",
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

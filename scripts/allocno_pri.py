#!/usr/bin/env python3
"""Read gcc 2.6.3's exact global-alloc pri inputs from the -da flow dump.

global.c allocno_compare sorts by
    pri = (floor_log2(n_refs) * n_refs / live_length) * 10000 * size
descending, tie -> ascending allocno (pseudo) number.  The .flow dump
prints the authoritative pre-local-alloc numbers verbatim:

    Register 131 used 6 times across 39 insns; ...

so pri is computable WITHOUT simulating flow.  Two documented caveats
(window cron-202610212014):
  1. floor_log2, NOT log2 - the previous window's 0.469-vs-0.448 claim
     used exact log2 and INVERTED the color/v4o order; with floors the
     color (2*6/39 = 0.308) correctly LOSES to v4o (3*12/106 = 0.340).
  2. local-alloc's copy propagation MUTATES reg_n_refs between the flow
     dump and the sort (local-alloc.c lines 780/912/1109), so the flow
     pri is the PRE-mutation ranking; the greg dump's "regs to allocate"
     line is the only ground truth for the post-mutation order.

Usage: allocno_pri.py <dump.flow> [pseudo ...]
Prints the pri table, and - when all 17 G-divider allocnos are among
the watch list - the predicted vs observed greg order.
"""
import math
import re
import sys

path = sys.argv[1]
watch = [int(x) for x in sys.argv[2:]] if len(sys.argv) > 2 else None

line_re = re.compile(
    r"^Register (\d+) used (\d+) times across (\d+) insns")
stats = {}
for ln in open(path):
    m = line_re.match(ln)
    if m:
        n, refs, ll = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if refs and ll:
            pri = int(math.floor(math.log2(refs))) * refs / ll * 10000
        else:
            pri = 0.0
        stats[n] = (refs, ll, pri)

if watch is None:
    watch = sorted(stats)

print(f"{'pseudo':>7} {'n_refs':>7} {'LL':>6} {'pri':>9}")
for n in watch:
    if n in stats:
        r, l, p = stats[n]
        print(f"{n:>7} {r:>7} {l:>6} {p:>9.1f}")
    else:
        print(f"{n:>7} {'-':>7} {'-':>6} {'-':>9}")

# the G-divider allocno set and its observed greg order (mmjp render)
ALLOCNOS = [167, 80, 81, 131, 82, 83, 78, 72, 73, 84, 79, 71, 138, 77, 75, 85, 76]
OBSERVED = "167 80 81 131 82 83 78 72 73 84 79 71 138 77 75 85 76"
if all(n in stats for n in ALLOCNOS):
    pred = sorted(ALLOCNOS, key=lambda n: (-stats[n][2], n))
    print(f"\npredicted (pre-local-alloc pri): {' '.join(map(str, pred))}")
    print(f"observed greg order            : {OBSERVED}")
    print("match" if " ".join(map(str, pred)) == OBSERVED else
          "MISMATCH - local-alloc copy propagation mutated n_refs "
          "(see header caveat 2); trust the greg line for the true order")

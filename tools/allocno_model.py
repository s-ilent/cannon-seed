#!/usr/bin/env python3
"""Predict the global-alloc order from a -da compile's dumps.

Banked instrument for lever (c) (window cron-20261021-1713).  The greg
"regs to allocate" line is fully predicted by sorting the .lreg register
table with global.c allocno_compare:

    pri = floor_log2(n_refs) * n_refs / reg_live_length * 10000 * size
    sort descending; tie -> ascending allocno number

(the *size factor is 1 for every SImode pseudo here and drops out of the
order; allocno numbers follow pseudo order 1:1 for the single-allocno
regs that reach global alloc).

Where the .lreg table's values come from (the mechanism chain, all
source-verified this window):
  reg_live_length = schedule_insns' writeback (sched.c 4899-4905,
      printed as ";; register N life shortened/extended from X to Y"
      in the .sched dump), then DOUBLED by update_equiv_regs for every
      pseudo it pins a REG_EQUIV note on (local-alloc.c 1063).  The
      doubling is detected here as lreg == 2x the sched-final value.
  reg_n_refs = the stale pre-combine reg_scan count: regclass()
      (toplev.c 3100) never recounts, and the copy-prop optimizers
      (local-alloc.c 780/782, 912/913) netted ZERO refs on this
      function across all 64 dumped rows.  The equiv-kill (line 1109)
      zeroes the equiv-replaced rows (74/122/139/150 on the G probe) -
      they vanish from the .lreg table.
  The .flow table is the PRE-combine baseline (life_analysis) - the
      flow->lreg reg_live_length delta is sched + the equiv doubling,
      NOT copy propagation.  This corrects the 2014/1443 inference
      that local-alloc copy prop owned the flow->greg order shift.

Consequence for the GsTMDdivG4LFG color war: the model reproduces the
observed greg line 17/17 and the numeric gate is exact - the color
(pri 2*6/33 = 0.3636) sits between v3o (36/98 = 0.3673) and v2o
(36/100 = 0.360); retail's color-above-v4o needs color LL <= 31 (or
n_refs >= 8, the refuted lever (a)), or BOTH v4o/v3o LL >= 100.  All
three numbers are sched-slaved spans of the loop body, so the color
flip is slaved to whatever re-times the stream - the entry cascade.

Usage:
    python3 tools/allocno_model.py build/probe/Gda
      (reads <base>.i.lreg, <base>.i.greg, optional <base>.i.sched)

Exit 0 = predicted order matches the greg line verbatim; 1 = mismatch;
2 = missing dumps.
"""
import re
import sys

ROW = re.compile(r"Register (\d+) used (\d+) times across (\d+) insns")
CROSSES = re.compile(r"crosses (\d+) calls")
GREG_LINE = re.compile(r";; (\d+) regs to allocate: (.*)")
SCHED_ROW = re.compile(
    r";; register (\d+) life (shortened|extended) from (\d+) to (\d+)"
)


def floor_log2(n):
    return n.bit_length() - 1


def read_lreg(path):
    """Global-alloc rows only: dump_flow_info tags single-block locals
    with 'in block N' (they never reach the greg line - local_alloc
    assigns them); block-global rows have no 'in block' tag.  The
    'dies in N places' clause is printed only when the reg has deaths
    and 'crosses M calls' only when M > 0 (row 131: '; crosses 3
    calls' with no dies clause) - parse them independently."""
    table = {}
    for ln in open(path, errors="replace"):
        m = ROW.search(ln)
        if not m or " in block " in ln:
            continue
        r = int(m.group(1))
        n = int(m.group(2))
        ll = int(m.group(3))
        c = CROSSES.search(ln)
        calls = int(c.group(1)) if c else 0
        table[r] = (n, ll, calls)
    return table


def read_greg(path):
    for ln in open(path, errors="replace"):
        m = GREG_LINE.search(ln)
        if m:
            return int(m.group(1)), [int(x) for x in m.group(2).split()]
    return None, None


def read_sched(path):
    final = {}
    for ln in open(path, errors="replace"):
        m = SCHED_ROW.search(ln)
        if m:
            final[int(m.group(1))] = int(m.group(4))
    return final


def predicted_order(table, lls):
    """allocno_compare over the table; lls overrides reg_live_length."""
    regs = sorted(table)
    keyed = []
    for r in regs:
        n, _, _ = table[r]
        ll = lls.get(r, table[r][1])
        if ll <= 0:
            ll = 1  # global.c 530: default size guard, keep the sort total
        pri = floor_log2(n) * n / ll
        keyed.append((-pri, r))
    keyed.sort()
    return [r for _, r in keyed]


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    base = sys.argv[1].rstrip("/")
    lreg_p, greg_p = f"{base}.i.lreg", f"{base}.i.greg"
    sched_p = f"{base}.i.sched"
    try:
        table = read_lreg(lreg_p)
        ngreg, greg = read_greg(greg_p)
    except OSError as e:
        print(f"allocno_model: {e}; run the probe compile with "
              f"CC1FLAGS_EXTRA='-da' first", file=sys.stderr)
        return 2
    sched = read_sched(sched_p) if sched_p else {}

    # equiv-doubling detector: lreg LL == 2x the sched-final value
    doubled, plain = [], []
    for r in sorted(table):
        n, ll, _ = table[r]
        if r in sched and ll == 2 * sched[r]:
            doubled.append(r)
        elif r in sched:
            plain.append(r)
    print(f"lreg table: {len(table)} rows; sched-final known for "
          f"{len(sched)}")
    print(f"equiv-DOUBLED LL rows (local-alloc.c 1063): {doubled}")
    print(f"sched-only LL rows (no equiv note): "
          f"{[r for r in sorted(table) if r in sched and r not in doubled]}")

    pred = predicted_order(table, {})
    print(f"\npredicted ({len(pred)}): {' '.join(map(str, pred))}")
    if greg is not None:
        print(f"observed  ({ngreg}): {' '.join(map(str, greg))}")
        if pred == greg:
            print("MATCH: the .lreg sort reproduces the greg line "
                  "verbatim.")
            return 0
        print("MISMATCH: model vs greg line differ at: "
              f"{[i for i, (a, b) in enumerate(zip(pred, greg)) if a != b]}")
        return 1
    print("no greg line found; prediction only")
    return 0


if __name__ == "__main__":
    sys.exit(main())

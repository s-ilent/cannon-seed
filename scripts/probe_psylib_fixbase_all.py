#!/usr/bin/env python3
"""probe_psylib_fixbase_all - the site-origin base route over ALL libs
(cron-20261101-0921, NEXT item 1).

For every module of every psyq 3.3 lib: run fixup_site_origin (the
t=0x52/0x82 lui-peak sweep) and classify the result against the two
banked base solvers:
  MATCH   base_valid == O_peak - size1 (the multi-cluster claim)
  ATBASE  base_valid == O_peak        (the single-object reading)
  DELTA0  base_valid == blob1 == O_peak - size1 anyway (both readings
          coincide - the delta-0 law class)
  DIFF/n  neither (report the delta)
  EMPTY   valid law empty (multi-cluster discriminator): the route's
          proof ground - report O_peak, size1, and the peak sharpness.
Modules with <4 hi sites or no peak are skipped (route not applicable).
"""
import glob
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import omf_pubsyms as op  # noqa: E402

DEFAULT_LIBS = sorted(glob.glob("/home/z/my-project/psyq/3.3/PSX/LIB/*.LIB"))


def main(argv):
    libs = argv[1:] or DEFAULT_LIBS
    verdicts = Counter()
    empty_sharp = []
    for path in libs:
        try:
            lib = op.PsyqLib(path)
        except (OSError, ValueError) as e:
            print(f"# {os.path.basename(path)}: {e}")
            continue
        d = lib.data
        for m in lib.modules:
            defs = [(n, off) for n, k, a, b, off in op.def_map(m)
                    if k == 0x0C and b == 2]
            if not defs:
                continue
            r = op.fixup_site_origin(d, m)
            if r is None:
                continue
            O, hits, n_sites, size1 = r
            if O is None or size1 is None or n_sites < 4 or hits < 4:
                continue
            val = op.solve_def_base_valid(d, m)
            base = val[0][0] if val else None
            pred = O - size1
            blob, _pe, _np = op.first_code_chunk(d, m)
            if base is None:
                verdicts["EMPTY-valid"] += 1
                empty_sharp.append(
                    (lib.name, m.name, O, size1, pred, hits, n_sites))
                continue
            if base == pred and base == blob:
                verdicts["DELTA0-coincident"] += 1
            elif base == pred:
                verdicts["MATCH"] += 1
            elif base == O:
                verdicts["ATBASE"] += 1
            else:
                verdicts[f"DIFF"] += 1
                print(f"DIFF {lib.name} {m.name}: base={base:#x} "
                      f"O={O:#x} size1={size1:#x} pred={pred:#x} "
                      f"hits={hits}/{n_sites}")
    print(f"verdicts: {dict(verdicts)}")
    print(f"EMPTY-valid modules with a sharp peak (the per-cluster proof "
          f"ground): {len(empty_sharp)}")
    for row in empty_sharp[:25]:
        print(f"  {row[0]}/{row[1]}: O={row[2]:#x} size1={row[3]:#x} "
              f"pred={row[4]:#x} hits={row[5]}/{row[6]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

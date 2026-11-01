#!/usr/bin/env python3
"""probe_psylib_fixbase - the fixup-stream base route, cross-module
(cron-20261101-0921).

The window's core finding on VMANAGER: the record-zone %hi fixup sites
(t=0x52) land on lui words under the site origin O = base + size1 where
size1 = the first 02-chunk's payload size (133/152 hits at
O=0x11664=0x10668+0xffc; the peak falls off 61/58/48 on ±0x10). The base
route: sweep O, take argmax of lui-hits, base = argmax(O) - size1.

This probe runs that route over every module of a lib and compares:
  - base_pred  = argmax_O(lui-hits) - size1
  - base_valid = solve_def_base_valid's UNIQ base (empty = multi-cluster)
  - base_vote  = solve_def_base's prologue-vote maximum
Target: does base_pred reproduce base_valid where the valid law works,
and does it SOLVE the multi-cluster discriminators (SEQREAD & co)?
"""
import os
import re
import struct
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import omf_pubsyms as op  # noqa: E402
from probe_psylib_fixsite import parse_fixups  # noqa: E402

MEM = frozenset((0x20, 0x21, 0x23, 0x24, 0x25, 0x28, 0x29, 0x2b,
                 0x04, 0x05, 0x06, 0x07, 0x09, 0x0c, 0x0d))


def first_chunk_size(d, mod):
    """The dominant leading 02-chunk's payload size (the code chunk).

    The leading run can carry tiny 02 fragments (VMANAGER: a 4-byte one);
    the CODE chunk is the max-size 02 before the first 0a record."""
    blob, pe, _np = op.first_code_chunk(d, mod)
    if blob is None:
        return None, None
    o = pe
    best = (0, None)
    while o + 3 <= len(d):
        b = d[o]
        if b == 0x06 and d[o + 2] == 0x00:
            o += 3
        elif b == 0x02:
            size = struct.unpack_from("<H", d, o + 1)[0]
            if size == 0:
                break
            if size > best[0]:
                best = (size, o + 3)
            o += 3 + size
        else:
            break
    return best if best[0] else (None, None)


def solve_base_fixups(d, mod, span=0x3000):
    """Sweep the site origin O over [blob1 - 0x800, blob1 + span); return
    (best_O, hits, n_hi, size1) maximizing %hi-fixup lui landings."""
    blob, pe, _np = op.first_code_chunk(d, mod)
    if blob is None:
        return None
    ts = mod.table_start or (mod.offset + mod.size)
    evs = parse_fixups(d, pe, ts)
    hisites = [e[1][1] for e in evs if e[0] == "0a" and e[1][0] == 0x52]
    if not hisites:
        return None
    lo = max(0, blob - 0x800)
    hi = min(len(d) - 8, blob + span)
    best = (0, None)
    for O in range(lo, hi, 2):
        h = 0
        for s in hisites:
            pos = O + s
            if 0 <= pos <= len(d) - 8:
                if struct.unpack_from("<I", d, pos)[0] >> 26 == 0x0F:
                    w2 = struct.unpack_from("<I", d, pos + 4)[0]
                    if w2 >> 26 in MEM:
                        h += 1
        if h > best[0]:
            best = (h, O)
    size1, _ = first_chunk_size(d, mod)
    return best[1], best[0], len(hisites), size1


def main(argv):
    libpath = argv[1]
    rx = re.compile(argv[2]) if len(argv) > 2 else None
    lib = op.PsyqLib(libpath)
    d = lib.data
    print(f"module\tn_hi\tbest_O\thits\tsize1\tbase_pred\t"
          f"base_valid\tbase_vote")
    for m in lib.modules:
        if rx and not rx.search(m.name):
            continue
        r = solve_base_fixups(d, m)
        if r is None:
            continue
        best_O, hits, n_hi, size1 = r
        if best_O is None or size1 is None:
            continue
        pred = best_O - size1
        val = op.solve_def_base_valid(d, m)
        bv = val[0][0] if val else None
        law = (f"uniq" if val and len(val) == 1 else
               (f"amb x{len(val)}" if val else "EMPTY"))
        vote = op.solve_def_base(d, m)
        bvote = vote[0] if vote else None
        agree = ""
        if bv is not None:
            agree = "MATCH" if bv == pred else f"DIFF{bv - pred:+#x}"
        print(f"{m.name}\t{n_hi}\t{best_O:#x}\t{hits}\t{size1:#x}\t"
              f"{pred:#x}\t{bv and hex(bv)}/{law}\t{bvote and hex(bvote)}\t{agree}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

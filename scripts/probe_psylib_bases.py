#!/usr/bin/env python3
"""probe_psylib_bases - per-def base histogram for the PSYLIB def-row offsets.

Follow-up to probe_psylib_chunks.py: the module-flat base model breaks on
multi-object modules (VMANAGER 23/38 under one base; SEQREAD 10/18). This
probe tests the per-object model: for EVERY b=2 0x0c def row, collect every
file position p in [blob1, table_start) whose word is an addiu-sp prologue
(0x27bd....) and record the implied base p - off. Histogram the implied
bases across the module's defs: real object bases appear as peaks shared by
many defs.

POST-HOC CORRECTION (same window): the histogram's near-tie double peaks 12
bytes apart (VMANAGER 0x1065c/0x10668) are NOT two def shapes - the -12
peak is the PREVIOUS function's epilogue restore ([addiu $sp][jr $ra]
[delay] tail) voting through the def of the next function. The tool's
solve_def_base refuses those votes (27bd word followed by jr $ra) and then
resolves VMANAGER to the true base 0x10668.

Usage:
    python3 scripts/probe_psylib_bases.py <lib> [module ...]
"""
import os
import struct
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import omf_pubsyms as op  # noqa: E402

from probe_psylib_chunks import module_chunks  # noqa: E402


def prologue_positions(d, lo, hi):
    pos = []
    for p in range(lo, hi - 4, 2):
        if (struct.unpack_from("<I", d, p)[0] >> 16) == 0x27BD:
            pos.append(p)
    return pos


def main(argv):
    lib = op.PsyqLib(argv[1])
    d = lib.data
    rx = None
    if len(argv) > 2:
        import re
        rx = re.compile(argv[2])
    for m in lib.modules:
        if rx and not rx.search(m.name):
            continue
        info = module_chunks(d, m)
        if info is None or info["first_blob"] is None:
            continue
        defs = [(n, off) for n, k, a, b, off in op.def_map(m)
                if k == 0x0C and b == 2]
        if not defs:
            continue
        ts = m.table_start or (m.offset + m.size)
        pros = prologue_positions(d, info["first_blob"], min(ts, len(d) - 4))
        pset = set(pros)
        votes = Counter()
        detail = []
        for n, off in defs:
            cands = [p - off for p in pros
                     if info["first_blob"] <= p - off <= p]  # base <= p
            cands = [c for c in cands if c >= info["first_blob"]]
            votes.update(cands)
            detail.append((n, off, cands))
        peaks = [(base, cnt) for base, cnt in votes.most_common(8) if cnt > 1]
        print(f"module {m.name!r} blob1={info['first_blob']:#x} "
              f"defs={len(defs)} prologues={len(pros)}")
        for base, cnt in peaks:
            names = [n for n, off, c in detail if base in c]
            pre = sum(1 for n, off, c in detail if (base + 12) in
                      {x + off for x in [base]})  # placeholder, see below
            print(f"  base {base:#x}: {cnt}/{len(defs)} defs "
                  f"(delta {base - info['first_blob']:+#x}) {names[:6]}")
        # unexplained defs
        explained = set()
        for base, _cnt in peaks:
            for n, off, c in detail:
                if base in c:
                    explained.add(n)
        unex = [(n, hex(off)) for n, off, c in detail if n not in explained]
        if unex:
            print(f"  unexplained: {unex[:8]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

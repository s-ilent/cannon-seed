#!/usr/bin/env python3
"""probe_libsn_paths.py - why the LNK walk fails on LIBSN.LIB, measured.

The 0859 window banked "LIBGCC2 maps to NO module in LIBSN.LIB (its path
records do not parse under the LNK walk)".  This probe measures, per
module: every 0x1C-tagged record candidate (tag, z, ln, payload class),
the LNK-walk outcome, the first_code_chunk outcome, and the def-row
inventory -- to pin the exact parser divergence before any tool change.
"""
import struct
import sys
from collections import Counter

sys.path.insert(0, "/home/z/my-project/cannon-seed/tools")
import omf_pubsyms as op  # noqa: E402

LIB = "/home/z/psyq/3.3/PSX/LIB/LIBSN.LIB"


def all_1c_records(d, lo, hi):
    """Every 0x1C byte whose next 3 bytes fit the structural record shape
    (any tag/z; 8 <= ln <= 0x40; printable payload)."""
    out = []
    o = lo
    while o < hi - 4:
        if d[o] == 0x1C:
            ln = d[o + 3]
            if 0x08 <= ln <= 0x40 and o + 4 + ln <= hi:
                pb = d[o + 4:o + 4 + ln]
                if all(32 <= c < 127 for c in pb):
                    out.append((o, d[o + 1], d[o + 2], ln, pb.decode()))
                    o += 4 + ln
                    continue
        o += 1
    return out


def walk_to_paths(d, mod):
    """Replicate last_path's LNK-record walk; report where it lands."""
    end = mod.offset + mod.size
    o = mod.offset + 20
    while o < end and d[o] != 0x00:
        o += 1 + d[o]
    if o >= end or d[o] != 0x00:
        return ("no-name-term", None)
    o += 1
    if d[o:o + 3] != b"LNK":
        return ("no-LNK", None)
    o += 3
    steps = 0
    while o < end:
        ln = d[o]
        p = o + 1 + ln
        if p >= end:
            return ("ran-off-end", steps)
        if d[p] == 0x1C:
            return ("landed-1C", o)
        o = p + 6
        steps += 1
    return ("zone-exhausted", steps)


def main():
    lib = op.PsyqLib(LIB)
    d = lib.data
    print(f"modules: {len(lib.modules)}")
    zc = Counter()
    tags = Counter()
    pathmods = []
    for m in lib.modules:
        end = m.offset + m.size
        recs = all_1c_records(d, m.offset, end)
        for _o, tag, z, ln, pb in recs:
            tags[tag] += 1
            zc[z] += 1
        outcome, where = walk_to_paths(d, m)
        blob, pe, np_ = op.first_code_chunk(d, m)
        defs = op.def_map(m)
        ndef = sum(1 for _n, k, _a, b, _off in defs if k == 0x0C and b == 2)
        if recs:
            pathmods.append((m.name, recs))
        print(f"{m.name:<12} off=0x{m.offset:06x} sz=0x{m.size:05x} "
              f"walk={outcome:<13} blob={'0x%06x' % blob if blob else 'None':>8} "
              f"paths={np_} defs(b2)={ndef} "
              f"1C-recs={[(hex(t), hex(z), ln, pb[-14:]) for _o, t, z, ln, pb in recs[:3]]}")
    print("\ntag population:", {hex(k): v for k, v in tags.most_common()})
    print("z population:  ", {hex(k): v for k, v in zc.most_common()})
    print(f"\nmodules WITH 0x1C path records: {len(pathmods)}")
    for name, recs in pathmods:
        print(f"  {name}: {[pb for _o, _t, _z, _l, pb in recs]}")


if __name__ == "__main__":
    main()

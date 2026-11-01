#!/usr/bin/env python3
"""probe_psylib_hilo - the %hi/%lo fixup-algebra probe (cron-20261101-0921).

Model under test (from probe_psylib_fixsite.py observations):
  t=0x52 = %hi site, t=0x54 = %lo site (pairs 4 bytes apart, same target),
  t=0x4a = 26-bit jump-field site;
  target = 2c0 u32 = row ORDINAL (the a-field namespace), possibly with a
  trailing 2c4 (w, v) annotation whose meaning is measured here.

The algebra: a pre-link lui/lw pair in the code composes
  A = (hi_imm << 16) + sext16(lo_imm).
If the fixup stream patches these with symbol S at image offset off(S),
then A == base + off(S) + delta for a per-pair constant delta and the
MODULE base. Histogramming A - off(ord) over all (code pair, fixup pair)
combinations must show a dominant value = base (+delta) if the model is
right - the vote-free mechanical route to the per-cluster base.

Usage:
    python3 scripts/probe_psylib_hilo.py <lib> <module-regex>
"""
import os
import re
import struct
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import omf_pubsyms as op  # noqa: E402
from probe_psylib_fixsite import parse_fixups  # noqa: E402

LOAD_OPS = frozenset((0x20, 0x21, 0x23, 0x24, 0x25))  # lb/lh/lwl/lw/lbu/lhu
STORE_OPS = frozenset((0x28, 0x29, 0x2b))             # sb/sh/swl/sw
BRANCH0 = frozenset((0x04, 0x05, 0x06, 0x07))         # beq/bne/blez/bgtz


def sext16(x):
    return x - 0x10000 if x & 0x8000 else x


def code_hilo_pairs(d, lo, hi):
    """Consecutive [lui][mem] word pairs in [lo, hi)."""
    out = []
    hi = min(hi, len(d) - 8)
    for p in range(lo, hi, 4):
        w1 = struct.unpack_from("<I", d, p)[0]
        w2 = struct.unpack_from("<I", d, p + 4)[0]
        if w1 >> 26 == 0x0F and (w2 >> 26) in (LOAD_OPS | STORE_OPS | BRANCH0 | {0x09, 0x0C, 0x0D}):
            h = w1 & 0xFFFF
            l = w2 & 0xFFFF
            out.append((p, (h << 16) + sext16(l), w1, w2))
    return out


def main(argv):
    libpath, rx = argv[1], argv[2]
    lib = op.PsyqLib(libpath)
    d = lib.data
    for m in lib.modules:
        if not re.search(rx, m.name):
            continue
        blob, pe, _np = op.first_code_chunk(d, m)
        if blob is None:
            continue
        end = m.offset + m.size
        ts = m.table_start or end
        val = op.solve_def_base_valid(d, m)
        base = val[0][0] if val else None

        # the a-ordinal map: every def row (both classes) keyed by a
        a2row = {}
        for s in m.symbols:
            if s.kind in (0x0C, 0x30):
                a2row.setdefault(s.a, []).append((s.kind, s.b, s.offset, s.name))
        print(f"=== {m.name} base={base and hex(base)} blob1={blob:#x} "
              f"rows={len(m.symbols)} distinct-a={len(a2row)}")
        print(f"  a-map (a: [(kind,b,off,name)]):")
        for a in sorted(a2row):
            rows = a2row[a]
            print(f"    a={a:<3} " + " | ".join(
                f"k={k:#04x} b={b} off={off:#x} {n}" for k, b, off, n in rows))

        # fixup pairs with ordinals
        evs = parse_fixups(d, pe, ts)
        pairs = []
        cur = None
        for e in evs:
            if e[0] == "0a":
                if cur:
                    pairs.append(cur)
                cur = {"site": e[1][1], "t": e[1][0], "ords": [], "cls": []}
            elif cur is not None:
                if e[0] == "2c0":
                    cur["ords"].append(e[1])
                elif e[0] == "2c4":
                    cur["cls"].append((e[1][0], e[1][1]))
                elif e[0] in ("02", "06"):
                    pairs.append(cur)
                    cur = None
        if cur:
            pairs.append(cur)

        hi_pairs = pairs  # t=0x52 (assume %hi)
        lo_pairs = pairs  # t=0x54 (%lo) - separate lists below
        his = [p for p in pairs if p["t"] == 0x52 and p["ords"]]
        los = [p for p in pairs if p["t"] == 0x54 and p["ords"]]
        js = [p for p in pairs if p["t"] == 0x4a]
        print(f"  fixups: %hi={len(his)} %lo={len(los)} j={len(js)} "
              f"total={len(pairs)}")

        # code hi/lo pairs in the module's chunk range
        cp = code_hilo_pairs(d, blob, ts)
        print(f"  code lui+mem pairs: {len(cp)}")

        # THE HISTOGRAM: A - off(ord) over all (code pair, fixup pair)
        # combos, both as-is and minus the 2c4 v annotation
        hist = Counter()
        hist_v = Counter()
        for (_p, A, _w1, _w2) in cp:
            for fp in his + los:
                for o in fp["ords"]:
                    rows = a2row.get(o)
                    if not rows:
                        continue
                    for k, b, off, _n in rows:
                        hist[A - off] += 1
                        for w_, v in fp["cls"]:
                            hist_v[A - off - v] += 1
        print(f"  top A-off (no v): {[(hex(x), c) for x, c in hist.most_common(6)]}")
        print(f"  top A-off-v:      {[(hex(x), c) for x, c in hist_v.most_common(6)]}")
        if base is not None:
            print(f"  (known base {base:#x}; A-off-base should be the "
                  f"displacement delta)")
            near = [(hex(x), c) for x, c in hist.most_common(40)
                    if abs(x - base) < 0x400]
            print(f"  hist entries near base: {near[:8]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

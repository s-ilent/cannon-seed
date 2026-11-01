#!/usr/bin/env python3
"""probe_psylib_fixsite - the fixup-SITE origin probe (cron-20261101-0921).

The cron-20261101-0806 NEXT item (1): solve the per-module (and per-cluster)
def base from FIXUP-TARGET/DEF-OFFSET agreement - the mechanical route the
prologue vote could never take.

Model under test: the record-zone fixup stream is a sequence of
  [0a][t][u16 site]            the SITE record (where to patch)
  [2c0][u32 v]                 target = row ordinal (the a-field namespace)
  [2c4][u16 w][u32 raw]        target class w, value v=(raw>>8)&0xffff
  [02][u8 a][00]               short row-ordinal target form
where each 0a record pairs with the target record(s) that FOLLOW it.

Hypotheses for the site origin O (file(O + site) should be a relocatable
word - jal/lui opcode - for jal/lui-class sites):
  H1 O = def base (the class-2 image root, base+off = file for defs)
  H2 O = first 02-chunk data start (blob1)
  H3 O = per-segment: the nearest preceding 06 [seg] marker selects the
        segment and RE-ROOTS the site counter (mid-zone re-selections!)

Hypothesis for the VALUE side (the algebra that solves the base):
  H4 a jal word at file(O + site) encodes the ABSOLUTE archive address of
     the target: imm<<2 == base + t_off (t_off = the paired 2c4 w=2 v or
     the def offset of the paired row-ordinal target) => base = (imm<<2) - t_off
     directly, one equation per jal site, over-determined and vote-free.

Usage:
    python3 scripts/probe_psylib_fixsite.py <lib> <module-regex> [origin]
"""
import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import omf_pubsyms as op  # noqa: E402

OP_NAMES = {0x0C: "jal", 0x0F: "lui", 0x09: "addiu", 0x23: "lw", 0x2B: "sw",
            0x04: "beq", 0x05: "bne", 0x02: "j", 0x03: "jal-r"}


def parse_fixups(d, o, end):
    """Walk [o, end) as the fixup record stream.

    Returns a list of events: ('06', seg) / ('02', size) /
    ('0a', site_off, t, pos) / ('2c0', v, pos) / ('2c4', w, v, pos) /
    ('02s', a, pos) / ('?', pos). Targets attach to the most recent 0a."""
    evs = []
    while o < end:
        b = d[o]
        if b == 0x06 and o + 3 <= end and d[o + 2] == 0x00:
            evs.append(("06", d[o + 1], o))
            o += 3
        elif b == 0x02 and o + 3 <= end and d[o + 1] == 0x00 and d[o + 2] in (0x00,):
            evs.append(("02s", None, o))
            o += 3
        elif b == 0x02 and o + 3 <= end:
            size = struct.unpack_from("<H", d, o + 1)[0]
            evs.append(("02", size, o))
            o += 3 + size
        elif b == 0x0A and o + 4 <= end:
            t = d[o + 1]
            site = struct.unpack_from("<H", d, o + 2)[0]
            evs.append(("0a", (t, site), o))
            o += 4
        elif b == 0x2C and o + 6 <= end and d[o + 1] == 0x00:
            v = struct.unpack_from("<I", d, o + 2)[0]
            evs.append(("2c0", v, o))
            o += 6
        elif b == 0x2C and o + 9 <= end and d[o + 1] == 0x04:
            w = struct.unpack_from("<H", d, o + 2)[0]
            raw = struct.unpack_from("<I", d, o + 4)[0]
            evs.append(("2c4", (w, (raw >> 8) & 0xFFFF, raw), o))
            o += 9
        else:
            evs.append(("?", None, o))
            o += 1
    return evs


def word_class(d, p):
    if p < 0 or p + 4 > len(d):
        return "oob"
    w = struct.unpack_from("<I", d, p)[0]
    if w == 0:
        return "nop"
    opc = w >> 26
    if opc == 0:
        return f"spec{w & 0x3f:#04x}"
    return OP_NAMES.get(opc, f"op{opc:#04x}")


def pr_zone(d, o, end):
    """Byte map of [o, end): [(lo, hi, kind)] with kind in
    rec06/rec0a/rec2c/rec02hdr/payload/'?'-blob. Every byte is covered."""
    out = []
    while o < end:
        b = d[o]
        if b == 0x06 and o + 3 <= end and d[o + 2] == 0x00:
            out.append((o, o + 3, "rec06"))
            o += 3
        elif b == 0x0A and o + 4 <= end:
            out.append((o, o + 4, "rec0a"))
            o += 4
        elif b == 0x2C and o + 6 <= end and d[o + 1] == 0x00:
            out.append((o, o + 6, "rec2c0"))
            o += 6
        elif b == 0x2C and o + 9 <= end and d[o + 1] == 0x04:
            out.append((o, o + 9, "rec2c4"))
            o += 9
        elif b == 0x02 and o + 3 <= end:
            size = struct.unpack_from("<H", d, o + 1)[0]
            out.append((o, o + 3, "rec02hdr"))
            if size:
                out.append((o + 3, min(o + 3 + size, end), "payload"))
                o += 3 + size
            else:
                o += 3
        else:
            start = o
            o += 1
            out.append((start, o, "blob?"))
    return out


def main(argv):
    libpath = argv[1]
    rx = argv[2]
    import re
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
        defs = [(s.name, s.a, s.offset) for s in m.symbols if s.kind == 0x0C and s.b == 2]
        a2off = {a: off for _n, a, off in defs}
        print(f"=== {m.name} mod={m.offset:#x} blob1={blob:#x} table={ts:#x} "
              f"defs={len(defs)}")

        # the known-good base (all-landings-valid) for scoring
        val = op.solve_def_base_valid(d, m)
        base = val[0][0] if val else None
        print(f"  base(all-valid)={base and hex(base)} law={val and len(val)}")

        evs = parse_fixups(d, pe, ts)
        from collections import Counter
        print(f"  events: {Counter(e[0] for e in evs)}")

        # group events into fixup pairs: 0a then following targets (up to
        # the next 0a/06/02-chunk)
        pairs = []
        cur = None
        last06 = None
        for e in evs:
            if e[0] == "06":
                last06 = e
            elif e[0] == "0a":
                if cur:
                    pairs.append(cur)
                cur = {"site": e[1][1], "t": e[1][0], "pos": e[2], "t06": last06,
                       "ords": [], "cls": []}
            elif cur is not None:
                if e[0] == "2c0":
                    cur["ords"].append(e[1])
                elif e[0] == "2c4":
                    cur["cls"].append((e[1][0], e[1][1]))
                elif e[0] == "02s":
                    pass
                elif e[0] in ("02", "06"):
                    pairs.append(cur)
                    cur = None
                    if e[0] == "06":
                        last06 = e
        if cur:
            pairs.append(cur)
        print(f"  fixup pairs: {len(pairs)}")

        # H1/H2/H3: where do sites land under each origin?
        for name, O in (("base", base), ("blob1", blob)):
            if O is None:
                continue
            hits = Counter()
            for p in pairs:
                wc = word_class(d, O + p["site"])
                hits[wc.split(":")[0]] += 1
            print(f"  origin {name} ({O:#x}): site-word classes {dict(hits)}")

        # H3: segment re-rooting - site decreases vs 06 markers
        dec = 0
        prev = None
        seg_sites = {}
        curseg = None
        for p in pairs:
            seg_sites.setdefault(p["t06"][1] if p["t06"] else None, []).append(p["site"])
            if prev is not None and p["site"] < prev:
                dec += 1
            prev = p["site"]
        print(f"  site decreases: {dec} / {len(pairs)}; 06 segs seen: "
              f"{sorted(k for k in seg_sites if k is not None)}")

        # H4b: pre-link jal encoding test. For every w=2 pair, read the word
        # at base+site (the flat image); if j/jal, is imm<<2 == v?
        n_j = n_abs = n_rel = 0
        rel_hits = []
        for p in pairs:
            for w_, v in p["cls"]:
                if w_ != 2:
                    continue
                pos = base + p["site"] if base else None
                if pos is None or pos + 4 > len(d):
                    continue
                word = struct.unpack_from("<I", d, pos)[0]
                if word >> 26 in (0x02, 0x03):  # j / jal
                    n_j += 1
                    imm = word & 0x3FFFFFF
                    if (imm << 2) == v:
                        n_rel += 1
                        rel_hits.append((p["site"], v, pos, word))
                    elif (imm << 2) == base + v:
                        n_abs += 1
        print(f"  [flat-base] j/jal sites: {n_j}; imm<<2==v (section-rel): "
              f"{n_rel}; imm<<2==base+v (abs): {n_abs}")
        for rh in rel_hits[:10]:
            print(f"    REL site={rh[0]:#06x} v={rh[1]:#06x} pos={rh[2]:#x} "
                  f"word={rh[3]:#010x}")

        # H5: the flat byte map of the module image. Walk the module's
        # zone+chunks classifying every byte: 06/0a/2c/02-header record
        # bytes vs 02-payload. Then classify every site landing.
        zone = pr_zone(d, pe, ts)
        def land_class(pos):
            if pos < 0 or pos >= len(d):
                return "oob"
            for (lo, hi, kind) in zone:
                if lo <= pos < hi:
                    return kind
            return "??"
        lc = Counter()
        for p in pairs:
            lc[land_class(base + p["site"])] += 1
        print(f"  [flat-base] site landing classes: {dict(lc)}")

        # H7: eyeball the first N sites' words vs their paired targets
        for i, p in enumerate(pairs[:32]):
            pos = base + p["site"]
            wc = word_class(d, pos) if base else "?"
            tg = []
            if p["ords"]:
                tg.append(f"ord={p['ords']}")
            tg += [f"w={w} v={v:#x}" for w, v in p["cls"]]
            print(f"    site[{i}] {p['site']:#06x} t={p['t']:#x} pos={pos and hex(pos)} "
                  f"word@base={wc:<10} targets: {' '.join(tg)}")

        # site-decrease neighborhoods: the per-cluster boundaries
        prev = None
        for i, p in enumerate(pairs):
            if prev is not None and p["site"] < prev:
                lo = max(0, i - 2)
                seg = f"seg={p['t06'][1]}@{p['t06'][2]:#x}" if p["t06"] else "seg=?"
                nb = ", ".join(f"{q['site']:#x}(t={q['t']:#x})"
                               for q in pairs[lo:i + 3])
                print(f"  DECREASE at pair {i}: site {prev:#x} -> {p['site']:#x} "
                      f"(t={p['t']:#x}, {seg}); neighbors: {nb}")
            prev = p["site"]
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

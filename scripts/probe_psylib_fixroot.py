#!/usr/bin/env python3
"""probe_psylib_fixroot - solve the per-run fixup ROOT from jump-fixup
agreement (cron-20261101-0921).

Model (probe_psylib_fixsite.py + probe_psylib_hilo.py findings):
  - the record-zone fixup stream is [0a t site][2c0 row-ord][2c4 w v]...
    where the 2c0 u32 indexes the module's SYMBOL TABLE rows and the 2c4
    (w, v) carries a class-relative value (v = (raw>>8)&0xffff);
  - t=0x52 %hi / t=0x54 %lo (pairs 4 apart, same row), t=0x4a jump field;
  - 06 [seg] markers RE-ROOT the site counter (site decreases coincide
    with them: VMANAGER 3 decreases at seg2@0x1165e, seg0@0x1777e x2).

THE ALGEBRA: for a jump fixup, the site's pre-link word is j/jal with
imm<<2 == ROOT + v (the pre-linked per-chunk class-2 address of the
target). Every jump fixup in a run votes root = imm<<2 - v; a consistent
winner = the run's class-2 root - THE MECHANICAL BASE ROUTE the 0806
window asked for (fixup-target/def-offset agreement).

Site-counter candidates: (a) all-bytes from the run's chunk start,
(b) payload-only cumulative from the module's first chunk.
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


def sext16(x):
    return x - 0x10000 if x & 0x8000 else x


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
        rows = m.symbols

        # fixup runs: split at 06 markers and 02-chunk headers
        evs = parse_fixups(d, pe, ts)
        runs = []
        cur = {"root06": None, "chunks": [], "fix": []}
        for e in evs:
            if e[0] == "06":
                if cur["fix"]:
                    runs.append(cur)
                    cur = {"root06": e, "chunks": [], "fix": []}
                else:
                    cur["root06"] = e
            elif e[0] == "02":
                if cur["fix"]:
                    runs.append(cur)
                    cur = {"root06": None, "chunks": [e[1]], "fix": []}
                else:
                    cur["chunks"].append(e[1])
            elif e[0] == "0a":
                cur["fix"].append({"site": e[1][1], "t": e[1][0],
                                   "ords": [], "cls": [], "pos": e[2]})
            elif e[0] in ("2c0", "2c4") and cur["fix"]:
                f = cur["fix"][-1]
                if e[0] == "2c0":
                    f["ords"].append(e[1])
                else:
                    f["cls"].append((e[1][0], e[1][1]))
        if cur["fix"]:
            runs.append(cur)

        print(f"=== {m.name} base={base and hex(base)} blob1={blob:#x} "
              f"runs={len(runs)}")

        for ri, run in enumerate(runs):
            jf = [f for f in run["fix"] if f["t"] == 0x4A and f["cls"]]
            hif = [f for f in run["fix"] if f["t"] == 0x52 and f["ords"]]
            lof = [f for f in run["fix"] if f["t"] == 0x54 and f["ords"]]
            print(f"  run {ri}: 06={run['root06'] and (hex(run['root06'][1]), hex(run['root06'][2]))} "
                  f"chunks={[hex(c) for c in run['chunks']]} "
                  f"fix={len(run['fix'])} (j={len(jf)} hi={len(hif)} lo={len(lof)})")

            # site-counter candidates: all-bytes from each candidate origin
            cands = []
            if run["chunks"]:
                for c in run["chunks"]:
                    cands.append((f"chunk@{c:#x}", c))
            if base:
                cands.append((f"base={base:#x}", base))
            cands.append((f"blob1={blob:#x}", blob))
            for cname, O in cands:
                jroots = Counter()
                nj = 0
                for f in jf:
                    for _w, v in f["cls"]:
                        pos = O + f["site"]
                        if pos + 4 > len(d):
                            continue
                        word = struct.unpack_from("<I", d, pos)[0]
                        if word >> 26 in (0x02, 0x03):
                            nj += 1
                            jroots[(word & 0x3FFFFFF) << 2] += 1
                top = jroots.most_common(3)
                print(f"    [{cname:>18}] j-words={nj}/{len(jf)} "
                      f"imm<<2 top: {[(hex(x), c) for x, c in top]}")

            # %hi/%lo algebra: composed address vs row def offset
            # zip hi/lo fixups in order (they strictly alternate)
            if hif and lof:
                votes = Counter()
                n_ok = 0
                for hf, lf in zip(hif, lof):
                    if abs(hf["site"] - lf["site"]) != 4:
                        continue
                    row_i = hf["ords"][0]
                    if row_i >= len(rows):
                        continue
                    s = rows[row_i]
                    if s.kind != 0x0C or s.b != 2:
                        continue
                    n_ok += 1
                    for cname, O in cands:
                        pos = O + hf["site"]
                        if pos + 8 > len(d):
                            continue
                        w1 = struct.unpack_from("<I", d, pos)[0]
                        w2 = struct.unpack_from("<I", d, pos + 4)[0]
                        if w1 >> 26 == 0x0F:
                            A = ((w1 & 0xFFFF) << 16) + sext16(w2 & 0xFFFF)
                            votes[(A - s.offset, cname)] += 1
                print(f"    hi/lo resolvable={n_ok}; votes (A-off, origin): "
                      f"{[(hex(a), c, n) for (a, c), n in votes.most_common(4)]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

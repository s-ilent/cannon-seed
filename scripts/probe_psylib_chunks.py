#!/usr/bin/env python3
"""probe_psylib_chunks - the PSYLIB chunk-grammar probe (window cron-20261101-0651).

The banked cron-20261101-0536 NEXT item: pin the chunk grammar between the LNK
table and the symbol ROW STREAM, so the tool can eventually emit archive file
offsets directly. This probe measures, over every module of every provisioned
psyq 3.3 lib:

  1. the debug-path records: [0x1c][u8 tag][0x00][u8 len][path] - counted per
     module, walk validated (every step starts 0x1c, tag decreasing not required);
  2. the chunk zone: 06 xx 00 section markers + 02 [u16 size] data chunks;
     LAW UNDER TEST: the 02-chunk u16 size field bounds its data EXACTLY
     (the walk from the first post-path chunk must land on the next record);
  3. the record zone shapes seen on VMANAGER (0a/02-3byte/2c) - counted, not
     parsed to a law (the base-derivation question stays open);
  4. the def-row base: for every module with b=2 0x0c def rows, solve the
     flat base by maximizing addiu-sp (0x27bd....) prologue hits over the
     blob1..table_start span (both 2-mod-4 alignments), report
     (module, blob1_start, best_base, hits, defs, delta=base-blob1).

Usage:
    python3 scripts/probe_psylib_chunks.py [lib ...]
Defaults to the psyq 3.3 LIB dir when run from the repo.
"""
import glob
import os
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import omf_pubsyms as op  # noqa: E402

DEFAULT_LIBS = sorted(glob.glob(
    "/home/z/my-project/psyq/3.3/PSX/LIB/*.LIB"))


def walk_paths(d, o, end):
    """Walk [0x1c][u8 tag][0x00][u8 len][path] records from o. Returns (count, o)."""
    n = 0
    while o < end and d[o] == 0x1C and o + 4 <= end:
        tag = d[o + 1]
        z = d[o + 2]
        ln = d[o + 3]
        if z != 0x00 or not (0x08 <= ln <= 0x40) or o + 4 + ln > end:
            break
        path = d[o + 4:o + 4 + ln]
        if not all(32 <= c < 127 for c in path):
            break
        n += 1
        o += 4 + ln
    return n, o


def first_chunk_after_paths(d, o, end):
    """From the end of the path region, walk the leading 06 xx 00 markers and
    return the file offset of the FIRST 02-chunk's data (None if none)."""
    markers = []
    while o + 3 <= end and d[o] == 0x06 and d[o + 2] == 0x00 and d[o + 1] != 0x00:
        markers.append(d[o + 1])
        o += 3
    first = None
    while o + 3 <= end:
        if d[o] == 0x06 and d[o + 2] == 0x00:
            markers.append(d[o + 1])
            o += 3
            continue
        if d[o] == 0x02:
            size = struct.unpack_from("<H", d, o + 1)[0]
            if size == 0:
                break
            if first is None:
                first = o + 3
            o += 3 + size
            continue
        break
    return first, o, markers


def module_chunks(d, mod):
    """Re-derive (paths_end, first_blob, chunk_zone_end, markers) for a module."""
    end = mod.offset + mod.size
    o = mod.offset + 20
    while o < end and d[o] != 0x00:
        nm = d[o]
        o += 1 + nm
    if o < end and d[o] == 0x00:
        o += 1
    if d[o:o + 3] != b"LNK":
        return None
    o += 3
    while o < end:
        ln = d[o]
        p = o + 1 + ln
        if p >= end or d[p] == 0x1C:
            o = p  # the 0x1c doubles as the first path record's kind byte
            break
        o = p + 6
    np_, o = walk_paths(d, o, end)
    first, o, markers = first_chunk_after_paths(d, o, end)
    return dict(paths=np_, paths_end=o, first_blob=first, zone_end=o,
                markers=markers)


def solve_base(d, mod, lo, hi):
    """Maximize 0x27bd.... prologue hits for b=2 def rows over [lo, hi)."""
    defs = [(n, off) for n, k, a, b, off in op.def_map(mod)
            if k == 0x0C and b == 2]
    if not defs:
        return None
    best = None
    for base in range(lo, hi):
        hits = 0
        for _n, off in defs:
            p = base + off
            if lo <= p <= hi - 4 and (struct.unpack_from("<I", d, p)[0] >> 16) == 0x27BD:
                hits += 1
        if best is None or hits > best[0]:
            best = (hits, base)
    return dict(hits=best[0], base=best[1], defs=len(defs))


def main(argv):
    libs = argv[1:] or DEFAULT_LIBS
    for path in libs:
        try:
            lib = op.PsyqLib(path)
        except (OSError, ValueError) as e:
            print(f"# {path}: {e}")
            continue
        d = lib.data
        n_mod = n_02 = n_02_exact = n_paths_tot = 0
        bases = []
        for m in lib.modules:
            info = module_chunks(d, m)
            if info is None or info["first_blob"] is None:
                continue
            n_mod += 1
            n_paths_tot += info["paths"]
            # 02-law probe: from first_blob, re-walk 02-chunks; the walk must
            # land either on another record or exactly at a marker/zone end;
            # count a module as EXACT when its leading 02-chunk's size lands
            # on a non-code record boundary (06/0a/2c/02) or a known stop.
            o = info["first_blob"]
            end = m.offset + m.size
            ok = False
            while o + 3 <= end:
                if d[o] == 0x02:
                    size = struct.unpack_from("<H", d, o + 1)[0]
                    if size == 0:
                        break
                    o2 = o + 3 + size
                    if o2 + 3 <= end and d[o2] in (0x02, 0x06):
                        n_02 += 1
                        ok = True
                        o = o2
                        continue
                    break
                break
            if ok:
                n_02_exact += 1
            # base solve for code-def modules (bounded span keeps this fast)
            ts = m.table_start or end
            if ts - info["first_blob"] < 0x8000 and m.offset + m.size <= len(d):
                sol = solve_base(d, m, info["first_blob"], min(ts, len(d) - 4))
                if sol and sol["hits"] * 2 >= sol["defs"]:
                    bases.append((m.name, info["first_blob"], sol))
        print(f"# {os.path.basename(path)}: {n_mod} chunked modules, "
              f"{n_paths_tot} path records, 02-chain-exact {n_02_exact}/{n_mod}")
        for name, blob, sol in bases:
            print(f"  {name:10s} blob1={blob:#08x} base={sol['base']:#08x} "
                  f"delta={sol['base'] - blob:+#x} hits={sol['hits']}/{sol['defs']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

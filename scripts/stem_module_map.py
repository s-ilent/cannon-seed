#!/usr/bin/env python3
"""stem->OMF-module map + multi-module def-row drift check.

The census "member" column is the OMF debug-path SOURCE-FILE STEM; the
def maps live per OMF module.  This probe maps stems to modules via the
path records (the module's OWN source is the LAST path record), solves
each module's def base (op.solve_def_base, the epilogue-refusing vote),
and re-runs the verbatim test over the union of the stem's def maps:

    implied_base = census_addr - archive_file_offset

ONE constant across a target's rows = byte-verbatim placement
(trustworthy, adoptable); a spread = the game-compiled reordering
profile (NOT adoptable from census rows).
"""
import re
import sys
from collections import defaultdict

sys.path.insert(0, "/home/z/my-project/cannon-seed/tools")
import omf_pubsyms as op  # noqa: E402

REPO = "/home/z/my-project/cannon-seed"
ROW = re.compile(
    r"^//\s+(0x[0-9a-fA-F]+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*(adoptable)?"
    r"\s*(?:\(sig-db\s+(\w+)\))?")
TGT = re.compile(r"^// target:\s*(\S+)")


def last_path(data, mod):
    """The module's own source path = the LAST debug-path record."""
    end = mod.offset + mod.size
    o = mod.offset + 20
    while o < end and data[o] != 0x00:
        nm = data[o]
        o += 1 + nm
    if o < end and data[o] == 0x00:
        o += 1
    if data[o:o + 3] != b"LNK":
        return None
    o += 3
    while o < end:
        ln = data[o]
        p = o + 1 + ln
        if p >= end or data[p] == 0x1C:
            o = p
            break
        o = p + 6
    last = None
    # z-byte law (cron-20261102-1013): psyq = z 0x00, the GNU-compiled
    # LIBSN.LIB members = z 0x36 (42/42 LIBSN records, no other lib)
    while o < end and data[o] == 0x1C and o + 4 <= end:
        tag, z, ln = data[o + 1], data[o + 2], data[o + 3]
        if z not in (0x00, 0x36) or not (0x08 <= ln <= 0x40) \
                or o + 4 + ln > end:
            break
        pb = data[o + 4:o + 4 + ln]
        if not all(32 <= c < 127 for c in pb):
            break
        last = pb.decode()
        o += 4 + ln
    return last


def stem_map(path):
    lib = op.PsyqLib(path)
    out = defaultdict(set)
    for m in lib.modules:
        lp = last_path(lib.data, m)
        if not lp:
            continue
        leaf = lp.replace("\\", "/").rsplit("/", 1)[-1]
        out[leaf.rsplit(".", 1)[0].upper()].add(m.name)
    return out, lib


def load_census(stem, libname):
    rows = []
    cur = None
    for ln in open(REPO + "/config/sdk_members.txt", errors="replace"):
        m = TGT.match(ln)
        if m:
            cur = m.group(1)
            continue
        m = ROW.match(ln)
        if m and cur and m.group(2) == libname and m.group(3) == stem:
            rows.append((cur, int(m.group(1), 16), m.group(5)))
    return rows


def drift_check(libpath, libname, stem):
    smap, lib = stem_map(libpath)
    mods = sorted(smap.get(stem, ()))
    print(f"== {libname} stem {stem}: modules {mods or 'NONE'}")
    if not mods:
        return
    d = lib.data
    by_mod = {}
    for mn in mods:
        mod = next((m for m in lib.modules if m.name == mn), None)
        if mod is None:
            continue
        sol = op.solve_def_base(d, mod)
        if not sol:
            by_mod[mn] = None
            print(f"   {mn}: no solved base")
            continue
        base, strict, ndefs, npro = sol
        defs = {n: base + off for n, _k, _a, b, off in op.def_map(mod)
                if b == 2}
        by_mod[mn] = defs
        print(f"   {mn}: base=0x{base:x} strict={strict}/{ndefs} "
              f"prologues={npro} defs={len(defs)}")
    file_of = defaultdict(list)
    for mn, defs in by_mod.items():
        if defs:
            for n, f in defs.items():
                file_of[n].append(f)
    rows = load_census(stem, libname)
    per_t = defaultdict(list)
    for t, addr, sname in rows:
        if sname in file_of:
            per_t[t].append((addr, sname))
    for t in sorted(per_t):
        lst = per_t[t]
        cand = []
        for addr, sname in lst:
            cand.append(sorted({addr - f for f in file_of[sname]}))
        common = set(cand[0])
        for c in cand[1:]:
            common &= set(c)
        if common:
            print(f"   {t:<12} {len(lst)} rows -> VERBATIM-CONSISTENT "
                  f"base candidate(s): "
                  + " ".join(f"0x{b:08X}" for b in sorted(common)))
        else:
            lo = min(min(c) for c in cand)
            hi = max(max(c) for c in cand)
            print(f"   {t:<12} {len(lst)} rows -> SPREAD x{len(set(sum(cand, [])))} "
                  f"span 0x{hi - lo:x} - projection")


def main():
    drift_check("/home/z/psyq/3.3/PSX/LIB/LIBGS.LIB", "LIBGS", "SCLIB")
    drift_check("/home/z/psyq/3.3/PSX/LIB/LIBGS.LIB", "LIBGS", "EMULIB")
    drift_check("/home/z/psyq/3.3/PSX/LIB/LIBSN.LIB", "LIBSN", "LIBGCC2")


if __name__ == "__main__":
    sys.exit(main())

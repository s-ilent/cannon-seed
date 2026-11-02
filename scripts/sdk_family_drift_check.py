#!/usr/bin/env python3
"""VMANAGER curation cross-check: census row addresses vs archive def rows.

For every census row of a given (lib, member), reconstruct the implied
placement base  base = census_addr - (def_off - module_base)  using the
omf_pubsyms def map, and test whether all rows in a target agree on ONE
base.  One base = the whole-member slide placed a byte-verbatim archive
copy, so the archive symbol offsets ARE the game addresses (names
adoptable at the census addresses).  Drifting bases = the game-compiled
reordered copy (the cron-20261101-0151 profile) - census symbol
addresses are unreliable there and nothing may adopt them.
The census "member" column is the SOURCE-FILE STEM from the OMF debug
path (SCLIB.C -> "SCLIB"), NOT the OMF module name omf_pubsyms --module
filters on - for LIBSND VMANAGER the two coincide, for LIBGS SCLIB /
LIBSN LIBGCC2 / LIBGS EMULIB they do not (their def maps need the
stem->module path-record mapping, still open).

BANKED RESULTS (2026-11-02): VMANAGER drift spread 0x6194 over 25
def-mapped rows, all 4 census-bearing targets (g3_jp/g3org_jp/
mainmenu_jp/slps_00270); LIBCD SYS spread 0x9b4 x12 IDENTICAL on all 8
targets (the same recompiled libcd in every image).  Both families are
archive-layout projections - nothing adopts them from the census rows.
"""

import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path("/home/z/my-project/cannon-seed")
REPORT = REPO / "config" / "sdk_members.txt"
CURATED = REPO / "config" / "symbols.curated.txt"
LIB = "/home/z/psyq/3.3/PSX/LIB/LIBSND.LIB"
MODULE = "VMANAGER"
BASE = 0x10668

ROW = re.compile(
    r"^//\s+(0x[0-9a-fA-F]+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*(adoptable)?"
    r"\s*(?:\(sig-db\s+(\w+)\))?")
TGT = re.compile(r"^// target:\s*(\S+)")
ASSIGN = re.compile(r"^([A-Za-z_]\w*) = (0x[0-9a-fA-F]+);")


def def_map():
    out = subprocess.run(
        ["python3", "tools/omf_pubsyms.py", LIB, "--module", MODULE,
         "--file-offsets"], capture_output=True, text=True, check=True,
        cwd=REPO).stdout
    defs = {}
    for ln in out.splitlines():
        m = re.match(r"^\s*(\S+)\toff=(0x[0-9a-f]+)\tfile=(0x[0-9a-f]+)\t"
                     r"\[(pub|loc)\]", ln)
        if m:
            defs[m.group(1)] = (int(m.group(3), 16), m.group(4))
    return defs


def census_rows():
    rows = []  # (target, addr, sname, mark, adopt, sig)
    cur = None
    for ln in REPORT.read_text(errors="replace").splitlines():
        m = TGT.match(ln)
        if m:
            cur = m.group(1)
            continue
        m = ROW.match(ln)
        if m and cur and m.group(3) == MODULE:
            rows.append((cur, int(m.group(1), 16), m.group(5),
                         m.group(4), bool(m.group(6)), m.group(7) or "-"))
    return rows


def curated_names():
    names = defaultdict(set)
    addrs = defaultdict(set)
    cur = None
    for ln in CURATED.read_text(errors="replace").splitlines():
        m = TGT.match(ln)
        if m:
            cur = m.group(1)
            continue
        m = ASSIGN.match(ln)
        if m and cur:
            names[cur].add(m.group(1))
            addrs[cur].add(int(m.group(2), 16))
    return names, addrs


def main():
    defs = def_map()
    rows = census_rows()
    names, addrs = curated_names()
    print(f"def map: {len(defs)} symbols for {MODULE} (base 0x{BASE:x})")
    per_t = defaultdict(list)
    for t, addr, sname, mark, adopt, sig in rows:
        if sname in defs:
            fileo, kind = defs[sname]
            per_t[t].append((addr, sname, fileo, kind, mark, adopt, sig))
        else:
            per_t[t].append((addr, sname, None, "?", mark, adopt, sig))
    for t in sorted(per_t):
        lst = per_t[t]
        with_off = [(a, s, rel, k) for a, s, rel, k, _m, _ad, _s in lst
                    if rel is not None]
        bases = sorted({a - rel for a, s, rel, k in with_off})
        print(f"\n== {t}: {len(lst)} census rows, {len(with_off)} with def "
              f"offsets, {len(bases)} distinct implied base(s)")
        if len(bases) == 1:
            print(f"   VERBATIM-CONSISTENT base 0x{bases[0]:08X} - addresses "
                  f"trustworthy")
        elif len(bases) <= 6:
            from collections import Counter
            c = Counter(a - rel for a, s, rel, k in with_off)
            for b, n in c.most_common():
                print(f"   base 0x{b:08X} x{n}")
        else:
            lo, hi = min(bases), max(bases)
            print(f"   DRIFT spread 0x{lo:08X}..0x{hi:08X} "
                  f"(span 0x{hi - lo:x}) - recompiled profile")
        for a, s, rel, k, mark, adopt, sig in sorted(lst)[:60]:
            if rel is None:
                print(f"   0x{a:08X} {s:<22} no-def-row  mark={mark} "
                      f"{'adoptable' if adopt else ''} sig={sig}")
                continue
            b = a - rel
            state = []
            if s in names[t]:
                state.append("name-curated")
            if a in addrs[t]:
                state.append("addr-curated")
            print(f"   0x{a:08X} {s:<22} off=+0x{rel:04x} {k:<3} "
                  f"base=0x{b:08X} mark={mark} "
                  f"{'adoptable' if adopt else '          '} sig={sig} "
                  f"{' '.join(state)}")


if __name__ == "__main__":
    sys.exit(main())

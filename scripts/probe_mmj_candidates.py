#!/usr/bin/env python3
"""probe_mmj_candidates.py - triage a byte-copy hit inside a yaml row.

For a reported byte-copy hit (needle name/size, hit offset, containing row
offset): is the surrounding region a contiguous run of recognisable sdk-code
bytes (a hidden code block -> re-carve-worthy) or an isolated coincidence
among pointer/table data (-> bank only)?  Method: (1) dump the 0x40 bytes
around the hit; (2) sweep the WHOLE containing row with a 0x10-B needle
threshold to see if MORE landed units hide inside it (a cluster is the
data_80066CF4 signature).

COORDINATE LAW (2026-10-29, cron-202610290525): yaml offsets are FILE offsets
into build/<t>.bin (the ld's AT() space; the PS-X EXE header is prepended on
top and is NOT part of the payload coordinate space). The fifteenth-return
run of this probe added EXE_HDR to every needle/hit - reading everything
0x800 late - the exact graveyard_sweep bug class fixed in cron-202610291209;
its two mainmenu_jp "hidden-code container" verdicts (SetFarColor inside
data_8004E4E4-claimed 0x52E0C, SsVabTransCompleted inside
data_80093EDC-claimed 0x657FC) were triage of SHIFTED positions and are
VOID: the corrected x8 sweep finds ZERO data-row hits in any target.
PARSE LAW (same window): the yaml writer emits aligned rows like
"[0xF9B8, c,   func_80031688]"; a ", " regex silently drops them (4 rows per
target) and their spans re-attribute to the preceding row - both tools now
parse with \\s* after the commas.

Usage: python3 scripts/probe_mmj_candidates.py <target> <hit_off> <row_off>
       (offsets in yaml/file coordinates, e.g. 0x52E0C 0x528F4)
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ROW = re.compile(r"^\s*- \[(0x[0-9A-Fa-f]+),\s*(asm|c|data),\s*([A-Za-z_][\w.]*)\]")


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        raise SystemExit(2)
    target = sys.argv[1]
    hit = int(sys.argv[2], 16)
    row_off = int(sys.argv[3], 16)

    bin_ = (REPO / f"build/{target}.bin").read_bytes()
    rows = []
    for ln in (REPO / f"config/splat.{target}.yaml").read_text().splitlines():
        m = ROW.match(ln)
        if m:
            rows.append((int(m.group(1), 16), m.group(2), m.group(3)))
    rows.sort()
    ext = {}
    for i, (off, kind, name) in enumerate(rows):
        end = rows[i + 1][0] if i + 1 < len(rows) else off
        ext[(off, name)] = end - off

    row = next((r for r in rows if r[0] == row_off), None)
    if row is None:
        print(f"no yaml row at 0x{row_off:X} in {target}")
        raise SystemExit(1)
    doff, dkind, dname = row
    dend = doff + ext[(doff, dname)]
    print(f"=== hit 0x{hit:X} inside {dkind}:{dname} "
          f"(0x{doff:X}..0x{dend:X}, 0x{ext[(doff, dname)]:X} B)")
    lo, hi = max(doff, hit - 0x20), min(dend, hit + 0x40)
    for a in range(lo, hi, 16):
        chunk = bin_[a : a + 16]
        print(f"  0x{a:X}: " + " ".join(f"{b:02x}" for b in chunk))
    # cluster probe: which landed c units (>=0x10) occur inside this row?
    c_rows = [(o, n) for (o, k, n) in rows if k == "c"]
    inside = []
    for co, cn in c_rows:
        cb = bin_[co : co + ext[(co, cn)]]
        if len(cb) < 0x10:
            continue
        pos = doff
        while True:
            pos = bin_.find(cb, pos, dend)
            if pos < 0:
                break
            inside.append((pos, cn, len(cb)))
            pos += 1
    inside.sort()
    print(f"  landed c units (>=0x10 B) inside {dname}: "
          f"{[(f'0x{o:X}', n, f'0x{s:X}') for o, n, s in inside] or 'NONE'}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""probe_mmj_candidates.py - triage the two mainmenu_jp re-carve candidates.

For each candidate hit, answer: is the surrounding region a contiguous run of
recognisable sdk-code bytes (a hidden code block -> re-carve-worthy) or an
isolated coincidence among pointer/table data (-> bank only)?  Method:
(1) dump the 0x40 bytes around the hit as words; (2) sweep the WHOLE
containing data row with a 0x10-B needle threshold to see if MORE landed
units hide inside it (a cluster is the data_80066CF4 signature).
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EXE_HDR = 0x800
ROW = re.compile(r"^\s*- \[(0x[0-9A-Fa-f]+), (asm|c|data), ([A-Za-z_][\w.]*)\]")

CANDIDATES = [
    ("SetFarColor", 0x20, 0x52E0C, "data_8007E4E4", 0x528F4),
    ("SsVabTransCompleted", 0x2C, 0x657FC, "data_80093EDC", 0x656FC),
]

bin_ = (REPO / "build/mainmenu_jp.bin").read_bytes()

# -- parse rows, take a 0x10 threshold inventory of the two data rows --------
rows = []
for ln in (REPO / "config/splat.mainmenu_jp.yaml").read_text().splitlines():
    m = ROW.match(ln)
    if m:
        rows.append((int(m.group(1), 16), m.group(2), m.group(3)))
rows.sort()
ext = {}
for i, (off, kind, name) in enumerate(rows):
    end = rows[i + 1][0] if i + 1 < len(rows) else off
    ext[(off, name)] = end - off

c_rows = [(o, n) for (o, k, n) in rows if k == "c"]
c_bytes = {n: bin_[EXE_HDR + o : EXE_HDR + o + ext[(o, n)]]
           for o, n in c_rows if ext[(o, n)] >= 0x10}

for name, size, hit, drow, doff in CANDIDATES:
    dend = doff + ext[(doff, drow)]
    print(f"=== {name} copy at 0x{hit:X} inside {drow} "
          f"(0x{doff:X}..0x{dend:X}, 0x{ext[(doff, drow)]:X} B)")
    lo, hi = max(doff, hit - 0x20), min(dend, hit + size + 0x20)
    for a in range(lo, hi, 16):
        chunk = bin_[EXE_HDR + a : EXE_HDR + a + 16]
        print(f"  0x{a:X}: " + " ".join(f"{b:02x}" for b in chunk))
    # cluster probe: which landed units (>=0x10) occur inside this data row?
    inside = []
    for cn, cb in c_bytes.items():
        pos = EXE_HDR + doff
        while True:
            pos = bin_.find(cb, pos, EXE_HDR + dend)
            if pos < 0:
                break
            inside.append((pos - EXE_HDR, cn, len(cb)))
            pos += 1
    inside.sort()
    print(f"  landed units (>=0x10 B) inside {drow}: "
          f"{[(f'0x{o:X}', n, f'0x{s:X}') for o, n, s in inside] or 'NONE'}")

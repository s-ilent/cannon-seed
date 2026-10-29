#!/usr/bin/env python3
"""graveyard_sweep.py - find landed-unit retail bytes hiding inside data rows.

The data_80066CF4 re-carve (45869f24) proved mainmenu_jp's framing-era data
rows can hide whole landed functions (the 0x160 GTE transform host at +8, the
0x110 composer head at the tail). This sweep asks, per target: does ANY landed
c row's retail byte run occur ELSEWHERE in the image, and if so, inside which
row class?  Hits inside data rows = re-carve candidates (the graveyard
sweep goal); hits inside asm rows = flip candidates (wave-3/4 class);
hits inside other c rows = already-landed copies (informational).

Search space = build/<t>.bin (byte-identical to retail per verify; witness
gates the run). Row extents = next-row offset minus row offset (the yaml rows
are contiguous). Usage: python3 scripts/graveyard_sweep.py <target> [<target>...]
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EXE_HDR = 0x800  # historical: the fifteenth-return +0x800 needle bug (fixed; see below)
# 2026-10-29 (cron-202610290525): \s* after each comma - the yaml writer emits
# aligned rows like "[0xF9B8, c,   func_80031688]" (extra spaces before the
# name); the old ", " pattern silently DROPPED those rows, so every landed c
# row formatted that way went invisible and its span was re-attributed to the
# preceding asm row - all nine "0x2c tail flip candidates" of the
# cron-202610291209 inventory were these already-landed rows (phantom flips).
ROW = re.compile(r"^\s*- \[(0x[0-9A-Fa-f]+),\s*(asm|c|data),\s*([A-Za-z_][\w.]*)\]")
MIN_EXTENT = 0x20  # skip degenerate slivers (8-B code snippets recur trivially)


def parse_rows(target):
    rows = []
    for ln in (REPO / f"config/splat.{target}.yaml").read_text().splitlines():
        m = ROW.match(ln)
        if m:
            rows.append((int(m.group(1), 16), m.group(2), m.group(3)))
    rows.sort()
    out = []
    for i, (off, kind, name) in enumerate(rows):
        end = rows[i + 1][0] if i + 1 < len(rows) else None
        ext = (end - off) if end else 0
        out.append((off, kind, name, ext))
    return out


def container(rows, off):
    for r in rows:
        if r[0] <= off < r[0] + max(r[3], 1):
            return r
    return None


def sweep(target):
    binp = REPO / f"build/{target}.bin"
    bin_ = binp.read_bytes()
    rows = parse_rows(target)
    c_rows = [(o, k, n, e) for o, k, n, e in rows if k == "c" and e >= MIN_EXTENT]
    print(f"=== {target}: {len(bin_)} bytes, {len(rows)} rows "
          f"({len(c_rows)} c rows >= {MIN_EXTENT} B)")
    findings = {}
    for off, kind, name, ext in c_rows:
        # yaml offsets are FILE offsets (the ld script places .r_<rom> at
        # AT(<yaml offset>); the PS-X EXE header is prepended on top and
        # is NOT part of the payload coordinate space). The fifteenth-return
        # run of this sweep added EXE_HDR to the needle source - grabbing the
        # bytes of the row 0x800 LATE while labelling them with the row at
        # `off` - so every hit it reported was a copy of the WRONG source
        # row's bytes at a 0x800-shifted position. Fixed 2026-10-29
        # (cron-202610291209): needle and hits both in file coordinates.
        needle = bin_[off : off + ext]
        if len(needle) != ext:
            continue
        pos, hits = 0, []
        while True:
            pos = bin_.find(needle, pos)
            if pos < 0:
                break
            hits.append(pos)
            pos += 1
        for h in hits:
            if h == off:
                continue  # self
            row = container(rows, h)
            cls = f"{row[1]}:{row[2]}@0x{row[0]:X}" if row else "?unknown?"
            findings.setdefault(cls, []).append(f"{name} (0x{ext:X} B) -> hit 0x{h:X}")
    if not findings:
        print("  no non-self occurrences of any landed c row")
        return
    for cls in sorted(findings):
        kind = cls.split(":")[0]
        tag = {"data": "RE-CARVE CANDIDATE", "asm": "flip candidate",
               "c": "landed copy"}.get(kind, "?")
        print(f"  [{tag}] {cls}: {len(findings[cls])} hit(s)")
        for f in findings[cls][:8]:
            print(f"      {f}")
        if len(findings[cls]) > 8:
            print(f"      ... +{len(findings[cls]) - 8} more")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    for t in sys.argv[1:]:
        sweep(t)

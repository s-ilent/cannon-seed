#!/usr/bin/env python3
"""surgery_e3dc_pair.py - the graveyard pair's yaml surgery: mainmenu_jp's
graveyard tail row (data_8005E1B8) three-way split.

Window cron-202610252321 staged the pair (src/func_8005E3DC.c +
src/func_8005E4E8.c; scripts/prove_e3dc_pair.py OFFLINE PROOF PASS, 67/67
words word-identical each to the committed row). The walk's
"double-rotate mega-host" is TWO whole 0x10c functions back to back at
the row's tail (the boundary probe's ROW2 accounting: three singletons
0x224 + 0x10c + 0x10c = 0x43c EXACT). One line

    - [0x3E9B8, data, data_8005E1B8]  # 0x43c
becoming three:
    - [0x3E9B8, data, data_8005E1B8]  # 0x224  (the three mainmenu_jp
        singletons keep the row's label: func_8005E1B8 0x48 +
        func_8005E200 0x58 + func_8005E258 0x184)
    - [0x3EBDC, c, func_8005E3DC]     # 0x10c  (0x8005E3DC..0x8005E4E8)
    - [0x3ECE8, c, func_8005E4E8]     # 0x10c  (0x8005E4E8..0x8005E5F4)

Arithmetic: 0x224 + 0x10c + 0x10c = 0x43c EXACT; cut 1 = 0x3E9B8 + 0x224
= 0x3EBDC (the banked file offset of func_8005E3DC's words, VA
0x8005E3DC = raw + 0x8001F800); cut 2 = 0x3EBDC + 0x10c = 0x3ECE8; the
row end 0x3ECE8 + 0x10c = 0x3EDF4 = the next yaml entry (ApplyMatrixLV's
start).

INDEPENDENCE: this surgery touches ONLY mainmenu_jp's data_8005E1B8 row
- the staged DED4 wave (data_80066CF4 + the seven #0x110 rows) and the
E064 one-cut (data_8005DF04) touch different rows, so this script runs
before or after either, in any order.

THE SEVEN OTHER TARGETS are NOT in this script: their pair twins sit
inside the five walk mega-row sizes (0x10c is one of the five sizes, so
head-vs-interior must be decided per target), and the per-target sites
come from the oracle-day word-search (`prove_e3dc_pair.py --sites`,
witness-gated). Once that search pins the sites, this script's pattern
extends the same way the DED4 wave's seven tail cuts did.

Usage:
    python3 scripts/surgery_e3dc_pair.py            # validate + dry-run
    python3 scripts/surgery_e3dc_pair.py --apply    # write in place
                                                    # (on the disc-return,
                                                    #  then make extract +
                                                    #  make verify
                                                    #  TARGET=mainmenu_jp)

Validations (all mandatory, the script refuses on any failure):
  - src/func_8005E3DC.c and src/func_8005E4E8.c exist;
  - the parent line exists exactly once, bare 0x43c comment;
  - split arithmetic closes and both cut addresses equal the banked
    sites; the tail end equals the next yaml entry's start;
  - post-surgery guards: the yaml parses and every entry address stays
    strictly increasing.
"""
import argparse
import difflib
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / "config"

PARENT = {
    "start": 0x3E9B8,
    "label": "data_8005E1B8",
    "size": 0x43C,
}
HEAD_SIZE = 0x224  # the three singletons stay data under the row's label
CUTS = [
    (0x3EBDC, "func_8005E3DC", 0x10C),
    (0x3ECE8, "func_8005E4E8", 0x10C),
]

LINE_RE = re.compile(
    r"^(?P<indent>\s*)-\s*\[(?P<addr>0x[0-9A-Fa-f]+), (?P<typ>\w+), "
    r"(?P<label>[A-Za-z0-9_.]+)\](?P<gap>\s*)#\s*(?P<comment>.*)$"
)


def fail(msg):
    print(f"surgery: FAIL {msg}")
    sys.exit(1)


def next_entry_start(lines, after_idx):
    """The next yaml entry's start address strictly after line after_idx."""
    for line in lines[after_idx + 1:]:
        m = LINE_RE.match(line.rstrip("\n"))
        if m:
            return int(m.group("addr"), 16)
    fail("no yaml entry follows the parent line")


def validate_result(new):
    """Post-surgery guards: yaml parses, addresses strictly increasing."""
    try:
        import yaml  # splat's own dependency; present wherever extract runs
    except ImportError:
        fail("pyyaml unavailable - cannot validate the result")
    try:
        yaml.safe_load("".join(new))
    except yaml.YAMLError as e:
        fail(f"post-surgery yaml does not parse: {e}")
    prev = None
    for line in new:
        m = LINE_RE.match(line.rstrip("\n"))
        if not m:
            continue
        addr = int(m.group("addr"), 16)
        if prev is not None and addr <= prev:
            fail(f"post-surgery address order broke at 0x{addr:X} "
                 f"(prev 0x{prev:X})")
        prev = addr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="write the surgery in place (default: dry-run)")
    args = ap.parse_args()

    for _, label, _sz in CUTS:
        if not (REPO / "src" / f"{label}.c").exists():
            fail(f"src/{label}.c missing - the rows would link nothing")

    path = CONFIG / "splat.mainmenu_jp.yaml"
    lines = path.read_text().splitlines(keepends=True)

    hits = []
    for i, line in enumerate(lines):
        m = LINE_RE.match(line.rstrip("\n"))
        if not m:
            continue
        if (int(m.group("addr"), 16) == PARENT["start"]
                and m.group("label") == PARENT["label"]
                and m.group("typ") == "data"):
            hits.append((i, m))
    if len(hits) != 1:
        fail(f"expected exactly one parent line [0x{PARENT['start']:X}, data, "
             f"{PARENT['label']}], found {len(hits)}")
    i, m = hits[0]

    cmt = m.group("comment").strip()
    if cmt != f"0x{PARENT['size']:x}":
        fail(f"parent comment {cmt!r} != bare 0x{PARENT['size']:x}")

    sizes = [HEAD_SIZE] + [sz for _, _, sz in CUTS]
    if sum(sizes) != PARENT["size"]:
        fail(f"split arithmetic: {' + '.join(f'0x{s:x}' for s in sizes)} != "
             f"0x{PARENT['size']:x}")
    addr = PARENT["start"]
    for (site, _label, sz) in CUTS:
        addr += sizes[0] if site == CUTS[0][0] else 0
        if site != addr:
            fail(f"cut 0x{site:X} != expected 0x{addr:X}")
        addr += sz
    if addr != PARENT["start"] + PARENT["size"]:
        fail(f"row end 0x{addr:X} != parent end")
    nxt = next_entry_start(lines, i)
    if addr != nxt:
        fail(f"row end 0x{addr:X} != next yaml entry start 0x{nxt:X}")

    head_txt = f"{m.group('indent')}- [0x{PARENT['start']:X}, data, {PARENT['label']}]"
    width = len(head_txt) + len(m.group("gap"))
    new = lines[:i]
    new.append(head_txt.ljust(width) + f"# 0x{HEAD_SIZE:x}\n")
    for site, label, sz in CUTS:
        cut_txt = f"{m.group('indent')}- [0x{site:X}, c, {label}]"
        new.append(cut_txt.ljust(width) + f"# 0x{sz:x}\n")
    new += lines[i + 1:]

    validate_result(new)
    diff = list(difflib.unified_diff(
        lines, new, fromfile=f"a/{path.relative_to(REPO)}",
        tofile=f"b/{path.relative_to(REPO)}", n=0))
    print("".join(diff), end="")
    if args.apply:
        path.write_text("".join(new))
        print(f"surgery: APPLIED {path.name}")
    else:
        print(f"surgery: {path.name} OK (dry-run)")
    print("surgery: 1 file surgically validated (1 three-way split = "
          "3 line changes)")


if __name__ == "__main__":
    main()

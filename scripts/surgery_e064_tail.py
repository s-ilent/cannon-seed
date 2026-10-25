#!/usr/bin/env python3
"""surgery_e064_tail.py - the E064 ROW1-final tail's yaml surgery, the
ONE-CUT composition on top of the staged DED4 wave.

Window cron-202610252206 staged func_8005E064 (the walk graveyard's
ROW1-final 0x30 whole function; scripts/prove_func_8005E064.py OFFLINE
PROOF PASS, 12/12 words word-identical to the committed row). After the
DED4 wave's three-way split (scripts/surgery_ded4_wave.py: data_80066CF4
0x6e0 -> 0x520 + 0x30 + 0x190), this unit's cut composes as ONE more
row-final cut of mainmenu_jp's yaml, one line

    - [0x3E704, data, data_8005DF04]   # 0x190
becoming two:
    - [0x3E704, data, data_8005DF04]   # 0x160  (the light-shuffle
        composite, the probe's 0x8005DF04..0x8005E064 extent)
    - [0x3E864, c, func_8005E064]      # 0x30   (0x8005E064..0x8005E094)

Arithmetic: 0x190 = 0x160 + 0x30 EXACT (the probe's boundary table: the
light-shuffle composite 0x160 + the ROW1-final 0x30), and the tail end
0x3E864 + 0x30 = 0x3E894 = the row's end = the next yaml entry's start.
The cut address is the banked site: E064's words sit at file offset
0x3E864 in mainmenu_jp.bin (VA 0x8005E064 = raw + 0x8001F800, the
classifier law) - the committed row's own comment column states it.

COMPOSITION ORDER (mandatory): this surgery runs AFTER
`surgery_ded4_wave.py --apply` - its parent line only exists post-DED4-
wave, and the script refuses otherwise.

THE SEVEN OTHER TARGETS are NOT in this script: their E064 twins sit
mid-row inside the five walk mega-row sizes, and the per-target sites
come from the oracle-day word-search (`prove_func_8005E064.py --sites`,
witness-gated). Once that search pins the seven sites, this script's
CUTS-table pattern extends the same way the DED4 wave's seven tail cuts
did (row_start + rel, one line -> two).

Usage:
    python3 scripts/surgery_e064_tail.py            # validate + dry-run
    python3 scripts/surgery_e064_tail.py --apply    # write in place
                                                    # (AFTER the DED4 wave
                                                    #  applied; then make
                                                    #  extract + make verify
                                                    #  TARGET=mainmenu_jp)

Validations (all mandatory, the script refuses on any failure):
  - src/func_8005E064.c exists;
  - the post-DED4 parent line exists exactly once, bare 0x190 comment;
  - cut arithmetic: parent_start + 0x160 == 0x3E864 == the banked site,
    0x190 == 0x160 + 0x30, tail end == the next yaml entry's start;
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

C_LABEL = "func_8005E064"
C_SIZE = 0x30
HEAD_SIZE = 0x160  # the light-shuffle composite stays data

PARENT = {
    "start": 0x3E704,
    "label": "data_8005DF04",
    "size": 0x190,
}
SITE = 0x3E864  # the banked file offset of E064's words (VA 0x8005E064)

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

    if not (REPO / "src" / f"{C_LABEL}.c").exists():
        fail(f"src/{C_LABEL}.c missing - the row would link nothing")

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
             f"{PARENT['label']}] (it exists only AFTER surgery_ded4_wave.py "
             f"--apply), found {len(hits)}")
    i, m = hits[0]

    cmt = m.group("comment").strip()
    if cmt != f"0x{PARENT['size']:x}":
        fail(f"parent comment {cmt!r} != bare 0x{PARENT['size']:x}")
    if PARENT["start"] + HEAD_SIZE != SITE:
        fail(f"cut 0x{PARENT['start'] + HEAD_SIZE:X} != banked site 0x{SITE:X}")
    if PARENT["size"] != HEAD_SIZE + C_SIZE:
        fail(f"split arithmetic: 0x{PARENT['size']:x} != "
             f"0x{HEAD_SIZE:x} + 0x{C_SIZE:x}")
    nxt = next_entry_start(lines, i)
    tail_end = SITE + C_SIZE
    if tail_end != nxt:
        fail(f"tail end 0x{tail_end:X} != next yaml entry start 0x{nxt:X}")

    head_txt = f"{m.group('indent')}- [0x{PARENT['start']:X}, data, {PARENT['label']}]"
    cut_txt = f"{m.group('indent')}- [0x{SITE:X}, c, {C_LABEL}]"
    width = len(head_txt) + len(m.group("gap"))
    new = lines[:i] + [
        head_txt.ljust(width) + f"# 0x{HEAD_SIZE:x}\n",
        cut_txt.ljust(width) + f"# 0x{C_SIZE:x}\n",
    ] + lines[i + 1:]

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
    print("surgery: 1 file surgically validated (1 one-cut = 2 line changes)")


if __name__ == "__main__":
    main()

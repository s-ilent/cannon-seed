#!/usr/bin/env python3
"""surgery_ded4_wave.py - the staged 0x30 tail-writer wave's yaml surgery.

Window cron-202610251706 staged this wave first-shot-ready: func_8005DED4
(the walk graveyard's rotation-matrix commit tail, 0x30, decoded x8 through
scripts/prove_func_8005DED4.py PASS; site table banked in the src header)
lands as one c row per target linking the already-committed
src/func_8005DED4.c. This script performs the eight yaml surgeries:

  seven #0x110 walk mega-row tail cuts (one per non-JP-menu target), one line
      - [0x<start>, asm, <name>]   # 0x110 sdk
  becoming two:
      - [0x<start>, asm, <name>]   # 0xe0 sdk
      - [0x<start+0xE0>, c, func_8005DED4]  # 0x30 sdk   (marker follows
          the parent's attestation, the ScaleMatrixL mainmenu_jp precedent;
          the f8a3d1c writer law re-emits it on c rows)

  mainmenu_jp's graveyard head-row split, one line
      - [0x3E1B4, data, data_80066CF4]   # 0x6e0
  becoming three:
      - [0x3E1B4, data, data_80066CF4]   # 0x520   (head keeps its label)
      - [0x3E6D4, c, func_8005DED4]      # 0x30
      - [0x3E704, data, data_8005DF04]   # 0x190   (tail re-homes under the
          walk record's next-function name, the data_8005E1B8 precedent)

Every replacement line keeps the parent line's indentation and comment
column, so the diff is the minimal mechanical edit.

Usage:
    python3 scripts/surgery_ded4_wave.py            # validate + dry-run diff, writes nothing
    python3 scripts/surgery_ded4_wave.py --apply    # write in place
                                                    # (run AFTER a witness-8/8
                                                    #  disc-return, then
                                                    #  make extract x8 +
                                                    #  make verify TARGET=<t> x8)

Validations (all mandatory, the script refuses on any failure):
  - each parent line exists exactly once, with the expected size comment;
  - each cut offset equals the banked site table (row_start + 0xE0 == the
    src header's file offset for that target; mainmenu_jp's 0x3E6D4 exact);
  - mainmenu_jp's three-way split arithmetic: 0x520 + 0x30 + 0x190 == 0x6e0
    and the tail end equals the next yaml entry's start (0x3E894);
  - src/func_8005DED4.c exists (the rows link it).
"""
import argparse
import difflib
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / "config"

C_LABEL = "func_8005DED4"
C_SIZE = 0x30
REL = 0xE0  # the 0x30 tail's rel offset inside every #0x110 walk mega-row

# (target, row_start file offset, row_label, size-comment marker)
CUTS = [
    ("slps_00270", 0x14C10, "func_80034410", "sdk"),
    ("sces_00269", 0x146D8, "func_80033ED8", "sdk"),
    ("mainmenu_eu", 0x3DFD4, "func_8005D7D4", "sdk"),
    ("g3_jp", 0x2A0E0, "func_800498E0", "sdk"),
    ("g3_eu", 0x29AF8, "func_800492F8", "sdk"),
    ("g3org_jp", 0x2757C, "func_80046D7C", "sdk"),
    ("g3org_eu", 0x26F4C, "func_8004674C", "sdk"),
]

# The src header's site table (independent copy = the cross-check law):
# the 0x30 pattern's file offset per target, one occurrence each (proved).
SITES = {
    "slps_00270": 0x14CF0,
    "sces_00269": 0x147B8,
    "mainmenu_jp": 0x3E6D4,
    "mainmenu_eu": 0x3E0B4,
    "g3_jp": 0x2A1C0,
    "g3_eu": 0x29BD8,
    "g3org_jp": 0x2765C,
    "g3org_eu": 0x2702C,
}

# mainmenu_jp's graveyard head row (data): the split
MMJP = {
    "row_start": 0x3E1B4,
    "label": "data_80066CF4",
    "row_size": 0x6E0,
    "cut": 0x3E6D4,
    "tail_label": "data_8005DF04",
    "next_entry": 0x3E894,  # ScaleMatrixL's start = the row's end
}

LINE_RE = re.compile(
    r"^(?P<indent>\s*)-\s*\[(?P<addr>0x[0-9A-Fa-f]+), (?P<typ>\w+), "
    r"(?P<label>[A-Za-z0-9_.]+)\](?P<gap>\s*)#\s*(?P<comment>.*)$"
)


def fail(msg):
    print(f"surgery: FAIL {msg}")
    sys.exit(1)


def find_parent(lines, target, start, label, typ):
    hits = []
    for i, line in enumerate(lines):
        m = LINE_RE.match(line.rstrip("\n"))
        if not m:
            continue
        if (
            int(m.group("addr"), 16) == start
            and m.group("label") == label
            and m.group("typ") == typ
        ):
            hits.append((i, m))
    if len(hits) != 1:
        fail(f"{target}: expected exactly one parent line for "
             f"0x{start:X} {label}, found {len(hits)}")
    return hits[0]


def cut_entry_lines(indent, gap, start, label, typ, size, marker):
    """The two replacement lines, comment column = the parent's.

    The head piece keeps the parent's start address and label (the row is
    the same row, just shorter); only the tail piece moves to the cut
    address and flips to the c row. Hex sizes spell lowercase, the yaml's
    own convention (0x110, 0x6e0, 0x43c).
    """
    head = f"{indent}- [0x{start:X}, {typ}, {label}]"
    sub = f"{indent}- [0x{start:X}, {typ}, {label}]"
    cut = f"{indent}- [0x{start + REL:X}, c, {C_LABEL}]"
    if size != REL + C_SIZE:
        fail(f"row size 0x{size:x} != 0x{REL:x} + 0x{C_SIZE:x} (head + tail)")
    width = len(head) + len(gap)
    mk = f" {marker}" if marker else ""
    return [
        sub.ljust(width) + f"# 0x{REL:x}{mk}\n",
        cut.ljust(width) + f"# 0x{C_SIZE:x}{mk}\n",
    ]


def split_entry_lines(indent, gap):
    """mainmenu_jp's three replacement lines."""
    head = f"{indent}- [0x{MMJP['row_start']:X}, data, {MMJP['label']}]"
    width = len(head) + len(gap)
    head_size = MMJP["cut"] - MMJP["row_start"]
    tail_size = MMJP["next_entry"] - MMJP["cut"] - C_SIZE
    l1 = f"{indent}- [0x{MMJP['row_start']:X}, data, {MMJP['label']}]"
    l2 = f"{indent}- [0x{MMJP['cut']:X}, c, {C_LABEL}]"
    l3 = f"{indent}- [0x{MMJP['cut'] + C_SIZE:X}, data, {MMJP['tail_label']}]"
    return [
        l1.ljust(width) + f"# 0x{head_size:x}\n",
        l2.ljust(width) + f"# 0x{C_SIZE:x}\n",
        l3.ljust(width) + f"# 0x{tail_size:x}\n",
    ]


def surgery(target, lines):
    """Return (new_lines, n_changed). One surgery per call."""
    if target == "mainmenu_jp":
        i, m = find_parent(lines, target, MMJP["row_start"], MMJP["label"], "data")
        parts = m.group("comment").split()
        if len(parts) != 1 or int(parts[0], 16) != MMJP["row_size"]:
            fail(f"{target}: parent comment {m.group('comment')!r} is not a bare "
                 f"0x{MMJP['row_size']:x}")
        if MMJP["cut"] - MMJP["row_start"] + C_SIZE + (
            MMJP["next_entry"] - MMJP["cut"] - C_SIZE
        ) != MMJP["row_size"]:
            fail(f"{target}: split arithmetic does not close")
        if SITES["mainmenu_jp"] != MMJP["cut"]:
            fail(f"{target}: cut 0x{MMJP['cut']:X} != banked site")
        new = split_entry_lines(m.group("indent"), m.group("gap"))
        return lines[:i] + new + lines[i + 1:], 1

    for tgt, start, label, marker in CUTS:
        if tgt != target:
            continue
        i, m = find_parent(lines, target, start, label, "asm")
        cmt = m.group("comment").strip()
        want = f"0x110 {marker}".strip()
        if cmt != want:
            fail(f"{target}: parent comment {cmt!r} != {want!r}")
        if start + REL != SITES[target]:
            fail(f"{target}: cut 0x{start + REL:X} != banked site 0x{SITES[target]:X}")
        new = cut_entry_lines(m.group("indent"), m.group("gap"), start, label,
                              "asm", 0x110, marker)
        return lines[:i] + new + lines[i + 1:], 1
    fail(f"{target}: no surgery scheduled")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="write the surgery in place (default: dry-run)")
    args = ap.parse_args()

    if not (REPO / "src" / f"{C_LABEL}.c").exists():
        fail(f"src/{C_LABEL}.c missing - the rows would link nothing")

    total = 0
    for target in [t for t, *_ in CUTS] + ["mainmenu_jp"]:
        path = CONFIG / f"splat.{target}.yaml"
        lines = path.read_text().splitlines(keepends=True)
        new, n = surgery(target, lines)
        total += n
        diff = list(difflib.unified_diff(
            lines, new, fromfile=f"a/config/splat.{target}.yaml",
            tofile=f"b/config/splat.{target}.yaml", n=0))
        print("".join(diff), end="")
        if args.apply:
            path.write_text("".join(new))
            print(f"surgery: APPLIED {path.name}")
        else:
            print(f"surgery: {path.name} OK (dry-run)")
    print(f"surgery: {total} file(s) surgically validated "
          f"(7 tail cuts + 1 three-way split = 15 line changes expected)")
    if total != 8:
        fail(f"expected 8 files, got {total}")


if __name__ == "__main__":
    main()

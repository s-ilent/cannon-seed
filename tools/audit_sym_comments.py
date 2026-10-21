#!/usr/bin/env python3
"""Audit splat symbols files for comment tokens that trip the attribute parser.

splat64 0.50 util/symbols.py ground truth (read at the source, 2026-10-21):
the text after '//' is space-split; every token containing ':' is parsed as
attr:val. Empty attr name or empty value = hard error. Known non-Boolean
attrs: type/size/rom/segment/name_end/filename/visibility/function_owner/
align (type validated against splat_sym_types + first-upper + the
disassembler's known types; size/rom/align must parse as ints). Everything
else falls to the Boolean branch: value must be truey/falsey (lowercased)
or it is a hard error; UNKNOWN boolean names are silently ignored.

Known booleans: defined/extract/ignore/force_migration/force_not_migration/
allow_addend/dont_allow_addend/can_reference/can_be_referenced/
allow_duplicated/use_non_matching_label/absolute.

This audit lists every LETHAL (file, line, token). Unknown-boolean tokens
with a valid truey/falsey value are reported as INFO (inert). Exit 1 if any
lethal token exists, 0 if clean. Scope: the eight per-target symbols files
the yamls actually load (symbols.curated.txt is sdk_curated.py's input, not
splat's, so its prose is out of scope).
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TARGETS = [
    "slps_00270", "sces_00269", "mainmenu_jp", "mainmenu_eu",
    "g3_jp", "g3_eu", "g3org_jp", "g3org_eu",
]
FILES = [REPO / f"config/symbols.{t}.txt" for t in TARGETS]

NONBOOL = {"type", "size", "rom", "segment", "name_end", "filename",
           "visibility", "function_owner", "align"}
BOOLS = {"defined", "extract", "ignore", "force_migration",
         "force_not_migration", "allow_addend", "dont_allow_addend",
         "can_reference", "can_be_referenced", "allow_duplicated",
         "use_non_matching_label", "absolute"}
TRUEY = {"true", "on", "yes", "y"}
FALSEY = {"false", "off", "no", "n"}
SYM_TYPES = {"func", "jtbl", "jtbl_label", "label", "alabel"}

try:
    sys.path.insert(0, str(REPO))
    from spimdisasm import common
    KNOWN_TYPES = set(common.gKnownTypes)
except Exception:
    KNOWN_TYPES = set()


def valid_type(val: str) -> bool:
    return val[:1].isupper() or val in SYM_TYPES or val in KNOWN_TYPES


lethal = 0
info = 0
for f in FILES:
    for ln, line in enumerate(f.read_text().splitlines(), 1):
        s = line.strip()
        if not s or s.startswith("//"):
            continue
        loc = line.find("//")
        if loc == -1:
            continue
        ext = line[loc + 2:].strip()
        for tok in ext.split(" "):
            if ":" not in tok:
                continue
            name, _, val = tok.partition(":")
            if val == "":
                print(f"LETHAL {f.name}:{ln}: empty value '{tok}'")
                lethal += 1
                continue
            if name == "":
                print(f"LETHAL {f.name}:{ln}: empty name '{tok}'")
                lethal += 1
                continue
            if name in NONBOOL:
                if name == "type" and not valid_type(val):
                    print(f"LETHAL {f.name}:{ln}: bad type '{tok}'")
                    lethal += 1
                elif name in {"size", "rom", "align"}:
                    try:
                        int(val, 0)
                    except ValueError:
                        print(f"LETHAL {f.name}:{ln}: bad int '{tok}'")
                        lethal += 1
                continue
            if val.lower() not in TRUEY | FALSEY:
                print(f"LETHAL {f.name}:{ln}: invalid boolean '{tok}'")
                lethal += 1
                continue
            if name not in BOOLS:
                print(f"INFO {f.name}:{ln}: unknown boolean (inert) '{tok}'")
                info += 1

print(f"audit: {lethal} lethal, {info} inert across {len(FILES)} target files")
sys.exit(1 if lethal else 0)

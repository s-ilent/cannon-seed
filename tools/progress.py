#!/usr/bin/env python3
"""progress.py — measure the tree; never transcribe counts into prose.

Counts matched and nonmatching functions over the standard splat layout:

    matched      = function definitions found in src/**/*.c (column-0,
                   C89-style definitions)
    nonmatching  = assembly stubs under asm/nonmatchings/**/*.s (splat keeps
                   every not-yet-C function there)

Two honesty notes, inherited from the projects this template distils:

1. This is a filesystem heuristic for dashboards and target selection. The
   only verdict that promotes work is the whole-image SHA-1 (`make verify`).
   A green per-function score proves nothing on its own.
2. Functions still spelled INCLUDE_ASM count as nonmatching, because their
   .s stub still lives under asm/nonmatchings. That is correct: they are
   not matched C.

Usage:
    python3 tools/progress.py            # human-readable report
    python3 tools/progress.py --list     # also list nonmatching functions
    python3 tools/progress.py --json     # machine-readable (CI / badges)
    python3 tools/progress.py --ratchet config/progress.baseline.json
                                         # fail if matched count regressed
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src"
NONMATCH = REPO / "asm" / "nonmatchings"

# Column-0 C89 function definition: identifier ( args ) {  — or ( args )
# with the opening brace on the next line. Prototypes end in ';' and are
# excluded. Control keywords are excluded explicitly.
_CONTROL = ("if", "for", "while", "switch", "return", "else", "sizeof",
            "typedef", "extern", "static", "goto", "do")
_DEF = re.compile(r"^[A-Za-z_][A-Za-z0-9_ \t\*]*?\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")


def _looks_like_definition(lines: list[str], i: int) -> bool:
    line = lines[i].strip()
    if not line or line.startswith(("#", "/*", "*", "//")):
        return False
    if line.endswith(";"):
        return False
    m = _DEF.match(lines[i])
    if not m:
        return False
    if m.group(1) in _CONTROL:
        return False
    if line.endswith("{"):
        return True
    # Brace-on-next-line style: s32 Foo(void)\n{
    for j in range(i + 1, min(i + 4, len(lines))):
        nxt = lines[j].strip()
        if not nxt or nxt.startswith(("#", "*", "//")):
            continue
        return nxt.startswith("{")
    return False


def count_matched_functions() -> int:
    total = 0
    for path in sorted(SRC.rglob("*")) if SRC.exists() else ():
        if path.suffix not in (".c", ".inc"):
            continue
        text = path.read_text(errors="replace")
        lines = text.splitlines()
        total += sum(1 for i in range(len(lines)) if _looks_like_definition(lines, i))
    return total


def count_nonmatching() -> list[str]:
    if not NONMATCH.exists():
        return []
    # splat layout: asm/nonmatchings/<unit>/<function>.s
    return sorted(p.stem for p in NONMATCH.rglob("*.s"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--list", action="store_true", help="list nonmatching functions")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--ratchet", type=Path, default=None,
                    help="JSON baseline file; fail if matched count decreased")
    args = ap.parse_args()

    matched = count_matched_functions()
    nonmatching_names = count_nonmatching()
    nonmatching = len(nonmatching_names)
    total = matched + nonmatching
    pct = (100.0 * matched / total) if total else 0.0

    if args.json:
        print(json.dumps({
            "matched": matched,
            "nonmatching": nonmatching,
            "total": total,
            "percent": round(pct, 2),
            "nonmatching_names": nonmatching_names,
        }, indent=2))
    else:
        print(f"matched      : {matched}")
        print(f"nonmatching  : {nonmatching}")
        print(f"total        : {total}")
        print(f"progress     : {pct:.2f}%  (filesystem heuristic; "
              "the whole-image SHA-1 is the real oracle)")
        if args.list and nonmatching_names:
            print("\nnonmatching functions:")
            for name in nonmatching_names:
                print(f"  {name}")

    if args.ratchet is not None:
        baseline = json.loads(args.ratchet.read_text())
        base_matched = int(baseline.get("matched", -1))
        if matched < base_matched:
            print(f"RATCHET FAIL: matched {matched} < baseline {base_matched} "
                  f"({args.ratchet}). Matched counts only go up.", file=sys.stderr)
            return 1
        if matched > base_matched:
            print(f"ratchet note: matched {matched} > baseline {base_matched}; "
                  f"lower {args.ratchet} in the same PR (ratchets must equal "
                  "the current tree).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

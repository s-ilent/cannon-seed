#!/usr/bin/env python3
"""progress.py — measure the tree; never transcribe counts into prose.

Per-target census driven by the committed yaml layouts (the ground truth
for segmentation). For every config/splat.<target>.yaml:

    matched      = function definitions in the src/<name>.c file of every
                   `c` subsegment (column-0, C89-style definitions; a unit
                   file holds many functions)
    nonmatching  = `glabel`s under the target's asm_path/**/*.s (splat
                   keeps every not-yet-C function there; data subsegments
                   carry only `dlabel`s, so glabels count functions)

Honesty notes, inherited from the projects this template distils:

1. This is a filesystem heuristic for dashboards and target selection. The
   only verdict that promotes work is the whole-image SHA-1 (`make verify`).
   A green per-function score proves nothing on its own.
2. Functions still spelled INCLUDE_ASM count as nonmatching, because their
   .s stub still lives under asm/nonmatchings. That is correct: they are
   not matched C.
3. matched(T) is attributed through the yaml `c` subsegment names; a src
   file shared by two targets would count for both (none exists today).

Usage:
    python3 tools/progress.py            # per-target + total report
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

# Column-0 C89 function definition: identifier ( args ) {  — or ( args )
# with the opening brace on the next line. Prototypes end in ';' and are
# excluded. Control keywords are excluded explicitly.
_CONTROL = ("if", "for", "while", "switch", "return", "else", "sizeof",
            "typedef", "extern", "static", "goto", "do")
_DEF = re.compile(r"^[A-Za-z_][A-Za-z0-9_ \t\*]*?\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")
_SUBSEG = re.compile(
    r"-\s*\[(0x[0-9A-Fa-f]+),\s*(asm|c|data),\s*([\w.]+)\]\s*#\s*(0x[0-9A-Fa-f]+)")
_GLABEL = re.compile(r"glabel\s+(\S+)")


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


_defcount_cache: dict[Path, int] = {}


def defs_in_file(path: Path) -> int:
    """Column-0 function definitions in one C source file (cached)."""
    if path in _defcount_cache:
        return _defcount_cache[path]
    n = 0
    if path.exists():
        text = path.read_text(errors="replace")
        lines = text.splitlines()
        n = sum(1 for i in range(len(lines)) if _looks_like_definition(lines, i))
    _defcount_cache[path] = n
    return n


def target_layouts() -> list[tuple[str, Path, list[str]]]:
    """(target, asm_path, c-unit src names) straight from the committed yamls."""
    out = []
    for y in sorted((REPO / "config").glob("splat.*.yaml")):
        target = y.stem[len("splat."):]
        asm_path, c_names = None, []
        for line in y.read_text(errors="replace").splitlines():
            m = re.match(r"\s*asm_path:\s*(\S+)", line)
            if m:
                asm_path = m.group(1)
            s = _SUBSEG.search(line)
            if s and s.group(2) == "c":
                c_names.append(s.group(3))
        if asm_path is None:
            print(f"progress: {y.name} has no asm_path; skipped", file=sys.stderr)
            continue
        out.append((target, REPO / asm_path, c_names))
    return out


def census() -> list[dict]:
    """Per-target matched / nonmatching / total, sorted by target name."""
    rows = []
    for target, asm_path, c_names in target_layouts():
        matched = sum(defs_in_file(SRC / f"{name}.c") for name in c_names)
        names: list[str] = []
        if asm_path.exists():
            for path in sorted(asm_path.rglob("*.s")):
                for line in path.read_text(errors="replace").splitlines():
                    m = _GLABEL.match(line)
                    if m:
                        names.append(m.group(1))
        nonmatching = len(names)
        total = matched + nonmatching
        rows.append({
            "target": target,
            "matched": matched,
            "nonmatching": nonmatching,
            "total": total,
            "percent": round(100.0 * matched / total, 2) if total else 0.0,
            "_names": names,
        })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--list", action="store_true", help="list nonmatching functions")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--ratchet", type=Path, default=None,
                    help="JSON baseline file; fail if matched count decreased")
    args = ap.parse_args()

    rows = census()
    tot_m = sum(r["matched"] for r in rows)
    tot_n = sum(r["nonmatching"] for r in rows)
    tot_t = tot_m + tot_n

    if args.json:
        out_rows = [{k: v for k, v in r.items() if k != "_names"} for r in rows]
        print(json.dumps({
            "targets": out_rows,
            "matched": tot_m,
            "nonmatching": tot_n,
            "total": tot_t,
            "percent": round(100.0 * tot_m / tot_t, 2) if tot_t else 0.0,
        }, indent=2))
    else:
        print(f"{'target':<14} {'matched':>7} {'nonmatch':>8} {'total':>7} "
              f"{'progress':>8}")
        for r in rows:
            print(f"{r['target']:<14} {r['matched']:>7} {r['nonmatching']:>8} "
                  f"{r['total']:>7} {r['percent']:>7.2f}%")
        pct = (100.0 * tot_m / tot_t) if tot_t else 0.0
        print(f"{'TOTAL':<14} {tot_m:>7} {tot_n:>8} {tot_t:>7} {pct:>7.2f}%")
        print("(filesystem heuristic; the whole-image SHA-1 is the real oracle)")
        if args.list:
            for r in rows:
                if r["_names"]:
                    print(f"\nnonmatching in {r['target']}:")
                    for name in r["_names"]:
                        print(f"  {name}")

    if args.ratchet is not None:
        baseline = json.loads(args.ratchet.read_text())
        base_matched = int(baseline.get("matched", -1))
        if tot_m < base_matched:
            print(f"RATCHET FAIL: matched {tot_m} < baseline {base_matched} "
                  f"({args.ratchet}). Matched counts only go up.", file=sys.stderr)
            return 1
        if tot_m > base_matched:
            print(f"ratchet note: matched {tot_m} > baseline {base_matched}; "
                  f"lower {args.ratchet} in the same PR (ratchets must equal "
                  "the current tree).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

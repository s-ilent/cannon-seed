#!/usr/bin/env python3
"""Stripped-comment body diff gate for the wave campaign's SHAREDMERGE rows.

Compares a drifted target-local c copy against its pin-named shared top-level
src/ file. Comments (/* */ and //) are stripped, whitespace collapsed, blank
lines dropped; an empty diff means body-identical (merge motion safe).
Usage: merge_diff_gate.py <drifted.c> <shared.c> [--show]
Exit 0 = identical body, 1 = differs.
"""
import re
import sys
from pathlib import Path


def strip(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"//[^\n]*", "", text)
    lines = []
    for ln in text.splitlines():
        ln = ln.strip()
        if ln:
            lines.append(re.sub(r"\s+", " ", ln))
    return "\n".join(lines)


def main() -> int:
    drifted, shared = Path(sys.argv[1]), Path(sys.argv[2])
    show = "--show" in sys.argv
    a, b = strip(drifted.read_text()), strip(shared.read_text())
    if a == b:
        print(f"IDENTICAL {drifted.name} == {shared.name} ({len(a.splitlines())} lines)")
        return 0
    import difflib

    diff = list(difflib.unified_diff(
        a.splitlines(), b.splitlines(),
        fromfile=drifted.name, tofile=shared.name, lineterm=""))
    n = sum(1 for l in diff if l[:1] in "+-" and l[:3] not in ("+++", "---"))
    print(f"DIFFERS {drifted.name} vs {shared.name}: {n} changed line(s)")
    if show:
        for l in diff:
            print(l)
    return 1


if __name__ == "__main__":
    sys.exit(main())

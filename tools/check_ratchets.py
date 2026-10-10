#!/usr/bin/env python3
"""check_ratchets.py — placeholder / debt ratchet, after Parasite Eve's discipline.

Counts placeholder-name tokens (func_XXXXXXXX, D_XXXXXXXX, ...) in src/ and
include/ and compares them with the committed baselines in
config/ratchets.json:

  * count > baseline  -> FAIL (debt increased; this is a regression)
  * count < baseline  -> FAIL (stale baseline; lower it in the same PR so
                          cleanups cannot be silently spent later)
  * count == baseline -> pass

Baseline updates that RAISE a count are policy changes and require explicit
review in the PR description; they are not a normal way to go green.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONFIG = REPO / "config" / "ratchets.json"
SCAN_DIRS = (REPO / "src", REPO / "include")
SCAN_SUFFIXES = (".c", ".h", ".inc")


def iter_source_files():
    for d in SCAN_DIRS:
        if not d.exists():
            continue
        for p in sorted(d.rglob("*")):
            if p.suffix in SCAN_SUFFIXES and p.is_file():
                yield p


def main() -> int:
    if not CONFIG.exists():
        print(f"ratchets: no {CONFIG.relative_to(REPO)}; nothing to audit "
              "(add it the day the first placeholder name appears).")
        return 0

    cfg = json.loads(CONFIG.read_text())
    patterns = [(p["name"], re.compile(p["regex"])) for p in cfg.get("patterns", [])]
    baselines = cfg.get("baselines", {})

    counts = {name: 0 for name, _ in patterns}
    for path in iter_source_files():
        text = path.read_text(errors="replace")
        for name, rx in patterns:
            counts[name] += len(rx.findall(text))

    failed = False
    for name, _ in patterns:
        count, base = counts[name], int(baselines.get(name, 0))
        if count > base:
            print(f"RATCHET FAIL: {name} = {count} > baseline {base} — debt "
                  "increased. Match it now (rename with evidence, or remove "
                  "the placeholder) or justify a baseline raise as a policy "
                  "change.", file=sys.stderr)
            failed = True
        elif count < base:
            print(f"RATCHET FAIL: {name} = {count} < baseline {base} — stale "
                  f"baseline. Lower config/ratchets.json to {count} in this "
                  "PR; an improvement may not leave a higher baseline behind.",
                  file=sys.stderr)
            failed = True
        else:
            print(f"ratchet ok: {name} = {count} (= baseline)")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

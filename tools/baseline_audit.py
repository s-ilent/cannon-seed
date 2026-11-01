#!/usr/bin/env python3
"""baseline_audit - read-only SESSION START guard over the baseline oracles.

The sandbox periodically rolls /home/z/my-project back to an old snapshot.
The 2026-11-01 audit window (cron-20261101-0237) found every local
`baselines/<t>.bin` replaced by the RETIRED woven-era dumps (raw MODE2/2352
reads with the 304-byte framing gaps left in) whose SHA-1s contradict the
committed per-target oracles in config/sha1/. Consequence: `verify.sh` exits
1 by design on EVERY target ("a different hash is a different build") and
every build/judge/carve item looks blocked until someone re-derives the
sandbox state by hand - forty minutes of archaeology that this guard
compresses to a ten-second warning at SESSION START.

What it does (read-only, stdlib-only, offline, always exit 0):
  * for each config/sha1/<t>.sha1: parse the expected hash exactly the way
    verify.sh does (first non-comment, non-blank line, field 1, lowercased);
  * sha1 the local baselines/<t>.bin when present;
  * print one row per target: EXPECTED / ACTUAL / MATCH|MISMATCH|MISSING;
  * a footer summarizing the state and the Law Zero consequence: a blocked
    baseline is a work-around-it state (offline queue work continues), NOT
    a crash - which is why rehydrate.sh calls this with `|| true`.

MISMATCH rows carry the banked woven-era hint: while the true retail is not
re-provisioned (disc_return.sh on live links), the dumps on disk are most
likely the retired contiguous-read artifacts - do NOT re-type rows from
deframe.py output computed against them (the --framing-rows trap, measured
end to end in the audit window's TASKS.md section).
"""
import argparse
import hashlib
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SHA1_DIR = REPO / "config" / "sha1"
BASELINE_DIR = REPO / "baselines"

# The committed oracle set, pinned by tests/test_baseline_audit.py.
KNOWN_TARGETS = {
    "g3_eu", "g3_jp", "g3org_eu", "g3org_jp",
    "mainmenu_eu", "mainmenu_jp", "sces_00269", "slps_00270",
}


def parse_expected(path: Path) -> str:
    """Mirror verify.sh's awk: first non-comment, non-blank line, field 1."""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        return line.split()[0].lower()
    return ""


def sha1_file(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def audit_row(target: str):
    """Return (target, expected, actual, status); status has no real-MATCH
    implication beyond the string: 'MATCH' | 'MISMATCH' | 'MISSING'
    | 'NO-ORACLE'."""
    sha1_path = SHA1_DIR / f"{target}.sha1"
    baseline_path = BASELINE_DIR / f"{target}.bin"
    expected = parse_expected(sha1_path) if sha1_path.is_file() else ""
    if not expected:
        return target, "-", "-", "NO-ORACLE"
    if not baseline_path.is_file():
        return target, expected, "-", "MISSING"
    actual = sha1_file(baseline_path)
    status = "MATCH" if actual == expected else "MISMATCH"
    return target, expected, actual, status


def run_table():
    """Audit every target with a committed oracle; return the row list."""
    targets = sorted(p.stem for p in SHA1_DIR.glob("*.sha1")) if SHA1_DIR.is_dir() else []
    return [audit_row(t) for t in targets]


def print_report(rows):
    width = max((len(r[0]) for r in rows), default=7)
    print(f"baseline_audit: {len(rows)} target(s), expected sha1 from config/sha1/, "
          f"actual from baselines/<t>.bin")
    print(f"  {'target':<{width}}  expected                                "
          f"actual                                status")
    for target, expected, actual, status in rows:
        print(f"  {target:<{width}}  {expected:<40}  {actual:<40}  {status}")
    matches = sum(1 for r in rows if r[3] == "MATCH")
    mismatch = sum(1 for r in rows if r[3] == "MISMATCH")
    missing = sum(1 for r in rows if r[3] == "MISSING")
    nooracle = sum(1 for r in rows if r[3] == "NO-ORACLE")
    print(f"  summary: {matches} MATCH / {mismatch} MISMATCH / "
          f"{missing} MISSING / {nooracle} NO-ORACLE")
    if mismatch or missing:
        print("  NOTE: verify.sh will exit 1 by design on every non-MATCH target "
              "('a different hash is a different build').")
        print("  MISMATCH dumps are most likely the retired woven-era dumps "
              "(cron-20261101-0237): do NOT re-type rows from deframe.py output "
              "computed against them.")
        print("  Law Zero: this is a work-around-it state, not a crash - offline "
              "queue work continues; witnessed windows re-provision via "
              "disc_return.sh.")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="read-only baseline oracle audit "
                                             "(always exit 0)")
    ap.parse_args(argv)
    rows = run_table()
    print_report(rows)
    return 0  # by design: never fail the session


if __name__ == "__main__":
    sys.exit(main())

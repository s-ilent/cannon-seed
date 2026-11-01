#!/usr/bin/env python3
"""tests/test_baseline_audit.py - the SESSION START guard must tell the truth
and must never fail the session.

The 2026-11-01 audit window (cron-20261101-0237) proved every local
baselines/*.bin could be a retired woven-era dump contradicting the
committed oracles while `verify.sh` exits 1 by design on every target. The
guard's contract (tools/baseline_audit.py):

  * read-only: fixture trees under tempfile, the real repo only READ;
  * expected-hash parsing mirrors verify.sh's awk exactly (first
    non-comment, non-blank line, field 1, lowercased);
  * statuses: MATCH / MISMATCH / MISSING (no baseline file) /
    NO-ORACLE (unparseable sha1 file);
  * main() ALWAYS returns 0 - a blocked baseline is a Law Zero
    work-around-it state, not a crash.

All fixtures are synthetic (temp dirs); no disc, no build, fully offline.
"""
import contextlib
import hashlib
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import baseline_audit  # noqa: E402

GOOD_SHA = "a" * 40


class BaselineAuditTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        self.sha_dir = self.repo / "config" / "sha1"
        self.bas_dir = self.repo / "baselines"
        self.sha_dir.mkdir(parents=True)
        self.bas_dir.mkdir(parents=True)

    def tearDown(self):
        self._tmp.cleanup()

    def write_oracle(self, target, sha, comment=True):
        lines = []
        if comment:
            lines.append(f"# config/sha1/{target}.sha1 - THE ORACLE for target '{target}'")
            lines.append("")
        lines.append(f"{sha}  baselines/{target}.bin")
        (self.sha_dir / f"{target}.sha1").write_text("\n".join(lines) + "\n")

    def write_baseline(self, target, blob):
        """Write the blob and return its real sha1 (oracles must be true)."""
        (self.bas_dir / f"{target}.bin").write_bytes(blob)
        return hashlib.sha1(blob).hexdigest()

    def point_repo(self):
        st = contextlib.ExitStack()
        st.enter_context(mock.patch.object(baseline_audit, "SHA1_DIR", self.sha_dir))
        st.enter_context(mock.patch.object(baseline_audit, "BASELINE_DIR", self.bas_dir))
        return st

    def test_match_row(self):
        real = self.write_baseline("t_a", b"true retail bytes")
        self.write_oracle("t_a", real)  # oracle = the blob's true sha
        with self.point_repo():
            rows = baseline_audit.run_table()
        self.assertEqual(rows, [("t_a", real, real, "MATCH")])

    def test_mismatch_row_reports_both_hashes(self):
        self.write_oracle("t_b", GOOD_SHA)
        self.write_baseline("t_b", b"woven-era dump with framing gaps")
        with self.point_repo():
            rows = baseline_audit.run_table()
        self.assertEqual(len(rows), 1)
        target, expected, actual, status = rows[0]
        self.assertEqual((target, status), ("t_b", "MISMATCH"))
        self.assertEqual(expected, GOOD_SHA)
        self.assertNotEqual(actual, expected)
        self.assertRegex(actual, r"^[0-9a-f]{40}$")

    def test_missing_baseline_is_not_mismatch(self):
        self.write_oracle("t_c", GOOD_SHA)
        with self.point_repo():
            rows = baseline_audit.run_table()
        self.assertEqual(rows, [("t_c", GOOD_SHA, "-", "MISSING")])

    def test_unparseable_oracle_is_no_oracle(self):
        (self.sha_dir / "t_d.sha1").write_text("# only comments\n\n")
        with self.point_repo():
            rows = baseline_audit.run_table()
        self.assertEqual(rows, [("t_d", "-", "-", "NO-ORACLE")])

    def test_expected_parse_mirrors_verify_awk(self):
        # comment lines skipped, blank lines skipped, field 1 taken, case-folded
        real = self.write_baseline("t_e", b"true retail bytes")
        self.write_oracle("t_e", real.upper())
        with self.point_repo():
            rows = baseline_audit.run_table()
        self.assertEqual(rows[0][1], real)  # lowercased
        self.assertEqual(rows[0][3], "MATCH")

    def test_exit_code_is_zero_even_all_mismatch(self):
        # the guard must never fail the session: main() returns 0 with the
        # worst possible table (every row MISMATCH/MISSING, plus garbage row)
        self.write_oracle("t_f", GOOD_SHA)
        self.write_baseline("t_f", b"wrong dump")
        self.write_oracle("t_g", GOOD_SHA)
        (self.sha_dir / "t_h.sha1").write_text("# empty\n")
        with self.point_repo():
            with mock.patch.object(baseline_audit.sys, "argv", ["x"]):
                rc = baseline_audit.main()
        self.assertEqual(rc, 0)

    def test_real_repo_oracle_set_is_the_eight_targets(self):
        # read-only against the real repo: the committed config/sha1/ glob
        # must be exactly the banked target set (pins accidental adds/drops)
        targets = {p.stem for p in baseline_audit.SHA1_DIR.glob("*.sha1")}
        self.assertEqual(targets, baseline_audit.KNOWN_TARGETS)


if __name__ == "__main__":
    unittest.main()

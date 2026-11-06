#!/usr/bin/env python3
"""test_cc_post_rule18.py - rule 18 (lt0-scc materialization rewrite).

The (x < 0) value materialization: the Sony psyq cc1 emits the scc form
(slti $d,$s,0) where the vanilla gcc 2.6.3 rebuild always takes
emit_store_flag's sign-extract special case (srl $d,$s,31) - proven at
the .rtl dump level + the scc-path control (see _rule18_lt0_scc). The
rewrite is semantics-identical (both materialize the sign bit as 0/1)
and site-contracted: `srl $d,$s,31` immediately followed by a $d-vs-$0
branch test.

Covers BOTH call paths for every rule added since rule 16: the banked
cron-202611040743 lesson is that a direct-call test alone passes while
main() is broken (the r16 CLI-path regression slipped through exactly
that way), so every behaviour here is asserted via the module API AND
via the cc_post.py CLI through subprocess on a temp .mas.s.
"""
import os
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POST = os.path.join(REPO, "tools", "cc_post.py")
sys.path.insert(0, os.path.join(REPO, "tools"))
import cc_post  # noqa: E402

# The d70b g3org_jp site (window cron-202611061501): andi/srl-31/bne,
# the n-check of the second loop's head.
SAMPLE = """\t.text
\t.globl\tSsVabOpenHeadWithMode
SsVabOpenHeadWithMode:
\tandi\t$3,$20,0x00ff
\tsrl\t$2,$3,31
\tbne\t$2,$0,$L44
\taddu\t$5,$0,$zero
\taddu\t$6,$3,$zero
$L44:
\tj\t$31
\tnop
"""

EXPECTED = SAMPLE.replace("\tsrl\t$2,$3,31\n", "\tslti\t$2,$3,0\n")
# main() flushes instruction runs through apply_rules on STRIPPED lines
# (directives and label lines pass through untouched), so the
# CLI-rewritten file keeps tabs only on the directive/label lines - the
# established cc_post output convention; the direct-call path preserves
# every line verbatim.
EXPECTED_CLI = """\t.text
\t.globl\tSsVabOpenHeadWithMode
SsVabOpenHeadWithMode:
andi\t$3,$20,0x00ff
slti\t$2,$3,0
bne\t$2,$0,$L44
addu\t$5,$0,$zero
addu\t$6,$3,$zero
$L44:
j\t$31
nop
"""


class TestRule18Direct(unittest.TestCase):
    def test_site_rewrites(self):
        lines = SAMPLE.splitlines()
        out, n = cc_post._rule18_lt0_scc(lines)
        self.assertEqual(n, 1)
        self.assertEqual(out, EXPECTED.splitlines())

    def test_no_match_returns_none(self):
        # srl-31 NOT followed by a $d-vs-$0 branch: the div-correction
        # shape (followed by addu) must never match.
        sample = "\tsrl\t$3,$5,31\n\taddu\t$3,$5,$3\n\tsra\t$3,$3,1\n"
        self.assertIsNone(cc_post._rule18_lt0_scc(sample.splitlines()))

    def test_non31_shift_never_matches(self):
        sample = "\tsrl\t$2,$3,8\n\tbne\t$2,$0,$L44\n"
        self.assertIsNone(cc_post._rule18_lt0_scc(sample.splitlines()))

    def test_dst_mismatch_never_matches(self):
        # branch tests a DIFFERENT register than the srl dst
        sample = "\tsrl\t$2,$3,31\n\tbne\t$5,$0,$L44\n"
        self.assertIsNone(cc_post._rule18_lt0_scc(sample.splitlines()))

    def test_beqz_spelling_matches(self):
        sample = "\tsrl\t$2,$3,31\n\tbeqz\t$2,$L9\n"
        out, n = cc_post._rule18_lt0_scc(sample.splitlines())
        self.assertEqual(n, 1)
        self.assertEqual(out[0], "\tslti\t$2,$3,0")

    def test_beq_zero_spelling_matches(self):
        sample = "\tsrl\t$4,$6,31\n\tbeq\t$4,$zero,$L9\n"
        out, n = cc_post._rule18_lt0_scc(sample.splitlines())
        self.assertEqual(n, 1)
        self.assertEqual(out[0], "\tslti\t$4,$6,0")

    def test_two_sites_count_two(self):
        sample = ("\tsrl\t$2,$3,31\n\tbne\t$2,$0,$L44\n\tnop\n"
                  "\tsrl\t$5,$6,31\n\tbnez\t$5,$L48\n")
        out, n = cc_post._rule18_lt0_scc(sample.splitlines())
        self.assertEqual(n, 2)
        self.assertEqual(out[0], "\tslti\t$2,$3,0")
        self.assertEqual(out[3], "\tslti\t$5,$6,0")


class TestRule18CLI(unittest.TestCase):
    def _run_cli(self, args, text):
        with tempfile.NamedTemporaryFile("w", suffix=".mas.s",
                                         delete=False) as f:
            f.write(text)
            path = f.name
        try:
            return subprocess.run(
                [sys.executable, POST] + args + [path],
                capture_output=True, text=True)
        finally:
            os.unlink(path)

    def test_cli_rewrites_and_passes(self):
        with tempfile.NamedTemporaryFile("w", suffix=".mas.s",
                                         delete=False) as f:
            f.write(SAMPLE)
            path = f.name
        try:
            r = subprocess.run([sys.executable, POST, "--lt0-scc", "1", path],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            with open(path) as f:
                self.assertEqual(f.read(), EXPECTED_CLI)
        finally:
            os.unlink(path)

    def test_cli_count_mismatch_loud_fails(self):
        # two sites in the file, marker expects one
        text = ("\tsrl\t$2,$3,31\n\tbne\t$2,$0,$L44\n"
                "\tsrl\t$5,$6,31\n\tbnez\t$5,$L48\n")
        r = self._run_cli(["--lt0-scc", "1"], text)
        self.assertEqual(r.returncode, 3)
        self.assertIn("rewrote 2 site(s)", r.stderr)

    def test_cli_no_site_loud_fails(self):
        r = self._run_cli(["--lt0-scc", "1"],
                          "\tsrl\t$3,$5,31\n\taddu\t$3,$5,$3\n")
        self.assertEqual(r.returncode, 3)
        self.assertIn("no lt0 site", r.stderr)

    def test_cli_bare_flag_usage_error(self):
        r = self._run_cli(["--lt0-scc"], SAMPLE)
        self.assertEqual(r.returncode, 2)
        self.assertIn("usage", r.stderr)

    def test_cli_bad_count_usage_error(self):
        r = self._run_cli(["--lt0-scc", "x"], SAMPLE)
        self.assertEqual(r.returncode, 2)
        self.assertIn("requires an integer count", r.stderr)


if __name__ == "__main__":
    unittest.main()

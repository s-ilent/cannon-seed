#!/usr/bin/env python3
"""test_cc_post_rule20.py - rule 20 (vol-extend).

The volatile-load zero-extend class (survey
docs/CC_POST_RULE_CLASSES.md section 4; window cron-202611070146): gcc
2.6.3 volatile reads bypass the zero-extend tracking, so the func_8007736C
copy-exit re-load's byte gets `andi $2,$2,0x00ff` at the merge where
retail's cc1 feeds the re-load's result to the merged zero-test directly.
The source surface is exhausted (probe c7: no C spelling yields both the
real re-load AND no andi; the asm-memory-clobber route breaks maspsx's
delay-slot handling), so the delete is a post-pass, shape-gated:
the andi's src must be the preceding lbu's dest (one maspsx load-use nop
tolerated) and its dest must feed the following zero-test; never
default-on - a 0x00ff andi is a genuine zero-extend elsewhere in the
corpus; the counted marker is the attestation.

The shape here is the LIVE c3 merge site (func_8007736C.mas.s,
window cron-202611070146): lbu / nop / andi / $L9: label / beq $d,$0.

Covers BOTH call paths per the banked cron-202611040743 lesson (a
direct-call test alone passed while main() was broken - the r16 CLI
regression class): the module API AND the cc_post.py CLI through
subprocess on a temp .mas.s. The live judge measurement rides the
window's worklog (func_8007736C c3 staging).
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

# The live c3 merge site: volatile re-load, its maspsx load-use fill, the
# andi, the merge label (carries no bytes), the merged NUL test.
SAMPLE = """\t.text
\t.ent\tfunc
func:
lbu\t$2,0($16)
nop
andi\t$2,$2,0x00ff
$L9:
beq\t$2,$0,$L40
addu\t$17,$17,1
$L40:
j\t$31
nop
"""

# direct-call path: the andi line blanked in place (blank lines carry no
# bytes for the assembler)
EXPECTED_DIRECT = SAMPLE.replace("andi\t$2,$2,0x00ff\n", "\n")
# CLI path: main() skips blank lines and flushes instruction runs through
# apply_rules on STRIPPED lines (directives and label lines pass through
# untouched) - the established cc_post output convention
EXPECTED_CLI = """\t.text
\t.ent\tfunc
func:
lbu\t$2,0($16)
nop
$L9:
beq\t$2,$0,$L40
addu\t$17,$17,1
$L40:
j\t$31
nop
"""


class TestRule20Direct(unittest.TestCase):
    def test_live_shape_blanks_the_andi(self):
        lines = SAMPLE.splitlines()
        out, n = cc_post._rule20_vol_extend(lines)
        self.assertEqual(n, 1)
        self.assertEqual(out, EXPECTED_DIRECT.splitlines())

    def test_no_nop_variant_matches(self):
        # maspsx's load-use fill is optional: lbu/andi/label/beq
        sample = "lbu\t$3,0($4)\nandi\t$3,$3,0x00ff\n$L2:\nbne\t$3,$0,$L3\n"
        out, n = cc_post._rule20_vol_extend(sample.splitlines())
        self.assertEqual(n, 1)
        self.assertEqual(out[1], "")

    def test_raw_maspsx_debug_nop_matches(self):
        # the LIVE regression (window cron-202611070146): raw maspsx emits
        # the load-use fill DEBUG-annotated, and the prepasses run BEFORE
        # main's NOP normalization - the walk must accept that form
        sample = ("lbu\t$2,0($16)\n"
                  "nop # DEBUG: Reuse of '$2'. 'andi\\t$2,$2,0x00ff' "
                  "does not use $at\n"
                  "andi\t$2,$2,0x00ff\n"
                  "$L9:\n"
                  "beq\t$2,$0,$L40\n")
        out, n = cc_post._rule20_vol_extend(sample.splitlines())
        self.assertEqual(n, 1)
        self.assertEqual(out[2], "")

    def test_zero_spelling_matches(self):
        sample = "lbu\t$4,0($5)\nandi\t$4,$4,0x00ff\nbeq\t$4,$zero,$L9\n"
        out, n = cc_post._rule20_vol_extend(sample.splitlines())
        self.assertEqual(n, 1)
        self.assertEqual(out[1], "")

    def test_beqz_bnez_spellings_match(self):
        for br in ("beqz\t$2,$L9", "bnez\t$2,$L9"):
            sample = "lbu\t$2,0($16)\nandi\t$2,$2,0x00ff\n" + br + "\n"
            out, n = cc_post._rule20_vol_extend(sample.splitlines())
            self.assertEqual(n, 1, br)
            self.assertEqual(out[1], "")

    def test_no_lbu_never_matches(self):
        # the src law: the previous real instruction is not the lbu
        sample = "addu\t$2,$3,$4\nandi\t$2,$2,0x00ff\nbeq\t$2,$0,$L40\n"
        self.assertIsNone(cc_post._rule20_vol_extend(sample.splitlines()))

    def test_src_mismatch_never_matches(self):
        # lbu dest differs from the andi src
        sample = "lbu\t$3,0($16)\nandi\t$2,$2,0x00ff\nbeq\t$2,$0,$L40\n"
        self.assertIsNone(cc_post._rule20_vol_extend(sample.splitlines()))

    def test_dest_mismatch_never_matches(self):
        # the next branch tests a register the andi did not write
        sample = "lbu\t$2,0($16)\nandi\t$2,$2,0x00ff\nbeq\t$5,$0,$L40\n"
        self.assertIsNone(cc_post._rule20_vol_extend(sample.splitlines()))

    def test_no_branch_never_matches(self):
        # the andi dest's next reader is not a zero-test
        sample = "lbu\t$2,0($16)\nandi\t$2,$2,0x00ff\naddu\t$5,$2,$3\n"
        self.assertIsNone(cc_post._rule20_vol_extend(sample.splitlines()))

    def test_wrong_imm_never_matches(self):
        sample = "lbu\t$2,0($16)\nandi\t$2,$2,0x003f\nbeq\t$2,$0,$L40\n"
        self.assertIsNone(cc_post._rule20_vol_extend(sample.splitlines()))

    def test_intervening_real_insn_never_matches(self):
        # one nop is the tolerated load-use fill; a second real insn
        # between the lbu and the andi breaks the src law
        sample = ("lbu\t$2,0($16)\nnop\nnop\nandi\t$2,$2,0x00ff\n"
                  "beq\t$2,$0,$L40\n")
        self.assertIsNone(cc_post._rule20_vol_extend(sample.splitlines()))

    def test_plain_insn_between_lbu_and_andi_never_matches(self):
        sample = ("lbu\t$2,0($16)\naddu\t$16,$16,1\nandi\t$2,$2,0x00ff\n"
                  "beq\t$2,$0,$L40\n")
        self.assertIsNone(cc_post._rule20_vol_extend(sample.splitlines()))

    def test_two_sites_count_two(self):
        sample = ("lbu\t$2,0($16)\nandi\t$2,$2,0x00ff\nbeq\t$2,$0,$L40\n"
                  "lbu\t$5,0($6)\nandi\t$5,$5,0x00ff\nbnez\t$5,$L48\n")
        out, n = cc_post._rule20_vol_extend(sample.splitlines())
        self.assertEqual(n, 2)
        self.assertEqual(out[1], "")
        self.assertEqual(out[4], "")


class TestRule20CLI(unittest.TestCase):
    def _run_cli(self, args, text):
        with tempfile.NamedTemporaryFile("w", suffix=".mas.s",
                                         delete=False) as f:
            f.write(text)
            path = f.name
        try:
            return subprocess.run(
                [sys.executable, POST] + args + [path],
                capture_output=True, text=True), path
        finally:
            pass

    def test_cli_blanks_andi_and_passes(self):
        r, path = self._run_cli(["--vol-extend", "1"], SAMPLE)
        try:
            self.assertEqual(r.returncode, 0, r.stderr)
            with open(path) as f:
                self.assertEqual(f.read(), EXPECTED_CLI)
        finally:
            os.unlink(path)

    def test_cli_marker_absent_is_noop(self):
        # gate 2: the rule cannot perturb unmarked units - without the
        # flag the andi stays and the output is the plain cc_post pass
        # (SAMPLE's instruction lines carry no leading whitespace, so the
        # strip convention leaves them verbatim)
        r, path = self._run_cli([], SAMPLE)
        try:
            self.assertEqual(r.returncode, 0, r.stderr)
            with open(path) as f:
                self.assertEqual(f.read(), SAMPLE)
        finally:
            os.unlink(path)

    def test_cli_count_mismatch_loud_fails(self):
        # two sites in the file, marker expects one
        text = ("lbu\t$2,0($16)\nandi\t$2,$2,0x00ff\nbeq\t$2,$0,$L40\n"
                "lbu\t$5,0($6)\nandi\t$5,$5,0x00ff\nbnez\t$5,$L48\n")
        r, _ = self._run_cli(["--vol-extend", "1"], text)
        self.assertEqual(r.returncode, 3)
        self.assertIn("blanked 2 site(s)", r.stderr)

    def test_cli_no_site_loud_fails(self):
        r, _ = self._run_cli(["--vol-extend", "1"],
                             "addu\t$2,$3,$4\nandi\t$2,$2,0x00ff\n")
        self.assertEqual(r.returncode, 3)
        self.assertIn("no vol-extend site", r.stderr)

    def test_cli_bare_flag_usage_error(self):
        r, _ = self._run_cli(["--vol-extend"], SAMPLE)
        self.assertEqual(r.returncode, 2)
        self.assertIn("usage", r.stderr)

    def test_cli_bad_count_usage_error(self):
        r, _ = self._run_cli(["--vol-extend", "x"], SAMPLE)
        self.assertEqual(r.returncode, 2)
        self.assertIn("requires an integer count", r.stderr)


if __name__ == "__main__":
    unittest.main()

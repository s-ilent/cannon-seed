#!/usr/bin/env python3
"""test_cc_post_rule22.py - rule 22 (reg-field).

The explicit-site register rewrite (survey
docs/CC_POST_RULE_CLASSES.md section 6; window cron-202611071331): the
func_8007736C walk block homes the 0x40 cache counter i in $s4 (sep's
dead register) in every source shape (probes c5a/c5b - four declaration
scopes/orders, all identical), where retail homes it in $s2 (level's
dead register). The i-home is allocation-order driven, unreachable by
source steering, and the textual .s cannot prove liveness - so the
marker's explicit site list IS the attestation: each site is
`label:insn-index:mnemonic`, every site is shape-verified (mnemonic +
the old register token present), any mismatch is a loud exit 3, and the
judge verdict is the semantic gate. Never default-on.

The shape here is the LIVE c3 walk block (func_8007736C.mas.s, window
cron-202611071331, numeric registers post-normalization): the i-init
under func, the increment and compare under $L31.

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

# The live c3 walk block: rec/name/i inits, the at-split empty check, the
# found call, the loop tail (i++, compare, back-edge with the off delay).
SAMPLE = """\t.text
\t.ent\tfunc
func:
la\t$16,D_8014788C-8
addu\t$19,$16,8
addu\t$20,$0,$zero
$L31:
lui\t$at,%hi(D_8014788C)
addu\t$at,$at,$17
lbu\t$2,%lo(D_8014788C)($at)
nop
beq\t$2,$0,$L29
addu\t$4,$19,$zero
addu\t$16,$16,24
addu\t$19,$19,24
addu\t$20,$20,1
slt\t$2,$20,64
bne\t$2,$0,$L31
addu\t$17,$17,24
$L29:
j\t$31
nop
"""

SITES = "func:2:addu,$L31:8:addu,$L31:9:slt"
MARKER = "/* cc-post: reg-field $20 $18 %s */\n" % SITES


def staged(text):
    return text.replace("func:\n", "func:\n" + MARKER, 1)


# direct-call path: the three sites rewritten in place, everything else
# byte-identical
EXPECTED_DIRECT = (SAMPLE
                   .replace("addu\t$20,$0,$zero\n", "addu\t$18,$0,$zero\n")
                   .replace("addu\t$20,$20,1\n", "addu\t$18,$18,1\n")
                   .replace("slt\t$2,$20,64\n", "slt\t$2,$18,64\n"))
# CLI path: main() strips instruction lines; directives and label lines
# pass through untouched - the established cc_post output convention
EXPECTED_CLI = "\n".join(
    ln if ln.strip() == "" or not cc_post.is_instruction(ln)
    else ln.strip()
    for ln in EXPECTED_DIRECT.splitlines()) + "\n"


class TestRule22Direct(unittest.TestCase):
    def test_live_shape_rewrites_all_three_sites(self):
        sites = cc_post._parse_reg_field_sites(SITES)
        self.assertEqual(sites, [("func", 2, "addu"),
                                 ("$L31", 8, "addu"),
                                 ("$L31", 9, "slt")])
        out = cc_post._rule22_reg_field(
            SAMPLE.splitlines(), "$20", "$18", sites)
        self.assertEqual(out, EXPECTED_DIRECT.splitlines())

    def test_both_register_fields_rewritten_in_one_insn(self):
        lines = ["a:",
                 "addu\t$20,$20,1"]
        out = cc_post._rule22_reg_field(lines, "$20", "$18",
                                        [("a", 0, "addu")])
        self.assertEqual(out, ["a:", "addu\t$18,$18,1"])

    def test_token_safety_2_never_matches_22(self):
        lines = ["a:",
                 "addu\t$2,$22,$22"]
        out = cc_post._rule22_reg_field(lines, "$22", "$18",
                                        [("a", 0, "addu")])
        self.assertEqual(out, ["a:", "addu\t$2,$18,$18"])
        out = cc_post._rule22_reg_field(lines, "$2", "$18",
                                        [("a", 0, "addu")])
        self.assertEqual(out, ["a:", "addu\t$18,$22,$22"])

    def test_named_registers_accepted(self):
        lines = ["a:",
                 "addu\t$s4,$s4,1"]
        out = cc_post._rule22_reg_field(lines, "$s4", "$s2",
                                        [("a", 0, "addu")])
        self.assertEqual(out, ["a:", "addu\t$s2,$s2,1"])

    def test_unknown_label_fails(self):
        self.assertIsNone(cc_post._rule22_reg_field(
            SAMPLE.splitlines(), "$20", "$18",
            [("nope", 0, "addu")]))

    def test_index_out_of_range_fails(self):
        self.assertIsNone(cc_post._rule22_reg_field(
            SAMPLE.splitlines(), "$20", "$18",
            [("$L31", 99, "addu")]))

    def test_mnemonic_mismatch_fails(self):
        self.assertIsNone(cc_post._rule22_reg_field(
            SAMPLE.splitlines(), "$20", "$18",
            [("$L31", 9, "addu")]))  # the compare is slt, not addu

    def test_old_token_absent_fails(self):
        self.assertIsNone(cc_post._rule22_reg_field(
            SAMPLE.splitlines(), "$20", "$18",
            [("$L31", 5, "addu")]))  # addu $4,$19,$zero - no $20

    def test_same_old_new_fails(self):
        self.assertIsNone(cc_post._rule22_reg_field(
            SAMPLE.splitlines(), "$20", "$20",
            [("func", 2, "addu")]))

    def test_duplicate_site_second_pass_fails(self):
        self.assertIsNone(cc_post._rule22_reg_field(
            SAMPLE.splitlines(), "$20", "$18",
            [("func", 2, "addu"), ("func", 2, "addu")]))

    def test_site_list_parser(self):
        self.assertIsNone(cc_post._parse_reg_field_sites(""))
        self.assertIsNone(cc_post._parse_reg_field_sites("a:1"))
        self.assertIsNone(cc_post._parse_reg_field_sites("a:x:addu"))
        self.assertIsNone(cc_post._parse_reg_field_sites("a:-1:addu"))
        self.assertEqual(
            cc_post._parse_reg_field_sites("a:0:nop"),
            [("a", 0, "nop")])


class TestRule22Cli(unittest.TestCase):
    def run_post(self, text, extra_args=()):
        with tempfile.NamedTemporaryFile("w", suffix=".mas.s",
                                         delete=False) as f:
            f.write(text)
            path = f.name
        r = subprocess.run(
            [sys.executable, POST] + list(extra_args) + [path],
            capture_output=True, text=True)
        content = open(path).read()
        os.unlink(path)
        return r, content

    def test_flag_drives_the_rewrite(self):
        # the marker lives in the .c source; cc.sh greps it out and passes
        # the args on - the .mas.s cc_post.py sees carries NO comment lines
        # (this is why is_instruction-counted site indices are stable), so
        # the CLI test feeds the plain sample plus the cc.sh-extracted flags
        r, content = self.run_post(
            SAMPLE, ["--reg-field", "$20", "$18", SITES])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(content, EXPECTED_CLI)

    def test_marker_absent_is_byte_identical(self):
        r, content = self.run_post(SAMPLE)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(content, SAMPLE)

    def test_bad_mnemonic_loud_fails_exit3(self):
        r, _ = self.run_post(
            SAMPLE, ["--reg-field", "$20", "$18",
                     SITES.replace("$L31:9:slt", "$L31:9:addu")])
        self.assertEqual(r.returncode, 3)
        self.assertIn("rule 22", r.stderr)

    def test_missing_label_loud_fails_exit3(self):
        r, _ = self.run_post(
            SAMPLE, ["--reg-field", "$20", "$18",
                     SITES.replace("func:2:addu", "nope:2:addu")])
        self.assertEqual(r.returncode, 3)
        self.assertIn("rule 22", r.stderr)

    def test_malformed_site_list_exits3(self):
        r, _ = self.run_post(
            SAMPLE, ["--reg-field", "$20", "$18", "func:2"])
        self.assertEqual(r.returncode, 3)
        self.assertIn("malformed site list", r.stderr)

    def test_bare_flag_is_usage_error_exit2(self):
        with tempfile.NamedTemporaryFile("w", suffix=".mas.s",
                                         delete=False) as f:
            f.write(SAMPLE)
            path = f.name
        try:
            r = subprocess.run([sys.executable, POST, "--reg-field", path],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 2)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()

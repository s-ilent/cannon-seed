"""test_cc_post_rule21.py - rule 21 (import-order).

The prologue import-pair order class (survey
docs/CC_POST_RULE_CLASSES.md section 5; window cron-202611070716): the
func_8007736C built prologue interleaves (sw $s3,0x3c / addu $s3,$a1)
before (sw $s5,0x44 / addu $s5,$a0) where retail imports $s5 FIRST. The
transform reorders each listed register's (save, copy) items to the front
in the listed order, leaving the pure saves (ra, other callee-saves) in
their built order. All three source-side order levers are refuted (c3 /
kr1 / c6), so the reorder is a post-pass.

Covers the module API and the cc_post.py CLI (subprocess) per the banked
cron-202611040743 lesson (a direct-call test alone passed while main()
was broken - the r16 CLI regression class). The live judge measurement
rides the window's worklog (func_8007736C c3 staging).
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

# The real c3 built prologue (judge artifacts build/judge/
# func_8007736C.mas.s, window cron-202611070716): the guard loads precede
# the frame, the (save, copy) pairs interleave, then the pure saves, then
# the body.
BASE = """\\t.text
\\t.ent\\tfunc
func:
.frame\\t$sp,80,$31
.mask\\t0x807f0000,-4
lw\\t$3,D_800C8028
lw\\t$2,D_800C7CFC
subu\\t$sp,$sp,80
sw\\t$19,60($sp)
addu\\t$19,$5,$zero
sw\\t$21,68($sp)
addu\\t$21,$4,$zero
sw\\t$31,76($sp)
sw\\t$22,72($sp)
sw\\t$20,64($sp)
sw\\t$18,56($sp)
sw\\t$17,52($sp)
beq\\t$3,$2,$L2
sw\\t$16,48($sp)
jal\\tfunc_80077678
nop
addu\\t$2,$0,$zero
$L37:
lw\\t$31,76($sp)
j\\t$31
addu\\t$sp,$sp,80
\\t.end\\tfunc
""".replace("\\t", "\t")

# retail's pair order: s5 first, then s3 (wordmap [20]-[32], 2026-11-07)
EXPECTED_REGION = [
    "subu\t$sp,$sp,80",
    "sw\t$21,68($sp)",
    "addu\t$21,$4,$zero",
    "sw\t$19,60($sp)",
    "addu\t$19,$5,$zero",
    "sw\t$31,76($sp)",      # the pure saves keep their built order
    "sw\t$22,72($sp)",
    "sw\t$20,64($sp)",
    "sw\t$18,56($sp)",
    "sw\t$17,52($sp)",
    "beq\t$3,$2,$L2",
]


class Rule21ApiTest(unittest.TestCase):
    def setUp(self):
        self.lines = BASE.splitlines()

    def test_transform(self):
        out = cc_post._rule21_import_order(self.lines, ["$21", "$19"])
        self.assertIsNotNone(out)
        i = out.index("subu\t$sp,$sp,80")
        self.assertEqual(out[i:i + len(EXPECTED_REGION)], EXPECTED_REGION)
        # the guard loads and the body are untouched
        self.assertIn("lw\t$3,D_800C8028", out)
        self.assertIn("jal\tfunc_80077678", out)
        self.assertIn("lw\t$31,76($sp)", out)
        # pure reorder: the same insn multiset, no register field changes
        body = [ln for ln in out if ln and not ln.startswith((".", "\t"))
                and not ln.endswith(":")]
        base_body = [ln for ln in self.lines if ln
                     and not ln.startswith((".", "\t"))
                     and not ln.endswith(":")]
        self.assertEqual(sorted(body), sorted(base_body))

    def test_marker_absent_noop(self):
        # gate 2: without the flag the rule never runs - the CLI leaves
        # the file byte-identical
        with tempfile.NamedTemporaryFile("w", suffix=".s", delete=False) as f:
            f.write(BASE)
            path = f.name
        try:
            r = subprocess.run([sys.executable, POST, path],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(open(path).read(), BASE)
        finally:
            os.unlink(path)

    def test_wrong_set_refused(self):
        # $20 has no import copy in the region: set inequality
        self.assertIsNone(
            cc_post._rule21_import_order(self.lines, ["$21", "$20"]))

    def test_partial_set_refused(self):
        self.assertIsNone(cc_post._rule21_import_order(self.lines, ["$21"]))

    def test_dependent_copy_refused(self):
        # a copy reading another copy's dest would change semantics
        lines = BASE.splitlines()
        i = lines.index("addu\t$19,$5,$zero")
        lines[i] = "addu\t$19,$21,$zero"
        self.assertIsNone(cc_post._rule21_import_order(lines, ["$21", "$19"]))

    def test_duplicate_save_refused(self):
        lines = BASE.splitlines()
        i = lines.index("sw\t$22,72($sp)")
        lines[i] = "sw\t$21,72($sp)"
        self.assertIsNone(cc_post._rule21_import_order(lines, ["$21", "$19"]))

    def test_no_frame_refused(self):
        lines = [ln for ln in BASE.splitlines()
                 if not ln.startswith("subu\t$sp")]
        self.assertIsNone(cc_post._rule21_import_order(lines, ["$21", "$19"]))

    def test_empty_order_refused(self):
        self.assertIsNone(cc_post._rule21_import_order(self.lines, []))
        self.assertIsNone(cc_post._rule21_import_order(self.lines, ["$21",
                                                                    "$21"]))


class Rule21CliTest(unittest.TestCase):
    def test_cli_path(self):
        with tempfile.NamedTemporaryFile("w", suffix=".s", delete=False) as f:
            f.write(BASE)
            path = f.name
        try:
            r = subprocess.run([sys.executable, POST, "--import-order",
                                "$21,$19", path],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            out = open(path).read().splitlines()
            i = out.index("subu\t$sp,$sp,80")
            self.assertEqual(out[i + 1:i + 3],
                             ["sw\t$21,68($sp)", "addu\t$21,$4,$zero"])
        finally:
            os.unlink(path)

    def test_cli_shape_mismatch_is_loud(self):
        with tempfile.NamedTemporaryFile("w", suffix=".s", delete=False) as f:
            f.write(BASE)
            path = f.name
        try:
            r = subprocess.run([sys.executable, POST, "--import-order",
                                "$21,$20", path],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 3)
            self.assertIn("import-order", r.stderr)
        finally:
            os.unlink(path)

    def test_cli_bare_flag_usage_error(self):
        with tempfile.NamedTemporaryFile("w", suffix=".s", delete=False) as f:
            f.write(BASE)
            path = f.name
        try:
            r = subprocess.run([sys.executable, POST, "--import-order",
                                path], capture_output=True, text=True)
            self.assertEqual(r.returncode, 2)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()

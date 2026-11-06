"""test_cc_post_rule19.py - rule 19 (site-fresh-const).

The hoisted-constant spill class (survey docs/CC_POST_RULE_CLASSES.md
section 3; window cron-202611070601): gcc 2.6.3 materializes a
loop-invariant constant into a callee-saved home (hoisted addiu + sw/lw
spill pair) where retail materializes it fresh at the compare site into
$2 and never saves the home. The transform retargets the compare,
inserts the fresh def, deletes the def + pair, and shifts the $sp
displacements above the deleted slot -4 while the frame TOTAL stays
(retail-decoded: `addiu $sp,$sp,-80`, ra at 72, freed slot as top pad).

Covers the module API and the cc_post.py CLI (subprocess) per the
banked cron-202611040743 lesson (a direct-call test alone passed while
main() was broken - the r16 CLI regression class). The live judge
measurement rides the window's worklog (func_8007736C c3 staging).
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

# A synthetic unit with the c3 shape: prologue saves s0-s6 + ra, the
# hoisted def at $L4's tail, the compare consuming $22 mid-file, the
# epilogue reloads. maspsx's `#nop # DEBUG` comment quotes a real insn
# (the comment-pollution guard's reason).
BASE = """\\t.text
\\t.ent\\tfunc
func:
.frame\\t$sp,80,$31
.mask\\t0x807f0000,-4
subu\\t$sp,$sp,80
sw\\t$31,76($sp)
sw\\t$22,72($sp)
sw\\t$21,68($sp)
sw\\t$16,48($sp)
#nop # DEBUG: 'lw\\t$22,72($sp)' does not load from $31
$L4:
addiu\\t$22,$zero,-1
$L7:
addu\\t$4,$2,$zero
beq\\t$4,$22,$L38
nop
addu\\t$2,$0,$zero
$L37:
lw\\t$31,76($sp)
lw\\t$22,72($sp)
lw\\t$21,68($sp)
lw\\t$16,48($sp)
j\\t$31
addu\\t$sp,$sp,80
\\t.end\\tfunc
""".replace("\\t", "\t")

EXPECTED_PROLOGUE = [
    "sw\t$31,72($sp)",      # ra takes the freed slot's place
    "",                     # the s6 save deleted
    "sw\t$21,68($sp)",
]
EXPECTED_SITE = [
    "addu\t$4,$2,$zero",
    "addiu\t$2,$zero,-1",   # the fresh def
    "beq\t$4,$2,$L38",      # retargeted
]
EXPECTED_EPILOGUE = [
    "lw\t$31,72($sp)",
    "",                     # the s6 reload deleted
]
EXPECTED_FRAME = ".frame\t$sp,80,$31"      # TOTAL unchanged (retail-decoded)
EXPECTED_SUBU = "subu\t$sp,$sp,80"


class Rule19ApiTest(unittest.TestCase):
    def setUp(self):
        self.lines = BASE.splitlines()

    def test_transform(self):
        out = cc_post._rule19_site_fresh_const(self.lines, "-1", "$22")
        self.assertIsNotNone(out)
        self.assertIn(EXPECTED_FRAME, out)
        self.assertIn(EXPECTED_SUBU, out)
        self.assertIn(".mask\t0x803f0000,-4", out)  # the s6 bit clears
        i = out.index("sw\t$31,72($sp)")
        self.assertEqual(out[i + 1:i + 3], ["", "sw\t$21,68($sp)"])
        j = out.index("addu\t$4,$2,$zero")
        self.assertEqual(out[j:j + 3], EXPECTED_SITE)
        k = out.index("$L37:")
        self.assertEqual(out[k + 1:k + 4], EXPECTED_EPILOGUE)
        # the hoisted def is gone; s6 has zero references left
        self.assertNotIn("addiu\t$22,$zero,-1", out)
        body = [ln for ln in out if ln and not ln.startswith("#")]
        self.assertEqual(sum("$22" in ln for ln in body), 0)

    def test_extra_ref_refused(self):
        lines = BASE.splitlines()
        lines.append("addu\t$5,$22,$zero")
        self.assertIsNone(cc_post._rule19_site_fresh_const(lines, "-1", "$22"))

    def test_missing_def_refused(self):
        lines = [ln for ln in BASE.splitlines()
                 if ln.strip() != "addiu\t$22,$zero,-1"]
        self.assertIsNone(cc_post._rule19_site_fresh_const(lines, "-1", "$22"))

    def test_branch_predecessor_refused(self):
        lines = BASE.splitlines()
        i = lines.index("addu\t$4,$2,$zero")
        lines[i] = "j\t$31"
        self.assertIsNone(cc_post._rule19_site_fresh_const(lines, "-1", "$22"))

    def test_comment_lines_do_not_pollute(self):
        # the DEBUG comment quotes `lw $22,72($sp)`; the census must
        # still see exactly one real sw and one real lw
        out = cc_post._rule19_site_fresh_const(BASE.splitlines(), "-1", "$22")
        self.assertIsNotNone(out)


class Rule19CliTest(unittest.TestCase):
    def test_cli_path(self):
        with tempfile.NamedTemporaryFile("w", suffix=".s", delete=False) as f:
            f.write(BASE)
            path = f.name
        try:
            r = subprocess.run([sys.executable, POST, "--site-fresh-const",
                                "-1", "$22", path],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            out = open(path).read().splitlines()
            self.assertIn("addiu\t$2,$zero,-1", out)
            self.assertIn("beq\t$4,$2,$L38", out)
        finally:
            os.unlink(path)

    def test_cli_bare_flag_usage_error(self):
        with tempfile.NamedTemporaryFile("w", suffix=".s", delete=False) as f:
            f.write(BASE)
            path = f.name
        try:
            r = subprocess.run([sys.executable, POST, "--site-fresh-const",
                                path], capture_output=True, text=True)
            self.assertEqual(r.returncode, 2)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()

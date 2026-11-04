#!/usr/bin/env python3
"""test_cc_post_rule17.py - rule 17 (merge-polarity invert+trampoline).

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

# The built merge site shape (g3org_jp SsVabOpenHeadWithMode draft20
# .mas.s, window cron-202611041358): beq $2,$0,$L19 with a filled
# delay, body falling through, the far-err tail defined forward.
SAMPLE = """\t.text
\t.globl\tSsVabOpenHeadWithMode
SsVabOpenHeadWithMode:
\tbeq\t$2,$0,$L19
\taddu\t$4,$19,$zero
\tsll\t$2,$5,2
\tsw\t$4,0x0($at)
\taddu\t$5,$5,1
$L19:
\tjal\t_spu_setInTransfer
\taddu\t$4,$0,$zero
\tj\t$31
\tnop
"""

EXPECTED = """\t.text
\t.globl\tSsVabOpenHeadWithMode
SsVabOpenHeadWithMode:
\tbne\t$2,$0,$Lr17c
\taddu\t$4,$19,$zero
\tj\t$L19
\taddu\t$4,$0,$zero
$Lr17c:
\tsll\t$2,$5,2
\tsw\t$4,0x0($at)
\taddu\t$5,$5,1
$L19:
\tjal\t_spu_setInTransfer
\taddu\t$4,$0,$zero
\tj\t$31
\tnop
"""


def run_cli(*args):
    return subprocess.run([sys.executable, POST, *args],
                          capture_output=True, text=True)


class Rule17Direct(unittest.TestCase):
    def test_invert_and_trampoline(self):
        out = cc_post._rule17_on_file(
            SAMPLE.splitlines(), "$L19", jdelay=("addu", "4", "0"))
        self.assertIsNotNone(out)
        norm = lambda s: "\n".join(l.strip() for l in s.strip().splitlines())
        self.assertEqual(norm("\n".join(out)), norm(EXPECTED))

    def test_jdelay_ops(self):
        # li/addiu delegate to the rule16 materializers; addu is the
        # gcc 2.6.3 zero-arg spelling; nop is the empty slot.
        self.assertEqual(cc_post._r17_jdelay_line(("li", "v0", "-1")),
                         "\tli\t$v0,-1")
        self.assertEqual(cc_post._r17_jdelay_line(("addiu", "a0", "0")),
                         "\taddiu\t$a0,$zero,0")
        self.assertEqual(cc_post._r17_jdelay_line(("addu", "a0", "0")),
                         "\taddu\t$a0,$0,$zero")
        self.assertEqual(cc_post._r17_jdelay_line(("addu", "4", "0")),
                         "\taddu\t$4,$0,$zero")
        self.assertEqual(cc_post._r17_jdelay_line(("nop", "0", "0")),
                         "\tnop")
        with self.assertRaises(SystemExit) as cm:
            cc_post._r17_jdelay_line(("sll", "v0", "16"))
        self.assertEqual(cm.exception.code, 3)

    def test_no_anchor_match(self):
        self.assertIsNone(cc_post._rule17_on_file(
            SAMPLE.splitlines(), "$L99", jdelay=("nop", "0", "0")))

    def test_backward_target_never_matches(self):
        # The trampoline only makes sense to a FORWARD tail; a beq whose
        # target is already defined above it is a loop back-edge.
        lines = SAMPLE.replace("$L19:", "$L17:",
                               1).replace("$L17:", "", 0)
        # move the label definition BEFORE the branch
        backward = ("\t.text\n$L19:\n"
                    + SAMPLE.split("$L19:\n", 1)[0].split("\n", 2)[2])
        self.assertIsNone(cc_post._rule17_on_file(
            backward.splitlines(), "$L19", jdelay=("nop", "0", "0")))

    def test_empty_delay_never_matches(self):
        lines = SAMPLE.replace("\tbeq\t$2,$0,$L19\n\taddu\t$4,$19,$zero",
                               "\tbeq\t$2,$0,$L19\n$L19x:")
        self.assertIsNone(cc_post._rule17_on_file(
            lines.splitlines(), "$L19", jdelay=("nop", "0", "0")))

    def test_beqz_spelling(self):
        lines = SAMPLE.replace("\tbeq\t$2,$0,$L19", "\tbeqz\t$2,$L19")
        out = cc_post._rule17_on_file(lines.splitlines(), "$L19",
                                      jdelay=("nop", "0", "0"))
        self.assertIsNotNone(out)
        text = "\n".join(out)
        self.assertIn("\tbne\t$2,$0,$Lr17c", text)
        self.assertIn("\tj\t$L19", text)
        self.assertIn("\tnop\n$Lr17c:", text)

    def test_zero_spelling_preserved(self):
        lines = SAMPLE.replace("\tbeq\t$2,$0,$L19",
                               "\tbeq\t$2,$zero,$L19")
        out = cc_post._rule17_on_file(lines.splitlines(), "$L19",
                                      jdelay=("nop", "0", "0"))
        self.assertIn("\tbne\t$2,$zero,$Lr17c", "\n".join(out))


def cc_post_index_of(lines, needle):
    for i, ln in enumerate(lines):
        if needle in ln:
            return i
    return -1




class Rule17Cli(unittest.TestCase):
    def test_happy_path(self):
        with tempfile.NamedTemporaryFile("w", suffix=".mas.s",
                                         delete=False) as f:
            f.write(SAMPLE)
            path = f.name
        try:
            r = run_cli("--rule17", "$L19", "jdelay", "addu", "4", "0",
                        path)
            self.assertEqual(r.returncode, 0, r.stderr)
            norm = lambda s: "\n".join(l.strip() for l in s.strip().splitlines())
            self.assertEqual(norm(open(path).read()), norm(EXPECTED))
        finally:
            os.unlink(path)

    def test_no_site_is_loud(self):
        with tempfile.NamedTemporaryFile("w", suffix=".mas.s",
                                         delete=False) as f:
            f.write(SAMPLE.replace("$L19:", "$Lother:", 1))
            path = f.name
        try:
            r = run_cli("--rule17", "$L19", "jdelay", "addu", "a0", "0",
                        path)
            self.assertEqual(r.returncode, 3)
            self.assertIn("rule 17", r.stderr)
        finally:
            os.unlink(path)

    def test_usage_short_args(self):
        with tempfile.NamedTemporaryFile("w", suffix=".mas.s",
                                         delete=False) as f:
            f.write(SAMPLE)
            path = f.name
        try:
            r = run_cli("--rule17", "$L19", "jdelay", "addu", path)
            self.assertEqual(r.returncode, 2)
        finally:
            os.unlink(path)

    def test_bad_op_rejected_at_parse(self):
        with tempfile.NamedTemporaryFile("w", suffix=".mas.s",
                                         delete=False) as f:
            f.write(SAMPLE)
            path = f.name
        try:
            r = run_cli("--rule17", "$L19", "jdelay", "xor", "a0", "0",
                        path)
            self.assertEqual(r.returncode, 2)
            self.assertIn("jdelay op", r.stderr)
        finally:
            os.unlink(path)

    def test_rule16_still_flows(self):
        # Shared-parser regression guard: the rule16 CLI path must keep
        # working after the rule17 parsing block was added beside it.
        sample = ("\t.text\nf:\n\tbeq\t$2,$3,$Ltail\n\tli\t$v0,-1\n"
                  "\taddu\t$4,$4,$zero\n$Ltail:\n\tj\t$31\n\tnop\n")
        with tempfile.NamedTemporaryFile("w", suffix=".mas.s",
                                         delete=False) as f:
            f.write(sample)
            path = f.name
        try:
            r = run_cli("--rule16", "jdelay", "li", "v0", "-1", path)
            self.assertEqual(r.returncode, 0, r.stderr)
            out = open(path).read()
            self.assertIn("bne\t$2,$3,$Lr16c", out)
            self.assertIn("j\t$Ltail", out)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()

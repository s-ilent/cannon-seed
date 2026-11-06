"""tests/test_wordmap.py - the wordmap tool's pure classification core.

Covers tools/wordmap.py (the in-repo judge-slice word map, the survey's
site-list source): the field classifier for every tag class, the diff
loop's truncation/step behaviour, and the VA math. No repo fixtures, no
baselines, no builds - the repo-coupled main() is thin by design.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "tools"))

import wordmap  # noqa: E402


def le(w: int) -> bytes:
    return w.to_bytes(4, "little")


class ClassifyTest(unittest.TestCase):
    def test_same_op_imm(self):
        # lui $2,0x8014 vs lui $2,0x8018 - the %hi displacement class
        self.assertEqual(wordmap.classify(le(0x3C028014), le(0x3C028018)),
                         "same-op-imm")

    def test_same_op_imm_branch_offset(self):
        # beq $4,$2,+2 vs beq $4,$2,+4 - the branch-offset cascade class
        self.assertEqual(wordmap.classify(le(0x10820002), le(0x10820004)),
                         "same-op-imm")

    def test_same_op_reg(self):
        # beq $4,$2,+2 vs beq $4,$3,+2 - the compare-retarget class
        # (the built beq $4,$22 vs the retail-fresh beq $4,$2 shape)
        self.assertEqual(wordmap.classify(le(0x10820002), le(0x10830002)),
                         "same-op-reg")

    def test_same_op_reg_i_type(self):
        # addiu $16,$4,8 vs addiu $16,$5,8 (op 9): same imm, rs differs
        self.assertEqual(wordmap.classify(le(0x27100008), le(0x27110008)),
                         "same-op-reg")

    def test_same_op_mixed(self):
        # sw $16,0x44($sp) vs sw $17,0x48($sp): both fields differ
        self.assertEqual(wordmap.classify(le(0xAF910044), le(0xAF930048)),
                         "same-op-mixed")

    def test_same_op_target(self):
        # j with only the target field differing
        self.assertEqual(wordmap.classify(le(0x08000123), le(0x08000456)),
                         "same-op-target")

    def test_funct(self):
        # addu $6,$4,$5 vs or $6,$4,$5 (SPECIAL, funct 0x21 vs 0x25)
        self.assertEqual(wordmap.classify(le(0x00853021), le(0x00853025)),
                         "funct")

    def test_opcode(self):
        # lui vs lw on the same low bits
        self.assertEqual(wordmap.classify(le(0x3C028014), le(0x8C028014)),
                         "opcode")

    def test_identical_words(self):
        # classify is only called on differing words, but equal fields
        # with equal everything must not crash into a wrong class
        self.assertEqual(wordmap.classify(le(0x10820002), le(0x10820002)),
                         "same-op")


class WordPairsTest(unittest.TestCase):
    def test_step_and_indexing(self):
        built = le(1) + le(2) + le(3) + le(4)
        retail = le(1) + le(9) + le(3) + le(9)
        pairs = wordmap.word_pairs(built, retail)
        self.assertEqual([i for i, _, _ in pairs], [4, 12])
        self.assertEqual(pairs[0][1], le(2))
        self.assertEqual(pairs[0][2], le(9))

    def test_min_length_truncation(self):
        built = le(1) + le(2)
        retail = le(1)
        self.assertEqual(wordmap.word_pairs(built, retail), [])

    def test_identical_is_empty(self):
        same = le(0x3C028014) * 4
        self.assertEqual(wordmap.word_pairs(same, same), [])


class VaTest(unittest.TestCase):
    def test_va_math(self):
        # BASE_VA 0x80020000, HDR 0x800, rom = yaml file offset
        self.assertEqual(wordmap.va_of(0x800, 0), 0x80020000)
        self.assertEqual(wordmap.va_of(0x800, 4), 0x80020004)


if __name__ == "__main__":
    unittest.main()

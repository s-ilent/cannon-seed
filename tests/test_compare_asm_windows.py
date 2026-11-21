"""Disc-free tests for source-only structural MIPS disassembly comparisons."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from compare_asm_windows import (
    WindowError, compare, parse_instructions, window,
)


def line(rom, va, word, mnemonic, arg="$v0, $zero, 1"):
    # spimdisasm annotation uses bytes in little-endian order.
    b = word.to_bytes(4, "little").hex().upper()
    return f"    /* {rom:05X} {va:08X} {b} */  {mnemonic} {arg}\n"


class TestAsmWindows(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.a = self.root / "a.s"
        self.b = self.root / "b.s"
        self.a.write_text(
            ".include \"macro.inc\"\n"
            + line(0x100, 0x80020100, 0x8C820010, "lw", "$v0, 0x10($a0)")
            + line(0x104, 0x80020104, 0x0C012345, "jal", "func_80048D14")
            + line(0x108, 0x80020108, 0x00000000, "nop", "")
        )
        self.b.write_text(
            ".include \"macro.inc\"\n"
            + line(0x100, 0x80020160, 0x8C820014, "lw", "$v0, 0x14($a0)")
            + line(0x104, 0x80020164, 0x0C045678, "jal", "func_80045B14")
            + line(0x108, 0x80020168, 0x00000000, "nop", "")
        )

    def sample(self):
        return (window(parse_instructions(self.a), 0x80020100, 0x8002010C),
                window(parse_instructions(self.b), 0x80020160, 0x8002016C))

    def test_disassembler_bytes_are_little_endian(self):
        insn = parse_instructions(self.a)[0x80020100]
        self.assertEqual(insn.word, 0x8C820010)
        self.assertEqual(insn.rom, 0x100)

    def test_identical_register_shape_with_different_immediates_and_targets(self):
        a, b = self.sample()
        got = compare(a, b)
        self.assertEqual(got["instructions"], 3)
        self.assertEqual(got["identical_words"], 1)
        self.assertEqual(got["changed_words"], 2)
        self.assertTrue(got["same_opcode_register_fields"])
        self.assertEqual(got["va_delta"], 0x60)
        self.assertEqual(got["calls"]["left"][0]["target"], "func_80048D14")
        self.assertFalse(got["retail_verified"])

    def test_register_mismatch_is_a_shape_change(self):
        contents = self.b.read_text().replace(
            (0x8C820014).to_bytes(4, "little").hex().upper(),
            (0x8C830014).to_bytes(4, "little").hex().upper(),
        )
        self.b.write_text(contents)
        a, b = self.sample()
        got = compare(a, b)
        self.assertFalse(got["same_opcode_register_fields"])
        self.assertEqual(got["shape_mismatches"][0]["left_va"], "0x80020100")

    def test_mnemonic_change_is_a_shape_change_even_with_same_encoding(self):
        self.b.write_text(self.b.read_text().replace("  nop \n", "  sll \n"))
        a, b = self.sample()
        self.assertFalse(compare(a, b)["same_opcode_register_fields"])

    def test_gap_refused_instead_of_smaller_denominator(self):
        self.a.write_text(self.a.read_text().replace(
            line(0x104, 0x80020104, 0x0C012345, "jal", "func_80048D14"), ""
        ))
        with self.assertRaisesRegex(WindowError, "missing words"):
            self.sample()

    def test_incorrect_end_refused(self):
        with self.assertRaisesRegex(WindowError, "4-byte"):
            window(parse_instructions(self.a), 0x80020100, 0x8002010A)

    def test_nonuniform_va_delta_refused(self):
        a, b = self.sample()
        from compare_asm_windows import Instruction
        b[1] = Instruction(b[1].rom, b[1].va + 4,
                           b[1].word, b[1].mnemonic, b[1].operands)
        with self.assertRaisesRegex(WindowError, "constant VA delta"):
            compare(a, b)

    def test_missing_asm_file_refused(self):
        with self.assertRaisesRegex(WindowError, "missing asm"):
            parse_instructions(self.root / "missing.s")

    def test_duplicate_annotation_refused(self):
        self.a.write_text(self.a.read_text() + line(
            0x200, 0x80020100, 0x8C820010, "lw", "$v0, 0x10($a0)"
        ))
        with self.assertRaisesRegex(WindowError, "duplicate VA"):
            parse_instructions(self.a)


if __name__ == "__main__":
    unittest.main()

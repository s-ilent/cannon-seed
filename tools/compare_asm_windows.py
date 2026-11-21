#!/usr/bin/env python3
"""Compare bounded, committed MIPS disassembly windows across two targets.

Uses ONLY disassembler comments from tracked asm files. Unlike a raw word
diff it distinguishes changed immediate/target fields from changed MIPS
opcode/register fields. It is a structural source-only check, NOT a
retail-byte witness or an argument for function identity on its own.

Example:
  python3 tools/compare_asm_windows.py \
      --left asm/g3_jp/nonmatchings/func_80022AFC.s \
      --left-start 0x80022E24 --left-end 0x80022FE4 \
      --right asm/g3_eu/nonmatchings/func_80022B5C.s \
      --right-start 0x80022E84 --json --require-shape
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

LINE_RE = re.compile(
    r"^\s*/\*\s*([0-9a-fA-F]+)\s+([0-9a-fA-F]{8})\s+"
    r"([0-9a-fA-F]{8})\s*\*/\s*(\S+)(?:\s+(.*?))?\s*$"
)


class WindowError(ValueError):
    pass


@dataclass(frozen=True)
class Instruction:
    rom: int
    va: int
    word: int
    mnemonic: str
    operands: str

    @property
    def shape(self) -> int:
        """Retain non-address operands (MIPS I): J opcode; I opcode+regs;
        R/COP0 special opcodes use full encoding, not a made-up immediate.
        """
        opcode = self.word >> 26
        if opcode in (2, 3):  # J/JAL encode 26-bit target; only opcode fixed
            return self.word & 0xFC000000
        if opcode in (0, 16, 17, 18, 19):  # R-type and COP opcodes
            return self.word
        return self.word & 0xFFFF0000  # I-type: opcode, rs, rt


def parse_instructions(path: Path) -> dict[int, Instruction]:
    if not path.is_file():
        raise WindowError(f"missing asm source: {path}")
    out = {}
    for lineno, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
        m = LINE_RE.match(line)
        if m is None:
            continue
        rom = int(m[1], 16)
        va = int(m[2], 16)
        # spimdisasm prints little-endian bytes, not a big-endian MIPS word.
        raw = bytes.fromhex(m[3])
        word = int.from_bytes(raw, "little")
        if va in out:
            raise WindowError(f"duplicate VA 0x{va:X} in {path}:{lineno}")
        out[va] = Instruction(rom, va, word, m[4], (m[5] or "").strip())
    if not out:
        raise WindowError(f"no annotated MIPS instructions found in {path}")
    return out


def window(insns: dict[int, Instruction], begin: int, end: int) -> list[Instruction]:
    if end <= begin or (end - begin) % 4:
        raise WindowError("window must have positive, 4-byte-aligned length")
    if begin % 4 or end % 4:
        raise WindowError("window VA must be 4-byte aligned")
    missing = [va for va in range(begin, end, 4) if va not in insns]
    if missing:
        raise WindowError(f"window has {len(missing)} missing words, "
                          f"first VA 0x{missing[0]:08X}")
    return [insns[va] for va in range(begin, end, 4)]


def compare(
    left: list[Instruction], right: list[Instruction]
) -> dict:
    if len(left) != len(right) or not left:
        raise WindowError("windows must contain the same nonzero word count")
    delta = right[0].va - left[0].va
    for a, b in zip(left, right):
        if a.va + delta != b.va:
            raise WindowError("windows are not aligned at a constant VA delta")
    unequal = [(a, b) for a, b in zip(left, right) if a.word != b.word]
    shape_changes = [(a, b) for a, b in zip(left, right)
                     if a.shape != b.shape or a.mnemonic != b.mnemonic]
    def calls(insns):
        return [{"va": f"0x{x.va:08X}", "target": x.operands.split()[0]}
                for x in insns if x.mnemonic == "jal" and x.operands]
    return {
        "source_only": True,
        "retail_verified": False,
        "left_start": f"0x{left[0].va:08X}",
        "right_start": f"0x{right[0].va:08X}",
        "va_delta": delta,
        "byte_length": len(left) * 4,
        "instructions": len(left),
        "identical_words": len(left) - len(unequal),
        "changed_words": len(unequal),
        "same_mnemonics": all(a.mnemonic == b.mnemonic
                              for a, b in zip(left, right)),
        "same_opcode_register_fields": not shape_changes,
        "shape_mismatches": [
            {"left_va": f"0x{a.va:08X}",
             "left": a.mnemonic + " " + a.operands,
             "right": b.mnemonic + " " + b.operands}
            for a, b in shape_changes
        ],
        "calls": {"left": calls(left), "right": calls(right)},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--left", type=Path, required=True)
    ap.add_argument("--right", type=Path, required=True)
    ap.add_argument("--left-start", type=lambda s: int(s, 0), required=True)
    ap.add_argument("--left-end", type=lambda s: int(s, 0), required=True)
    ap.add_argument("--right-start", type=lambda s: int(s, 0), required=True)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--require-shape", action="store_true",
                    help="exit nonzero if opcode/register shapes differ")
    args = ap.parse_args()
    try:
        left = window(parse_instructions(args.left), args.left_start,
                      args.left_end)
        right = window(parse_instructions(args.right), args.right_start,
                       args.right_start + args.left_end - args.left_start)
        result = compare(left, right)
    except WindowError as exc:
        print(f"asm-window: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"{result['left_start']} ↔ {result['right_start']} "
              f"({result['byte_length']} bytes, VA delta "
              f"{result['va_delta']:+#x})")
        print(f"{result['identical_words']}/{result['instructions']} "
              "identical words; "
              f"{result['changed_words']} changed; "
              "opcode/register shape "
              f"{'SAME' if result['same_opcode_register_fields'] else 'DIFFERENT'}")
        print("(tracked ASM only; no baseline/oracle was checked)")
    if args.require_shape and not result["same_opcode_register_fields"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

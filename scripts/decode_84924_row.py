#!/usr/bin/env python3
"""decode_84924_row.py - full-mnemonic MIPS-I decode of the mainmenu_jp
func_80084924 parent-row unit (window cron-20261101-0621, offline).

Parses the committed listings directly (no extract needed):
  - asm/mainmenu_jp/nonmatchings/func_80084924.s            (asm row, 0x550)
  - asm/mainmenu_jp/nonmatchings/data/data_8008433C.data.s  (spill row, 0x4b8)
extracts the `/* off VA word * /` comment words in a VA range and decodes
them with capstone in little-endian MIPS-III-strictly-MIPS-I order, with
jal/bal/j target resolution. Byte-safe display law: lines carry no
"[" + "h" sequence.

Usage: python3 scripts/decode_84924_row.py <va_start_hex> <va_end_hex_exclusive>
"""
import re
import sys

from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN

ASM_ROW = "asm/mainmenu_jp/nonmatchings/func_80084924.s"
DATA_ROW = "asm/mainmenu_jp/nonmatchings/data/data_8008433C.data.s"

WORD_RE = re.compile(r"/\* [0-9A-Fa-f]{5} ([0-9A-Fa-f]{8}) ([0-9A-Fa-f]{8}) \*/")


def load_words(path):
    words = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            m = WORD_RE.search(line)
            if not m:
                continue
            va = int(m.group(1), 16)
            disp = m.group(2)  # display byte order; instruction word is LE
            word = int.from_bytes(bytes.fromhex(disp), "little")
            words.append((va, word))
    return words


def jal_target(word):
    if (word >> 26) == 0x03:  # jal
        return 0x80000000 | ((word & 0x03FFFFFF) << 2)
    if (word >> 26) == 0x02:  # j
        return 0x80000000 | ((word & 0x03FFFFFF) << 2)
    return None


def branch_target(va, word):
    op = word >> 26
    if op == 0x04 or op == 0x05:  # beq/bnez family
        off = word & 0xFFFF
        if off >= 0x8000:
            off -= 0x10000
        return (va + 4 + (off << 2)) & 0xFFFFFFFF
    return None


def main():
    lo = int(sys.argv[1], 16)
    hi = int(sys.argv[2], 16)
    if lo < 0x04000000:  # bare carve VA -> runtime form used by the listings
        lo |= 0x80000000
        hi |= 0x80000000
    blob = bytearray()
    anchors = []
    for path in (DATA_ROW, ASM_ROW):
        for va, word in load_words(path):
            if lo <= va < hi:
                anchors.append((va, len(blob), path.split("/")[-1]))
                blob += word.to_bytes(4, "little")
    if not blob:
        print("no words in range")
        return 1
    md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 | CS_MODE_LITTLE_ENDIAN)
    md.skipdata = True
    va_of = {}
    for va, off, _ in anchors:
        va_of[off] = va
    for insn in md.disasm(bytes(blob), lo):
        va = insn.address
        line = f"{va:08X}:  {insn.mnemonic:<10} {insn.op_str}"
        word = int.from_bytes(insn.bytes, "little")
        jt = jal_target(word)
        if jt is not None:
            line += f"   -> 0x{jt:08X}"
        bt = branch_target(va, word)
        if bt is not None:
            line += f"   -> 0x{bt:08X}"
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())

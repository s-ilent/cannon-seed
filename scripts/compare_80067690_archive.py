#!/usr/bin/env python3
"""compare_80067690_archive.py - how verbatim is the game's copy?

Parses the 4-byte hex from the g3_eu func_80066BC4.s dump comments for the
merged function 0x80067690..0x80067AC8 and compares against the psyq 3.3
LIBSND.LIB VMANAGER module bytes, anchored at the record-run hit 0x126d0
(= game 0x80067928). Reports per-word verdicts: MATCH, REL (differs -
candidate relocation: lui/lw/sw/sh/jal/j/addiu-with-data imm), or DIFF.
"""
import re

S = "/home/z/my-project/cannon-seed/asm/g3_eu/nonmatchings/func_80066BC4.s"
LIB = "/home/z/my-project/psyq/3.3/PSX/LIB/LIBSND.LIB"
ARCHIVE_ANCHOR = 0x126D0   # record-run site
GAME_ANCHOR = 0x80067928   # game record-run site
FN_START = 0x80067690
FN_END = 0x80067AC8

word_re = re.compile(r"/\* [0-9A-Fa-f]+ ([0-9A-Fa-f]{8}) ([0-9A-Fa-f]{8}) \*/")

data = open(LIB, "rb").read()
delta = ARCHIVE_ANCHOR - GAME_ANCHOR

words = []
for ln in open(S, encoding="utf-8", errors="replace"):
    m = word_re.search(ln)
    if not m:
        continue
    addr = int(m.group(1), 16)
    w = int(m.group(2), 16)
    words.append((addr, w, ln))

def rel_class(w: int) -> str:
    op = w >> 26
    # lui(0x0F) always data-imm; jal(0x03)/j(0x02) pseudo-abs; ori/and/addiu with
    # nonzero imm can be data refs; loads/stores with base $at/$gp likely data.
    if op in (0x0F, 0x03, 0x02):
        return "REL?"
    rs = (w >> 21) & 0x1F
    if op in (0x23, 0x2B, 0x25, 0x29, 0x28, 0x39, 0x20, 0x21):  # lw/sw/lh/sh/sb/swr/lwc?/lb classes
        if rs in (0x01, 0x1C, 0x1E, 0x28):  # $at, $gp, $s8, $t? heuristic
            return "REL?"
    return ""

match = rel_mismatch = hard_diff = 0
report = []
for addr, w, ln in words:
    if not (FN_START <= addr < FN_END):
        continue
    off = (addr + delta) & 0xFFFFFFFF
    if off + 4 > len(data):
        continue
    a = int.from_bytes(data[off:off + 4], "little")
    if a == w:
        match += 1
        verdict = "MATCH"
    else:
        cls = rel_class(w)
        if cls:
            rel_mismatch += 1
            verdict = "REL  "
        else:
            hard_diff += 1
            verdict = "DIFF "
        report.append((addr, w, a, verdict, ln.split("*/")[-1].strip()))

print(f"words compared: {match + rel_mismatch + hard_diff}")
print(f"MATCH {match}  REL {rel_mismatch}  DIFF {hard_diff}")
for addr, w, a, verdict, txt in report[:60]:
    print(f"{addr:08x}  game {w:08x}  arch {a:08x}  {verdict} {txt}")

#!/usr/bin/env python3
"""Extract the SsVabOpenHeadWithMode insn words from a row/composite asm file.

Usage: twin_words.py <asm-file> <anchor-hex-addr> [count=274]
Prints one insn word per line starting at the anchor (the function's first
insn = the addiu $sp prologue). Works on any comment shape (the rom field
is 4-8 hex digits): field 2 = VA, field 3 = insn word.
"""
import re
import sys

path, anchor = sys.argv[1], sys.argv[2]
count = int(sys.argv[3]) if len(sys.argv) > 3 else 274
pat = re.compile(r"/\*\s*[0-9A-Fa-f]+\s+([0-9A-Fa-f]{8})\s+([0-9A-Fa-f]{8})\s*\*/")
words = []
started = False
for ln in open(path, errors="replace"):
    m = pat.search(ln)
    if not m:
        continue
    va, insn = m.group(1), m.group(2)
    if not started and va.lower() == anchor.lower():
        started = True
    if started:
        words.append(insn)
        if len(words) >= count:
            break
print("\n".join(words))

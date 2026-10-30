#!/usr/bin/env python3
"""linked_diff - difflib the MINI-LINKED judge .elf against the retail row.

The standalone-as proxy (word_diff.py) resolves relocations/branches with
standalone section layout; the judge mini-links and its layout is what the
verdict counts. This tool disassembles build/judge/<unit>.elf at the retail
VA, byteswaps into the retail dump convention, and prints a compact
per-region diff map.

Usage: python3 scripts/linked_diff.py <unit.elf> <row.s> <start_va_hex>
"""
import re
import subprocess
import sys
import difflib
from pathlib import Path

OD = "/home/z/my-project/tools-local/mipsel-root/usr/bin/mipsel-linux-gnu-objdump"

elf, row_path, va0 = sys.argv[1], sys.argv[2], int(sys.argv[3], 16)
r = subprocess.run([OD, "-d", elf], capture_output=True, text=True)
built = []
for ln in r.stdout.splitlines():
    m = re.match(r"\s*([0-9a-f]+):\s+([0-9a-f]{8})\s", ln)
    if not m:
        continue
    va = int(m.group(1), 16)
    if va < va0:
        continue
    w = m.group(2)
    built.append("".join(w[i:i+2] for i in (6, 4, 2, 0)))

retail = []
for ln in Path(row_path).read_text().splitlines():
    m = re.search(r"/\*\s*[0-9A-Fa-f]+\s+([0-9A-Fa-f]{8})\s+([0-9A-Fa-f]{8})\s*\*/", ln)
    if m:
        retail.append(m.group(2).lower())

print(f"built {len(built)} words ({len(built)*4} B), retail {len(retail)} words ({len(retail)*4} B)")
sm = difflib.SequenceMatcher(None, built, retail, autojunk=False)
blocks = list(sm.get_opcodes())
matched = sum(i2 - i1 for tag, i1, i2, j1, j2 in blocks if tag == "equal")
print(f"aligned-match {matched}/{len(retail)} retail words")
n = 0
for tag, i1, i2, j1, j2 in blocks:
    if tag == "equal":
        continue
    n += 1
    print(f"[{n:02d}] {tag:7s} built[{i1}:{i2}]({(i2-i1)*4}B) retail[{j1}:{j2}]({(j2-j1)*4}B) @VA {va0+j1*4:#x}")

#!/usr/bin/env python3
"""linked_sidediff - full side-by-side mnemonic dump of the mini-linked
judge .elf vs the retail row, difflib-aligned on insn words.

Usage: python3 scripts/linked_sidediff.py <unit.elf> <row.s> <start_va_hex> [out.txt]
"""
import re
import subprocess
import sys
import difflib
from pathlib import Path

OD = "/home/z/my-project/tools-local/mipsel-root/usr/bin/mipsel-linux-gnu-objdump"

elf, row_path, va0 = sys.argv[1], sys.argv[2], int(sys.argv[3], 16)
out = sys.argv[4] if len(sys.argv) > 4 else None

r = subprocess.run([OD, "-d", elf], capture_output=True, text=True)
if r.returncode != 0:
    print("OBJDUMP FAILED:", r.stderr[:400])
    sys.exit(2)
built = []   # (word, mnemonic)
for ln in r.stdout.splitlines():
    m = re.match(r"\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+(.*)", ln)
    if not m:
        continue
    va = int(m.group(1), 16)
    if va < va0:
        continue
    w = m.group(2)
    bw = "".join(w[i:i+2] for i in (6, 4, 2, 0))
    built.append((bw, m.group(3).strip()))

retail = []  # (word, mnemonic)
for ln in Path(row_path).read_text().splitlines():
    m = re.search(r"/\*\s*[0-9A-Fa-f]+\s+([0-9A-Fa-f]{8})\s+([0-9A-Fa-f]{8})\s*\*/\s+(.*)", ln)
    if m:
        retail.append((m.group(2).lower(), m.group(3).strip()))

lines = []
lines.append(f"built {len(built)} words ({len(built)*4} B), retail {len(retail)} words ({len(retail)*4} B)")
sm = difflib.SequenceMatcher(None, [w for w, _ in built], [w for w, _ in retail], autojunk=False)
blocks = list(sm.get_opcodes())
matched = sum(i2 - i1 for tag, i1, i2, j1, j2 in blocks if tag == "equal")
lines.append(f"aligned-match {matched}/{len(retail)} retail words")

for tag, i1, i2, j1, j2 in blocks:
    if tag == "equal":
        continue
    lines.append(f"=== {tag} built[{i1}:{i2}] retail[{j1}:{j2}] @VA {va0+j1*4:#x}")
    for k in range(i1, i2):
        lines.append(f"  B {va0+k*4:#x} {built[k][0]}  {built[k][1]}")
    for k in range(j1, j2):
        lines.append(f"  R {va0+k*4:#x} {retail[k][0]}  {retail[k][1]}")

txt = "\n".join(lines)
print(txt[:1500])
if out:
    Path(out).write_text(txt + "\n")
    print(f"\n[full dump -> {out}]")

#!/usr/bin/env python3
"""Mini offline judge: assemble a .mas.s with the pinned as, objdump it,
and compare the word stream against the retail row's /* addr VA WORD */ column."""
import re
import subprocess
import sys
from pathlib import Path

AS = "/home/z/my-project/tools-local/mipsel-root/usr/bin/mipsel-linux-gnu-as"
OD = "/home/z/my-project/tools-local/mipsel-root/usr/bin/mipsel-linux-gnu-objdump"


def built_words(mas_path):
    o = Path("/tmp/wd_out.o")
    r = subprocess.run([AS, "-mips1", "-o", str(o), mas_path],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("AS FAILED:", r.stderr[:800])
        sys.exit(2)
    r = subprocess.run([OD, "-d", str(o)], capture_output=True, text=True)
    words = []
    for ln in r.stdout.splitlines():
        m = re.match(r"\s*[0-9a-f]+:\s+([0-9a-f]{8})\s", ln)
        if m:
            w = m.group(1)
            # retail dump is big-endian words of LE bytes; objdump prints BE
            words.append("".join(w[i:i+2] for i in (6, 4, 2, 0)))
    return words


def retail_words(row_path, start_va, end_va):
    lo, hi = int(start_va, 16), int(end_va, 16)
    out = []
    for ln in Path(row_path).read_text().splitlines():
        m = re.search(r"/\*\s*[0-9A-Fa-f]+\s+([0-9A-Fa-f]{8})\s+([0-9A-Fa-f]{8})\s*\*/", ln)
        if not m:
            continue
        va = int(m.group(1), 16)
        if lo <= va < hi:
            out.append(m.group(2).lower())
    return out


if __name__ == "__main__":
    import difflib
    mas, row, va0, va1 = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    bw = built_words(mas)
    rw = retail_words(row, va0, va1)
    print(f"built {len(bw)} words, retail {len(rw)} words")
    sm = difflib.SequenceMatcher(None, bw, rw, autojunk=False)
    blocks = list(sm.get_opcodes())
    matched = sum(i2 - i1 for tag, i1, i2, j1, j2 in blocks if tag == "equal")
    print(f"aligned-match {matched}/{len(rw)} retail words")
    for tag, i1, i2, j1, j2 in blocks:
        if tag == "equal":
            continue
        print(f"--- {tag} built[{i1}:{i2}] retail[{j1}:{j2}] (@{j1*4:#06x})")
        for k in range(max(i1 - 1, 0), min(i2 + 1, len(bw))):
            print(f"  B[{k*4:#06x}] {bw[k]}")
        print("  ...")
        for k in range(max(j1 - 1, 0), min(j2 + 1, len(rw))):
            print(f"  R[{k*4:#06x}] {rw[k]}")

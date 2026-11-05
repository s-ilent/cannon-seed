#!/usr/bin/env python3
"""Side-by-side mnemonic compare: built .mas.s (assembled, disassembled)
vs the retail row text, walked in lockstep over the full row.

Usage: LD_LIBRARY_PATH=$TOOLROOT/usr/lib/x86_64-linux-gnu \
         python3 scripts/sbs.py <built.mas.s> <retail-row.s> <va0> <va1> [lo] [hi]
Prints one line per 4-byte offset: `off  <built-mnemonic>   |   <retail-mnemonic>`
with `===` when the words are equal (byte-order-normalized).
"""
import re
import subprocess
import sys

AS = "/home/z/my-project/tools-local/mipsel-root/usr/bin/mipsel-linux-gnu-as"
OD = "/home/z/my-project/tools-local/mipsel-root/usr/bin/mipsel-linux-gnu-objdump"


def built_dis(mas_path):
    o = "/tmp/sbs_out.o"
    subprocess.run([AS, "-march=mips64", "-mabi=32", "-EL", "-G0",
                    "-o", o, mas_path], check=True, capture_output=True)
    r = subprocess.run([OD, "-d", o], capture_output=True, text=True)
    out = []
    for ln in r.stdout.splitlines():
        m = re.match(r"\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+(.*)", ln)
        if m:
            addr = int(m.group(1), 16)
            w = m.group(2)
            # objdump prints the BE reading of the LE byte stream; the true
            # instruction word = the byte swap back
            true = "".join(w[i:i + 2] for i in (6, 4, 2, 0))
            out.append((addr, true, m.group(3).strip()))
    return out


def retail_dis(row_path, va0):
    out = []
    for ln in open(row_path):
        m = re.search(
            r"/\*\s*[0-9A-Fa-f]+\s+([0-9A-Fa-f]{8})\s+([0-9A-Fa-f]{8})\s*\*/\s*(.*)",
            ln)
        if not m:
            continue
        va = int(m.group(1), 16)
        word = m.group(2).lower()
        text = m.group(3).strip()
        out.append((va - va0, word, text))
    return out


if __name__ == "__main__":
    mas, row, va0, va1 = sys.argv[1], sys.argv[2], int(sys.argv[3], 16), int(sys.argv[4], 16)
    diff_mode = len(sys.argv) > 5 and sys.argv[5] == "diff"
    lo = 0 if diff_mode else (int(sys.argv[5], 16) if len(sys.argv) > 5 else 0)
    hi = (va1 - va0) if diff_mode else (int(sys.argv[6], 16) if len(sys.argv) > 6 else (va1 - va0))
    if len(sys.argv) > 5 and sys.argv[5] == "diff":
        # normalized structural diff: mnemonic + operand forms, placeholders
        # (relocation targets) and bare immediates masked; prints the
        # unified diff of built vs retail instruction streams
        import difflib
        alias = {"li": "ori", "move": "addu"}

        def norm(t):
            m = t.split()[0]
            return alias.get(m, m)

        bwords = built_dis(mas)
        blines = [f"{a:#06x} {norm(t)}" for a, w, t in bwords if lo <= a < hi]
        rwords = retail_dis(row, va0)
        rlines = [f"{o:#06x} {norm(t)}" for o, w, t in rwords if lo <= o < hi]
        sm = difflib.SequenceMatcher(None, blines, rlines, autojunk=False)
        ins = dele = 0
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                continue
            print(f"--- {tag} built[{i1}:{i2}] retail[{j1}:{j2}]")
            for ln in blines[i1:i2]:
                print(f"  - {ln}")
            for ln in rlines[j1:j2]:
                print(f"  + {ln}")
            if tag in ("insert", "replace"):
                ins += j2 - j1
            if tag in ("delete", "replace"):
                dele += i2 - i1
        print(f"SUMMARY: retail-only {ins} words, built-only {dele} words"
              f" (built {len(blines)}, retail {len(rlines)})")
        sys.exit(0)
    bd = {a: (w, t) for a, w, t in built_dis(mas) if lo <= a < hi}
    rd = {o: (w, t) for o, w, t in retail_dis(row, va0) if lo <= o < hi}
    offs = sorted(set(bd) | set(rd))
    for o in offs:
        b = bd.get(o)
        r = rd.get(o)
        bw = b[0] if b else "--------"
        bt = b[1] if b else "(none)"
        rw = r[0] if r else "--------"
        rt = r[1] if r else "(none)"
        mark = "  " if (b and r and b[0] == r[0]) else "!!"
        # normalize jal/j/lui/addiu placeholders so the form compare stays honest
        bn = re.sub(r"0x[0-9a-f]+|<[a-zA-Z_][\w.]*>", "X", bt)
        rn = re.sub(r"0x[0-9a-f]+|<\S+>", "X", rt)
        bnorm = " ".join(bn.split()[:2])
        rnorm = " ".join(rn.split()[:2])
        if b and r and bnorm == rnorm and (bw == rw or "X" in bnorm):
            mark = "~~"  # same form, placeholder target word
        print(f"{o:#06x} {mark} {bw} {bt:<38} | {rw} {rt}")

#!/usr/bin/env python3
"""Shift-track: align the built word stream against the retail stream at all
small shifts (0..4) and print, per built index, which shift matches. The
longest-run view exposes exactly where the deficit words sit."""
import re
import subprocess
import sys

AS = "/home/z/my-project/tools-local/mipsel-root/usr/bin/mipsel-linux-gnu-as"
OD = "/home/z/my-project/tools-local/mipsel-root/usr/bin/mipsel-linux-gnu-objdump"


def built_words(mas):
    subprocess.run([AS, "-march=mips64", "-mabi=32", "-EL", "-G0",
                    "-o", "/tmp/st.o", mas], check=True, capture_output=True)
    r = subprocess.run([OD, "-d", "/tmp/st.o"], capture_output=True, text=True)
    out = []
    for ln in r.stdout.splitlines():
        m = re.match(r"\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+(.*)", ln)
        if m:
            w = m.group(2)
            out.append(("".join(w[i:i + 2] for i in (6, 4, 2, 0)),
                        m.group(1), m.group(3).strip()))
    return out


def retail_words(row):
    out = []
    for ln in open(row):
        m = re.search(r"/\*\s*[0-9A-Fa-f]+\s+([0-9A-Fa-f]{8})\s+"
                      r"([0-9A-Fa-f]{8})\s*\*/\s*(.*)", ln)
        if m:
            out.append((m.group(2).lower(), m.group(1), m.group(3).strip()))
    return out


if __name__ == "__main__":
    mas, row = sys.argv[1], sys.argv[2]
    b = built_words(mas)
    r = retail_words(row)
    n = min(len(b), len(r))
    # mask: jal/lui/addiu-at placeholders + load-delay nops are instrument noise
    def noisy(w, t):
        return (w in ("0000000c", "00000000") or t.startswith("jal 0 ")
                or "0($at)" in t and w.endswith("0000"))
    runs = []
    cur_shift, cur_start = None, 0
    for i in range(n):
        match = None
        for s in range(0, 5):
            if i + s < len(r) and b[i][0] == r[i + s][0]:
                match = s
                break
        if match != cur_shift:
            if cur_shift is not None:
                runs.append((cur_start, i, cur_shift))
            cur_shift, cur_start = match, i
    runs.append((cur_start, n, cur_shift))
    for s0, s1, sh in runs:
        if s1 - s0 < 3:
            continue
        print(f"built[{s0:#05x}..{s1:#05x}) shift={sh}")
        if sh:
            for k in range(max(s0 - 2, 0), min(s1 + 2, n)):
                bw, ba, bt = b[k]
                rw, ra, rt = r[k + sh] if k + sh < len(r) else ("?", "?", "?")
                mark = "  " if bw == rw else "!!"
                print(f"   {k:#06x} {mark} B {bt:<40} | R {rt}")

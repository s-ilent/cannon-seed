#!/usr/bin/env python3
"""tail_screen.py - tail-side shape screen for the block-move unit (LAW 5).

Companion to div2_screen.py, which screens the HEAD.  This tool compiles a
candidate func_8002ADA0 C form through tools/cc.sh (offline, no oracle),
disassembles the WHOLE text and diffs the TAIL against the retail tail
extracted from the pinned pre-carve row asm/nonmatchings/func_800272F8.s
(lines 5374..5971 = the unit's retail bytes, git-tracked ground truth).

The retail tail (LAW 5 territory) is the open/close verify sequence plus the
SHARED EPILOGUE THUNK (func_8002B444: six lw reloads, jr ra, frame release
in the branch delay slot) reached by j func_8002B444 with the return value
riding the jump's delay slot.  The screen prints an aligned tail diff so
the scheduling deltas (slot pairing, compare forms, block layout) can be
read directly.

Usage: python3 scripts/bm_unit_decode/tail_screen.py <candidate.c> [n_tail]
"""
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLROOT = os.environ.get("TOOLROOT", "/home/z/my-project/tools-local/mipsel-root")
OBJDUMP = os.path.join(TOOLROOT, "usr/bin/mipsel-linux-gnu-objdump")
GIANT = os.path.join(REPO, "asm/nonmatchings/func_800272F8.s")
UNIT_LINES = (5374, 5971)  # the retail unit bytes, per wire_split.py

INSN = re.compile(r"^\s+[0-9a-f]+:\s+([0-9a-f]{8})\s+(.*)$")
BRANCH = re.compile(r"^\s+[0-9a-f]+:\s+([0-9a-f]{8})\s+j(?:al|r)?\s")


def norm_objdump(text):
    sig = []
    for ln in text.splitlines():
        m = INSN.match(ln)
        if not m:
            continue
        ins = m.group(2).split("#")[0].strip()
        ins = re.sub(r"\s+", " ", ins)
        sig.append(ins)
    return sig


def norm_row(text):
    """Normalize pinned-row lines (mnemonic-first, $-regs, no addr comments)."""
    lines = text if isinstance(text, list) else text.splitlines()
    sig = []
    for ln in lines:
        m = re.search(r"\*/\s+(.*)$", ln)
        body = m.group(1) if m else ln
        body = body.strip()
        if not body or body.startswith((".", "glabel", "endlabel", "nonmatching", "/*")):
            continue
        body = re.sub(r"\s+", " ", body)
        # normalize: 'addu $a0, $s0, $zero' -> 'move a0,s0' shape
        body = body.replace(", $zero, $zero", ",zero,zero")
        sig.append(body)
    return sig


def retail_tail(n_tail):
    lines = open(GIANT, errors="replace").read().splitlines()[UNIT_LINES[0] - 1:UNIT_LINES[1]]
    return norm_row(lines)[-n_tail:]


def run(cmd):
    return subprocess.run(cmd, cwd=REPO, capture_output=True, text=True,
                          env=dict(os.environ,
                                   LD_LIBRARY_PATH=f"{TOOLROOT}/usr/lib/x86_64-linux-gnu"))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    cand = os.path.abspath(sys.argv[1])
    n_tail = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    base = os.path.splitext(os.path.basename(cand))[0]
    work_o = f"build/judge/tailscr_{base}.o"
    os.makedirs(os.path.join(REPO, "build/judge"), exist_ok=True)
    r = run([f"{REPO}/tools/cc.sh", "-o", work_o, cand])
    if r.returncode:
        print(f"COMPILE-FAIL:\n{r.stderr[-1500:]}")
        return 1
    r = run([OBJDUMP, "-d", work_o])
    if r.returncode:
        print(f"OBJDUMP-FAIL: {r.stderr[-400:]}")
        return 1
    sig = norm_objdump(r.stdout)
    # the compiled unit: skip the assembler preamble labels; func body = all
    # insns (cc.sh compiles one translation unit = one function here)
    ret = retail_tail(n_tail)
    got = sig[-n_tail:]
    print(f"=== {base}: {len(sig)} total insns (retail unit = 433) ===")
    print(f"=== aligned tail diff, last {n_tail} insns (retail left, built right) ===")
    # align from the END: walk both backwards, print mismatches
    i = 0
    mismatches = 0
    while i < min(len(ret), len(got)):
        a, b = ret[len(ret) - 1 - i], got[len(got) - 1 - i]
        an = re.sub(r"[$\s]", "", a)
        bn = re.sub(r"[$\s]", "", b)
        # fold jal-target and branch-target differences (symbol resolution)
        an = re.sub(r"(jal|j|jr|beq|bne|blez|bgtz|bltz|bgez)[a-z]*,?", r"\1", an)
        bn = re.sub(r"(jal|j|jr|beq|bne|blez|bgtz|bltz|bgez)[a-z]*,?", r"\1", bn)
        an = re.sub(r"<[^>]*>|0x[0-9a-f]+<[^>]*>", "", an)
        bn = re.sub(r"<[^>]*>|0x[0-9a-f]+<[^>]*>", "", bn)
        same = an == bn
        if not same:
            mismatches += 1
            print(f"  -{i:3d}  RET {a:34s} | BLT {b}")
        i += 1
    print(f"=== tail: {mismatches} mismatching word(s) in the last {min(len(ret), len(got))} "
          f"(retail {len(ret)}, built {len(got)}) ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())

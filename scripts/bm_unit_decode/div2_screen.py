#!/usr/bin/env python3
"""div2_screen.py - fast shape screen for the block-move unit's div2 hunt.

Compiles a candidate func_8002ADA0 C form through the repo's own pipeline
(tools/cc.sh: cc1 under qemu + maspsx + mipsel-as), disassembles the head
region (prologue .. fill-loop entry, retail VA 0x8002ADA0..0x8002AE10) and
prints its instruction signature so it can be eyeballed against the retail
sequence.  This is a SHAPE screen (not an oracle): it tells whether the
second branchy division survives and which register/shape it took.

Usage: python3 scripts/bm_unit_decode/div2_screen.py <candidate.c> [n_head]
"""
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLROOT = os.environ.get("TOOLROOT", "/home/z/my-project/tools-local/mipsel-root")
OBJDUMP = os.path.join(TOOLROOT, "usr/bin/mipsel-linux-gnu-objdump")

# retail head signature: the interesting window is the prologue through the
# fill-loop counter init (VA 0x8002ADA0..0x8002AE10 = 0x70 bytes = 28 insns)
RETAIL = [
    "addiu $sp,$sp,-0x28", "sw $ra,0x24($sp)", "sw $s4,0x20($sp)",
    "sw $s3,0x1c($sp)", "sw $s2,0x18($sp)", "sw $s1,0x14($sp)",
    "sw $s0,0x10($sp)", "addu $s4,$a0,$zero", "addu $s3,$a3,$zero",
    "lw $v1,0x44($sp)", "addu $s2,$a1,$zero", "lw $s0,0x38($sp)",
    "addiu $v1,$v1,0x200",
    "bgez $v1,", "addu $v0,$v1,$zero", "addiu $v0,$v1,0x1fff",
    "sra $v0,$v0,0xd", "sll $a0,$v0,0xd",
    "addu $v0,$v1,$zero", "bgez $v0,", "nop", "addiu $v0,$v0,0x1fff",
    "sra $v0,$v0,0xd", "sll $v0,$v0,0xd",
    "beq $v1,$v0,", "ori $a1,$zero,0xff", "addiu $a0,$a0,0x2000",
    "addu $v1,$zero,$zero",
]


def run(cmd):
    return subprocess.run(cmd, cwd=REPO, capture_output=True, text=True,
                          env=dict(os.environ,
                                   LD_LIBRARY_PATH=f"{TOOLROOT}/usr/lib/x86_64-linux-gnu"))


def screen(c_path, n_head=40):
    base = os.path.splitext(os.path.basename(c_path))[0]
    work_o = f"build/judge/div2_{base}.o"
    os.makedirs(os.path.join(REPO, "build/judge"), exist_ok=True)
    r = run([f"{REPO}/tools/cc.sh", "-o", work_o, c_path])
    if r.returncode:
        print(f"COMPILE-FAIL:\n{r.stderr[-1500:]}")
        return 1
    r = run([OBJDUMP, "-d", work_o])
    if r.returncode:
        print(f"OBJDUMP-FAIL: {r.stderr[-400:]}")
        return 1
    lines = r.stdout.splitlines()
    # the function's text section: find the first label after the .text header
    body = []
    started = False
    for ln in lines:
        if not started and re.match(r"^\s*[0-9a-f]+:\s", ln):
            started = True
        if started:
            body.append(ln)
        if len(body) >= n_head:
            break
    sig = []
    for ln in body:
        m = re.match(r"^\s*[0-9a-f]+:\s+([0-9a-f]{8})\s+(.*)$", ln)
        if not m:
            continue
        ins = m.group(2).split("#")[0].strip()
        ins = re.sub(r"\s+", "", ins)
        ins = re.sub(r",0x([0-9a-f]+)$", lambda mm: f",0x{int(mm.group(1), 16):x}", ins)
        sig.append(ins)
    print(f"=== {base}: {len(sig)} head insns ===")
    for i, ins in enumerate(sig):
        print(f"  {i:2d}  {ins}")
    # compare against the retail signature, skipping jal/label differences
    n = min(len(RETAIL), len(sig))
    match, first_bad = 0, None
    for i in range(n):
        want = RETAIL[i].replace(" ", "")
        got = sig[i]
        if got.startswith(want.rstrip(",")) or got == want or \
           (want.endswith(",") and got.startswith(want)):
            match += 1
        elif first_bad is None:
            first_bad = i
    print(f"=== prefix match: {match}/{n}"
          + (f" (first divergence at {first_bad}: retail '{RETAIL[first_bad]}' vs built '{sig[first_bad]}')" if first_bad is not None else "") + " ===")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(screen(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 40))

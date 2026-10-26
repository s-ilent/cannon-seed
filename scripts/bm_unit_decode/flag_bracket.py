#!/usr/bin/env python3
"""flag_bracket.py - bracket the retail div2 shape across cc1 flag regimes.

cron-202610261804 NEXT WINDOW item (2): the falsification matrix proved
v19/v20/v21 merge at default and survive only in non-retail shapes at
-fno-cse-skip-blocks.  This probe compiles a variant across a flag matrix
and prints the full head signature (30 insns) for each regime so the div2
region can be read directly.

BANKED (cron-202610261919): the div2 merge is governed by ONE flag,
-fcse-skip-blocks (ON = merge, OFF = survive); -fexpensive-optimizations,
-fschedule-insns/-insns2, -fthread-jumps, -fcse-follow-jumps,
-fstrength-reduce, -fcaller-saves and the -O1 level have NO effect on the
div2 region.  The survive-shape is ALWAYS the cse-canonicalized form
(tight when the operand pseudo's qty is a reg-link, recompute when it is
an expression) - never the retail loose-copy form, because cse.c's
canon_reg unconditionally rewrites a pseudo operand to qty_first_reg.

Usage: python3 scripts/bm_unit_decode/flag_bracket.py [v21|v19|v20|all]
"""
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLROOT = os.environ.get("TOOLROOT", "/home/z/my-project/tools-local/mipsel-root")
OBJDUMP = os.path.join(TOOLROOT, "usr/bin/mipsel-linux-gnu-objdump")
VAR = os.path.join(REPO, "scripts/bm_unit_decode/variants")

RETAIL_DIV2 = [
    "addu$v0,$v1,$zero", "bgez$v0,", "nop", "addiu$v0,$v0,0x1fff",
    "sra$v0,$v0,0xd", "sll$v0,$v0,0xd", "beq$v1,$v0,",
]


def run(cmd, cwd=REPO, env=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                          env=env if env is not None else dict(
                              os.environ,
                              LD_LIBRARY_PATH=f"{TOOLROOT}/usr/lib/x86_64-linux-gnu"))


def head_sig(work_o, n=64):
    r = run([OBJDUMP, "-d", work_o])
    if r.returncode:
        return None
    lines = r.stdout.splitlines()
    sig = []
    for ln in lines:
        m = re.match(r"^\s*[0-9a-f]+:\s+([0-9a-f]{8})\s+(.*)$", ln)
        if not m:
            continue
        ins = m.group(2).split("#")[0].strip()
        ins = re.sub(r"\s+", "", ins)
        ins = re.sub(r",0x([0-9a-f]+)$", lambda mm: f",0x{int(mm.group(1), 16):x}", ins)
        sig.append(ins)
        if len(sig) >= n:
            break
    return sig


def classify(insns):
    if insns is None:
        return "OBJDUMP-FAIL", ""
    # window: from div1's closing sll (first sll with the 0xd shift after the
    # first sra 0xd) to the fill-loop init (counter zero / fill constant)
    win = []
    started = False
    seen_sra = False
    for op in insns:
        if not started:
            if op.startswith("sra") and "0xd" in op:
                seen_sra = True
            if seen_sra and op.startswith("sll") and "0xd" in op:
                started = True
            continue
        if op.startswith("addu$v1,$zero,$zero") or op.startswith("li$a1") or op.startswith("ori$a1,$zero,0xff"):
            break
        win.append(op)
        if len(win) >= 20:
            break
    if not win:
        return "NO-WINDOW", ""
    n_bgez = sum(1 for op in win if op.startswith("bgez"))
    if n_bgez == 0:
        return "MERGED", " | ".join(win)
    # retail check: exact subsequence
    sig = " | ".join(win)
    retail = " | ".join(RETAIL_DIV2)
    if retail in sig:
        return "RETAIL_SHAPE", sig
    # tight: bgez immediately followed by the copy (delay slot copy)
    for i, op in enumerate(win):
        if op.startswith("bgez") and i + 1 < len(win) and win[i + 1].startswith("addu$v0,$v1,$zero"):
            return "TIGHT", sig
    if "0x200" in sig and "0x1fff" in sig:
        return "SURVIVES-RECOMPUTE/STACKED", sig
    return "OTHER", sig


def probe(variant, extra, tag):
    os.makedirs(os.path.join(REPO, "build/judge"), exist_ok=True)
    stem = f"build/judge/fb_{variant}_{tag}"
    stem = stem.replace("+", "_").replace("=", "_")
    env = dict(os.environ, CC1FLAGS_EXTRA=extra,
               LD_LIBRARY_PATH=f"{TOOLROOT}/usr/lib/x86_64-linux-gnu")
    r = run([f"{REPO}/tools/cc.sh", "-o", f"{stem}.o", f"{VAR}/{variant}.c"], env=env)
    if r.returncode:
        return f"{variant:22s} {tag:38s} COMPILE-FAIL"
    cls, sig = classify(head_sig(f"{stem}.o"))
    head = head_sig(f"{stem}.o", 30)
    lines = "\n      ".join(f"{i:2d} {op}" for i, op in enumerate(head))
    return f"{variant:22s} {tag:38s} [classifier: {cls}]\n      {lines}"


MATRIX = {
    "v21_expr_on_t.c": [
        ("default-O2", ""),
        ("O1", "-O1"),
        ("O1+skip", "-O1 -fcse-skip-blocks"),
        ("O2-no-skip", "-fno-cse-skip-blocks"),
        ("O1+expensive", "-O1 -fexpensive-optimizations"),
        ("O1+sched2", "-O1 -fschedule-insns2"),
        ("O1+sched", "-O1 -fschedule-insns"),
        ("O1+threadj", "-O1 -fthread-jumps"),
        ("O1+csefollow", "-O1 -fcse-follow-jumps"),
        ("O1+strength", "-O1 -fstrength-reduce"),
        ("O1+callersaves", "-O1 -fcaller-saves"),
        ("O1+exp+skip", "-O1 -fexpensive-optimizations -fcse-skip-blocks"),
        ("O1+all-O2", "-O1 -fcse-skip-blocks -fexpensive-optimizations -fthread-jumps -fcaller-saves"),
    ],
}


def main():
    sel = sys.argv[1] if len(sys.argv) > 1 else "v21"
    for fname, flags in MATRIX.items():
        variant = fname[:-2]
        if sel != "all" and not variant.startswith(sel):
            continue
        for tag, extra in flags:
            print(probe(variant, extra, tag), flush=True)


if __name__ == "__main__":
    main()

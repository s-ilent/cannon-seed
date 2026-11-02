#!/usr/bin/env python3
"""align787.py - structural alignment diff: built judge unit vs the retail row.

difflib on normalized streams (register names -> numbers, branch targets
dropped, directives/labels flagged) prints ONLY the insert/delete/replace
blocks - no offset-drift noise. The word-diff (judge_unit) pairs by offset
and misreads once the streams shift; this tool is the shape authority.

Usage: python3 scripts/align787.py [built.mas.s [retail.s]]
Defaults: build/judge/<unit>.mas.s vs asm/<target>/nonmatchings/<unit>.s
for the CdGetToc2 ladder (mainmenu_eu func_80078724).
"""
import difflib
import re
import sys

BUILT = sys.argv[1] if len(sys.argv) > 1 else \
    "/home/z/my-project/cannon-seed/build/judge/func_80078724.mas.s"
RETAIL = sys.argv[2] if len(sys.argv) > 2 else \
    "/home/z/my-project/cannon-seed/asm/mainmenu_eu/nonmatchings/func_80078724.s"

COMMENT = re.compile(r"/\*.*?\*/")
LABEL = re.compile(r"^(\.L\w+|gcc2_compiled\.|__gnu_compiled_c|func_\w+):")


def load_built():
    out = []
    for ln in open(BUILT):
        ln = ln.strip()
        if not ln:
            continue
        if ln.startswith("."):
            continue  # directives: .file/.text/.ent/.set/.frame/...
        if ln.endswith(":"):
            out.append(("LABEL", ln[:-1]))
            continue
        parts = ln.split("\t")
        op = parts[0].strip()
        args = " ".join(p.strip() for p in parts[1:] if p.strip())
        out.append((op, args))
    return out


def load_retail():
    out = []
    for ln in open(RETAIL):
        m = COMMENT.search(ln)
        if not m:
            continue
        body = ln[m.end():].strip()
        if not body:
            continue
        if body.startswith("."):
            # label like .L800788B8:
            out.append(("LABEL", body))
            continue
        body = re.sub(r"\s+", " ", body)
        op, _, args = body.partition(" ")
        out.append((op, args.strip()))
    return out


REGS = ["zero", "at", "v0", "v1", "a0", "a1", "a2", "a3",
        "t0", "t1", "t2", "t3", "t4", "t5", "t6", "t7",
        "s0", "s1", "s2", "s3", "s4", "s5", "s6", "s7",
        "t8", "t9", "k0", "k1", "gp", "sp", "fp", "ra"]


def normreg(m):
    name = m.group(1)
    if name in REGS:
        return "$%d" % REGS.index(name)
    return "$" + name


def norm(t):
    op, args = t
    if op == "LABEL":
        return "L"
    args = re.sub(r"\s+", "", args)
    args = re.sub(r"\$(\w+)", normreg, args)
    args = args.replace("$", "")
    # normalize branch targets away (offsets differ with scheduling)
    if op in ("beq", "bne", "beqz", "bnez", "bltz", "bgez", "blez", "bgtz",
              "j", "jal", "bltzal", "bgezal"):
        return op
    return op + ":" + args


built = [t for t in load_built() if t[0] != "LABEL" or True]
retail = [t for t in load_retail()]

b = [norm(t) for t in built]
r = [norm(t) for t in retail]

print(f"built {len(b)} insns, retail {len(r)} insns")
sm = difflib.SequenceMatcher(None, b, r, autojunk=False)
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == "equal":
        continue
    print(f"-- {tag} built[{i1}:{i2}] retail[{j1}:{j2}]")
    for k in range(i1, i2):
        print(f"   B {built[k][0]:8s} {built[k][1]}")
    for k in range(j1, j2):
        print(f"   R {retail[k][0]:8s} {retail[k][1]}")

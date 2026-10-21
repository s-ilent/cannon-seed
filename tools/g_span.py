#!/usr/bin/env python3
"""Measure per-register def->death spans: a retail row vs the probe render.

Banked instrument for the GsTMDdivG4LFG color war (window
 cron-20261021-1828).  Both streams are post-scheduled, so first-write ->
last-use-in-body distance is the apples-to-apples analogue of sched's
reg_live_length writeback.  The window's finding: retail and probe spans
are IDENTICAL for all nine register-resident pseudos (color 34=34, v4o
104=104, v3o/v2o/v1o 101=101, vt 67=67, nt 123=123, giv/pk +-1 frame
slot) - the 1713 numeric gate's LL arms are false in retail itself and
the color war is NOT an LL war.  Deltas retail-vs-probe are what matter,
not the absolute LL (loop-wrapping lives make the absolute value differ
from sched's number; the retail-vs-probe comparison does not).

Usage:
    python3 tools/g_span.py [retail_row.s [probe_render.s]]
Defaults: the mainmenu_jp GsTMDdivG4LFG row vs build/probe/gdiv.mas.s
(compile the probe first: CC1FLAGS_EXTRA='-da' tools/cc.sh -o
build/probe/gdiv.o probes/gcc263/GsTMDdivG4LFG.c).  Exit 0 always.
"""
import os
import re
import sys

REPO = __file__.rsplit(os.sep + "tools" + os.sep, 1)[0]
RETAIL = (f"{REPO}/asm/mainmenu_jp/nonmatchings/func_80076388.s"
          if len(sys.argv) < 2 else sys.argv[1])
PROBE = f"{REPO}/build/probe/gdiv.mas.s" if len(sys.argv) < 3 else sys.argv[2]

WORD = re.compile(r"/\*\s*[0-9A-Fa-f]+\s+[0-9A-Fa-f]{8}\s+([0-9A-Fa-f]{8})\s*\*/\s*(.*)")
INSN = re.compile(r"^\s*(\S+)\s*(.*)$")

NAMED = {"zero": 0, "at": 1, "v0": 2, "v1": 3, "a0": 4, "a1": 5, "a2": 6,
         "a3": 7, "t0": 8, "t1": 9, "t2": 10, "t3": 11, "t4": 12, "t5": 13,
         "t6": 14, "t7": 15, "s0": 16, "s1": 17, "s2": 18, "s3": 19,
         "s4": 20, "s5": 21, "s6": 22, "s7": 23, "t8": 24, "t9": 25,
         "k0": 26, "k1": 27, "gp": 28, "sp": 29, "fp": 30, "s8": 30, "ra": 31}

# register-number -> (mnemonic name, role) for each stream
RETAIL_MAP = {16: "s0/giv", 17: "s1/color", 18: "s2/v4o", 19: "s3/v3o",
              20: "s4/v2o", 21: "s5/v1o", 22: "s6/pk", 23: "s7/vt", 30: "fp/nt"}
PROBE_MAP = {16: "s0/giv", 17: "s1/v4o", 18: "s2/v3o", 19: "s3/color",
             20: "s4/v2o", 21: "s5/v1o", 22: "s6/pk", 23: "s7/vt", 30: "fp/nt"}

# instructions whose FIRST register operand is a WRITE destination
WRITE_FIRST = {"addiu", "addu", "add", "subu", "sub", "and", "or", "xor",
               "nor", "slt", "sltu", "sll", "srl", "sra", "sllv", "srlv",
               "srav", "lw", "lbu", "lhu", "lb", "lh", "lwl", "lwr",
               "lwc2", "lwc1", "mflo", "mfhi", "mfc2", "mfc1", "move",
               "li", "la", "negu", "neg", "not", "mult", "div", "divu"}
# stores/branches: first operand (or rt for stores) is a READ
STORES = {"sw", "sb", "sh", "swl", "swr", "swc2", "swc1"}


def reg_names_line(text):
    """register numbers mentioned in an instruction operand string"""
    out = []
    for m in re.finditer(r"\$(\w+)", text):
        tok = m.group(1)
        if tok.isdigit():
            out.append(int(tok))
        elif tok in NAMED:
            out.append(NAMED[tok])
    return out


def retail_lines():
    out = []
    in_fn = False
    for ln in open(RETAIL):
        if ln.startswith("glabel GsTMDdivG4LFG"):
            in_fn = True
            continue
        if in_fn and ln.startswith("endlabel"):
            break
        if not in_fn:
            continue
        m = WORD.search(ln)
        if m:
            word = m.group(1)
            # decode the mnemonic from the disassembled text after */
            txt = ln.split("*/", 1)[1].strip()
            out.append((word, txt))
    return out


def probe_lines():
    out = []
    for ln in open(PROBE):
        t = ln.strip()
        if not t or t.startswith(".") or t.startswith("#"):
            continue
        if ":" in t.split()[0]:
            continue  # label
        out.append((None, t))
    return out


def epilogue_start(lines):
    """index of the first callee-save restore of the epilogue block
    (the run of lw $sN/$fp,N($sp) that ends the function)"""
    n = len(lines)
    for i in range(n - 1, -1, -1):
        txt = lines[i][1]
        m = re.match(r"(lw|addiu)\s+(\$\w+),", txt)
        if m:
            pass
    # scan from the end: the epilogue is the trailing run of lw/addiu/jr
    start = None
    for i in range(n - 1, -1, -1):
        op = INSN.match(lines[i][1])
        if not op:
            continue
        o = op.group(1)
        if o == "nop":
            continue
        if o.startswith("j") or o in ("addiu", "addu"):
            start = i
            continue
        if o == "lw":
            start = i
            continue
        break
    return start if start is not None else n


def analyze(lines, rmap, label):
    print(f"=== {label} ({len(lines)} insns) ===")
    epi = epilogue_start(lines)
    print(f"epilogue starts at insn {epi}: {lines[epi][1][:50]}")
    for reg, role in sorted(rmap.items()):
        occ = []
        for i, (word, txt) in enumerate(lines):
            m = INSN.match(txt)
            if not m:
                continue
            op, operands = m.group(1), m.group(2)
            hits = reg_names_line(operands)
            if reg not in hits:
                continue
            if op in WRITE_FIRST:
                kind = "W" if hits and hits[0] == reg else "R"
            elif op in STORES:
                kind = "R"
            elif op.startswith("j") or op.startswith("b"):
                kind = "R"
            else:
                kind = "R"
            occ.append((i, kind, op, txt))
        if not occ:
            continue
        writes = [o for o in occ if o[1] == "W"]
        first_w = writes[0] if writes else None
        # death = last use before the epilogue restores
        body = [o for o in occ if o[0] < epi]
        last = body[-1] if body else occ[-1]
        if first_w:
            span = last[0] - first_w[0]
            print(f"{role:9s} reg${reg:<2d} def@{first_w[0]:<4d} last@{last[0]:<4d} "
                  f"span {span:<4d} n_occ {len(occ):<3d} last = {last[3][:46]}")
        else:
            print(f"{role:9s} reg${reg:<2d} (no write; first@{occ[0][0]} "
                  f"last@{last[0]}) last = {last[3][:46]}")


def main():
    analyze(retail_lines(), RETAIL_MAP, "RETAIL tree row (mainmenu_jp)")
    print()
    analyze(probe_lines(), PROBE_MAP, "PROBE render (gdiv.mas.s)")


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Full-mnemonic MIPS I + COP2/GTE decode of the graveyard walk interiors
(window cron-202610251936, offline staging prep - the decode record for the
three clean landing classes is in docs/TASKS.md).

Reads the committed mainmenu_jp walk rows through probe_graveyard_walk's
parser (the witnessed extract, oracle-free) and prints full mnemonics -
the probe's own dec() stops at word classes, this adds the register-level
view the C recipes need. Byte-safe display law: the output channel eats
the two-character sequence "[" + "h" in text; this decoder's lines carry
no such sequence, and any audit that doubts a display dumps bytes.

Usage: python3 scripts/decode_interior.py <va_hex> [<va_hex>...]"""
import sys

import probe_graveyard_walk as P

R = ["zero", "at", "v0", "v1", "a0", "a1", "a2", "a3",
     "t0", "t1", "t2", "t3", "t4", "t5", "t6", "t7",
     "s0", "s1", "s2", "s3", "s4", "s5", "s6", "s7",
     "t8", "t9", "k0", "k1", "gp", "sp", "fp", "ra"]

GTE_FUNCT = {0x01: "RTPS", 0x06: "NCLIP", 0x10: "NCDS_", 0x11: "NCDT_",
             0x12: "MVMVA", 0x13: "NCDS", 0x14: "NCDT", 0x16: "NCCS",
             0x17: "NCCT", 0x18: "CDP", 0x1A: "NCDS16", 0x1B: "NCDT16",
             0x1E: "NCCS16", 0x20: "SQR12", 0x21: "SQR", 0x28: "OP12",
             0x29: "OP", 0x2D: "RTPT", 0x30: "GP", 0x3D: "GPF", 0x3E: "GPL",
             0x3F: "NCCT_"}


def mnem(w):
    op = w >> 26
    rs = (w >> 21) & 0x1F
    rt = (w >> 16) & 0x1F
    rd = (w >> 11) & 0x1F
    sa = (w >> 6) & 0x1F
    f = w & 0x3F
    imm = w & 0xFFFF
    simm = imm - 0x10000 if imm >= 0x8000 else imm
    if w == 0:
        return "nop"
    if op == 0:
        if f == 0x00 and (w >> 21) & 0x1F == 0:
            return f"sll   ${R[rd]}, ${R[rt]}, {sa}"
        if f == 0x02:
            return f"srl   ${R[rd]}, ${R[rt]}, {sa}"
        if f == 0x03:
            return f"sra   ${R[rd]}, ${R[rt]}, {sa}"
        if f == 0x04:
            return f"sllv  ${R[rd]}, ${R[rt]}, ${R[rs]}"
        if f == 0x08:
            return f"jr    ${R[rs]}"
        if f == 0x09:
            return f"jalr  ${R[rd]}, ${R[rs]}"
        if f == 0x18:
            return f"mult  ${R[rs]}, ${R[rt]}"
        if f == 0x19:
            return f"multu ${R[rs]}, ${R[rt]}"
        if f == 0x1A:
            return f"div   ${R[rs]}, ${R[rt]}"
        if f == 0x10:
            return f"mfhi  ${R[rd]}"
        if f == 0x12:
            return f"mflo  ${R[rd]}"
        if f == 0x20:
            return f"addu  ${R[rd]}, ${R[rs]}, ${R[rt]}"
        if f == 0x21:
            return f"addu  ${R[rd]}, ${R[rs]}, ${R[rt]}  (add)"
        if f == 0x23:
            return f"subu  ${R[rd]}, ${R[rs]}, ${R[rt]}"
        if f == 0x24:
            return f"and   ${R[rd]}, ${R[rs]}, ${R[rt]}"
        if f == 0x25:
            return f"or    ${R[rd]}, ${R[rs]}, ${R[rt]}"
        if f == 0x26:
            return f"xor   ${R[rd]}, ${R[rs]}, ${R[rt]}"
        if f == 0x27:
            return f"nor   ${R[rd]}, ${R[rs]}, ${R[rt]}"
        if f == 0x2A:
            return f"slt   ${R[rd]}, ${R[rs]}, ${R[rt]}"
        return f"special f=0x{f:02x}"
    if op == 1:
        m = {0: "bltz", 1: "bgez", 16: "bltzal", 17: "bgezal"}
        return f"{m.get(rt, 'regimm'+str(rt))} ${R[rs]}, {simm*4+4:+#x}"
    if op == 2:
        return f"j     0x{((w & 0x3FFFFFF) << 2):08x}"
    if op == 3:
        return f"jal   0x{((w & 0x3FFFFFF) << 2):08x}"
    if op == 4:
        return f"beq   ${R[rs]}, ${R[rt]}, {simm*4+4:+#x}"
    if op == 5:
        return f"bne   ${R[rs]}, ${R[rt]}, {simm*4+4:+#x}"
    if op == 6:
        return f"blez  ${R[rs]}, {simm*4+4:+#x}"
    if op == 7:
        return f"bgtz  ${R[rs]}, {simm*4+4:+#x}"
    if op in (8, 9):
        return f"{'addi' if op == 8 else 'addiu'} ${R[rt]}, ${R[rs]}, {simm:+#x}"
    if op == 0xA:
        return f"slti  ${R[rt]}, ${R[rs]}, {simm:+#x}"
    if op == 0xB:
        return f"sltiu ${R[rt]}, ${R[rs]}, {simm:+#x}"
    if op == 0xC:
        return f"andi  ${R[rt]}, ${R[rs]}, 0x{imm:#06x}"
    if op == 0xD:
        return f"ori   ${R[rt]}, ${R[rs]}, 0x{imm:#06x}"
    if op == 0xE:
        return f"xori  ${R[rt]}, ${R[rs]}, 0x{imm:#06x}"
    if op == 0xF:
        return f"lui   ${R[rt]}, 0x{imm:#06x}"
    if op in (0x20, 0x21, 0x23, 0x24, 0x25):
        m = {0x20: "lb", 0x21: "lh", 0x23: "lw", 0x24: "lbu", 0x25: "lhu"}[op]
        return f"{m:<5} ${R[rt]}, {simm:+#x}(${R[rs]})"
    if op in (0x28, 0x29, 0x2B):
        m = {0x28: "sb", 0x29: "sh", 0x2B: "sw"}[op]
        return f"{m:<5} ${R[rt]}, {simm:+#x}(${R[rs]})"
    if op == 0x12:
        if rs == 0:
            return f"mfc2  ${R[rt]}, r{rd}"
        if rs == 2:
            return f"cfc2  ${R[rt]}, c{rd}"
        if rs == 4:
            return f"mtc2  ${R[rt]}, r{rd}"
        if rs == 6:
            return f"ctc2  ${R[rt]}, c{rd}"
        return f"COP2  {GTE_FUNCT.get(f, f'funct=0x{f:02x}')}"
    if op == 0x32:
        return f"lwc2  r{rt}, {simm:+#x}(${R[rs]})"
    if op == 0x3A:
        return f"swc2  r{rt}, {simm:+#x}(${R[rs]})"
    return f"op=0x{op:02x}"


for va_want in [int(a, 16) for a in sys.argv[1:]]:
    for row in (P.ROW1, P.ROW2):
        for fn in P.parse(row):
            if fn["va"] != va_want:
                continue
            print(f"== {fn['name']} 0x{fn['va']:08x}..0x{fn['va'] + len(fn['words']) * 4:08x}")
            for i, (va, w) in enumerate(fn["words"]):
                print(f"  [{i:2d}] {va:08x} {w:08x}  {mnem(w)}")

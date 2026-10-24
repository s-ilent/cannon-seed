#!/usr/bin/env python3
"""probe_sdk_hosts.py - full decode of the two mainmenu_jp host data rows
around the three sibling sites, hunting for further unlanded SDK members."""
import struct

DELTA = 0x8001F800
BIN = "baselines/mainmenu_jp.bin"
REGS = ["zero", "at", "v0", "v1", "a0", "a1", "a2", "a3", "t0", "t1", "t2",
        "t3", "t4", "t5", "t6", "t7", "s0", "s1", "s2", "s3", "s4", "s5",
        "s6", "s7", "t8", "t9", "k0", "k1", "gp", "sp", "fp", "ra"]


def words(path, off, n):
    with open(path, "rb") as f:
        f.seek(off)
        return list(struct.unpack(f"<{n}I", f.read(4 * n)))


def decode(w, va):
    op = w >> 26
    rs = (w >> 21) & 31
    rt = (w >> 16) & 31
    rd = (w >> 11) & 31
    imm = w & 0xFFFF
    simm = imm - 0x10000 if imm >= 0x8000 else imm
    if w == 0:
        return "nop"
    if op == 3:
        return f"jal 0x{0x80000000 | ((w & 0x3FFFFFF) << 2):08x}"
    if op == 9:
        return f"addiu ${REGS[rt]}, ${REGS[rs]}, {simm:#x}"
    if op == 0x23:
        return f"lw ${REGS[rt]}, {simm:#x}(${REGS[rs]})"
    if op == 0x2b:
        return f"sw ${REGS[rt]}, {simm:#x}(${REGS[rs]})"
    if op == 0x12:  # COP2 group words: LWC2 / MTC2 / CTC2 / MFC2 by rs
        if rs == 0:
            return f"mfc2 ${REGS[rt]}, c{rd}"
        if rs == 2:
            return f"c2_op{rt:#x}"
        if rs == 4:
            return f"mtc2 ${REGS[rt]}, c{rd}"
        if rs == 6:
            return f"ctc2 ${REGS[rt]}, c{rd}"
        return f"lwc2 ${REGS[rt]}, {simm:#x}(${REGS[rs]})" if rs not in (0, 2, 4, 6) else "?"
    if op == 0x32 and rs not in (0, 2, 4, 6):
        return f"lwc2 ${REGS[rt]}, {simm:#x}(${REGS[rs]})"
    if op == 0x3A:
        return f"swc2 ${REGS[rt]}, {simm:#x}(${REGS[rs]})"
    if op == 0x29:
        return f"sh ${REGS[rt]}, {simm:#x}(${REGS[rs]})"
    if op == 0x0f:
        return f"lui ${REGS[rt]}, {imm:#x}"
    if op == 4:
        return f"beq ${REGS[rs]}, ${REGS[rt]}, {va + 4 + (simm << 2):#x}"
    if op == 5:
        return f"bne ${REGS[rs]}, ${REGS[rt]}, {va + 4 + (simm << 2):#x}"
    if op == 0:
        names = {0x21: "addu", 0x23: "subu", 0x24: "and", 0x25: "or",
                 0x2a: "slt", 0x00: "sll", 0x02: "srl", 0x03: "sra",
                 0x12: "mflo", 0x11: "mthi", 0x10: "mfhi", 0x18: "mult"}
        if fn := w & 63:
            if fn in (0x00, 0x02, 0x03):
                return f"{names[fn]} ${REGS[rd]}, ${REGS[rt]}, {(w >> 6) & 31}"
            return f"{names.get(fn, f'fn{fn:#x}')} ${REGS[rd]}, ${REGS[rs]}, ${REGS[rt]}"
    return f"op{op:#x} rs={REGS[rs]} rt={REGS[rt]} rd={rd} imm={simm:#x}"


def dump_range(title, off, n):
    ws = words(BIN, off, n)
    print(f"--- {title} file {off:#x}..{off + 4 * n:#x} (VA {off + DELTA:#x}..) ---")
    for i, w in enumerate(ws):
        print(f"  {off + 4 * i:#08x} {w:08x}  {decode(w, off + DELTA + 4 * i)}")


if __name__ == "__main__":
    # data_8005E6A0 full row: file 0x3EEA0, 0x1A8 bytes = 106 words
    dump_range("data_8005E6A0 (full 0x1a8)", 0x3EEA0, 0x1A8 // 4)
    print()
    # data_80066CF4 tail: last 0x140 bytes before row end 0x3EE44
    dump_range("data_80066CF4 tail 0x140", 0x3EE44 - 0x140, 0x140 // 4)

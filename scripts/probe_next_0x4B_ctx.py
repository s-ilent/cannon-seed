#!/usr/bin/env python3
"""probe_next_0x4B_ctx.py - little-endian decode of the three 9/12 sites
plus surrounding context to locate each site's true function head."""
import struct

DELTA = 0x8001F800

SITES = [
    ("g3_eu",    "baselines/g3_eu.bin",    0x27038, "func_80046660"),
    ("g3_jp",    "baselines/g3_jp.bin",    0x273D0, "func_800469F8"),
    ("g3org_eu", "baselines/g3org_eu.bin", 0x2448C, "func_80043AB4"),
]

REGS = ["zero","at","v0","v1","a0","a1","a2","a3","t0","t1","t2","t3","t4","t5",
        "t6","t7","s0","s1","s2","s3","s4","s5","s6","s7","t8","t9","k0","k1",
        "gp","sp","fp","ra"]


def decode(w, va):
    op = w >> 26
    rs = (w >> 21) & 31
    rt = (w >> 16) & 31
    rd = (w >> 11) & 31
    sa = (w >> 6) & 31
    fn = w & 63
    imm = w & 0xFFFF
    simm = imm - 0x10000 if imm >= 0x8000 else imm
    if op == 3:
        return f"jal 0x{0x80000000 | ((w & 0x3FFFFFF) << 2):08x}"
    if op == 2:
        return f"j 0x{0x80000000 | ((w & 0x3FFFFFF) << 2):08x}"
    if op == 9:
        return f"addiu ${REGS[rt]}, ${REGS[rs]}, {simm:#x}"
    if op == 0x23:
        return f"lw ${REGS[rt]}, {simm:#x}(${REGS[rs]})"
    if op == 0x2b:
        return f"sw ${REGS[rt]}, {simm:#x}(${REGS[rs]})"
    if op == 4:
        return f"beq ${REGS[rs]}, ${REGS[rt]}, {va + 4 + (simm << 2):#x}"
    if op == 5:
        return f"bne ${REGS[rs]}, ${REGS[rt]}, {va + 4 + (simm << 2):#x}"
    if op == 0:
        names = {0x21: "addu", 0x23: "subu", 0x24: "and", 0x25: "or", 0x2a: "slt",
                 0x00: "sll", 0x02: "srl", 0x03: "sra", 0x0c: "syscall", 0x0d: "break"}
        if fn == 0 and w == 0:
            return "nop"
        if fn in (0x00, 0x02, 0x03):
            return f"{names[fn]} ${REGS[rd]}, ${REGS[rt]}, {sa}"
        return f"{names.get(fn, f'fn{fn:#x}')} ${REGS[rd]}, ${REGS[rs]}, ${REGS[rt]}"
    return f"op{op:#x} rs={REGS[rs]} rt={REGS[rt]} imm={simm:#x}"


def dump(data, raw, va, n, label):
    print(f"  -- {label} (VA {va:#x}, raw {raw:#x}) --")
    words = struct.unpack_from(f">{0}I", data, 0) if False else None
    for i in range(n):
        off = raw + i * 4
        (w,) = struct.unpack_from("<I", data, off)
        print(f"    {va + i*4:#x}: {w:08x}  {decode(w, va + i*4)}")


def main():
    for tgt, path, raw_site, refname in SITES:
        with open(path, "rb") as f:
            data = f.read()
        va_site = raw_site + DELTA
        print(f"== {tgt}: site {va_site:#x} (vs landed {refname}) ==")
        dump(data, raw_site - 0x20, va_site - 0x20, 8, f"context before ({va_site-0x20:#x})")
        dump(data, raw_site, va_site, 12, "THE SITE BLOCK")
        dump(data, raw_site + 0x30, va_site + 0x30, 6, "context after")
        print()


if __name__ == "__main__":
    main()

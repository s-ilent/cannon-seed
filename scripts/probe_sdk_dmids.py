#!/usr/bin/env python3
"""probe_sdk_dmids.py - mainmenu_jp D-MID-ROW SDK set (queue item b).

Sites (census 2026-10-25 0436 re-derive):
  ApplyMatrixSV VA 0x8005E5F4 (file 0x3EDF4) votes 9 eq 14/23
  SetColorMatrix VA 0x8005E7E8 (file 0x3EFE8) votes 2 eq 7/12
  SetColorMatrix VA 0x8005E818 (file 0x3F018) votes 2 eq 7/12

Geography: landed ApplyMatrixSV row = file 0x3EE44 (0x5c), landed
SetColorMatrix row = file 0x3F048 (0x30); both starts coincide with the
host data rows' ends. DELTA = VA - file = 0x8001F800.

This probe dumps candidate + landed windows and word-compares candidate
vs landed reference to classify each site BEFORE any cut.
"""
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
    sa = (w >> 6) & 31
    fn = w & 63
    imm = w & 0xFFFF
    simm = imm - 0x10000 if imm >= 0x8000 else imm
    if w == 0:
        return "nop"
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
    if op == 0x1c and fn == 0x02:
        return f"madd ${REGS[rs]}, ${REGS[rt]}"
    if op == 0x10:
        # COP2 - distinguish mtc2 (rs=4) / ctc2 (rs=6) / mfc2 (rs=0) by rt field layout
        if rs == 0:
            return f"mfc2 ${REGS[rt]}, c{rd}{'' if sa == 0 else f'[{sa}]'}"
        if rs == 4:
            return f"mtc2 ${REGS[rt]}, c{rd}{'' if sa == 0 else f'[{sa}]'} (rs=4)"
        if rs == 6:
            return f"ctc2 ${REGS[rt]}, c{rd}{'' if sa == 0 else f'[{sa}]'} (rs=6)"
        if rs == 2:
            return f"c2 op{rt:#x}"
        return f"cop2 rs={rs} rt={rt} rd={rd} sa={sa}"
    if op == 0x12:
        return f"lwc2 ${REGS[rt]}, {simm:#x}(${REGS[rs]})"
    if op == 0x1a:
        return f"swc2 ${REGS[rt]}, {simm:#x}(${REGS[rs]})"
    if op == 0x29:
        return f"sh ${REGS[rt]}, {simm:#x}(${REGS[rs]})"
    if op == 0x08:
        return f"addi ${REGS[rt]}, ${REGS[rs]}, {simm:#x}"
    if op == 0x0f:
        return f"lui ${REGS[rt]}, {imm:#x}"
    if op == 4:
        return f"beq ${REGS[rs]}, ${REGS[rt]}, {va + 4 + (simm << 2):#x}"
    if op == 5:
        return f"bne ${REGS[rs]}, ${REGS[rt]}, {va + 4 + (simm << 2):#x}"
    if op == 0:
        names = {0x21: "addu", 0x23: "subu", 0x24: "and", 0x25: "or",
                 0x2a: "slt", 0x00: "sll", 0x02: "srl", 0x03: "sra",
                 0x0c: "syscall", 0x0d: "break", 0x12: "mflo", 0x11: "mthi"}
        if fn in (0x00, 0x02, 0x03):
            return f"{names[fn]} ${REGS[rd]}, ${REGS[rt]}, {sa}"
        return f"{names.get(fn, f'fn{fn:#x}')} ${REGS[rd]}, ${REGS[rs]}, ${REGS[rt]}"
    return f"op{op:#x} rs={REGS[rs]} rt={REGS[rt]} rd={rd} imm={simm:#x}"


def dump(title, off, n):
    ws = words(BIN, off, n)
    print(f"--- {title} (file {off:#x} VA {off + DELTA:#x}, {n} words) ---")
    for i, w in enumerate(ws):
        print(f"  [{i:2d}] {w:08x}  {decode(w, off + DELTA + 4 * i)}")
    return ws


def cmp_ref(title, cand_off, ref_off, n):
    cw = words(BIN, cand_off, n)
    rw = words(BIN, ref_off, n)
    diff = [i for i in range(n) if cw[i] != rw[i]]
    eq = n - len(diff)
    print(f"== {title}: candidate file {cand_off:#x} vs landed ref {ref_off:#x}: {eq}/{n} word-eq, differing {diff}")
    for i in diff:
        print(f"   [{i:2d}] cand {cw[i]:08x} ({decode(cw[i], cand_off + DELTA + 4*i)})"
              f"  vs ref {rw[i]:08x} ({decode(rw[i], ref_off + DELTA + 4*i)})")
    return eq, diff


if __name__ == "__main__":
    print("########## APPLYMATRIXSV SITE ##########")
    dump("data_80066CF4 tail context", 0x3ED80, 12)   # pre-candidate context
    dump("CANDIDATE window (23 words)", 0x3EDF4, 23)
    dump("landed ApplyMatrixSV row", 0x3EE44, 23)
    cmp_ref("ApplyMatrixSV", 0x3EDF4, 0x3EE44, 23)

    print()
    print("########## SETCOLORMATRIX SITES ##########")
    dump("data_8005E6A0 context", 0x3EF90, 10)
    dump("CANDIDATE-1 window (12 words)", 0x3EFE8, 12)
    dump("CANDIDATE-2 window (12 words)", 0x3F018, 12)
    dump("landed SetColorMatrix row", 0x3F048, 12)
    cmp_ref("SetColorMatrix #1", 0x3EFE8, 0x3F048, 12)
    cmp_ref("SetColorMatrix #2", 0x3F018, 0x3F048, 12)

    print()
    print("########## CROSS-TARGET: do these copies exist elsewhere? ##########")
    for tgt in ["mainmenu_eu", "g3_jp", "g3_eu", "g3org_jp", "g3org_eu",
                "slps_00270", "sces_00269"]:
        try:
            with open(f"baselines/{tgt}.bin", "rb") as f:
                blob = f.read()
        except FileNotFoundError:
            continue
        for label, off in [("AMSV cand", 0x3EDF4), ("SCM cand12", 0x3EFE8),
                           ("SCM cand2", 0x3F018)]:
            pat = struct.pack("<8I", *words(BIN, off, 8))
            cnt = blob.count(pat)
            if cnt:
                print(f"  {tgt}: first-8-words of {label} x{cnt}")
            else:
                print(f"  {tgt}: {label} first-8 no hit")

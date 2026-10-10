#!/usr/bin/env python3
"""Diagnose whether data blobs hide function prologues (scan v2 seed).

Walks every asm subsegment that restores callee-saved registers in its
epilogue (frame teardown `addiu $sp,$sp,+N`) but whose listed body lacks
the matching prologue (`addiu $sp,$sp,-N` + register saves). For each,
scans the PRECEDING subsegment's bytes for a plausible prologue pattern
in the tail: sw $ra,<off>($sp) / sw $s0.. / addiu $sp,$sp,-frame.

Read-only: prints a report; changes nothing.
"""
import re, struct, sys

YAML = "config/splat.slps_00270.yaml"
BASE = "baselines/slps_00270.bin"
VLOAD = 0x80020000  # payload vram base (file offset 0x800)

subsegs = []
for ln in open(YAML):
    m = re.match(r"\s*-\s*\[(0x[0-9A-Fa-f]+),\s*(asm|c|data),\s*(\w+)\]\s*#\s*(0x[0-9A-Fa-f]+)", ln)
    if m:
        subsegs.append((int(m.group(1), 16), m.group(2), m.group(3), int(m.group(4), 16)))

payload = open(BASE, "rb").read()

def word_at(vram_addr):
    off = vram_addr - VLOAD
    if off < 0 or off + 4 > len(payload):
        return None
    return struct.unpack("<I", payload[off:off + 4])[0]

def disasm_word(w):
    """Very small MIPS-I disassembler for the patterns we care about."""
    op = w >> 26
    rs, rt, rd, sa, fn = (w >> 21) & 31, (w >> 16) & 31, (w >> 11) & 31, (w >> 6) & 31, w & 63
    imm = w & 0xFFFF
    simm = imm - 0x10000 if imm >= 0x8000 else imm
    R = ["zero","at","v0","v1","a0","a1","a2","a3","t0","t1","t2","t3","t4","t5","t6","t7",
         "s0","s1","s2","s3","s4","s5","s6","s7","t8","t9","k0","k1","gp","sp","fp","ra"]
    if op == 9:  return f"addiu {R[rt]}, {R[rs]}, {simm:#x}"
    if op == 35: return f"lw {R[rt]}, {simm:#x}({R[rs]})"
    if op == 43: return f"sw {R[rt]}, {simm:#x}({R[rs]})"
    if op == 0 and fn == 8: return "jr"
    return None

print("== per-glabel census: functions (first or later glabel in an asm file)\n   whose body tears down a frame + restores $ra but shows no prologue ==")
for i, (start, typ, name, size) in enumerate(subsegs):
    if typ not in ("asm", "c"):
        continue
    asmfile = f"asm/nonmatchings/{name}.s"
    try:
        text = open(asmfile).read()
    except OSError:
        continue
    # split per glabel: each function in the file judged independently
    blocks = re.split(r"(?=\n?glabel\s+)", text)
    for blk in blocks:
        m = re.match(r"\n?glabel\s+(\S+)", blk)
        if not m:
            continue
        gname = m.group(1)
        has_teardown = re.search(r"addiu\s+\$sp, \$sp, (0x[0-9A-Fa-f]+)\s*$", blk, re.M)
        has_ra_restore = re.search(r"lw\s+\$ra, (0x[0-9A-Fa-f]+)\(\$sp\)", blk)
        has_prologue = re.search(r"addiu\s+\$sp, \$sp, -(0x[0-9A-Fa-f]+)", blk)
        if not (has_teardown and has_ra_restore and not has_prologue):
            continue
        frame = int(has_teardown.group(1), 16)
        # the glabel's own address: spimdisasm labels are func_XXXXXXXX
        gaddr = int(gname.split("_")[-1], 16) if re.fullmatch(r"func_[0-9A-Fa-f]{8}", gname) else None
        if gaddr is None or i == 0:
            continue
        # scan backward across contiguous preceding subsegments (data or
        # asm), up to 0x400 bytes total, for the frame-matching prologue
        found = []
        budget = 0x400
        j = i - 1
        vstart = gaddr  # vram; word_at takes vram
        while j >= 0 and budget > 0:
            pstart, ptyp, pname, psize = subsegs[j]
            plo = VLOAD + pstart
            lo = max(plo, vstart - budget)
            for a in range(vstart - 4, lo - 1, -4):
                w = word_at(a)
                d = disasm_word(w) if w else None
                if d and d.startswith("addiu $sp, $sp, -") and int(d.split(", ")[-1], 16) == frame:
                    found.append((a, d, pname))
            budget -= vstart - lo
            vstart = lo
            j -= 1
        tag = "HIDDEN-PROLOGUE" if found else "NO-PROLOGUE-FOUND"
        if "_hdr" not in globals():
            print(f"{'fragment':<24} {'frame':>6}  verdict (backward scan <=0x400)")
            globals()["_hdr"] = True
        extra = ""
        if found:
            a, d, pname = found[-1]
            extra = f"  <- {a:#x} inside {pname}"
        print(f"{gname:<24} {frame:>6}  {tag}{extra}")

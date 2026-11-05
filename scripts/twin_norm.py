#!/usr/bin/env python3
"""Relocation-normalized twin comparison for SsVabOpenHeadWithMode.

Masks the displacement/immediate fields of j/jal/branch instructions so
per-target link addresses stop counting as differences, then diffs the
normalized streams.

Usage: twin_norm.py <base.words> <twin.words>
Prints a summary: total, diff words after normalization, and the first
few differing indices with both raw words.
"""
import sys

JAL_OP = 0x03
J_OP = 0x02


def mask(w):
    v = int(w, 16)
    op = v >> 26
    if op == JAL_OP or op == J_OP:
        return v & 0xFC000000          # keep opcode, drop the target
    if op == 0x05 or op == 0x04 or op == 0x06 or op == 0x07:  # bne/beq/blez/bgtz
        return v & 0xFFFF0000          # drop the 16-bit displacement
    if op == 0x01:                     # regimm (bltz/bgez/...)
        return v & 0xFC1FFFFF
    return v


a = [l.strip() for l in open(sys.argv[1]) if l.strip()]
b = [l.strip() for l in open(sys.argv[2]) if l.strip()]
n = min(len(a), len(b))
diffs = [(i, a[i], b[i]) for i in range(n) if mask(a[i]) != mask(b[i])]
print(f"compared {n} words; {len(diffs)} normalized diffs")
for i, wa, wb in diffs[:12]:
    print(f"  [{i:3d}] base {wa} twin {wb}")

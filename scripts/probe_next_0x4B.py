#!/usr/bin/env python3
"""probe_next_0x4B.py - classify the census's three 9/12 sites against the
landed 0x4B wrapper shapes (cron-202610250436).

The census (post-landing, fresh oracle) votes:
  g3_eu    0x80046838 vs src func_80046660 (raw 0x26E60)
  g3_jp    0x80046BD0 vs src func_800469F8 (raw 0x271F8)
  g3org_eu 0x80043C8C vs src func_80043AB4 (raw 0x242B4)
Each site sits +0x1D8 after its landed reference. word-eq 9/12: exactly
three words differ per site. This probe prints the diffs and decodes the
differing words as MIPS-I (jal / addiu-style const slots).
"""
import struct

DELTA = 0x8001F800  # VA = raw + DELTA (yaml_off law)

SITES = [
    ("g3_eu",    "baselines/g3_eu.bin",    0x26E60, 0x80046660, 0x80046838, "func_80046660"),
    ("g3_jp",    "baselines/g3_jp.bin",    0x271F8, 0x800469F8, 0x80046BD0, "func_800469F8"),
    ("g3org_eu", "baselines/g3org_eu.bin", 0x242B4, 0x80043AB4, 0x80043C8C, "func_80043AB4"),
]


def jal_target(w):
    if (w >> 26) != 3:  # opcode 3 = J
        return None
    return 0x80000000 | ((w & 0x3FFFFFF) << 2)


def decode(w):
    op = w >> 26
    if op == 3:
        return f"jal 0x{jal_target(w):08x}"
    rs = (w >> 21) & 31
    rt = (w >> 16) & 31
    imm = w & 0xFFFF
    simm = imm - 0x10000 if imm >= 0x8000 else imm
    if op == 9:  # addiu
        return f"addiu ${rt}, ${rs}, {simm:#x} ({simm})"
    if op == 0:
        return f"special fn={w & 63}"
    return f"op={op} rs={rs} rt={rt} imm={simm:#x}"


def main():
    for tgt, path, raw_ref, va_ref, va_site, refname in SITES:
        with open(path, "rb") as f:
            data = f.read()
        raw_site = va_site - DELTA
        ref = struct.unpack_from(">12I", data, raw_ref)
        site = struct.unpack_from(">12I", data, raw_site)
        print(f"== {tgt}: site VA {va_site:#x} (raw {raw_site:#x}) vs landed "
              f"{refname} VA {va_ref:#x} (raw {raw_ref:#x}) ==")
        diffs = []
        for i, (a, b) in enumerate(zip(ref, site)):
            mark = "  ==" if a == b else "  !="
            if a != b:
                diffs.append(i)
            print(f"  w{i:02d} ref={a:08x} site={b:08x}{mark}  "
                  f"| ref: {decode(a):<28} site: {decode(b)}")
        print(f"  -> {12 - len(diffs)}/12 word-eq, differing words: {diffs}")
        print()


if __name__ == "__main__":
    main()

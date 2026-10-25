#!/usr/bin/env python3
"""probe_setrot_dw2.py - decode the six dw=2 SetRotMatrix-variant candidates
in mainmenu_jp (census 10/12 vs the landed SetRotMatrix row).

For each candidate VA: dump the 12 baseline words, diff word-by-word against
the landed SetRotMatrix body words, and print the divergence positions with
both encodings decoded as MIPS-I (capstone) so the variant class names itself.
"""
import struct, sys
sys.path.insert(0, "tools")

REPO = "."

# landed reference: mainmenu_jp SetRotMatrix row (yaml carve 0x3EFE8, size 0x30)
REF_VA = 0x8005E7E8
REF_SIZE = 0x30

CANDS = [0x8005D9BC, 0x8005DB1C, 0x8005DDF4, 0x8005DF04, 0x8005E3DC, 0x8005E4E8]

baseline = open("baselines/mainmenu_jp.bin", "rb").read()

# baseline VA->file offset: PSX-EXE, image base 0x80020000, header 0x800, LE words
def off(va):
    return va - 0x80020000 + 0x800

ref_words = list(struct.unpack_from("<12I", baseline, off(REF_VA)))

try:
    from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32
    md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32)
    def dis(w, va):
        b = struct.pack(">I", w)
        for i in md.disasm(b, va):
            return f"{i.mnemonic} {i.op_str}"
        return ".word"
except Exception:
    def dis(w, va):
        return ".word"

print(f"reference SetRotMatrix @ {REF_VA:#x} (landed c row):")
for i, w in enumerate(ref_words):
    print(f"  [{i:2d}] {w:08x}  {dis(w, REF_VA + 4*i)}")

for va in CANDS:
    cw = list(struct.unpack_from("<12I", baseline, off(va)))
    diffs = [i for i in range(12) if cw[i] != ref_words[i]]
    print(f"\ncandidate {va:#x}: dw={len(diffs)} at {diffs}")
    for i in diffs:
        print(f"  [{i:2d}] cand {cw[i]:08x} ({dis(cw[i], va + 4*i)})"
              f"  !=  ref {ref_words[i]:08x} ({dis(ref_words[i], REF_VA + 4*i)})")

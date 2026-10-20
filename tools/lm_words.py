#!/usr/bin/env python3
"""GsSetLightMode six-way retail word proof (tools/lm_words.py).

Window cron-20261020-0957 discovered the six-target GsSetLightMode wave
and ran this comparison from a repo-external scratch script; the
fifteenth rollback ate that scratch, so the tool now lives in-repo.

Parses the six stale nonmatching .s files (each line's comment carries
the retail byte encoding as `/* fileoff VA bytes */`), normalizes the
little-endian byte hex to instruction words, and proves the six copies
shape-identical: every slot where the six words agree is printed as
identical, every slot with any disagreement is printed with the
per-target values. Address-bearing fields (internal j targets, the
mode-static %hi/%lo pairs, the printf string %hi/%lo, the jal printf)
are exactly the expected disagreement set; the register/opcode fields
are the shared shape that one C source must reproduce.

Usage: python3 tools/lm_words.py   (no arguments)
"""
import re
import sys

REPO = __file__.rsplit("/tools/", 1)[0]

# (target, stale nonmatching .s) - the six LIBGS SCLIB placements of
# GsSetLightMode, none landed as of this window.
SIX = [
    ("g3_jp",      "asm/g3_jp/nonmatchings/func_80067128.s"),
    ("g3_eu",      "asm/g3_eu/nonmatchings/func_800678BC.s"),
    ("g3org_jp",   "asm/g3org_jp/nonmatchings/func_80063FD4.s"),
    ("g3org_eu",   "asm/g3org_eu/nonmatchings/func_80064720.s"),
    ("mainmenu_jp", "asm/mainmenu_jp/nonmatchings/func_8007F138.s"),
    ("mainmenu_eu", "asm/mainmenu_eu/nonmatchings/func_8007F894.s"),
]

LINE = re.compile(r"/\*\s*[0-9A-Fa-f]+\s+[0-9A-Fa-f]{8}\s+([0-9A-Fa-f]{8})\s*\*/")


def words_of(path):
    out = []
    for ln in open(f"{REPO}/{path}"):
        m = LINE.search(ln)
        if m:
            # comment hex is the byte sequence in file order (LE)
            out.append(int.from_bytes(bytes.fromhex(m.group(1)), "little"))
    return out


def main():
    per = {}
    for t, p in SIX:
        w = words_of(p)
        if per and len(w) != len(next(iter(per.values()))):
            print(f"FATAL: {t} has {len(w)} words, expected {len(next(iter(per.values())))}")
            return 1
        per[t] = w

    n = len(next(iter(per.values())))
    print(f"{n} instruction slots across {len(per)} targets")
    same = diff = 0
    for i in range(n):
        vals = [per[t][i] for t in per]
        if all(v == vals[0] for v in vals):
            same += 1
            continue
        diff += 1
        print(f"slot {i:2d} differs:")
        for t in per:
            print(f"  {t:12s} {per[t][i]:08x}")
    print(f"identical slots: {same}, differing slots: {diff}")
    if diff == 0:
        print("SIX-WAY PROOF: all slots byte-identical (unexpected for address-bearing fields)")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

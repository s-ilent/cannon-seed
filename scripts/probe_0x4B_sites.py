#!/usr/bin/env python3
"""probe_0x4B_sites.py - ground-truth probe for the 0x4B pair family wave
(window cron-20261025-0321): decode the oracle wrapper bodies (0x30) at the
census-re-derived sites and locate each containing yaml row.

The family shapes are the landed mainmenu_eu wrappers:
  src/func_8005AC68.c  -> callee(x, y, 0x4B)   (12 words)
  src/func_8005AE70.c  -> callee(x, y, 0x17)   (12 words, same stream)
Only the third-arg immediate and the per-target jal differ.
"""
import re
import struct
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HDR = 0x800
BASE_VA = 0x80020000

SITES = [
    ("g3_eu", 0x80046660),
    ("g3_eu", 0x80046868),
    ("g3_jp", 0x800469F8),
    ("g3_jp", 0x80046C00),
    ("g3org_eu", 0x80043AB4),
    ("g3org_eu", 0x80043CBC),
    ("g3org_jp", 0x8004409C),
    ("mainmenu_jp", 0x8005B038),
    ("mainmenu_jp", 0x8005B240),
]

# reference: mainmenu_eu landed wrappers (0x30 each)
REFS = [("0x4B shape (func_8005AC68)", "mainmenu_eu", 0x8005AC68),
        ("0x17 shape (func_8005AE70)", "mainmenu_eu", 0x8005AE70)]


def words(target, va, n):
    buf = open(REPO / "baselines" / f"{target}.bin", "rb").read()
    off = va - BASE_VA + HDR
    b = buf[off:off + 4 * n]
    assert len(b) == 4 * n, (target, hex(va), len(b))
    return list(struct.unpack(f"<{n}I", b))


def rows_of(target):
    """[(raw_start, extent, kind, name)] from the target's splat yaml."""
    out = []
    txt = open(REPO / "config" / f"splat.{target}.yaml").read()
    for m in re.finditer(r"\[0x([0-9a-fA-F]+), (\w+), ([\w.]+)\]\s*#\s*0x([0-9a-fA-F]+)", txt):
        start, kind, name, ext = int(m.group(1), 16), m.group(2), m.group(3), int(m.group(4), 16)
        out.append((start, ext, kind, name))
    return out


def containing(rows, raw):
    for start, ext, kind, name in rows:
        if start <= raw < start + ext:
            return (start, ext, kind, name, raw - start)
    return None


# reference word streams
print("=== reference bodies (mainmenu_eu, landed) ===")
refs = {}
for tag, t, va in REFS:
    w = words(t, va, 12)
    refs[tag] = w
    jal = [i for i, x in enumerate(w) if (x >> 26) == 3]
    imm = [i for i, x in enumerate(w) if x in (0x4B, 0x17) or (x & 0xFFFF) in (0x4B, 0x17)]
    print(f"{tag}: va={va:08X} jal_word(s)={jal} const_word(s)={imm}")
    for i, x in enumerate(w):
        print(f"    {i:2d}: {x:08X}")

print()
print("=== candidate sites ===")
for t, va in SITES:
    w = words(t, va, 12)
    raw = va - BASE_VA + HDR
    row = containing(rows_of(t), raw)
    rowtxt = (f"{row[3]} [{row[2]}] +{row[4]:#x} (row {row[0]:#x} #{row[1]:#x})"
              if row else "NO CONTAINING ROW")
    verdicts = []
    for tag, rw in refs.items():
        diffs = [(i, rw[i], w[i]) for i in range(12)
                 if (rw[i] >> 26) != 3 and (w[i] >> 26) != 3 and rw[i] != w[i]]
        if not diffs:
            verdicts.append(f"{tag} IDENTICAL")
        elif len(diffs) == 1 and (diffs[0][1] ^ diffs[0][2]) >> 16 == 0:
            verdicts.append(f"{tag} 1 low-half diff w{diffs[0][0]}: "
                            f"{diffs[0][1]:08X} vs {diffs[0][2]:08X}")
        else:
            verdicts.append(f"{tag} {len(diffs)} diffs: " +
                            "; ".join(f"w{i} {e:08X}/{g:08X}" for i, e, g in diffs[:3]))
    jals = [(i, w[i]) for i, x in enumerate(w) if (x >> 26) == 3]
    print(f"{t:12s} {va:08X} (raw {raw:#x}) in {rowtxt}")
    print(f"    jal: {jals}")
    for v in verdicts:
        print(f"    vs {v}")

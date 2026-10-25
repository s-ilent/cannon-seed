#!/usr/bin/env python3
"""land_scalematrixl_edits.py - the ScaleMatrixL x8 landing's tree edits.

Seven whole-row asm->c flips (one line each) + mainmenu_jp's data-row
cut (data_80066CF4 0xc40 -> head 0x6e0 / c block 0x124 / tail 0x43c).
Exact-string replacement, one pattern per file, loud failure on any
miss - the sed -e accumulation bug banked in cron-202610251206 must not
recur.
"""
import sys
from pathlib import Path

REPO = Path("/home/z/my-project/cannon-seed")

FLIPS = [
    ("config/splat.g3_eu.yaml",
     "      - [0x29D98, asm, func_80049598]   # 0x124 sdk",
     "      - [0x29D98, c, ScaleMatrixL]   # 0x124 sdk"),
    ("config/splat.g3_jp.yaml",
     "      - [0x2A380, asm, func_80049B80]   # 0x124 sdk",
     "      - [0x2A380, c, ScaleMatrixL]   # 0x124 sdk"),
    ("config/splat.g3org_eu.yaml",
     "      - [0x271EC, asm, func_800469EC]   # 0x124 sdk",
     "      - [0x271EC, c, ScaleMatrixL]   # 0x124 sdk"),
    ("config/splat.g3org_jp.yaml",
     "      - [0x2781C, asm, func_8004701C]   # 0x124 sdk",
     "      - [0x2781C, c, ScaleMatrixL]   # 0x124 sdk"),
    ("config/splat.mainmenu_eu.yaml",
     "      - [0x3E274, asm, func_8005DA74]   # 0x124 sdk",
     "      - [0x3E274, c, ScaleMatrixL]   # 0x124 sdk"),
    ("config/splat.sces_00269.yaml",
     "      - [0x14978, asm, func_80034178]   # 0x124 sdk",
     "      - [0x14978, c, ScaleMatrixL]   # 0x124 sdk"),
    ("config/splat.slps_00270.yaml",
     "      - [0x14EB0, asm, func_800346B0]   # 0x124 sdk",
     "      - [0x14EB0, c, ScaleMatrixL]   # 0x124 sdk"),
]

CUT_OLD = "      - [0x3E1B4, data, data_80066CF4]   # 0xc40\n"
CUT_NEW = (
    "      - [0x3E1B4, data, data_80066CF4]   # 0x6e0\n"
    "      - [0x3E894, c, ScaleMatrixL]      # 0x124 sdk\n"
    "      - [0x3E9B8, data, data_8005E1B8]  # 0x43c\n"
)

for rel, old, new in FLIPS:
    p = REPO / rel
    text = p.read_text()
    n = text.count(old)
    if n != 1:
        print(f"FAIL {rel}: pattern count {n} (want 1):\n  {old}")
        sys.exit(1)
    p.write_text(text.replace(old, new))
    print(f"flipped {rel}")

p = REPO / "config/splat.mainmenu_jp.yaml"
text = p.read_text()
n = text.count(CUT_OLD)
if n != 1:
    print(f"FAIL mainmenu_jp cut: pattern count {n} (want 1)")
    sys.exit(1)
p.write_text(text.replace(CUT_OLD, CUT_NEW))
print("cut     config/splat.mainmenu_jp.yaml (data_80066CF4 -> 0x6e0 | ScaleMatrixL 0x124 | data_8005E1B8 0x43c)")
print("OK: 8 yamls edited")

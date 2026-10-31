#!/usr/bin/env python3
"""probe_80067690_member.py - is func_80067690 (g3_eu) a psyq archive member?

The function's per-voice record-default store run (g3_eu 0x80067928..0x4C)
carries ten instructions whose immediates are ALL non-relocated (ori
immediates + store offsets):

    ori  $v0, $zero, 0x200   sh $v0, 0x6($a0)
    ori  $v0, $zero, 0x1000  sh $v0, 0x4($a0)
    ori  $v0, $zero, 0x80FF  sh $v0, 0x8($a0)
    ori  $v0, $zero, 0x4000  sh $zero, 0x0($a0)   (rt=$zero)
    sh $zero, 0x2($a0)       sh $v0, 0xA($a0)

If the game's copy IS an archive member, these 40 bytes appear verbatim in
the archive. A hit maps to its container module via the module @offsets
from tools/omf_pubsyms.py. Also checks the opening 0x18-byte prologue run
(addiu sp,-0x18 / sw s0,0x10 / addu s0,a0 / sw ra,0x14) which carries no
relocated fields either.
"""
import glob
import re
import struct
import sys

RECORD_RUN = bytes.fromhex(
    "00020234" "060082A4" "00100234" "040082A4" "FF800234"
    "080082A4" "00400234" "000080A4" "020080A4" "0A0082A4"
)
PROLOGUE_RUN = bytes.fromhex(
    "E8FFBD27"  # addiu $sp, $sp, -0x18
    "1000B0AF"  # sw $s0, 0x10($sp)
    "21808000"  # addu $s0, $a0, $zero
    "1400BFAF"  # sw $ra, 0x14($sp)
)

MODULE_RE = re.compile(r"module '([^']+)' @0x([0-9a-f]+) size=0x([0-9a-f]+)")


def module_map(tool_out: str):
    mods = []
    for m in MODULE_RE.finditer(tool_out):
        mods.append((m.group(1), int(m.group(2), 16), int(m.group(3), 16)))
    return mods


def owner(mods, off):
    for name, start, size in mods:
        if start <= off < start + size:
            return name
    return "?"


def main() -> int:
    import subprocess

    tool = "/home/z/my-project/cannon-seed/tools/omf_pubsyms.py"
    libs = sorted(glob.glob("/home/z/my-project/psyq/3.3/PSX/LIB/*.LIB"))
    hits = 0
    for lib in libs:
        data = open(lib, "rb").read()
        out = subprocess.run(
            [sys.executable, tool, lib], capture_output=True, text=True
        ).stdout
        mods = module_map(out)
        for tag, pat in (("record-run", RECORD_RUN), ("prologue-run", PROLOGUE_RUN)):
            idx = data.find(pat)
            while idx != -1:
                name = owner(mods, idx)
                print(f"{lib.split('/')[-1]:14s} {tag:12s} @0x{idx:06x} module={name}")
                hits += 1
                idx = data.find(pat, idx + 1)
    print(f"total hits: {hits}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

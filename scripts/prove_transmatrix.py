#!/usr/bin/env python3
"""prove_transmatrix.py - offline word-proof for the staged TransMatrix
x8 landing (window cron-202610251051, the survey-class item that turned
into the next SDK set).

Compile src/TransMatrix.c with the pinned toolchain (tools/cc.sh), read
the .o's .text words, and compare word-for-word against the oracle body
read straight from each target's baseline at the eight census/anchor
sites (the twin scan: the 9-word body is byte-identical in all eight
executables, always opening the graveyard pair TransMatrix+ScaleMatrix):

  slps_00270   0x154BC   g3_jp       0x2A98C
  sces_00269   0x14F84   g3_eu       0x2A3A4
  mainmenu_jp  0x3EEA0   g3org_jp    0x27E28
  mainmenu_eu  0x3E880   g3org_eu    0x277F8

No reloc slots: the body is a frameless leaf whose every word is
position-independent (no jal, no lui/%lo). A full word-identical verdict
against all eight sites is the dw=0 class the first-shot landing wants.
"""
import struct
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CC = REPO / "tools" / "cc.sh"
WORK = Path("/home/z/my-project/build/prove_transmatrix")
WORK.mkdir(parents=True, exist_ok=True)

SITES = [
    ("slps_00270", 0x154BC),
    ("sces_00269", 0x14F84),
    ("mainmenu_jp", 0x3EEA0),
    ("mainmenu_eu", 0x3E880),
    ("g3_jp", 0x2A98C),
    ("g3_eu", 0x2A3A4),
    ("g3org_jp", 0x27E28),
    ("g3org_eu", 0x277F8),
]

N = 9  # 0x24 words


def o_text_words(o_path):
    """The .o's .text as a list of 32-bit LE words, parsed from the ELF."""
    d = open(o_path, "rb").read()
    assert d[:4] == b"\x7fELF", o_path
    (_t, _m, _v, _e, _p, e_shoff, _f, _eh, _ph, _pn,
     e_shentsize, e_shnum, e_shstrndx) = struct.unpack_from("<HHIIIIIHHHHHH", d, 16)
    secs = []
    for i in range(e_shnum):
        (sh_name, sh_type, sh_flags, sh_addr, sh_offset, sh_size,
         sh_link, sh_info, sh_addralign, sh_entsize) = \
            struct.unpack_from("<10I", d, e_shoff + i * e_shentsize)
        secs.append((sh_name, sh_type, sh_flags, sh_offset, sh_size))
    _, _, _, so, ss = secs[e_shstrndx]
    names = d[so:so + ss]
    for sh_name, sh_type, sh_flags, sh_offset, sh_size in secs:
        end = names.find(b"\0", sh_name)
        if names[sh_name:end] == b".text":
            buf = d[sh_offset:sh_offset + sh_size]
            return [int.from_bytes(buf[i:i + 4], "little")
                    for i in range(0, len(buf) - 3, 4)]
    raise AssertionError(f"no .text in {o_path}")


src = REPO / "src" / "TransMatrix.c"
out = WORK / "TransMatrix.o"
try:
    subprocess.run(["sh", str(CC), "-o", str(out), str(src)],
                   check=True, capture_output=True, text=True)
except subprocess.CalledProcessError as e:
    print(f"COMPILE FAILED\n{e.stderr[-800:]}")
    sys.exit(1)

got = o_text_words(out)
print(f"compiled .text: {len(got)} words")
failures = 0
for target, off in SITES:
    data = open(REPO / "baselines" / f"{target}.bin", "rb").read()
    expected = list(struct.unpack_from(f"<{N}I", data, off))
    diffs = [(i, expected[i], got[i]) for i in range(min(len(got), N))
             if expected[i] != got[i]]
    extra = got[N:]
    # gas pads the default .text section to 16 bytes on MIPS (cc.sh's own
    # note); the real build avoids it by renaming the section (.r_<rom>)
    # in build.sh's C staging, so trailing all-zero words here are the
    # known artifact and carry no instruction bytes.
    pad = all(w == 0 for w in extra)
    verdict = "WORD-IDENTICAL" if not diffs and pad else \
        f"{len(diffs)} DIFF, {len(extra)} EXTRA({'zeroes' if pad else 'NONZERO'})"
    print(f"{target:12} @{off:06x}: {verdict}")
    for i, e, g in diffs:
        print(f"   [{i:2d}] oracle {e:08x} vs got {g:08x}")
    if extra and not pad:
        print(f"   extra: {' '.join(f'{w:08x}' for w in extra)}")
    if diffs or not pad:
        failures += 1

print()
if failures:
    print(f"FAIL: {failures} site(s) differ")
    sys.exit(1)
print("PASS: TransMatrix word-identical at all 8 sites")

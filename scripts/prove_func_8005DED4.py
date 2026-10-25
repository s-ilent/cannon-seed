#!/usr/bin/env python3
"""prove_func_8005DED4.py - offline word-proof for the staged
func_8005DED4 x8 landing (window cron-202610251706, the walk's smallest
clean landing class: the 0x30 rotation-matrix commit tail).

Compile src/func_8005DED4.c with the pinned toolchain (tools/cc.sh), read
the .o's .text words, and compare word-for-word against the oracle body
located by word-search in each target's baseline: the 12-word pattern is
banked byte-identical in all eight executables (the walk's sibling map,
window cron-202610251551) - mainmenu_jp holds it inside the data_80066CF4
graveyard head row, the seven other targets carry it as the tail of their
#0x110 walk mega-row (rel +0xE0). The search asserts exactly ONE
occurrence per target, so the proof both locates and verifies the sites.

No reloc slots: the body is a frameless leaf whose every word is
position-independent (no jal, no lui/%lo; ctc2 and the CPU packing words
assemble natively). A full word-identical verdict against all eight
sites is the dw=0 class the first-shot landing wants.
"""
import struct
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CC = REPO / "tools" / "cc.sh"
WORK = Path("/home/z/my-project/build/prove_func_8005DED4")
WORK.mkdir(parents=True, exist_ok=True)

TARGETS = [
    "slps_00270", "sces_00269", "mainmenu_jp", "mainmenu_eu",
    "g3_jp", "g3_eu", "g3org_jp", "g3org_eu",
]

N = 12  # 0x30 words


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


src = REPO / "src" / "func_8005DED4.c"
out = WORK / "func_8005DED4.o"
try:
    subprocess.run(["sh", str(CC), "-o", str(out), str(src)],
                   check=True, capture_output=True, text=True)
except subprocess.CalledProcessError as e:
    print(f"COMPILE FAILED\n{e.stderr[-800:]}")
    sys.exit(1)

got = o_text_words(out)
print(f"compiled .text: {len(got)} words")

failures = 0
for target in TARGETS:
    data = open(REPO / "baselines" / f"{target}.bin", "rb").read()
    pattern = struct.pack(f"<{N}I", *got[:N])
    sites = []
    start = 0
    while True:
        i = data.find(pattern, start)
        if i < 0:
            break
        sites.append(i)
        start = i + 1
    if len(sites) != 1:
        print(f"{target:12}: {len(sites)} SITE(S) {[hex(s) for s in sites]} - "
              f"sibling map expects exactly one")
        failures += 1
        continue
    off = sites[0]
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

print("PROOF PASS" if failures == 0 else f"PROOF FAIL ({failures})")
sys.exit(0 if failures == 0 else 1)

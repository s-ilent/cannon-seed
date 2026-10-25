#!/usr/bin/env python3
"""prove_scalematrix.py - offline word-proof for the staged ScaleMatrix
x8 landing (window cron-202610251206, the graveyard pair's second
member opened by the TransMatrix wave).

Compile src/ScaleMatrix.c with the pinned toolchain (tools/cc.sh), read
the .o's .text words, and compare word-for-word against the oracle body
read straight from each target's baseline at the eight census/anchor
sites (the TransMatrix wave's twin scan: the 0x124 body is byte-identical
in all eight executables, always closing the graveyard pair
TransMatrix+ScaleMatrix):

  slps_00270   0x154E0   g3_jp       0x2A9B0
  sces_00269   0x14FA8   g3_eu       0x2A3C8
  mainmenu_jp  0x3EEC4   g3org_jp    0x27E4C
  mainmenu_eu  0x3E8A4   g3org_eu    0x2781C

No reloc slots: the body is a frameless leaf whose every word is
position-independent (no jal, no lui/%lo). The C's asm block carries
the first 71 retail words verbatim; GCC's frameless epilogue emits the
jr $ra and its delayed-branch fill must place the C-level store
`m[4] = last` (register-bound to $9) into the branch delay slot -
exactly the retail tail. A full word-identical verdict against all
eight sites is the dw=0 class the first-shot landing wants.
"""
import struct
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CC = REPO / "tools" / "cc.sh"
WORK = Path("/home/z/my-project/build/prove_scalematrix")
WORK.mkdir(parents=True, exist_ok=True)

SITES = [
    ("slps_00270", 0x154E0),
    ("sces_00269", 0x14FA8),
    ("mainmenu_jp", 0x3EEC4),
    ("mainmenu_eu", 0x3E8A4),
    ("g3_jp", 0x2A9B0),
    ("g3_eu", 0x2A3C8),
    ("g3org_jp", 0x27E4C),
    ("g3org_eu", 0x2781C),
]

N = 73  # 0x124 words


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


src = REPO / "src" / "ScaleMatrix.c"
out = WORK / "ScaleMatrix.o"
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
print("PASS: ScaleMatrix word-identical at all 8 sites")

#!/usr/bin/env python3
"""prove_sdk_siblings.py - offline word-proof for the three staged
D-MID-ROW SDK sibling landings (window cron-202610250706, queue item b).

For each staged src unit: compile with the pinned toolchain (tools/cc.sh),
read the .o's .text words, and compare word-for-word against the oracle
body words read straight from baselines/mainmenu_jp.bin at the three
census-parked sites:

  SetRotMatrix    file 0x3EFE8 (VA 0x8005E7E8) 12 words
  SetLightMatrix  file 0x3F018 (VA 0x8005E818) 12 words
  ApplyMatrixLV   file 0x3EDF4 (VA 0x8005E5F4) 20 words

No reloc slots: all three bodies are frameless leaves whose every word is
position-independent (no jal, no lui/%lo - the only .word is the banked
mvmva constant). A full word-identical verdict here is the dw=0 class the
first-shot landings want.
"""
import struct
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CC = REPO / "tools" / "cc.sh"
BIN = REPO / "baselines" / "mainmenu_jp.bin"
WORK = Path("/home/z/my-project/build/prove_sdk_siblings")
WORK.mkdir(parents=True, exist_ok=True)

SITES = [
    ("SetRotMatrix", 0x3EFE8, 12),
    ("SetLightMatrix", 0x3F018, 12),
    ("ApplyMatrixLV", 0x3EDF4, 20),
]

TOOLROOT = "/home/z/my-project/tools-local"
OBJDUMP = f"{TOOLROOT}/mipsel-root/usr/bin/mipsel-linux-gnu-objdump"


def o_text_words(o_path):
    """The .o's .text as a list of 32-bit LE words, parsed from the ELF."""
    d = open(o_path, "rb").read()
    assert d[:4] == b"\x7fELF", o_path
    (e_type, e_machine, e_version, e_entry, e_phoff, e_shoff, e_flags,
     e_ehsize, e_phentsize, e_phnum, e_shentsize, e_shnum, e_shstrndx) = \
        struct.unpack_from("<HHIIIIIHHHHHH", d, 16)
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


def oracle_words(off, n):
    with open(BIN, "rb") as f:
        f.seek(off)
        return list(struct.unpack(f"<{n}I", f.read(4 * n)))


failures = 0
for name, off, n in SITES:
    src = REPO / "src" / f"{name}.c"
    out = WORK / f"{name}.o"
    try:
        subprocess.run(["sh", str(CC), "-o", str(out), str(src)],
                       check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"{name}: COMPILE FAILED\n{e.stderr[-800:]}")
        failures += 1
        continue
    got = o_text_words(out)
    expected = oracle_words(off, n)
    if len(got) < n:
        print(f"{name}: .text too short ({len(got)} words < {n})")
        failures += 1
        continue
    # compare the LAST n words too (gcc could in principle pad or lead)
    diffs = [(i, expected[i], got[i]) for i in range(n) if expected[i] != got[i]]
    extra = got[n:]
    verdict = "WORD-IDENTICAL" if not diffs and not extra else \
        f"{len(diffs)} DIFF, {len(extra)} EXTRA"
    print(f"{name}: {verdict} (compiled {len(got)} words vs oracle {n})")
    for i, e, g in diffs:
        print(f"   [{i:2d}] oracle {e:08x} vs got {g:08x}")
    if extra:
        print(f"   extra words: {' '.join(f'{w:08x}' for w in extra)}")
    if diffs or extra:
        failures += 1

print()
if failures:
    print(f"FAIL: {failures} unit(s) differ")
    sys.exit(1)
print("PASS: all staged units word-identical to the oracle bodies")

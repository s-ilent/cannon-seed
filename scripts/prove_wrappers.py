#!/usr/bin/env python3
"""prove_wrappers.py - offline word-proof for the four staged palette-fade
wrapper landings (window cron-20261024-1502).

For each staged src unit: compile with the pinned toolchain (tools/cc.sh),
read the .o's .text words, and compare word-for-word against the census
candidate body's words (read from the committed walk-row .s comment words).
The jal word is masked on BOTH sides: the callee is a per-target extern
(the near-twin law's one per-target reloc slot).

Verdict per unit: word-identical (the dw=0 class the first-shot landings
want) or the exact per-word delta list.
"""
import re
import struct
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CC = REPO / "tools" / "cc.sh"
WORK = Path("/home/z/my-project/build/prove_wrappers")
WORK.mkdir(parents=True, exist_ok=True)

# candidate bodies: (src name, target, [words]; None = jal reloc slot).
# Words are written as the walk-row .s comment hex (raw file BYTES) and
# converted to little-endian 32-bit words below - the comments print the
# byte sequence, not the numeric word.
def _w(hexstr):
    return int.from_bytes(bytes.fromhex(hexstr), "little")

BODIES = [
    ("func_8005AE34", "mainmenu_eu", [
        "E8FFBD27", "1000BFAF", "00240400", "83230400", "00018424",
        "00240400", "03240400", "002C0500", "032C0500", None,
        "14000634", "1000BF8F", "00000000", "0800E003", "1800BD27"]),
    ("func_8005AE70", "mainmenu_eu", [
        "E8FFBD27", "1000BFAF", "00240400", "03240400", "002C0500",
        "032C0500", None, "17000634", "1000BF8F", "00000000",
        "0800E003", "1800BD27"]),
    ("func_8005AC68", "mainmenu_eu", [
        "E8FFBD27", "1000BFAF", "00240400", "03240400", "002C0500",
        "032C0500", None, "4B000634", "1000BF8F", "00000000",
        "0800E003", "1800BD27"]),
    ("func_80043E94", "g3org_jp", [
        "E8FFBD27", "1000BFAF", "00240400", "03240400", "002C0500",
        "032C0500", None, "4B000634", "1000BF8F", "00000000",
        "0800E003", "1800BD27"]),
]
BODIES = [(n, t, [_w(x) if x else None for x in ws]) for n, t, ws in BODIES]

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
    # e_shstrndx section's bytes name the sections
    _, _, _, so, ss = secs[e_shstrndx]
    names = d[so:so + ss]
    for sh_name, sh_type, sh_flags, sh_offset, sh_size in secs:
        end = names.find(b"\0", sh_name)
        if names[sh_name:end] == b".text":
            buf = d[sh_offset:sh_offset + sh_size]
            return [int.from_bytes(buf[i:i + 4], "little")
                    for i in range(0, len(buf) - 3, 4)]
    raise AssertionError(f"no .text in {o_path}")


def compile_unit(name):
    src = REPO / "src" / f"{name}.c"
    out = WORK / f"{name}.o"
    subprocess.run(["sh", str(CC), "-o", str(out), str(src)],
                   check=True, capture_output=True, text=True)
    return out


failures = 0
for name, target, expected in BODIES:
    try:
        o = compile_unit(name)
    except subprocess.CalledProcessError as e:
        print(f"{name}: COMPILE FAILED\n{e.stderr[-800:]}")
        failures += 1
        continue
    got = o_text_words(o)
    n = len(expected)
    head = got[:n]
    if len(got) < n:
        print(f"{name}: .text too short ({len(got)} words < {n})")
        failures += 1
        continue
    diffs = []
    for i, (e, g) in enumerate(zip(expected, head)):
        if e is None or e == g:
            continue
        diffs.append((i, e, g))
    tag = "WORD-IDENTICAL (jal masked)" if not diffs else \
        f"{len(diffs)} DIFF WORD(S)"
    print(f"{name} [{target}] n={n}: {tag}")
    for i, e, g in diffs:
        print(f"    word {i}: candidate {e:08X} != compiled {g:08X}")
    if diffs:
        failures += 1
    # the masked jal word for the record
    j = expected.index(None)
    print(f"    jal slot {j}: compiled {head[j]:08X} (reloc, masked)")
    tail = got[n:]
    if any(t != 0 for t in tail):
        print(f"    note: {len(tail)} trailing word(s) beyond the body, "
              f"first {tail[0]:08X}" if tail else "")

print("PROOF:", "PASS" if failures == 0 else f"{failures} FAILURE(S)")
sys.exit(1 if failures else 0)

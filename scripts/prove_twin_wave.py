#!/usr/bin/env python3
"""prove_twin_wave.py - offline word-proof for the census six-twin wave
(window cron-20261024-1812): the func_8005AE34-shape palette-fade
wrapper, one C body across the game modules.

Two layers:

1. ORACLE SIDE: read each target's twin body (0x3C bytes) from
   baselines/<t>.bin at the census twin VA and compare word-for-word
   against the landed reference body (baselines/mainmenu_eu.bin at
   0x8005AE34). The jal slot (word 9) is masked on both sides - the
   near-twin law's one per-target reloc. Covers ALL six twins including
   the already-landed g3_eu copy (inside func_8004C4CC) and the parked
   mainmenu_jp copy (callee uncarved, see src/func_80046BC4.c).

2. COMPILER SIDE: compile each new src unit with the pinned toolchain
   (tools/cc.sh), read the .o's .text words, and compare against that
   target's oracle body words, jal masked on both sides. Verdict per
   unit: word-identical (the dw=0 class the first-shot landings want).
"""
import struct
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CC = REPO / "tools" / "cc.sh"
WORK = Path("/home/z/my-project/build/prove_twin_wave")
WORK.mkdir(parents=True, exist_ok=True)

HDR = 0x800
BASE_VA = 0x80020000
SIZE = 0x3C
JAL_WORD = 9  # the near-twin law's one per-target reloc slot

# census twin VAs (build/invariant_census.txt, fresh oracle 2026-10-24)
TWINS = [
    # (target, twin VA, src unit or None-when-already-landed/parked)
    ("mainmenu_eu", 0x8005AE34, "src/func_8005AE34.c (landed, reference)"),
    ("g3_eu", 0x8004682C, None),  # landed: func_8004C4CC's own first member
    ("g3_jp", 0x80046BC4, "src/func_80046BC4.c"),
    ("g3org_eu", 0x80043C80, "src/func_80043C80.c"),
    ("g3org_jp", 0x80044060, "src/func_80044060.c"),
    ("mainmenu_jp", 0x8005B204, None),  # parked: callee uncarved (data row)
]


def body_words(target, va):
    buf = open(REPO / "baselines" / f"{target}.bin", "rb").read()
    off = va - BASE_VA + HDR
    b = buf[off:off + SIZE]
    assert len(b) == SIZE, (target, hex(va), len(b))
    return list(struct.unpack("<15I", b))


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


failures = 0

# --- layer 1: oracle-side identity across all six twins ----------------
ref = body_words("mainmenu_eu", 0x8005AE34)
print(f"reference: mainmenu_eu 0x8005AE34 (src/func_8005AE34.c)")
for target, va, unit in TWINS:
    if target == "mainmenu_eu":
        continue
    w = body_words(target, va)
    diffs = [(i, ref[i], w[i]) for i in range(15)
             if i != JAL_WORD and ref[i] != w[i]]
    tag = "WORD-IDENTICAL (jal masked)" if not diffs else \
        f"{len(diffs)} UNEXPECTED DIFF WORD(S)"
    print(f"  {target:12s} {va:08X} [{unit or 'landed'}]: {tag}")
    for i, e, g in diffs:
        print(f"      word {i}: ref {e:08X} != twin {g:08X}")
    if diffs:
        failures += 1
    else:
        print(f"      jal slot {JAL_WORD}: {w[JAL_WORD]:08X} "
              f"(per-target reloc)")

# --- layer 2: compiler-side proof for the new src units ----------------
for target, va, unit in TWINS:
    if not unit or "landed" in unit:
        continue
    name = Path(unit).stem
    src = REPO / unit
    out = WORK / f"{name}.o"
    try:
        subprocess.run(["sh", str(CC), "-o", str(out), str(src)],
                       check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"{name}: COMPILE FAILED\n{e.stderr[-800:]}")
        failures += 1
        continue
    got = o_text_words(out)
    want = body_words(target, va)
    if len(got) < 15:
        print(f"{name}: .text too short ({len(got)} words < 15)")
        failures += 1
        continue
    diffs = [(i, want[i], got[i]) for i in range(15)
             if i != JAL_WORD and want[i] != got[i]]
    tag = "WORD-IDENTICAL (jal masked)" if not diffs else \
        f"{len(diffs)} DIFF WORD(S)"
    print(f"{name} [{target}] n=15: {tag}")
    for i, e, g in diffs:
        print(f"    word {i}: oracle {e:08X} != compiled {g:08X}")
    if diffs:
        failures += 1
    else:
        print(f"    jal slot {JAL_WORD}: compiled {got[JAL_WORD]:08X} "
              f"(reloc, masked)")

print("PROOF:", "PASS" if failures == 0 else f"{failures} FAILURE(S)")
sys.exit(1 if failures else 0)

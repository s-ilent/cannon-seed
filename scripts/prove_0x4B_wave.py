#!/usr/bin/env python3
"""prove_0x4B_wave.py - offline word-proof for the 0x4B pair family wave
(window cron-20261025-0321): the palette-fade wrapper pair, the landed
mainmenu_eu func_8005AC68 (0x4B) / func_8005AE70 (0x17) shapes, landing
across g3_eu / g3_jp / g3org_eu / g3org_jp.

Two layers (prove_twin_wave.py's pattern, 12-word bodies, jal word 6
masked - the near-twin law's one per-target reloc):

1. ORACLE SIDE: each site's 0x30 bytes from baselines/<t>.bin vs the
   landed reference bodies. The const slot (word 7) must equal the
   shape's constant; every other non-jal word identical.

2. COMPILER SIDE: compile each new src unit with the pinned toolchain
   (tools/cc.sh) and compare the .o's .text against that target's oracle
   body words, jal masked on both sides. Verdict per unit: word-identical
   (the dw=0 class the first-shot landings want).
"""
import struct
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CC = REPO / "tools" / "cc.sh"
WORK = Path("/home/z/my-project/build/prove_0x4B_wave")
WORK.mkdir(parents=True, exist_ok=True)

HDR = 0x800
BASE_VA = 0x80020000
SIZE = 0x30
NWORDS = 12
JAL_WORD = 6  # the near-twin law's one per-target reloc slot

# (target, site VA, src unit, const) - mainmenu_jp parks (callee uncarved)
SITES = [
    ("g3_eu", 0x80046660, "src/func_80046660.c", 0x4B),
    ("g3_jp", 0x800469F8, "src/func_800469F8.c", 0x4B),
    ("g3org_eu", 0x80043AB4, "src/func_80043AB4.c", 0x4B),
    ("g3_jp", 0x80046C00, "src/func_80046C00.c", 0x17),
    ("g3org_eu", 0x80043CBC, "src/func_80043CBC.c", 0x17),
    ("g3org_jp", 0x8004409C, "src/func_8004409C.c", 0x17),
]

REFS = {0x4B: ("mainmenu_eu", 0x8005AC68), 0x17: ("mainmenu_eu", 0x8005AE70)}


def body_words(target, va):
    buf = open(REPO / "baselines" / f"{target}.bin", "rb").read()
    off = va - BASE_VA + HDR
    b = buf[off:off + SIZE]
    assert len(b) == SIZE, (target, hex(va), len(b))
    return list(struct.unpack(f"<{NWORDS}I", b))


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

# --- layer 1: oracle-side identity per site ---------------------------
refs = {c: body_words(t, va) for c, (t, va) in REFS.items()}
print("reference bodies: mainmenu_eu 0x8005AC68 (0x4B) / 0x8005AE70 (0x17)")
for target, va, unit, const in SITES:
    w = body_words(target, va)
    ref = refs[const]
    diffs = [(i, ref[i], w[i]) for i in range(NWORDS)
             if i != JAL_WORD and ref[i] != w[i]]
    tag = "WORD-IDENTICAL (jal masked)" if not diffs else \
        f"{len(diffs)} UNEXPECTED DIFF WORD(S)"
    print(f"  {target:12s} {va:08X} const {const:#x} [{Path(unit).stem}]: {tag}")
    for i, e, g in diffs:
        print(f"      word {i}: ref {e:08X} != site {g:08X}")
    if diffs:
        failures += 1
    else:
        print(f"      jal slot {JAL_WORD}: {w[JAL_WORD]:08X} "
              f"(per-target reloc); const slot 7: {w[7]:08X}")

# --- layer 2: compiler-side proof for the new src units ----------------
for target, va, unit, const in SITES:
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
    if len(got) < NWORDS:
        print(f"{name}: .text too short ({len(got)} words < {NWORDS})")
        failures += 1
        continue
    diffs = [(i, want[i], got[i]) for i in range(NWORDS)
             if i != JAL_WORD and want[i] != got[i]]
    tag = "WORD-IDENTICAL (jal masked)" if not diffs else \
        f"{len(diffs)} DIFF WORD(S)"
    print(f"{name} [{target}] n={NWORDS}: {tag}")
    for i, e, g in diffs:
        print(f"    word {i}: oracle {e:08X} != compiled {g:08X}")
    if diffs:
        failures += 1
    else:
        print(f"    jal slot {JAL_WORD}: compiled {got[JAL_WORD]:08X} "
              f"(reloc, masked)")

print("PROOF:", "PASS" if failures == 0 else f"{failures} FAILURE(S)")
sys.exit(1 if failures else 0)

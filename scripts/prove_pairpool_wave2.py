#!/usr/bin/env python3
"""prove_pairpool_wave2.py - offline word-proof for the pair-pool's second
harvest wave (window cron-202610260534): _SsUtBuildADSR x8 + SetDQB x4 +
Square0/Square12 x4.

Compile each src/<name>.c with the pinned toolchain (tools/cc.sh), read
the .o's .text words, and compare word-for-word against the oracle body
read straight from each target's baseline at the anchor sites (all of
them the row-family-normalized pair-report exact-unmatched pool,
byte-identical across each region pair at 100.00% while both sides were
still asm):

  _SsUtBuildADSR (0x8c, all four pairs):
    slps_00270   0x283CC   sces_00269  0x284C8
    mainmenu_jp  0x6443C   mainmenu_eu 0x6509C
    g3_jp        0x4EE20   g3_eu       0x4FAB8
    g3org_jp     0x4C2BC   g3org_eu    0x4CF0C
  SetDQB (0xc function, 0x18 row - tail zero words are row padding):
    slps_00270   0x137A0   sces_00269  0x13268
    g3_jp        0x2F2E8   g3_eu       0x2EC24
  Square0 / Square12 (0x28, g3 pair):
    g3_jp  0x322AC / 0x32284     g3_eu  0x31BE8 / 0x31BC0

No reloc slots: every body is a frameless leaf whose every word is
position-independent (no jal, no lui/%lo). gas pads the default .text
section to 16 bytes on MIPS (cc.sh's own note); trailing all-zero words
are the known artifact and carry no instruction bytes.
"""
import struct
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CC = REPO / "tools" / "cc.sh"
WORK = Path("/home/z/my-project/build/prove_pairpool_wave2")
WORK.mkdir(parents=True, exist_ok=True)

WAVES = [
    ("_SsUtBuildADSR", 35, [
        ("slps_00270", 0x283CC),
        ("sces_00269", 0x284C8),
        ("mainmenu_jp", 0x6443C),
        ("mainmenu_eu", 0x6509C),
        ("g3_jp", 0x4EE20),
        ("g3_eu", 0x4FAB8),
        ("g3org_jp", 0x4C2BC),
        ("g3org_eu", 0x4CF0C),
    ]),
    ("SetDQB", 3, [
        ("slps_00270", 0x137A0),
        ("sces_00269", 0x13268),
        ("g3_jp", 0x2F2E8),
        ("g3_eu", 0x2EC24),
    ]),
    ("Square0", 10, [
        ("g3_jp", 0x322AC),
        ("g3_eu", 0x31BE8),
    ]),
    ("Square12", 10, [
        ("g3_jp", 0x32284),
        ("g3_eu", 0x31BC0),
    ]),
]


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


def main():
    total_fail = 0
    for name, n_words, sites in WAVES:
        src = REPO / "src" / f"{name}.c"
        out = WORK / f"{name}.o"
        try:
            subprocess.run(["sh", str(CC), "-o", str(out), str(src)],
                           check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            print(f"{name}: COMPILE FAILED\n{e.stderr[-800:]}")
            total_fail += 1
            continue

        got = o_text_words(out)
        print(f"== {name}: compiled .text {len(got)} words, oracle {n_words} ==")
        fail = 0
        for target, off in sites:
            data = open(REPO / "baselines" / f"{target}.bin", "rb").read()
            expected = list(struct.unpack_from(f"<{n_words}I", data, off))
            diffs = [(i, expected[i], got[i]) for i in range(min(len(got), n_words))
                     if expected[i] != got[i]]
            extra = got[n_words:]
            pad = all(w == 0 for w in extra)
            verdict = "WORD-IDENTICAL" if not diffs and pad else \
                f"{len(diffs)} DIFF, {len(extra)} EXTRA({'zeroes' if pad else 'NONZERO'})"
            print(f"  {target:12} @{off:06x}: {verdict}")
            for i, e, g in diffs:
                print(f"     [{i:2d}] oracle {e:08x} vs got {g:08x}")
            if extra and not pad:
                print(f"     extra: {' '.join(f'{w:08x}' for w in extra)}")
            if diffs or not pad:
                fail += 1
        total_fail += fail

    print()
    if total_fail:
        print(f"FAIL: {total_fail} site(s) differ")
        sys.exit(1)
    print("PASS: pair-pool wave 2 word-identical at all 14 sites")


if __name__ == "__main__":
    main()

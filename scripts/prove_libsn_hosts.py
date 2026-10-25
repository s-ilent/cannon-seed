#!/usr/bin/env python3
"""prove_libsn_hosts.py - offline word-proof for the LIBSN host-call
landing (window cron-202610252019): PCopen x4, PClseek x2, _SN_write x4.

Compile src/PCopen.c, src/PClseek.c and src/_SN_write.c with the pinned
toolchain (tools/cc.sh), read each .o's .text words, and compare
word-for-word against the oracle body read straight from each target's
baseline at the anchor sites (the "LIBSN unique" rows in
config/sdk_anchors.txt; every site is one of this window's pair-report
exact-unmatched pool, byte-identical across its region pair at 100.00%
while both sides are still asm):

  PCopen     g3_jp 0x2969C  g3_eu 0x290B4  g3org_jp 0x26B38  g3org_eu 0x26508
  PClseek    g3_jp 0x296BC  g3_eu 0x290D4
  _SN_write  g3_jp 0x297B0  g3_eu 0x291C8  g3org_jp 0x26C4C  g3org_eu 0x2661C

No reloc slots: frameless leaves whose every word is
position-independent (no jal, no lui/%lo). The C's asm block carries
the retail words through the error tail 1:1 (the shared-label form);
GCC's frameless epilogue emits the jr $ra + nop. A full word-identical
verdict at all ten sites is the dw=0 class the first-shot landing
wants.
"""
import struct
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CC = REPO / "tools" / "cc.sh"
WORK = Path("/home/z/my-project/build/prove_libsn_hosts")
WORK.mkdir(parents=True, exist_ok=True)

WAVES = [
    ("PCopen", 8, [
        ("g3_jp", 0x2969C),
        ("g3_eu", 0x290B4),
        ("g3org_jp", 0x26B38),
        ("g3org_eu", 0x26508),
    ]),
    ("PClseek", 9, [
        ("g3_jp", 0x296BC),
        ("g3_eu", 0x290D4),
    ]),
    ("_SN_write", 6, [
        ("g3_jp", 0x297B0),
        ("g3_eu", 0x291C8),
        ("g3org_jp", 0x26C4C),
        ("g3org_eu", 0x2661C),
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
    failures = 0
    for name, n, sites in WAVES:
        out = WORK / f"{name}.o"
        try:
            subprocess.run(["sh", str(CC), "-o", str(out),
                            str(REPO / "src" / f"{name}.c")],
                           check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            print(f"{name}: COMPILE FAILED\n{e.stderr[-800:]}")
            failures += 1
            continue
        got = o_text_words(out)
        print(f"{name}: compiled .text {len(got)} words (want {n})")
        if len(got) < n or any(w != 0 for w in got[n:]):
            print(f"  extra words: {' '.join(f'{w:08x}' for w in got[n:])}")
            failures += 1
        for target, off in sites:
            data = open(REPO / "baselines" / f"{target}.bin", "rb").read()
            expected = list(struct.unpack_from(f"<{n}I", data, off))
            diffs = [(i, expected[i], got[i])
                     for i in range(min(len(got), n)) if expected[i] != got[i]]
            verdict = "WORD-IDENTICAL" if not diffs and len(got) >= n else \
                f"{len(diffs)} DIFF"
            print(f"  {target:10} @{off:06x}: {verdict}")
            for i, e, g in diffs:
                print(f"     [{i:2d}] oracle {e:08x} vs got {g:08x}")
            if diffs:
                failures += 1

    print()
    if failures:
        print(f"FAIL: {failures} problem(s)")
        sys.exit(1)
    print("PASS: PCopen x4 / PClseek x2 / _SN_write x4 word-identical "
          "at all 10 sites")


if __name__ == "__main__":
    main()

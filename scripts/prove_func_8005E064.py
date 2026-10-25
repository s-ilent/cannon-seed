#!/usr/bin/env python3
"""prove_func_8005E064.py - the staged ROW1-final 0x30 whole function's
word proof (window cron-202610252206, offline) + the oracle-day x8 site
search it hands the disc-return window.

Two modes:

  (default) OFFLINE PROOF, zero oracle: compile src/func_8005E064.c with
  the pinned toolchain (tools/cc.sh) and compare the .o's .text words
  word-for-word against the function's twelve words extracted LIVE from
  the committed mainmenu_jp graveyard head row (asm/mainmenu_jp/
  nonmatchings/data/data_80066CF4.data.s, VA 0x8005E064..0x8005E094) -
  the same committed-row class the wrapper quartet proved under
  (scripts/prove_wrappers.py). Every word of this body is position-
  independent (lw/mtc2/nop/mvmva/swc2/addu/jr/nop: no jal, no lui/%lo),
  so a word-identical verdict is the dw=0 class the first-shot landing
  wants.

  --sites   THE ORACLE'S FIRST DECODING JOB, witness-gated: the x8 twin
  word-search the 2051 record queued. Refuses to run unless witness is
  8/8 STRICT (the same sha1 gate judge_unit/pair_report carry - the
  woven-set rollback class slices garbage into every byte comparison).
  On the fresh baselines it searches each target's .bin for the 12-word
  pattern, asserts EXACTLY ONE occurrence per target, and prints the
  site table (file offset, VA = raw + 0x8001F800, the banked classifier
  law) the E064 landing cuts need. Expectation per the graveyard-x8-
  family law: byte-identical twins in ALL EIGHT executables; in the
  seven non-mainmenu_jp targets the twin sits INSIDE one of the five
  walk mega-rows (0x30 is not one of the five row sizes), mid-row.
"""
import struct
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CC = REPO / "tools" / "cc.sh"
WORK = Path("/home/z/my-project/build/prove_func_8005E064")
WORK.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(REPO / "scripts"))
import probe_graveyard_walk as P  # the committed-row parser (ROW1)

TARGETS = [
    "slps_00270", "sces_00269", "mainmenu_jp", "mainmenu_eu",
    "g3_jp", "g3_eu", "g3org_jp", "g3org_eu",
]

VA0, VA1 = 0x8005E064, 0x8005E094
N = (VA1 - VA0) // 4  # 12 words / 0x30
DELTA = 0x8001F800    # VA = raw_off + DELTA (banked classifier law)


def row_words():
    """The 12 words at VA0..VA1 from the committed row, + a shape guard."""
    wm = {}
    for fn in P.parse(P.ROW1):
        for va, w in fn["words"]:
            wm[va] = w
    if any(va not in wm for va in range(VA0, VA1, 4)):
        raise AssertionError("E064 range not fully covered by the committed row")
    words = [wm[va] for va in range(VA0, VA1, 4)]
    # transcription guard: the banked instruction sketch must hold
    sketch = [
        (0x23, "lw $8,0($4)"), (0x23, "lw $9,4($4)"),
        (0x12, "mtc2 $8->r0"), (0x12, "mtc2 $9->r1"),
        (0, "nop"), (0x12, "mvmva 0x4A486012"),
        (0x3A, "swc2 r9"), (0x3A, "swc2 r10"), (0x3A, "swc2 r11"),
        (0, "addu v0,a2"), (0, "jr ra"), (0, "nop"),
    ]
    # jr is SPECIAL (op 0, funct 8); pin the full retail spellings
    assert words[10] == 0x03E00008, "jr $ra spelling drifted"
    for i, (op, name) in enumerate(sketch):
        w = words[i]
        got = w >> 26
        assert got == op or (op == 0 and w == 0), \
            f"word {i} ({name}): op 0x{got:02x} != 0x{op:02x} (w={w:08x})"
    assert words[5] == 0x4A486012, "mvmva control word drifted"
    assert words[0] == 0x8C880000 and words[1] == 0x8C890004, "staging drifted"
    assert words[9] == 0x00C01021, "return tail drifted"
    return words


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


def compile_unit():
    src = REPO / "src" / "func_8005E064.c"
    out = WORK / "func_8005E064.o"
    try:
        subprocess.run(["sh", str(CC), "-o", str(out), str(src)],
                       check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"COMPILE FAILED\n{e.stderr[-800:]}")
        sys.exit(1)
    return o_text_words(out)


def offline_proof(got, want):
    print(f"compiled .text: {len(got)} words; committed row body: {N} words")
    diffs = [(i, want[i], got[i]) for i in range(N) if got[i] != want[i]]
    extra = got[N:]
    # gas pads the default .text section to 16 bytes on MIPS; trailing
    # all-zero words are the known artifact and carry no instructions.
    pad = all(w == 0 for w in extra)
    if not diffs and pad:
        for i in range(N):
            print(f"  [{i:2d}] {want[i]:08x}  WORD-IDENTICAL")
        print("OFFLINE PROOF PASS (committed-row class, zero oracle)")
        return 0
    print(f"OFFLINE PROOF FAIL: {len(diffs)} diff, {len(extra)} extra "
          f"({'zeroes' if pad else 'NONZERO'})")
    for i, e, g in diffs:
        print(f"   [{i:2d}] row {e:08x} vs got {g:08x}")
    if extra and not pad:
        print(f"   extra: {' '.join(f'{w:08x}' for w in extra)}")
    return 1


def baseline_witness(target):
    """(ok, why) - mirrors judge_unit/pair_report's sha1 gate exactly."""
    path = REPO / "baselines" / f"{target}.bin"
    if not path.exists():
        return False, f"baselines/{target}.bin missing"
    expected = None
    with open(REPO / "config" / "sha1" / f"{target}.sha1") as f:
        for ln in f:
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                expected = ln.split()[0].lower()
                break
    if expected is None:
        return False, f"config/sha1/{target}.sha1 has no hash field"
    import hashlib
    actual = hashlib.sha1(path.read_bytes()).hexdigest()
    if expected != actual:
        return False, (f"sha1 {actual[:12]} != committed oracle "
                       f"{expected[:12]} (the woven-set class; witness 0/8)")
    return True, ""


def site_search(want):
    """The x8 word-search - runs ONLY on the witness-8/8 fresh baselines."""
    bad = []
    for t in TARGETS:
        ok, why = baseline_witness(t)
        if not ok:
            print(f"  GATE REFUSED {t}: {why}")
            bad.append(t)
    if bad:
        print(f"\nSITE SEARCH REFUSED ({len(bad)}/8 unwitnessed) - the x8 "
              f"twin word-search is the oracle's first decoding job; it runs "
              f"on the disc-return, after witness 8/8 STRICT. Never compare "
              f"against the woven set.")
        return 1
    import hashlib  # noqa: F401  (already imported in the gate)
    failures = 0
    pattern = b"".join(w.to_bytes(4, "little") for w in want)
    for t in TARGETS:
        data = (REPO / "baselines" / f"{t}.bin").read_bytes()
        sites = []
        start = 0
        while True:
            i = data.find(pattern, start)
            if i < 0:
                break
            sites.append(i)
            start = i + 1
        if len(sites) != 1:
            print(f"{t:12}: {len(sites)} SITE(S) {[hex(s) for s in sites]} "
                  f"- the x8 law expects exactly one")
            failures += 1
            continue
        off = sites[0]
        print(f"{t:12} file 0x{off:06x}  VA 0x{off + DELTA:08x}  SITE")
    print("SITE SEARCH PASS" if failures == 0 else
          f"SITE SEARCH FAIL ({failures})")
    return 0 if failures == 0 else 1


def main():
    want = row_words()
    got = compile_unit()
    if len(sys.argv) > 1 and sys.argv[1] == "--sites":
        rc = site_search(want)
    else:
        rc = offline_proof(got, want)
    sys.exit(rc)


if __name__ == "__main__":
    main()

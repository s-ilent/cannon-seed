#!/usr/bin/env python3
"""prove_e3dc_pair.py - the graveyard pair's word proof (window
cron-202610252321, offline) + the oracle-day x8 site search it hands the
disc-return window.

The pair: func_8005E3DC (0x8005E3DC..0x8005E4E8) and func_8005E4E8
(0x8005E4E8..0x8005E5F4), the two whole 0x10c functions the boundary
probe resolved the walk's "double-rotate mega-host" into - byte-identical
streams except six words (commit base (a0) vs (a1), return a0 vs a1).

Two modes:

  (default) OFFLINE PROOF, zero oracle: compile src/func_8005E3DC.c and
  src/func_8005E4E8.c with the pinned toolchain (tools/cc.sh) and compare
  each .o's .text words word-for-word against the body's 67 words
  extracted LIVE from the committed mainmenu_jp graveyard tail row
  (asm/mainmenu_jp/nonmatchings/data/data_8005E1B8.data.s) - the
  committed-row class (scripts/prove_wrappers.py precedent). Every word
  is position-independent (the lone lui is the 0xffff mask constant), so
  a word-identical verdict is the dw=0 class the first-shot landings
  want.

  --sites   THE ORACLE'S FIRST DECODING JOB, witness-gated: the x8 twin
  word-search the 2051/2206 records queued for the pair. Refuses to run
  unless witness is 8/8 STRICT (the sha1 gate judge_unit/pair_report
  carry). On the fresh baselines it searches each target's .bin for both
  67-word patterns and prints the site table (file offset, VA = raw +
  0x8001F800, the banked classifier law). For the pair the per-target
  expectation is subtle: 0x10c IS one of the five walk mega-row sizes,
  so a target's twin may sit as a WHOLE row (head) or INSIDE a bigger
  row (interior) - the search reports raw occurrences; the landing cut
  design reads the covering row off the target's yaml.
"""
import struct
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CC = REPO / "tools" / "cc.sh"
WORK = Path("/home/z/my-project/build/prove_e3dc_pair")
WORK.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(REPO / "scripts"))
import probe_graveyard_walk as P  # the committed-row parser (ROW2)

TARGETS = [
    "slps_00270", "sces_00269", "mainmenu_jp", "mainmenu_eu",
    "g3_jp", "g3_eu", "g3org_jp", "g3org_eu",
]

UNITS = [
    ("func_8005E3DC", 0x8005E3DC, 0x8005E4E8),
    ("func_8005E4E8", 0x8005E4E8, 0x8005E5F4),
]
DELTA = 0x8001F800  # VA = raw_off + DELTA (banked classifier law)

# the shared body sketch both units must match (67 words); the six-word
# A/B delta (commit base + return) is pinned separately per unit.
HEAD_SKETCH = [
    (0x23,)] * 5 + [  # lw $8..$12, 0..0x10($4)
    (0x12, 6), (0x12, 6), (0x12, 6), (0x12, 6), (0x12, 6),  # ctc2 x5
]


def row_words(lo, hi):
    """The words at VA lo..hi from the committed row + shape guards."""
    wm = {}
    for fn in P.parse(P.ROW2):
        for va, w in fn["words"]:
            wm[va] = w
    if any(va not in wm for va in range(lo, hi, 4)):
        raise AssertionError(f"range 0x{lo:08x}..0x{hi:08x} not fully covered")
    words = [wm[va] for va in range(lo, hi, 4)]
    assert len(words) == 0x10C // 4, f"expected 67 words, got {len(words)}"
    # head: 5 lw from ($4) + 5 ctc2 into c0..c4
    for i in range(5):
        w = words[i]
        assert w >> 26 == 0x23 and (w >> 21) & 0x1F == 4, f"head lw {i}: {w:08x}"
        assert (w >> 16) & 0x1F == 8 + i and (w & 0xFFFF) == 4 * i, \
            f"head lw {i} spelling: {w:08x}"
    for i in range(5):
        w = words[5 + i]
        assert w >> 26 == 0x12 and (w >> 21) & 0x1F == 6, f"head ctc2 {i}: {w:08x}"
        assert (w >> 16) & 0x1F == 8 + i and (w >> 11) & 0x1F == i, \
            f"head ctc2 {i} spelling: {w:08x}"
    # the three mvmva control words sit at their banked offsets
    for idx in (19, 31, 44):
        assert words[idx] == 0x4A486012, f"mvmva at {idx}: {words[idx]:08x}"
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


def compile_unit(name):
    src = REPO / "src" / f"{name}.c"
    out = WORK / f"{name}.o"
    try:
        subprocess.run(["sh", str(CC), "-o", str(out), str(src)],
                       check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"COMPILE FAILED {name}\n{e.stderr[-800:]}")
        sys.exit(1)
    return o_text_words(out)


def offline_proof():
    failures = 0
    for name, lo, hi in UNITS:
        want = row_words(lo, hi)
        got = compile_unit(name)
        print(f"{name}: compiled .text {len(got)} words; committed row body "
              f"{len(want)} words")
        diffs = [(i, want[i], got[i]) for i in range(len(want))
                 if i >= len(got) or got[i] != want[i]]
        extra = got[len(want):]
        # gas pads the default .text section to 16 bytes on MIPS; trailing
        # all-zero words are the known artifact and carry no instructions.
        pad = all(w == 0 for w in extra)
        if not diffs and pad:
            print(f"  {name}: {len(want)}/{len(want)} WORD-IDENTICAL")
        else:
            print(f"  {name}: FAIL {len(diffs)} diff, {len(extra)} extra "
                  f"({'zeroes' if pad else 'NONZERO'})")
            for i, e, g in diffs:
                print(f"   [{i:2d}] row {e:08x} vs got {g:08x}")
            if extra and not pad:
                print(f"   extra: {' '.join(f'{w:08x}' for w in extra)}")
            failures += 1
    if failures == 0:
        print("OFFLINE PROOF PASS (committed-row class, zero oracle)")
        return 0
    print(f"OFFLINE PROOF FAIL ({failures})")
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


def site_search():
    patterns = {}
    for name, lo, hi in UNITS:
        patterns[name] = b"".join(w.to_bytes(4, "little")
                                  for w in row_words(lo, hi))
    bad = []
    for t in TARGETS:
        ok, why = baseline_witness(t)
        if not ok:
            print(f"  GATE REFUSED {t}: {why}")
            bad.append(t)
    if bad:
        print(f"\nSITE SEARCH REFUSED ({len(bad)}/8 unwitnessed) - the x8 "
              f"twin word-search runs on the disc-return, after witness 8/8 "
              f"STRICT. Never compare against the woven set.")
        return 1
    failures = 0
    for t in TARGETS:
        data = (REPO / "baselines" / f"{t}.bin").read_bytes()
        line = [t]
        for name, pat in patterns.items():
            sites = []
            start = 0
            while True:
                i = data.find(pat, start)
                if i < 0:
                    break
                sites.append(i)
                start = i + 1
            if len(sites) != 1:
                line.append(f"{name}: {len(sites)} SITE(S) "
                            f"{[hex(s) for s in sites]}")
                failures += 1
            else:
                line.append(f"{name}: file 0x{sites[0]:06x} "
                            f"VA 0x{sites[0] + DELTA:08x}")
        print("  ".join(line))
    print("SITE SEARCH PASS" if failures == 0 else
          f"SITE SEARCH FAIL ({failures})")
    return 0 if failures == 0 else 1


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--sites":
        sys.exit(site_search())
    sys.exit(offline_proof())


if __name__ == "__main__":
    main()

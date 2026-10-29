#!/usr/bin/env python3
"""Pre-check the same-name maxdiff=0.000 sdk pairs (20th-return NEXT 3):
the MulMatrix (0x10C) / MulMatrix2 (0x10C) waves and the memmove (0x90)
wave - the psyq-decode class.

waveE8E4_check.py pattern with one offline adaptation: the disc-derived
baselines are woven-era in a rolled-back sandbox, so byte-identity is
proven from the COMMITTED LISTINGS' hex comment columns (byte-true because
verify 8/8 GREEN assembles them into the witnessed image, the same trust
model as gmd_offline_screen.py). The baseline bytes at the yaml offsets are
still cross-checked and reported, but a mismatch there is EXPECTED (stale
container) and is not a gate; the return-window rerun re-checks them
against the fresh per-sector baselines.

DISCOVERY BEYOND THE CENSUS (this window's finding): the census ranked
MulMatrix/MulMatrix2 as "0x10C x2 targets each" and memmove as "0x88 x3";
the committed listings prove THREE members for MulMatrix (mainmenu_eu
func_8005DDBC joins - the C8-wave lesson, third confirmation) and FOUR
byte-identical 0x90 members for memmove (all four curated pins are
own-row). The pre-check hard-codes the discovered member lists.

Checks (per the e3dc method):
1. listing existence for all member names,
2. byte-identity of each wave (listing hex words, per wave),
3. the rows' neighborhoods in each yaml (predecessor/successor rows for
   judge extent pinning),
4. name-collision scan (symbols files + config/symbols.curated.txt),
5. word-level scan of each wave's reference body: jals, lui, gp-relative
   candidates, GTE census (cop2 class + the mvmva raw word 0x4A486012).
"""
import re
import struct
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

WAVE_MM = [
    ("slps_00270", "func_80037BD8", 0x800349F8),
    ("mainmenu_eu", "func_8005DDBC", 0x8005DDBC),
    ("g3_eu", "func_8004FCA0", 0x800498E0),
]
WAVE_MM2 = [
    ("slps_00270", "func_80037CE4", 0x80034B04),
    ("g3_eu", "func_8004FDAC", 0x800499EC),
]
WAVE_MEMMOVE = [
    ("slps_00270", "func_80030D90", 0x8002E9F0),
    ("mainmenu_jp", "func_8006661C", 0x8005D40C),
    ("g3_jp", "func_8004EF2C", 0x80048DCC),
    ("g3org_jp", "func_8004BDD8", 0x80046268),
]
SIZE_10C = 0x10C
SIZE_90 = 0x90
HEXCOL = re.compile(r"/\*\s*[0-9A-Fa-f]+\s+[0-9A-Fa-f]+\s+([0-9A-Fa-f]{8})\s*\*/")


def listing_path(target: str, fn: str) -> Path:
    if target == "slps_00270":
        return REPO / "asm" / "nonmatchings" / f"{fn}.s"
    return REPO / "asm" / target / "nonmatchings" / f"{fn}.s"


def listing_words(target: str, fn: str, size: int) -> list[int]:
    """MIPS words as LITTLE-ENDIAN values (the spimdisasm hex column is the
    big-endian BYTE display; the actual instruction word is byte-reversed)."""
    text = listing_path(target, fn).read_text()
    words = []
    for ln in text.splitlines():
        m = HEXCOL.search(ln)
        if m:
            words.append(int.from_bytes(bytes.fromhex(m.group(1)), "little"))
    want = size // 4
    if len(words) != want:
        raise SystemExit(f"{target}/{fn}: listing has {len(words)} hex words, want {want}")
    return words


def yaml_row(target: str, fn: str) -> tuple[int, int, list[str]]:
    yml = (REPO / "config" / f"splat.{target}.yaml").read_text().splitlines()
    for i, l in enumerate(yml):
        if f", asm, {fn}]" in l:
            m = re.search(r"\[0x([0-9A-Fa-f]+), asm, ", l)
            return int(m.group(1), 16), i, yml
    raise SystemExit(f"{target}: no asm row for {fn}")


def wave_report(title: str, wave: list[tuple[str, str, int]], size: int) -> bool:
    print(f"\n{'=' * 72}\n{title}\n{'=' * 72}")
    ok = True
    blobs = {}
    offs = {}
    for t, fn, va in wave:
        p = listing_path(t, fn)
        if not p.exists():
            print(f"  {t}/{fn}: LISTING MISSING at {p}")
            ok = False
            continue
        words = listing_words(t, fn, size)
        blobs[t] = words
        off, idx, yml = yaml_row(t, fn)
        offs[t] = (off, idx, yml)
        tag = "sdk" if " sdk" in yml[idx] else "---"
        print(f"  {t:<13} {fn} @0x{off:X} (va 0x{va:X}) {tag}: {len(words)} words, "
              f"head {words[0]:08X} tail {words[-1]:08X}")
    ref = blobs.get(wave[0][0])
    ident = [t for t, _f, _v in wave if t in blobs and blobs[t] != ref]
    print(f"  BYTE-IDENTICAL x{len(wave)} (listing hex): {not ident}")
    for t in ident:
        diffs = [4 * i for i in range(len(ref)) if blobs[t][i] != ref[i]]
        print(f"    {t} differs at word offsets: {[hex(d) for d in diffs]}")
        ok = False
    # baseline cross-check (EXPECTED to fail on the woven-era stale container;
    # informational only this window)
    print("  BASELINE CROSS-CHECK (stale woven-era baselines; informational):")
    for t, fn, va in wave:
        off = offs[t][0]
        p = REPO / "baselines" / f"{t}.bin"
        if not p.exists():
            print(f"    {t}: no baseline file")
            continue
        data = p.read_bytes()[off : off + size]
        words = [struct.unpack("<I", data[i : i + 4])[0] for i in range(0, size, 4)]
        same = words == blobs[t]
        print(f"    {t} @0x{off:X}: {'MATCH' if same else 'differ (stale container - expected offline)'}")
    # neighborhoods
    print("  YAML NEIGHBORHOODS:")
    for t, fn, va in wave:
        off, idx, yml = offs[t]
        print(f"    == {t} L{idx + 1}")
        for k in (idx - 1, idx, idx + 1):
            if 0 <= k < len(yml):
                print(f"       {yml[k].strip()}")
    # name collisions
    print("  NAME-COLLISION SCAN:")
    cur = (REPO / "config" / "symbols.curated.txt").read_text()
    for t, fn, va in wave:
        sym = (REPO / "config" / f"symbols.{t}.txt").read_text()
        hits = [l for l in sym.splitlines() if fn in l]
        chits = [l for l in cur.splitlines() if fn in l]
        flag = "YES" if (hits or chits) else "no"
        print(f"    {t}: symbols={'YES' if hits else 'no'} curated={'YES' if chits else 'no'}")
        if chits:
            ok = False
    # word scan of the reference body
    ref = blobs[wave[0][0]]
    jals = [(4 * i, hex(w & 0x3FFFFFF)) for i, w in enumerate(ref) if (w >> 26) == 3]
    luis = [(4 * i, hex((w >> 16) & 0xFFFF)) for i, w in enumerate(ref) if (w >> 26) == 0xF]
    gp = sum(1 for w in ref if (w >> 26) in (0x23, 0x2B) and ((w >> 21) & 31) == 28)
    cop2 = sum(1 for w in ref if (w >> 26) in (0x12, 0x13, 0x32, 0x3A))
    mvmva = sum(1 for w in ref if w == 0x4A486012)
    print(
        f"  BODY WORD SCAN (ref): {len(ref)} words; jals={jals}; lui={luis}; "
        f"gp-rel={gp}; cop2-class={cop2} (mvmva raw 0x4A486012 x{mvmva})"
    )
    return ok


def main() -> int:
    ok1 = wave_report("x3 size=0x10C wave - MulMatrix (in-place m0*m1, returns m0)", WAVE_MM, SIZE_10C)
    ok2 = wave_report("x2 size=0x10C wave - MulMatrix2 (stores+returns m1)", WAVE_MM2, SIZE_10C)
    ok3 = wave_report("x4 size=0x90 wave - memmove (hand-asm LIBC member, 0x88 fn + 2 zero tail words)", WAVE_MEMMOVE, SIZE_90)
    print(f"\nPRE-CHECK VERDICT: MulMatrix={'OK' if ok1 else 'FAIL'} "
          f"MulMatrix2={'OK' if ok2 else 'FAIL'} memmove={'OK' if ok3 else 'FAIL'}")
    return 0 if (ok1 and ok2 and ok3) else 1


if __name__ == "__main__":
    sys.exit(main())

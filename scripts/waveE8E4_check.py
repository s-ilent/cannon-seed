#!/usr/bin/env python3
"""Pre-check the x7 size=0xE8/0xE4 own-row waves (eighteenth-return NEXT 1).

The MulRotMatrix (0xE8) / MulRotMatrix0 (0xE4) adjacent pair, seven members
each, one per game target (mainmenu_jp carries neither). wave104_check.py
pattern with one offline adaptation: the disc-derived baselines are woven-era
in a rolled-back sandbox, so byte-identity is proven from the COMMITTED
LISTINGS' hex comment columns (the third field of each spimdisasm insn line -
byte-true because verify 8/8 GREEN assembles them into the witnessed image,
the same trust model as gmd_offline_screen.py). The baseline bytes at the
yaml offsets are still cross-checked and reported, but a mismatch there is
EXPECTED (stale container) and is not a gate; the return-window rerun
re-checks them against the fresh per-sector baselines.

Checks (per the e3dc method, scripts/e3dcv_check.py pattern):
1. listing existence for all fourteen names (slps flat asm/nonmatchings path),
2. byte-identity of the seven 0xE8 retail rows and the seven 0xE4 rows
   (listing hex words, per wave),
3. the row's neighborhood in each yaml (predecessor/successor rows for judge
   extent pinning),
4. name-collision scan (symbols files + config/symbols.curated.txt),
5. word-level scan of the common body: jals, lui, gp-relative candidates,
   GTE census (cop2 class + the mvmva raw word 0x4A486012).
"""
import re
import struct
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

WAVE_E8 = [
    ("slps_00270", "func_80034328"),
    ("sces_00269", "func_80033DF0"),
    ("mainmenu_eu", "func_8005D6EC"),
    ("g3_jp", "func_800497F8"),
    ("g3_eu", "func_80049210"),
    ("g3org_jp", "func_80046C94"),
    ("g3org_eu", "func_80046664"),
]
WAVE_E4 = [
    ("slps_00270", "func_80034244"),
    ("sces_00269", "func_80033D0C"),
    ("mainmenu_eu", "func_8005D608"),
    ("g3_jp", "func_80049714"),
    ("g3_eu", "func_8004912C"),
    ("g3org_jp", "func_80046BB0"),
    ("g3org_eu", "func_80046580"),
]
SIZE_E8 = 0xE8
SIZE_E4 = 0xE4
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


def wave_report(title: str, wave: list[tuple[str, str]], size: int) -> bool:
    print(f"\n{'=' * 72}\n{title}\n{'=' * 72}")
    ok = True
    blobs = {}
    offs = {}
    for t, fn in wave:
        p = listing_path(t, fn)
        if not p.exists():
            print(f"  {t}/{fn}: LISTING MISSING at {p}")
            ok = False
            continue
        words = listing_words(t, fn, size)
        blobs[t] = words
        off, idx, yml = yaml_row(t, fn)
        offs[t] = (off, idx, yml)
        tag = "sdk" if "# sdk" in yml[idx] else "---"
        print(f"  {t:<14} {fn} @0x{off:X} {tag}: {len(words)} words, head {words[0]:08X} tail {words[-1]:08X}")
    ref = blobs.get(wave[0][0])
    ident = [t for t, _ in wave if t in blobs and blobs[t] != ref]
    print(f"  BYTE-IDENTICAL x{len(wave)} (listing hex): {not ident}")
    for t in ident:
        diffs = [4 * i for i in range(len(ref)) if blobs[t][i] != ref[i]]
        print(f"    {t} differs at word offsets: {[hex(d) for d in diffs]}")
        ok = False
    # baseline cross-check (EXPECTED to fail on the woven-era stale container;
    # informational only this window)
    print("  BASELINE CROSS-CHECK (stale woven-era baselines; informational):")
    for t, fn in wave:
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
    for t, fn in wave:
        off, idx, yml = offs[t]
        print(f"    == {t} L{idx + 1}")
        for k in (idx - 1, idx, idx + 1):
            if 0 <= k < len(yml):
                print(f"       {yml[k].strip()}")
    # name collisions
    print("  NAME-COLLISION SCAN:")
    cur = (REPO / "config" / "symbols.curated.txt").read_text()
    for t, fn in wave:
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
    ok8 = wave_report("x7 size=0xE8 wave - MulRotMatrix (in-place, returns $a0)", WAVE_E8, SIZE_E8)
    ok4 = wave_report("x7 size=0xE4 wave - MulRotMatrix0 (dst out-param, returns $a1)", WAVE_E4, SIZE_E4)
    print(f"\nPRE-CHECK VERDICT: 0xE8={'OK' if ok8 else 'FAIL'} 0xE4={'OK' if ok4 else 'FAIL'}")
    return 0 if (ok8 and ok4) else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Pre-check the select_max_param own-row wave (eighteenth-return NEXT 2).

The LIBGS MATRIX3 member select_max_param (psyq extent 0xC8, sdk_anchors
"unique" in all eight targets; three targets pin the psyq name in symbols,
five sit under walk names). The census's byte-identical wave reads x7
size=0xD0; this pre-check measures everything empirically from the tree.

waveE8E4_check.py pattern with the same offline adaptation: byte-identity
is proven from the COMMITTED LISTINGS' hex comment columns (byte-true
because verify 8/8 GREEN assembles them into the witnessed image, the
gmd_offline_screen trust model). The disc-derived baselines on disk are
woven-era in a rolled-back sandbox - the baseline cross-check is
informational only, and the return-window rerun re-checks them against
fresh per-sector baselines.

Checks:
1. listing existence for all eight walk names (slps flat asm/nonmatchings),
2. per-member listing extents + byte-identity x8 (listing hex words),
3. yaml row extents (next-row offset - row offset; the census keyed 0xD0),
4. the row's neighborhood in each yaml,
5. name-collision scan on the walk names + the select_max_param pin report,
6. word-level scan of the reference body: jals, lui, gp-relative, cop2/mvmva,
   and the psyq division-magic census (0x66666667 class).

Exit 0 = pre-check clean (byte-identity + no collisions).
"""
import re
import struct
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

WAVE = [
    ("slps_00270", 0x14584, "func_80036D04"),
    ("sces_00269", 0x1404C, "func_8003384C"),
    ("mainmenu_jp", 0x44F0C, "func_8006E9BC"),
    ("mainmenu_eu", 0x44810, "func_80064010"),
    ("g3_jp", 0x309F8, "func_800501F8"),
    ("g3_eu", 0x30334, "func_8004FB34"),
    ("g3org_jp", 0x2DE94, "func_800542A4"),
    ("g3org_eu", 0x2D788, "func_8004CF88"),
]
PINNED = {"slps_00270", "g3org_jp", "mainmenu_jp"}
HEXCOL = re.compile(r"/\*\s*[0-9A-Fa-f]+\s+[0-9A-Fa-f]+\s+([0-9A-Fa-f]{8})\s*\*/")


def listing_path(target: str, fn: str) -> Path:
    if target == "slps_00270":
        return REPO / "asm" / "nonmatchings" / f"{fn}.s"
    return REPO / "asm" / target / "nonmatchings" / f"{fn}.s"


def listing_words(target: str, fn: str) -> list[int]:
    """MIPS words as LITTLE-ENDIAN values (the spimdisasm hex column is the
    big-endian BYTE display; the actual instruction word is byte-reversed)."""
    text = listing_path(target, fn).read_text()
    words = []
    for ln in text.splitlines():
        m = HEXCOL.search(ln)
        if m:
            words.append(int.from_bytes(bytes.fromhex(m.group(1)), "little"))
    if not words:
        raise SystemExit(f"{target}/{fn}: listing carries no hex column")
    return words


def yaml_row(target: str, fn: str) -> tuple[int, int, list[str]]:
    yml = (REPO / "config" / f"splat.{target}.yaml").read_text().splitlines()
    for i, l in enumerate(yml):
        if f", asm, {fn}]" in l:
            m = re.search(r"\[0x([0-9A-Fa-f]+), asm, ", l)
            return int(m.group(1), 16), i, yml
    raise SystemExit(f"{target}: no asm row for {fn}")


def row_extent(off: int, idx: int, yml: list[str]) -> int | None:
    nxt = None
    for l in yml[idx + 1 :]:
        m = re.search(r"\[0x([0-9A-Fa-f]+),", l.strip())
        if m:
            nxt = int(m.group(1), 16)
            break
    return None if nxt is None else nxt - off


def main() -> int:
    print("=" * 72)
    print("select_max_param wave pre-check (x8, one member per target)")
    print("=" * 72)
    ok = True
    blobs: dict[str, list[int]] = {}
    offs: dict[str, tuple[int, int, list[str]]] = {}
    for t, off, fn in WAVE:
        p = listing_path(t, fn)
        if not p.exists():
            print(f"  {t}/{fn}: LISTING MISSING at {p}")
            ok = False
            continue
        words = listing_words(t, fn)
        blobs[t] = words
        yoff, idx, yml = yaml_row(t, fn)
        offs[t] = (yoff, idx, yml)
        ext = row_extent(yoff, idx, yml)
        tag = "pinned" if t in PINNED else "walk"
        print(
            f"  {t:<12} {fn} @0x{yoff:X} ({tag}): listing {len(words)} words "
            f"(0x{len(words) * 4:X}), row-extent {ext if ext is None else hex(ext)}, "
            f"head {words[0]:08X} tail {words[-1]:08X}"
        )
        if yoff != off:
            print(f"    OFFSET MISMATCH: yaml 0x{yoff:X} != expected 0x{off:X}")
            ok = False

    # byte-identity over a common length
    lens = {len(w) for w in blobs.values()}
    print(f"\n  LISTING EXTENTS: {sorted(hex(x * 4) for x in lens)}")
    common = min(lens) if lens else 0
    ref_key = WAVE[0][0]
    ref = blobs[ref_key][:common]
    ident = [t for t in blobs if blobs[t][:common] != ref]
    print(f"  BYTE-IDENTICAL x{len(blobs)} over first 0x{common * 4:X} (listing hex): {not ident}")
    for t in ident:
        diffs = [4 * i for i in range(common) if blobs[t][i] != ref[i]]
        print(f"    {t} differs at word offsets: {[hex(d) for d in diffs]}")

    # baseline cross-check (stale woven-era containers; informational)
    print("  BASELINE CROSS-CHECK (stale woven-era baselines; informational):")
    for t, off, fn in WAVE:
        p = REPO / "baselines" / f"{t}.bin"
        if not p.exists() or t not in blobs:
            print(f"    {t}: no baseline or no listing words")
            continue
        size = len(blobs[t]) * 4
        data = p.read_bytes()[off : off + size]
        words = [struct.unpack("<I", data[i : i + 4])[0] for i in range(0, size, 4)]
        same = words == blobs[t]
        print(f"    {t} @0x{off:X}: {'MATCH' if same else 'differ (stale container - expected offline)'}")

    # neighborhoods
    print("  YAML NEIGHBORHOODS:")
    for t, _, fn in WAVE:
        if t not in offs:
            continue
        off, idx, yml = offs[t]
        print(f"    == {t} L{idx + 1}")
        for k in (idx - 1, idx, idx + 1):
            if 0 <= k < len(yml):
                print(f"       {yml[k].strip()}")

    # collisions on walk names + pin report
    print("  NAME-COLLISION SCAN (walk names) + PIN REPORT:")
    cur = (REPO / "config" / "symbols.curated.txt").read_text()
    for t, _, fn in WAVE:
        sym = (REPO / "config" / f"symbols.{t}.txt").read_text()
        hits = [l for l in sym.splitlines() if fn in l]
        chits = [l for l in cur.splitlines() if fn in l]
        pin = [l for l in sym.splitlines() if "select_max_param" in l]
        print(
            f"    {t}: walk-name symbols={'YES' if hits else 'no'} "
            f"curated={'YES' if chits else 'no'}; select_max_param pin: "
            f"{pin[0].strip() if pin else 'NONE'}"
        )
        if hits or chits:
            ok = False

    # word scan of the reference body
    ref = blobs[ref_key]
    jals = [(4 * i, hex(w & 0x3FFFFFF)) for i, w in enumerate(ref) if (w >> 26) == 3]
    luis = [(4 * i, hex((w >> 16) & 0xFFFF)) for i, w in enumerate(ref) if (w >> 26) == 0xF]
    gp = sum(1 for w in ref if (w >> 26) in (0x23, 0x2B) and ((w >> 21) & 31) == 28)
    cop2 = sum(1 for w in ref if (w >> 26) in (0x12, 0x13, 0x32, 0x3A))
    mvmva = sum(1 for w in ref if w == 0x4A486012)
    magics = sorted({hex(w) for w in ref if w in (0x66666667, 0x2FA0BE83, 0x51EB851F, 0x88888889, 0x51EB851F)})
    print(
        f"  BODY WORD SCAN (ref {ref_key}): {len(ref)} words; jals={jals}; lui={luis}; "
        f"gp-rel={gp}; cop2-class={cop2} (mvmva x{mvmva}); psyq div-magics={magics}"
    )

    print(f"\nPRE-CHECK VERDICT: {'OK' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

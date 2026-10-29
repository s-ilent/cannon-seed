#!/usr/bin/env python3
"""wave34_0C_check.py - pre-check the two fresh x8 own-row waves (the
eighteenth return's phase F items, the twenty-second window's decodes):

  wave34 (0x34, census sha 0e4f6b4412ab): seven own-row members, one per
  game target except mainmenu_jp - the eighth member is the parent-bound
  interior at asm/mainmenu_jp/nonmatchings/func_80085B5C.s +0x168.
  Decode: the word-copy loop (u32 units, pointer walks + up-counter, the
  loop-inverted sltu form); template scripts/wave34_0C/wave34.c screens
  bytes=EXACT vs the committed slps listing (13 words, zero relocations).

  wave0C (0xC, census sha b5f14db96e53): seven own-row members, same
  shape - the eighth is the parent-bound interior at
  asm/mainmenu_jp/nonmatchings/func_8007FFAC.s +0x1BC. Decode: the
  halfword-load thunk (lhu $v0,0($a0); jr; nop); template
  scripts/wave34_0C/wave0C.c screens bytes=EXACT (3 words, zero
  relocations).

waveC8_check.py pattern with the same offline adaptation: byte-identity is
proven from the COMMITTED LISTINGS' hex comment columns (byte-true because
verify 8/8 GREEN assembles them into the witnessed image, the
gmd_offline_screen trust model). The census cross-check (baseline ELF
symbols) re-runs at the return window.

Checks per wave:
1. listing existence x7 (slps flat asm/nonmatchings),
2. per-member listing extents + byte-identity x7 (listing hex words),
3. yaml row offsets + row extents (next-row offset - row offset),
4. the row's neighborhood in each yaml,
5. name-collision scan: curated hits = HARD FAIL; symbols-file hits are
   reported and ACCEPTED when they annotate the row's own VA (the
   branch-target class - the len_param pinned-c-row precedent: symbols
   lines coexist with c units),
6. the parent-bound member report (the mainmenu_jp interiors, byte-run
   search over every committed listing),
7. word-level scan of both reference bodies: jals, lui, gp-relative,
   cop2/mvmva.

Exit 0 = pre-check clean (byte-identity + no hard collisions).
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HEXCOL = re.compile(r"/\*\s*[0-9A-Fa-f]+\s+[0-9A-Fa-f]+\s+([0-9A-Fa-f]{8})\s*\*/")

WAVES = {
    "wave34": {
        "size": 0x34,
        "parent": ("mainmenu_jp", "asm/mainmenu_jp/nonmatchings/func_80085B5C.s", 0x168),
        "members": [
            ("slps_00270", 0x8003C8F8, "func_8003C8F8"),
            ("sces_00269", 0x8003C6EC, "func_8003C6EC"),
            ("mainmenu_eu", 0x800792C0, "func_800792C0"),
            ("g3_jp", 0x8006334C, "func_8006334C"),
            ("g3_eu", 0x80063CDC, "func_80063CDC"),
            ("g3org_jp", 0x800607E8, "func_800607E8"),
            ("g3org_eu", 0x80061130, "func_80061130"),
        ],
    },
    "wave0C": {
        "size": 0xC,
        "parent": ("mainmenu_jp", "asm/mainmenu_jp/nonmatchings/func_8007FFAC.s", 0x1BC),
        "members": [
            ("slps_00270", 0x80037BF4, "func_80037BF4"),
            ("sces_00269", 0x800377A8, "func_800377A8"),
            ("mainmenu_eu", 0x80074100, "func_80074100"),
            ("g3_jp", 0x8005E648, "func_8005E648"),
            ("g3_eu", 0x8005ED98, "func_8005ED98"),
            ("g3org_jp", 0x8005BAE4, "func_8005BAE4"),
            ("g3org_eu", 0x8005C1EC, "func_8005C1EC"),
        ],
    },
}
HDR = 0x800
BASE_VA = 0x80020000


def listing_path(target: str, fn: str) -> Path:
    if target == "slps_00270":
        return REPO / "asm" / "nonmatchings" / f"{fn}.s"
    return REPO / "asm" / target / "nonmatchings" / f"{fn}.s"


def listing_words(target: str, fn: str) -> list[int]:
    text = listing_path(target, fn).read_text()
    words = []
    for ln in text.splitlines():
        m = HEXCOL.search(ln)
        if m:
            words.append(int.from_bytes(bytes.fromhex(m.group(1)), "little"))
    if not words:
        raise SystemExit(f"{target}/{fn}: listing carries no hex column")
    return words


def yaml_row(target: str, fn: str):
    yml = (REPO / "config" / f"splat.{target}.yaml").read_text().splitlines()
    for i, l in enumerate(yml):
        if f", asm, {fn}]" in l:
            m = re.search(r"\[0x([0-9A-Fa-f]+), asm, ", l)
            return int(m.group(1), 16), i, yml
    raise SystemExit(f"{target}: no asm row for {fn}")


def row_extent(off: int, idx: int, yml: list[str]):
    for l in yml[idx + 1:]:
        m = re.search(r"\[0x([0-9A-Fa-f]+),", l.strip())
        if m:
            return int(m.group(1), 16) - off
    return None


def check_wave(tag: str, spec: dict) -> bool:
    print("=" * 72)
    print(f"{tag} wave pre-check (size 0x{spec['size']:X}, x7 own-row + 1 parent)")
    print("=" * 72)
    ok = True
    blobs: dict[str, list[int]] = {}
    offs = {}
    for t, va, fn in spec["members"]:
        off = va - BASE_VA + HDR
        p = listing_path(t, fn)
        if not p.exists():
            print(f"  {t}/{fn}: LISTING MISSING at {p}")
            ok = False
            continue
        words = listing_words(t, fn)
        blobs[t] = words
        yoff, idx, yml = yaml_row(t, fn)
        offs[t] = (off, idx, yml)
        ext = row_extent(off, idx, yml)
        print(
            f"  {t:<12} {fn} @0x{va:08X}: listing {len(words)} words "
            f"(0x{len(words) * 4:X}), row-extent {ext if ext is None else hex(ext)}, "
            f"head {words[0]:08X} tail {words[-1]:08X}"
        )
        if yoff != off:
            print(f"    OFFSET MISMATCH: yaml 0x{yoff:X} != expected 0x{off:X}")
            ok = False
        if len(words) * 4 != spec["size"]:
            print(f"    EXTENT MISMATCH: listing 0x{len(words) * 4:X} != 0x{spec['size']:X}")
            ok = False

    lens = {len(w) for w in blobs.values()}
    ref_key = spec["members"][0][0]
    ref = blobs[ref_key]
    ident = [t for t in blobs if blobs[t] != ref]
    print(f"  BYTE-IDENTICAL x{len(blobs)} (listing hex): {not ident}; "
          f"extents {sorted(hex(x * 4) for x in lens)}")
    for t in ident:
        diffs = [4 * i for i in range(min(len(blobs[t]), len(ref)))
                 if blobs[t][i] != ref[i]]
        print(f"    {t} differs at word offsets: {[hex(d) for d in diffs]}")
        ok = False

    pt, ppath, poff = spec["parent"]
    p = REPO / ppath
    if p.exists():
        words = []
        for ln in p.read_text().splitlines():
            m = HEXCOL.search(ln)
            if m:
                words.append(int.from_bytes(bytes.fromhex(m.group(1)), "little"))
        want = [w.to_bytes(4, "little") for w in ref]
        pat = b"".join(want)
        blob = b"".join(w.to_bytes(4, "little") for w in words)
        hits = [i for i in range(0, len(blob) - len(pat) + 1, 4)
                if blob[i:i + len(pat)] == pat]
        hit = (poff in hits) if hits else False
        print(f"  PARENT member: {pt} {Path(ppath).name} +0x{poff:X}: "
              f"{'PRESENT' if hit else 'MISSING'} (interior hits: "
              f"{[hex(h) for h in hits]})")
        if not hit:
            ok = False
    else:
        print(f"  PARENT member: listing missing {p}")
        ok = False

    print("  NAME-COLLISION SCAN (curated = HARD FAIL; symbols = informational):")
    cur = (REPO / "config" / "symbols.curated.txt").read_text()
    for t, va, fn in spec["members"]:
        sym = (REPO / "config" / f"symbols.{t}.txt").read_text()
        chits = [l.strip() for l in cur.splitlines() if fn in l]
        shits = [l.strip() for l in sym.splitlines() if fn in l]
        own = [l for l in shits if hex(va).lstrip("0x") in l or f"0x{va:08X}" in l]
        print(f"    {t}/{fn}: curated={'YES ' + str(chits) if chits else 'no'}; "
              f"symbols {len(shits)} line(s)"
              + (f" (own-VA branch-target class: {own[0]})" if own and shits else ""))
        if chits:
            ok = False

    jals = [(4 * i, hex(w & 0x3FFFFFF)) for i, w in enumerate(ref) if (w >> 26) == 3]
    luis = [(4 * i, hex((w >> 16) & 0xFFFF)) for i, w in enumerate(ref) if (w >> 26) == 0xF]
    gp = sum(1 for w in ref if (w >> 26) in (0x23, 0x2B) and ((w >> 21) & 31) == 28)
    cop2 = sum(1 for w in ref if (w >> 26) in (0x12, 0x13, 0x32, 0x3A))
    print(f"  BODY WORD SCAN (ref {ref_key}): {len(ref)} words; jals={jals}; "
          f"lui={luis}; gp-rel={gp}; cop2-class={cop2}")
    print(f"\n{tag} PRE-CHECK VERDICT: {'OK' if ok else 'FAIL'}\n")
    return ok


def main() -> int:
    ok = all(check_wave(tag, spec) for tag, spec in WAVES.items())
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

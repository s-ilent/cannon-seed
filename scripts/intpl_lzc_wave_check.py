#!/usr/bin/env python3
"""Pre-check the Intpl/Lzc completion wave (the cross-target re-scope class).

The data-typed-sdk census check (this window's queue item) found the
residual members the earlier re-scope waves could not flip:
  - mainmenu_jp Intpl  0x80065F74  row 0x46774 extent 0x8c (needs the
    0x24 c split + 0x68 data remainder - the E3DC surgery shape)
  - mainmenu_jp Lzc    0x800660DC  row 0x468DC extent 0x18 (exact body,
    no pad - the sibling rows are 0x1c with 4 zero pad)
  - sces_00269  Lzc    0x800360FC  row 0x168FC extent 0x18 (same shape)

Unlike wave10C_check.py (written against the stale woven-era baselines),
THIS window's sandbox holds the hardened extract-twin baselines (rehydrate
restored them, oracle UP), so byte-identity is proven DIRECTLY from
baselines/<t>.bin at the yaml offsets - the same trust model as the
disc-derived witness chain (extract twins, d637286a medium, proven by the
1946 window's GREEN verify).

Checks:
1. baseline-to-baseline byte identity per row (dw count) vs all landed
   siblings (slps_00270 WAVE C f70e1943, g3_jp, g3_eu),
2. the Lzc pad law: slps/g3_jp/g3_eu 0x1c rows' trailing 4 bytes zero,
3. the mainmenu_jp Intpl remainder 0x68: census members inside?, word
   dump for the eyeball,
4. name-collision scan (symbols.<t>.txt + symbols.curated.txt),
5. neighborhood print for each flip row.
"""
import re
import struct
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# (target, yaml_off, extent, VA)
ROWS = {
    "mmj_intpl": ("mainmenu_jp", 0x46774, 0x8C, 0x80065F74),
    "mmj_lzc": ("mainmenu_jp", 0x468DC, 0x18, 0x800660DC),
    "sces_lzc": ("sces_00269", 0x168FC, 0x18, 0x800360FC),
    # landed siblings
    "slps_intpl": ("slps_00270", 0x16CCC, 0x24, 0x800364CC),
    "g3jp_intpl": ("g3_jp", 0x32260, 0x24, 0x80051A60),
    "g3eu_intpl": ("g3_eu", 0x31B9C, 0x24, 0x8005139C),
    "slps_lzc": ("slps_00270", 0x16E34, 0x1C, 0x80036634),
    "g3jp_lzc": ("g3_jp", 0x323C8, 0x1C, 0x80051BC8),
    "g3eu_lzc": ("g3_eu", 0x31D04, 0x1C, 0x80051D04),
}
INTPL_SIZE = 0x24
LZC_SIZE = 0x18


def blob(t: str, off: int, size: int) -> bytes:
    p = REPO / "baselines" / f"{t}.bin"
    data = p.read_bytes()
    if off + size > len(data):
        raise SystemExit(f"{t}: baseline too small ({len(data)}) for "
                         f"0x{off:X}+0x{size:X}")
    return data[off:off + size]


def words_le(b: bytes) -> list[int]:
    return [struct.unpack("<I", b[i:i + 4])[0] for i in range(0, len(b), 4)]


def census_line(target: str, va: int):
    """The census line for an address in target's block, if any."""
    out = []
    cur = None
    for line in (REPO / "config" / "sdk_members.txt").read_text().splitlines():
        m = re.match(r"^// target: (\S+)", line)
        if m:
            cur = m.group(1)
            continue
        if cur == target and f"0x{va:08x}" in line:
            out.append(line.strip())
    return out


def yaml_lines_with(target: str, needle: str):
    yml = (REPO / "config" / f"splat.{target}.yaml").read_text().splitlines()
    return [(i, l.strip()) for i, l in enumerate(yml) if needle in l]


def main() -> int:
    ok = True
    print("== 1. BYTE IDENTITY (hardened baselines, direct read)")
    # Intpl bodies: candidate rows' first 0x24 vs the three landed siblings
    refs_intpl = {k: blob(*ROWS[k][:2], INTPL_SIZE)
                  for k in ("slps_intpl", "g3jp_intpl", "g3eu_intpl")}
    ref_intpl = refs_intpl["slps_intpl"]
    for k in ("g3jp_intpl", "g3eu_intpl"):
        dw = sum(a != b for a, b in zip(words_le(refs_intpl[k]),
                                        words_le(ref_intpl)))
        print(f"   sibling check {k} vs slps_intpl: dw={dw}")
        if dw:
            ok = False
    for k in ("mmj_intpl",):
        t, off, ext, va = ROWS[k]
        b = blob(t, off, INTPL_SIZE)
        dw = sum(a != b for a, b in zip(words_le(b), words_le(ref_intpl)))
        print(f"   {k} ({t} @0x{off:X} va 0x{va:X}) vs slps_intpl: dw={dw}"
              f" -> {'IDENTICAL' if dw == 0 else 'DIFFERS'}")
        if dw:
            ok = False
    # Lzc bodies: first 0x18 of each sibling row + pad check
    refs_lzc = {}
    for k in ("slps_lzc", "g3jp_lzc", "g3eu_lzc"):
        t, off, ext, va = ROWS[k]
        b = blob(t, off, LZC_SIZE)
        refs_lzc[k] = b
        pad = blob(t, off + LZC_SIZE, ext - LZC_SIZE)
        print(f"   {k} ({t} @0x{off:X} ext 0x{ext:X}): body head "
              f"{b[:8].hex()} tail {b[-8:].hex()}; pad {pad.hex()} "
              f"({'all zero' if pad == b'\\x00' * len(pad) else 'NONZERO'})")
    ref_lzc = refs_lzc["slps_lzc"]
    for k in ("g3jp_lzc", "g3eu_lzc"):
        dw = sum(a != b for a, b in zip(words_le(refs_lzc[k]),
                                        words_le(ref_lzc)))
        print(f"   sibling check {k} vs slps_lzc: dw={dw}")
        if dw:
            ok = False
    for k in ("mmj_lzc", "sces_lzc"):
        t, off, ext, va = ROWS[k]
        b = blob(t, off, LZC_SIZE)
        dw = sum(a != b for a, b in zip(words_le(b), words_le(ref_lzc)))
        print(f"   {k} ({t} @0x{off:X} va 0x{va:X}) vs slps_lzc: dw={dw}"
              f" -> {'IDENTICAL' if dw == 0 else 'DIFFERS'}")
        if dw:
            ok = False

    print("== 2. mainmenu_jp Intpl REMAINDER 0x68 @0x46798 (stays data)")
    rem = blob("mainmenu_jp", 0x46798, 0x68)
    ws = words_le(rem)
    jals = [(4 * i, f"{w:08X}") for i, w in enumerate(ws) if (w >> 26) == 3]
    print(f"   words={len(ws)} jals={jals}")
    for i in range(0, len(ws), 4):
        print(f"     +0x{4*i:02X}: " + " ".join(f"{w:08X}" for w in ws[i:i+4]))
    for va in range(0x80065F98, 0x80066000, 4):
        lines = census_line("mainmenu_jp", va)
        if lines:
            print(f"   census @0x{va:08X}: {lines}")

    print("== 3. NAME-COLLISION SCAN")
    for t, names in (("mainmenu_jp", ("Intpl", "Lzc")),
                     ("sces_00269", ("Lzc",))):
        sym = (REPO / "config" / f"symbols.{t}.txt").read_text()
        cur = (REPO / "config" / "symbols.curated.txt").read_text()
        for n in names:
            shits = [l.strip() for l in sym.splitlines() if re.search(
                rf"^{'|'.join(['Intpl', 'Lzc']) if n in ('Intpl', 'Lzc') else n}", l)]
            chits = [l.strip() for l in cur.splitlines()
                     if l.startswith(n) or f" {n} =" in l or f"{n} =" in l]
            print(f"   {t} {n}: symbols={shits or 'no'} curated={chits or 'no'}")
            if chits:
                print(f"      -> CURATED COLLISION: do not apply")
                ok = False

    print("== 4. NEIGHBORHOODS (flip rows, yaml context)")
    for t, needle in (("mainmenu_jp", "0x46774"),
                      ("mainmenu_jp", "0x468DC"),
                      ("sces_00269", "0x168FC")):
        yml = (REPO / "config" / f"splat.{t}.yaml").read_text().splitlines()
        for i, l in enumerate(yml):
            if f"[{needle}," in l:
                print(f"   == {t} L{i+1}")
                for k in range(max(0, i - 2), min(len(yml), i + 3)):
                    mark = ">>" if k == i else "  "
                    print(f"   {mark} {yml[k].strip()}")
                break

    print(f"\nPRE-CHECK VERDICT: {'OK' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

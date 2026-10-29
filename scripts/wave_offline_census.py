#!/usr/bin/env python3
"""wave_offline_census.py - the byte-identical wave census from COMMITTED ARTIFACTS ONLY.

tools/near_twin_census.py needs the witnessed baselines + build ELFs
(pair_report.input_gates); a rolled-back sandbox has neither (witness 0/8,
re-confirmed every disc-blocked window). But the committed listings' hex
columns carry the retail bytes byte-true (the gmd_offline_screen trust
model: verify 8/8 GREEN assembles them into the witnessed image), and the
yamls carry the row structure. This tool re-derives the byte-identical
wave pool offline so dead-disc windows can keep decoding (Law Zero).

Universe (the census's, adapted to committed artifacts): every
[0xOFF, asm, name] yaml row = one non-matched walk function (the census's
non-matched STT_FUNC rows; matched c rows are excluded by the census and
carry no committed listing); bytes from its listing's spimdisasm hex
column. Groups keyed (word-count, sha1) spanning >= 2 targets.

Parent-bound members (interior blocks of bigger rows) are NOT first-class
here: found afterwards by pattern-searching every committed listing for
each wave's word run (--parents). The census cross-check (baseline ELF
symbols) happens at the return window - this tool ranks decode candidates,
it is not a landing gate.

Usage:
    python3 scripts/wave_offline_census.py            # the wave pool
    python3 scripts/wave_offline_census.py --parents  # + interior searches
Exit 0 always (a census, not a gate).
"""
import hashlib
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TARGETS = [
    "slps_00270", "sces_00269",
    "mainmenu_jp", "mainmenu_eu",
    "g3_jp", "g3_eu",
    "g3org_jp", "g3org_eu",
]
BASE_VA = 0x80020000
HDR = 0x800
ROW_RE = re.compile(r"^\s*- \[0x([0-9A-Fa-f]+), (\w+), (\w+)\]")
HEXCOL = re.compile(r"/\*\s*[0-9A-Fa-f]+\s+[0-9A-Fa-f]+\s+([0-9A-Fa-f]{8})\s*\*/")


def listing_path(target: str, fn: str) -> Path:
    if target == "slps_00270":
        return REPO / "asm" / "nonmatchings" / f"{fn}.s"
    return REPO / "asm" / target / "nonmatchings" / f"{fn}.s"


def all_listing_paths():
    """Every committed nonmatching listing, all targets (for --parents)."""
    out = []
    d = REPO / "asm" / "nonmatchings"
    if d.is_dir():
        out += sorted(d.glob("*.s"))
    for t in TARGETS:
        if t == "slps_00270":
            continue
        d = REPO / "asm" / t / "nonmatchings"
        if d.is_dir():
            out += sorted(d.glob("*.s"))
    return out


def listing_words(path: Path) -> list[int]:
    """MIPS words as LITTLE-ENDIAN values (spimdisasm's hex column is the
    big-endian byte display; the instruction word is byte-reversed)."""
    words = []
    for ln in path.read_text(errors="replace").splitlines():
        m = HEXCOL.search(ln)
        if m:
            words.append(int.from_bytes(bytes.fromhex(m.group(1)), "little"))
    return words


def asm_rows(target: str):
    """[(file_off, name, extent_comment_or_None)] for every asm yaml row."""
    rows = []
    for ln in (REPO / "config" / f"splat.{target}.yaml").read_text().splitlines():
        m = ROW_RE.match(ln)
        if m and m.group(2) == "asm":
            off = int(m.group(1), 16)
            ext = None
            me = re.search(r"#\s*0x([0-9A-Fa-f]+)\s*$", ln)
            if me:
                ext = int(me.group(1), 16)
            rows.append((off, m.group(3), ext))
    return rows


def collect():
    """{target: [(off, name, ext, words)]} - skip rows whose listing is
    missing or hex-silent (reported, not fatal)."""
    pool = {}
    for t in TARGETS:
        rows = asm_rows(t)
        got = []
        miss = 0
        for off, name, ext in rows:
            p = listing_path(t, name)
            if not p.exists():
                miss += 1
                continue
            w = listing_words(p)
            if not w:
                miss += 1
                continue
            got.append((off, name, ext, w))
        pool[t] = got
        print(f"  {t:<12} asm rows {len(rows):4d}, listing-read {len(got):4d}, "
              f"unread {miss}")
    return pool


def main() -> int:
    want_parents = "--parents" in sys.argv
    print("=" * 72)
    print("OFFLINE WAVE CENSUS (committed listings only; witness not required)")
    print("=" * 72)
    pool = collect()

    # group by (word-count, sha1) across targets
    groups = {}
    for t, rows in pool.items():
        for off, name, ext, w in rows:
            key = (len(w), hashlib.sha1(
                b"".join(x.to_bytes(4, "little") for x in w)).hexdigest())
            groups.setdefault(key, []).append((t, off, name, ext))

    waves = [(k, v) for k, v in groups.items()
             if len({m[0] for m in v}) >= 2 and len(v) >= 2]
    # rank: member count desc, then size desc
    waves.sort(key=lambda kv: (-len(kv[1]), -kv[0][0]))

    print(f"\n  byte-identical waves (>=2 members, >=2 targets): {len(waves)}")
    print(f"  {'words':>5} {'size':>6} {'members':>7}  member targets")
    for (n, _sha), members in waves[:40]:
        tgts = sorted({m[0] for m in members})
        print(f"  {n:>5} 0x{n * 4:<4X} {len(members):>7}  {'+'.join(tgts)}")

    # drill into the multi-target waves with the largest member counts
    print("\n  DETAIL - waves with >=6 members:")
    for (n, sha), members in waves:
        if len(members) < 6:
            continue
        print(f"  wave size=0x{n * 4:X} sha1={sha[:12]} members={len(members)}")
        for t, off, name, ext in members:
            va = off - HDR + BASE_VA
            ext_s = hex(ext) if ext is not None else "?"
            flag = "own-row" if ext == n * 4 else "EXT-MISMATCH"
            print(f"    {t:<12} {name} @0x{va:08X} ext={ext_s} [{flag}]")

    if want_parents:
        print("\n  INTERIOR PARENT SEARCH (every committed listing):")
        listings = [(p, listing_words(p)) for p in all_listing_paths()]
        listings = [(p, w) for p, w in listings if w]
        for (n, _sha), members in waves:
            if len(members) < 6 or n < 2:
                continue
            pat = members[0]
            # rebuild the word run from any member's listing
            ref = None
            for t, off, name, ext in members:
                w = listing_words(listing_path(t, name))
                if len(w) == n:
                    ref = w
                    break
            if ref is None:
                continue
            hits = []
            for p, w in listings:
                if len(w) <= n:
                    continue
                for i in range(len(w) - n + 1):
                    if w[i:i + n] == ref:
                        hits.append((p, i * 4))
            own = {m[2] for m in members}
            ext_hits = [h for h in hits if h[0].stem not in own]
            print(f"    wave size=0x{n * 4:X}: interior hits "
                  f"{len(ext_hits)} (excl. the own-row listings)")
            for p, boff in ext_hits:
                print(f"      {p.relative_to(REPO)} +0x{boff:X}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

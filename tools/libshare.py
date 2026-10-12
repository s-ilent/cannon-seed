#!/usr/bin/env python3
"""libshare.py - measure the Psy-Q library share of a retail target.

Whole-member scanning (tools/sdk_members.py) requires a member's ENTIRE
.text to be present, so it reports only the members the original link kept
intact. Most library code in these binaries was linked function-granular,
which that test misses: on slps_00270 the whole-member scan covers ~2% of
the payload, the function-level scan below ~24%.

This tool splits each member's .text at its own symbols and matches every
function slice anywhere in the payload, 4-byte aligned. Relocated fields are
zero in an unlinked object, so zero bytes are wildcards; a slice with fewer
than --min-fixed non-zero bytes is skipped as too little evidence to place.

Two limits:

* The SDK release decides the answer. These targets are Psy-Q ~3.3 (kernel
  RCS tags dated 1995-10, docs/RECON.md); the same scan against 4.0 finds
  ~2% of the payload, against 3.3 ~13%. Point --libs at the right release.
* The code/data carve is unreliable (docs/TASKS.md: library code sits inside
  ranges the splat map calls data), so the "code" column inherits that
  error. The payload column does not, and is the one to quote.

Usage:
    python3 tools/libshare.py --libs ~/psyq/3.3/PSX/LIB
    python3 tools/libshare.py --libs ~/psyq/3.3/PSX/LIB --target g3_jp
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parent
sys.path.insert(0, str(TOOLS))
import sdk_members as sm  # noqa: E402

_FUNC_SYM = re.compile(r"=\s*(0x[0-9A-Fa-f]+);\s*//\s*type:func")


def code_regions(target: str) -> tuple[list[tuple[int, int]], int, int]:
    """([(start, end)] of asm/c subsegments, payload_lo, payload_vram).

    Subsegment lengths live in the yaml comments, not the parsed data, so an
    extent is the gap to the next subsegment start.
    """
    cfg = yaml.safe_load((REPO / "config" / f"splat.{target}.yaml").read_text())
    seg = cfg["segments"][0]
    lo, vram = seg["start"], seg["vram"]
    tgt = (REPO / "config" / cfg["options"]["base_path"]
           / cfg["options"]["target_path"]).resolve()
    end = lo + tgt.stat().st_size
    subs = sorted((lo + s[0], s[1]) for s in seg["subsegments"]
                  if isinstance(s, list) and len(s) >= 2 and isinstance(s[0], int))
    out = []
    for i, (st, ty) in enumerate(subs):
        en = subs[i + 1][0] if i + 1 < len(subs) else end
        if ty in ("asm", "c"):
            out.append((st, en))
    return out, lo, vram


def match_slice(payload: bytes, sl: bytes, min_fixed: int) -> list[tuple[int, int]]:
    """4-aligned [start, end) offsets where every non-zero byte of `sl` holds."""
    if len(sl) < 8:
        return []
    fixed = [i for i, b in enumerate(sl) if b]
    if len(fixed) < min_fixed:
        return []
    k = fixed[0]
    hits, start = [], 0
    while True:
        j = payload.find(bytes([sl[k]]), start)
        if j < 0:
            return hits
        start = j + 1
        s = j - k
        if s < 0 or (s & 3) or s + len(sl) > len(payload):
            continue
        if all(payload[s + i] == sl[i] for i in fixed):
            hits.append((s, s + len(sl)))
    return hits


def union_len(ivs: list[tuple[int, int]]) -> int:
    if not ivs:
        return 0
    ivs = sorted(ivs)
    total, (cs, ce) = 0, ivs[0]
    for s, e in ivs[1:]:
        if s > ce:
            total += ce - cs
            cs, ce = s, e
        else:
            ce = max(ce, e)
    return total + ce - cs


def func_starts(target: str, lo: int, vram: int) -> list[int]:
    """File offsets of every `type:func` symbol in the target's symbols file."""
    f = REPO / "config" / f"symbols.{target}.txt"
    offs = {int(m.group(1), 16) - vram + lo for m in
            (_FUNC_SYM.search(line) for line in f.read_text().splitlines()) if m}
    return sorted(offs)


def measure(libdir: Path, target: str, min_fixed: int) -> dict:
    members = []
    for lib in sorted(libdir.glob("LIB*.LIB")):
        members.extend(sm.parse_archive(lib))
    members = [m for m in members if m.text()]
    payload, lo, vram = sm.load_target(target)
    code, _, _ = code_regions(target)

    covers, names = [], set()
    for m in members:
        syms = m.text_syms()
        text = m.text()
        bounds = sorted({o for o, _ in syms} | {len(text)})
        for i in range(len(bounds) - 1):
            sl = text[bounds[i]:bounds[i + 1]]
            nm = next((n for o, n in syms if o == bounds[i]), None)
            for s, e in match_slice(payload, sl, min_fixed):
                covers.append((s, e))
                if nm:
                    names.add(nm)

    lib_all = union_len(covers)
    lib_code = union_len([(max(s, cs), min(e, ce)) for s, e in covers
                          for cs, ce in code if max(s, cs) < min(e, ce)])
    code_bytes = sum(e - s for s, e in code)
    starts = func_starts(target, lo, vram)
    lib_funcs = sum(1 for a in starts if any(s <= a < e for s, e in covers))
    return dict(target=target, payload=len(payload), code=code_bytes,
                lib_bytes=lib_all, lib_code=lib_code, names=len(names),
                funcs=len(starts), lib_funcs=lib_funcs)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--libs", type=Path, required=True,
                    help="directory holding the Psy-Q *.LIB archives")
    ap.add_argument("--target", action="append", default=None)
    ap.add_argument("--min-fixed", type=int, default=8,
                    help="non-zero bytes a slice needs to be placed (default 8)")
    args = ap.parse_args(argv[1:])
    if not args.libs.is_dir():
        print(f"libshare: no such directory {args.libs}", file=sys.stderr)
        return 0
    targets = args.target or [p.name[len("splat."):-len(".yaml")]
                              for p in sorted((REPO / "config").glob("splat.*.yaml"))]
    rows = [measure(args.libs, t, args.min_fixed) for t in targets]
    print(f"{'target':12s} {'payload':>8s} {'lib bytes':>10s} {'%pay':>6s} "
          f"{'%code':>6s} {'sdk fns':>8s} {'funcs':>6s} {'lib fns':>8s} {'%fn':>6s}")
    for r in rows:
        print(f"{r['target']:12s} {r['payload']:8d} {r['lib_bytes']:10d} "
              f"{100 * r['lib_bytes'] / r['payload']:5.1f}% "
              f"{100 * r['lib_code'] / max(r['code'], 1):5.1f}% {r['names']:8d} "
              f"{r['funcs']:6d} {r['lib_funcs']:8d} "
              f"{100 * r['lib_funcs'] / max(r['funcs'], 1):5.1f}%")
    pay = sum(r["payload"] for r in rows)
    lib = sum(r["lib_bytes"] for r in rows)
    fns = sum(r["funcs"] for r in rows)
    lfn = sum(r["lib_funcs"] for r in rows)
    print(f"{'TOTAL':12s} lib/payload {100 * lib / pay:.1f}%   "
          f"lib funcs {lfn}/{fns} ({100 * lfn / max(fns, 1):.1f}%)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

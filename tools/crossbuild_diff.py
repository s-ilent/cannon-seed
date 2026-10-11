#!/usr/bin/env python3
"""crossbuild_diff.py - cross-build carve audit for the 8 shipped executables.

A single-build static pass cannot see a mis-typed subsegment: scan_functions.py
seeds the yaml from one image, so "asm where it is really data" stays
self-consistent. Two builds sharing code do see it: a VRAM range that one
carve calls code and another calls data is a boundary error in one of them.

For every pair of builds this reports (1) VRAM ranges the two maps label a
different kind (code vs data), and (3) ranges one side carves as `asm` whose
bytes differ substantially from the counterpart (the asm side is likely data).

It also reports (2) the longest byte-identical runs, but that signal is WEAK
here and must not be trusted: the JP/EU images are index-shifted, so at fixed
VRAM only ~16-24% of the shared payload matches, the average run is ~1.7 bytes,
and well under 2% of runs >= 8 bytes end on a subsegment boundary. A matching
run does NOT corroborate a boundary in this game and is reported for reference
only.

Caveat on (1): most of the 28 pairs compare DIFFERENT executables (slps vs
mainmenu), whose maps legitimately disagree, so only the four same-program
region pairs (slps/sces, mainmenu_jp/eu, g3_jp/eu, g3org_jp/eu) carry a real
carve signal. The rest is printed for completeness.

Offsets come from the committed yaml (ground truth): payload_offset =
OFFSET - 0x800, VRAM = 0x80020000 + payload_offset.

Usage: python3 tools/crossbuild_diff.py [--json] [A B]   (default: all pairs)
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASE = 0x80020000
HDR = 0x800
# `asm`/`c` are code; `data` is data. A pair disagreeing across this line is
# the signal. Same-line disagreements (asm vs c) are legal and not reported.
CODE = ("asm", "c")
JP = ["slps_00270", "mainmenu_jp", "g3_jp", "g3org_jp"]
EU = ["sces_00269", "mainmenu_eu", "g3_eu", "g3org_eu"]
ALL = JP + EU
# Region counterparts that share code, by basename suffix.
MATCHED = [("slps_00270", "sces_00269"), ("mainmenu_jp", "mainmenu_eu"),
           ("g3_jp", "g3_eu"), ("g3org_jp", "g3org_eu")]
ASM_DIFF_MIN_BYTES = 16   # ignore tiny asm stubs when scoring a diff fraction
ASM_DIFF_THRESHOLD = 0.25  # fraction of differing bytes that flags an asm range
RUN_MIN = 8               # shortest identical run counted as boundary evidence


def region(t):
    return "JP" if t in JP else "EU"


def load(target):
    """Parse the yaml subsegment map and the baseline payload for one target.
    Returns (subsegs, payload); subsegs are dicts in VRAM with s < e."""
    payload = (REPO / "baselines" / f"{target}.bin").read_bytes()[HDR:]
    subsegs = []
    for ln in (REPO / "config" / f"splat.{target}.yaml").read_text().splitlines():
        m = re.match(r"\s*-\s*\[(0x[0-9A-Fa-f]+),\s*(asm|c|data),\s*(\w+)\]"
                     r"\s*#\s*(0x[0-9A-Fa-f]+)", ln)
        if m:
            s = BASE + (int(m.group(1), 16) - HDR)
            subsegs.append(dict(s=s, e=s + int(m.group(4), 16), kind=m.group(2),
                                name=m.group(3)))
    return subsegs, payload


def kind_at(subsegs, vram):
    for sg in subsegs:
        if sg["s"] <= vram < sg["e"]:
            return sg
    return None


def boundaries(subsegs):
    b = set()
    for sg in subsegs:
        b.add(sg["s"])
        b.add(sg["e"])
    return b


def label_disagreements(a, b):
    """One dict per maximal VRAM range where a and b fall on different sides of
    the code/data line. Sweeps the union of both maps' boundaries."""
    bs = sorted(boundaries(a) | boundaries(b))
    out = []
    for i in range(len(bs) - 1):
        s, e = bs[i], bs[i + 1]
        sa, sb = kind_at(a, s), kind_at(b, s)
        if sa is None or sb is None:
            continue
        ca, cb = sa["kind"] in CODE, sb["kind"] in CODE
        if ca == cb:
            continue
        if out and out[-1]["e"] == s and \
                out[-1]["ka"] == sa["kind"] and out[-1]["kb"] == sb["kind"]:
            out[-1]["e"] = e
        else:
            out.append(dict(s=s, e=e, ka=sa["kind"], kb=sb["kind"]))
    return out


def runs_identical(pa, pb):
    """Maximal byte-identical runs over the shared payload length. Returns a
    sorted-by-length list of (vram, length)."""
    n = min(len(pa), len(pb))
    runs, i = [], 0
    while i < n:
        if pa[i] == pb[i]:
            j = i
            while j < n and pa[j] == pb[j]:
                j += 1
            runs.append((BASE + i, j - i))
            i = j
        else:
            i += 1
    return runs


def asm_diff_flags(side, subsegs, pa, pb):
    """Ranges this build carves `asm` whose bytes differ from the counterpart
    payload. Returns (side, vram, size, ndiff, fraction) sorted by fraction."""
    n = min(len(pa), len(pb))
    out = []
    for sg in subsegs:
        if sg["kind"] != "asm":
            continue
        lo, hi = sg["s"] - BASE, min(sg["e"] - BASE, n)
        cnt = hi - lo
        if cnt < ASM_DIFF_MIN_BYTES:
            continue
        nd = sum(1 for i in range(lo, hi) if pa[i] != pb[i])
        if nd / cnt >= ASM_DIFF_THRESHOLD:
            out.append((side, sg["s"], cnt, nd, nd / cnt))
    out.sort(key=lambda r: -r[4])
    return out


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    as_json = "--json" in argv
    targets = args if len(args) == 2 else ALL
    img = {t: load(t) for t in targets}

    pairs = []
    for i in range(len(targets)):
        for j in range(i + 1, len(targets)):
            pairs.append((targets[i], targets[j]))

    report = dict(label_disagreements=[], byte_identical=[], asm_diff=[])
    for a, b in pairs:
        sa, pa = img[a]
        sb, pb = img[b]
        dis = label_disagreements(sa, sb)
        report["label_disagreements"].append(
            dict(a=a, b=b, count=len(dis), ranges=dis))

    # byte-level comparison only for matched JP/EU counterparts
    for a, b in MATCHED:
        if a not in img or b not in img:
            continue
        sa, pa = img[a]
        sb, pb = img[b]
        runs = runs_identical(pa, pb)
        bnd = boundaries(sa) | boundaries(sb)
        sub = [(v, L) for v, L in runs if L >= RUN_MIN]
        aligned = sum(1 for v, L in sub if v in bnd or (v + L) in bnd)
        flags = asm_diff_flags(a, sa, pa, pb) + asm_diff_flags(b, sb, pb, pa)
        report["byte_identical"].append(
            dict(a=a, b=b, runs=runs, aligned=aligned, substantial=len(sub),
                 total=sum(L for _, L in runs), compared=min(len(pa), len(pb))))
        report["asm_diff"].append(dict(a=a, b=b, flags=flags))

    if as_json:
        print(json.dumps(report, indent=1))
        return 0

    print("== cross-build carve audit: %d targets, %d pairs ==" %
          (len(targets), len(pairs)))
    for e in report["label_disagreements"]:
        a, b = e["a"], e["b"]
        print("\n-- %s(%s) vs %s(%s): %d code/data label disagreements --" %
              (a, region(a), b, region(b), e["count"]))
        for r in sorted(e["ranges"], key=lambda r: -(r["e"] - r["s"]))[:5]:
            print("   %#x-%#x %6dB  %s=%s  %s=%s" %
                  (r["s"], r["e"], r["e"] - r["s"], a, r["ka"], b, r["kb"]))

    print("\n== JP/EU byte comparison (matched counterparts) ==")
    for e in report["byte_identical"]:
        pct = 100.0 * e["total"] / e["compared"] if e["compared"] else 0.0
        print("\n-- %s vs %s: %d/%d bytes identical (%.1f%%), %d runs "
              "(>=%dB: %d), %d of those end on a carve boundary --" %
              (e["a"], e["b"], e["total"], e["compared"], pct, len(e["runs"]),
               RUN_MIN, e["substantial"], e["aligned"]))
        for v, L in sorted(e["runs"], key=lambda r: -r[1])[:5]:
            print("   identical %#x %6dB" % (v, L))
        print("   asm ranges differing from counterpart (>= %.0f%%):" %
              (100 * ASM_DIFF_THRESHOLD))
        fl = [f for f in report["asm_diff"]
              if f["a"] == e["a"] and f["b"] == e["b"]][0]["flags"]
        if not fl:
            print("      none")
        for side, v, cnt, nd, frac in fl[:5]:
            print("   %s %#x %6dB  %d/%d differ (%.0f%%)" %
                  (side, v, cnt, nd, cnt, 100 * frac))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

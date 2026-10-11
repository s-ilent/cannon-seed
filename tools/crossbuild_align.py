#!/usr/bin/env python3
"""crossbuild_align.py - align a JP/EU pair by shared unique k-mers, then ask
whether the two yaml carves agree once the images are aligned.

tools/crossbuild_diff.py compares a pair at a FIXED VRAM offset. Measured, that
signal is weak: the two images are index-shifted by insertions/deletions, so at
a fixed offset only ~16-24% of the shared payload is byte-identical and the
mean identical run is ~1.7 bytes. This tool drops the fixed-offset assumption.

Method:
  1. Hash every k-mer in both payloads (blake2b, k=32 by default).
  2. Keep k-mers that occur EXACTLY ONCE in their own payload. A k-mer unique
     on both sides is an anchor pair (a_off, b_off): same bytes, unambiguous.
  3. Sort anchors by a_off, take the longest strictly-increasing subsequence of
     b_off (patience, O(n log n)). The chain is the dominant diagonal - the
     monotonic correspondence between the two images.
  4. A maximal run of chain anchors with the SAME delta (b_off - a_off) is one
     COLLINEAR REGION: a 1:1 stretch. A change of delta between anchors is a
     GAP - bytes present on one side with no counterpart (inserted/removed).

Data is the baseline payload (file minus 0x800 header). Offsets below are
payload offsets; VRAM = 0x80020000 + payload offset. A gap's "delta before ->
after" is the local byte shift across it.

Limits, measured on the four same-program pairs (k=32):
  - At a fixed offset 15.7-23.8% of the shared payload is byte-identical. Inside
    the aligned regions 87.9-93.2% of bytes agree, so the shift model is real.
  - Anchors need a k-mer unique in BOTH payloads, so repetitive runs (zero fill,
    repeated tables/strings) give no anchors. That is why the chain brackets
    66-80% of each payload and not all of it.
  - Bracketed bytes are not proven equal: between two anchors a short local diff
    (< k) leaves both flanking unique k-mers intact. Coverage is an upper bound;
    the "identical inside aligned regions" line is the lower, measured bound.
  - The delta is piecewise constant, but a local diff changes it by a few bytes,
    producing a short region between two gaps. Short regions are real local
    diffs, not noise; they are why many carve boundaries land in a gap.
  - A boundary is corroborated only when it maps EXACTLY onto the other map's
    boundary (a mapped boundary within NEAR bytes is reported apart).
  - The chain is the dominant monotonic diagonal; it is not proof that a given
    anchor pair is the same code, only that the surrounding shift is consistent.

Usage: python3 tools/crossbuild_align.py [--k N] [--json] [A B]
       (default: the four same-program pairs; A B selects one)
"""
import bisect
import hashlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASE = 0x80020000
HDR = 0x800
K = 32
NEAR = 8  # bytes: mapped boundary this close to a real one is a near miss
MATCHED = [("slps_00270", "sces_00269"), ("mainmenu_jp", "mainmenu_eu"),
           ("g3_jp", "g3_eu"), ("g3org_jp", "g3org_eu")]


def load_payload(target):
    """Payload bytes: the baseline file minus its 0x800 PS-X EXE header."""
    return (REPO / "baselines" / f"{target}.bin").read_bytes()[HDR:]


def load_boundaries(target):
    """Every subsegment start/end from the committed yaml, as payload offsets.
    yaml OFFSET is a file offset: payload_off = OFFSET - 0x800."""
    bnd, subsegs = set(), []
    txt = (REPO / "config" / f"splat.{target}.yaml").read_text().splitlines()
    for ln in txt:
        m = re.match(r"\s*-\s*\[(0x[0-9A-Fa-f]+),\s*(asm|c|data),\s*(\w+)\]"
                     r"\s*#\s*(0x[0-9A-Fa-f]+)", ln)
        if not m:
            continue
        off = int(m.group(1), 16) - HDR
        size = int(m.group(4), 16)
        bnd.add(off)
        bnd.add(off + size)
        subsegs.append((off, off + size, m.group(2)))
    return sorted(b for b in bnd if b >= 0), subsegs


def kmer_positions(payload, k):
    """Map blake2b(k-mer) -> position if it occurs exactly once, else -1."""
    n = len(payload) - k + 1
    pos = {}
    if n <= 0:
        return pos
    for i in range(n):
        h = hashlib.blake2b(payload[i:i + k], digest_size=16).digest()
        if h in pos:
            pos[h] = -1
        else:
            pos[h] = i
    return pos


def anchors(pa, pb, k):
    """Anchor pairs from k-mers unique in each payload, sorted by A offset."""
    ma, mb = kmer_positions(pa, k), kmer_positions(pb, k)
    out = []
    for h, a in ma.items():
        if a < 0:
            continue
        b = mb.get(h)
        if b is not None and b >= 0:
            out.append((a, b))
    out.sort()
    return out


def lis_chain(anchors_ab):
    """Longest strictly-increasing-by-B subsequence of anchors sorted by A.
    Patience sort with predecessor links: O(n log n)."""
    tails_val, tails_idx, prev = [], [], [-1] * len(anchors_ab)
    for i, (a, b) in enumerate(anchors_ab):
        j = bisect.bisect_left(tails_val, b)
        if j == len(tails_val):
            tails_val.append(b)
            tails_idx.append(i)
        else:
            tails_val[j] = b
            tails_idx[j] = i
        prev[i] = tails_idx[j - 1] if j > 0 else -1
    chain, i = [], (tails_idx[-1] if tails_idx else -1)
    while i != -1:
        chain.append(anchors_ab[i])
        i = prev[i]
    chain.reverse()
    return chain


def regions_and_gaps(chain):
    """Maximal same-delta runs (collinear regions) and the delta changes
    (gaps) between them. Each region carries a0,a1,b0,b1,delta."""
    regions = []
    if not chain:
        return regions, []
    cur = dict(a0=chain[0][0], b0=chain[0][1], delta=chain[0][1] - chain[0][0],
               a1=chain[0][0], b1=chain[0][1])
    for a, b in chain[1:]:
        d = b - a
        if d == cur["delta"]:
            cur["a1"], cur["b1"] = a, b
        else:
            regions.append(cur)
            cur = dict(a0=a, b0=b, delta=d, a1=a, b1=b)
    regions.append(cur)
    gaps = []
    for i in range(1, len(regions)):
        p, q = regions[i - 1], regions[i]
        gaps.append(dict(a0=p["a1"], a1=q["a0"], b0=p["b1"], b1=q["b0"],
                         la=q["a0"] - p["a1"], lb=q["b0"] - p["b1"],
                         before=p["delta"], after=q["delta"]))
    return regions, gaps


def coverage(regions, k):
    """Bytes covered by the chain: interval union of [x0, x1+k) per region for
    the A and B sides. +k counts the k-mer anchored at the region's last
    position. Overlaps from short gaps are merged."""
    def span(lo_key, hi_key):
        iv = sorted((r[lo_key], r[hi_key] + k) for r in regions)
        total, cur = 0, -1
        for s, e in iv:
            s = max(s, cur)
            if e > s:
                total += e - s
                cur = e
        return total
    return span("a0", "a1"), span("b0", "b1")


def map_offset(x, regions, side, k):
    """Map a payload offset through the collinear region holding it. side 'a'
    maps an A offset forward (x + delta); side 'b' maps a B offset back
    (x - delta). The region spans [x0, x1+k) so the trailing k-mer is included.
    Returns None in a gap (no single-delta region covers the offset)."""
    hit = None
    for r in regions:
        if side == "a":
            if r["a0"] <= x < r["a1"] + k:
                hit = r
        else:
            if r["b0"] <= x < r["b1"] + k:
                hit = r
    if hit is None:
        return None
    return x + hit["delta"] if side == "a" else x - hit["delta"]


def nearest(bnds, x):
    """Distance from x to the closest boundary in a sorted list."""
    if not bnds:
        return None, None
    j = bisect.bisect_left(bnds, x)
    best = None
    for cand in (bnds[j] if j < len(bnds) else None,
                 bnds[j - 1] if j > 0 else None):
        if cand is None:
            continue
        d = abs(cand - x)
        if best is None or d < best[0]:
            best = (d, cand)
    return best


def boundary_agreement(regions, bnd_a, bnd_b, k):
    """Map A's carve boundaries forward into B and classify each against B's
    boundary set: exact (d==0), near (d<=NEAR), or off. Then the reverse."""
    def run(src, dst, side):
        exact = near = off = unmapped = 0
        rows = []
        for x in src:
            y = map_offset(x, regions, side, k)
            if y is None:
                unmapped += 1
                rows.append(dict(x=x, y=None, d=None))
                continue
            d, nb = nearest(dst, y)
            if d == 0:
                exact += 1
            elif d <= NEAR:
                near += 1
            else:
                off += 1
            rows.append(dict(x=x, y=y, d=d, nearest=nb))
        return dict(exact=exact, near=near, off=off, unmapped=unmapped,
                    total=len(src), rows=rows)
    return run(bnd_a, bnd_b, "a"), run(bnd_b, bnd_a, "b")


def region_identity(pa, pb, regions):
    """Bytes proven identical inside the collinear regions (region interior,
    no +k tail). This is the honest 'alignment matched this much' number:
    coverage brackets bytes, this counts the ones that actually agree."""
    ident = 0
    for r in regions:
        lo, hi = r["a0"], r["a1"]
        ca, cb = pa[lo:hi], pb[r["b0"]:r["b0"] + (hi - lo)]
        ident += sum(1 for i in range(len(ca)) if ca[i] == cb[i])
    return ident


def kind_at(subsegs, off):
    for s, e, kind in subsegs:
        if s <= off < e:
            return kind
    return None


def kind_agreement(regions, subs_a, subs_b, k):
    """Of the A boundaries that map into B, how many land in a B subsegment of
    the same code/data class as the A subsegment holding them."""
    agree = disagree = 0
    for x in [b for b in sorted({s for s, _, _ in subs_a} |
                                {e for _, e, _ in subs_a})]:
        y = map_offset(x, regions, "a", k)
        if y is None:
            continue
        ka, kb = kind_at(subs_a, x), kind_at(subs_b, y)
        if ka is None or kb is None:
            continue
        if (ka in ("asm", "c")) == (kb in ("asm", "c")):
            agree += 1
        else:
            disagree += 1
    return agree, disagree


def analyze(a, b, k):
    pa, pb = load_payload(a), load_payload(b)
    anc = anchors(pa, pb, k)
    chain = lis_chain(anc)
    regs, gaps = regions_and_gaps(chain)
    cov_a, cov_b = coverage(regs, k)
    ident = region_identity(pa, pb, regs)
    bnd_a, subs_a = load_boundaries(a)
    bnd_b, subs_b = load_boundaries(b)
    fa, rb = boundary_agreement(regs, bnd_a, bnd_b, k)
    ka, kd = kind_agreement(regs, subs_a, subs_b, k)
    return dict(a=a, b=b, k=k, len_a=len(pa), len_b=len(pb),
                anchors=len(anc), chain=len(chain), regions=regs, gaps=gaps,
                cov_a=cov_a, cov_b=cov_b, ident=ident,
                bnd_a=len(bnd_a), bnd_b=len(bnd_b), kind_agree=ka,
                kind_disagree=kd, a_to_b=fa, b_to_a=rb)


def fmt_pct(x, n):
    return 100.0 * x / n if n else 0.0


def emit(r):
    a, b = r["a"], r["b"]
    print(f"\n===== {a} (A) vs {b} (B), k={r['k']} =====")
    print(f"  payload: A {r['len_a']:,} B {r['len_b']:,} bytes")
    print(f"  anchors (k-mers unique on both sides): {r['anchors']:,}")
    pct_chain = 100.0 * r["chain"] / r["anchors"] if r["anchors"] else 0.0
    print(f"  monotonic chain length:                {r['chain']:,} "
          f"({pct_chain:.0f}% of anchors)")
    print(f"  collinear regions: {len(r['regions'])}  "
          f"gaps (delta changes): {len(r['gaps'])}")
    print(f"  chain-bracketed bytes: A {r['cov_a']:,} "
          f"({fmt_pct(r['cov_a'], r['len_a']):.1f}%)  "
          f"B {r['cov_b']:,} ({fmt_pct(r['cov_b'], r['len_b']):.1f}%)")
    print(f"  identical inside aligned regions: {r['ident']:,} "
          f"({fmt_pct(r['ident'], r['len_a']):.1f}% of A payload)")

    regs = sorted(r["regions"], key=lambda x: -(x["a1"] - x["a0"]))
    print("  largest collinear regions (A offset -> B offset, delta):")
    for x in regs[:5]:
        print(f"    {x['a0']:#08x}-{x['a1']:#08x} "
              f"({x['a1']-x['a0']:,}B) -> {x['b0']:#08x}-{x['b1']:#08x} "
              f"delta {x['delta']:+#x}")

    gaps = sorted(r["gaps"], key=lambda g: -max(g["la"], g["lb"]))
    print("  largest gaps (delta before -> after; net shift):")
    for g in gaps[:5]:
        net = g["lb"] - g["la"]
        side = "B inserts" if net > 0 else ("A inserts" if net < 0 else "shift")
        print(f"    A {g['a0']:#08x}-{g['a1']:#08x} ({g['la']:,}B)  "
              f"B {g['b0']:#08x}-{g['b1']:#08x} ({g['lb']:,}B)  "
              f"delta {g['before']:+#x} -> {g['after']:+#x}  ({side} {net:+,}B)")

    for tag, e in (("A->B", r["a_to_b"]), ("B->A", r["b_to_a"])):
        mappable = e["total"] - e["unmapped"]
        print(f"  boundaries {tag}: {e['total']} total, {mappable} mappable  "
              f"exact {e['exact']} ({fmt_pct(e['exact'], mappable):.0f}% of "
              f"mappable), near {e['near']}, off {e['off']}, "
              f"in-gap {e['unmapped']}")
    ka, kd = r["kind_agree"], r["kind_disagree"]
    print(f"  code/data class agrees at mapped A boundaries: {ka} vs "
          f"{kd} disagree ({fmt_pct(ka, ka + kd):.0f}% agree)")
    # strongest counterexamples: mapped boundaries far from any counterpart
    off_rows = [x for x in r["a_to_b"]["rows"] if x["d"] and x["d"] > NEAR]
    off_rows.sort(key=lambda x: -x["d"])
    if off_rows:
        print("  strongest carve disagreements (A boundary -> mapped B vs "
              "nearest B boundary):")
        for x in off_rows[:3]:
            print(f"    A {x['x']:#08x} -> B {x['y']:#08x}, nearest B "
                  f"{x['nearest']:#08x} (off {x['d']:,}B)")


def main(argv):
    args = [t for t in argv[1:] if not t.startswith("-")]
    as_json = "--json" in argv
    k = K
    for i, t in enumerate(argv):
        if t == "--k":
            k = int(argv[i + 1])
    pairs = [(args[0], args[1])] if len(args) == 2 else MATCHED
    reports = [analyze(a, b, k) for a, b in pairs]
    if as_json:
        print(json.dumps([{x: r[x] for x in
                           ("a", "b", "k", "len_a", "len_b", "anchors",
                            "chain", "cov_a", "cov_b", "ident", "bnd_a",
                            "bnd_b", "kind_agree", "kind_disagree", "a_to_b",
                            "b_to_a", "regions", "gaps")}
                          for r in reports], indent=1))
        return 0
    for r in reports:
        emit(r)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

#!/usr/bin/env python3
"""audit_eu_twins.py — find the g3_eu twins of g3_jp probe windows by
normalized word-sequence alignment (read-only, exit 0).

Born from the R1 pass-19 EU twin check (docs/research/
G3_MUSIC_LANE_EU_TWINS_20261126.md). The EU and JP images carve the same
code at different addresses and with different row seams, so a twin is
matched on NORMALIZED instruction words: j/jal targets, branch offsets and
lui/addiu/ori immediates are allowed to shift (regions differ in data
bases), everything else must match exactly. A candidate scores
1.0 per exact word and 0.5 per immediate-only divergence over the aligned
window; the report prints every candidate at >=0.55 so a human reads the
decisive ones rather than trusting the score alone.

Both streams are vram-sorted and de-duplicated before alignment: the .s
row files tile the whole image, so consecutive stream entries are
consecutive vram. Alignment still breaks at EU carve seams that fall
inside a JP probe window (the EU image interleaves other functions
between JP-adjacent chunks) — a MISS there is a carve artifact, not
evidence of absence; the pass-19 note records which probes needed a hand
read instead.

The default probe table is the pass-19 music-lane map with the VERIFIED
EU twin addresses annotated (they reproduce the note's table); replace
or extend with --add NAME=0xSTART:0xEND.

Usage:
  python3 tools/audit_eu_twins.py
  python3 tools/audit_eu_twins.py --add myName=0x80012345:0x80012400

Exit 0 always (convention: tools/audit_c_names.py).
"""
import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INSN_RE = re.compile(
    r"/\*\s*([0-9A-Fa-f]{4,5})\s+([0-9A-Fa-f]{8})\s+([0-9A-Fa-f]{8})\s*\*/\s*(.*)$")

# The R1 pass-19 music-lane probe map (g3_jp true-space windows) with the
# verified EU twins from the note's table (None = not re-derived there).
DEFAULT_PROBES = {
    "func_800299D8_sched":      (0x800299D8, 0x80029B20, 0x800299D4),
    "func_8002FFB8_driver2":    (0x8002FFB8, 0x8003002C, 0x8002FC48),
    "func_8002FF48_driver1":    (0x8002FF48, 0x8002FFB8, 0x8002FBD8),
    "func_800276B8_tick1":      (0x800276B8, 0x80027780, 0x800276B4),
    "func_800270E8_tick2":      (0x800270E8, 0x80027230, 0x800270E4),
    "func_80026B64_init":       (0x80026B64, 0x80026D6C, None),
    "func_80026D6C_binding":    (0x80026D6C, 0x8002704C, 0x80026D68),
    "func_80029840_dispatch":   (0x80029840, 0x800299D8, 0x8002983C),
    "func_8002945C_eval":       (0x8002945C, 0x800295D8, 0x80029458),
    "func_800295E0_ramp8":      (0x800295E0, 0x80029738, 0x800295DC),
    "func_80029738_ramp2":      (0x80029738, 0x80029840, None),
    "func_800279CC_snapshot":   (0x800279CC, 0x80027BCC, 0x800279C8),
    "func_8002704C_steal":      (0x8002704C, 0x800276B8, None),
    "func_80026718_t1cons":     (0x80026718, 0x80026A80, 0x800266F4),
    "func_80026A80_scene":      (0x80026A80, 0x80026B64, 0x80026A5C),
    "func_8002343C_orch":       (0x8002343C, 0x800236F8, 0x8002349C),
    "func_800236F8_t2cons":     (0x800236F8, 0x80023D78, 0x80023758),
    "func_8002FC68_frame":      (0x8002FC68, 0x8002FF48, 0x8002F8F8),
    "func_80022FE4_sceneupd":   (0x80022FE4, 0x800232D0, None),
    "func_80024224_chain1":     (0x80024224, 0x800242DC, None),
    "func_80023DCC_chain2":     (0x80023DCC, 0x80024224, 0x80023E2C),
    "func_80042C6C_dispatcher": (0x80042C6C, 0x80042D84, None),
}

PROBE_CAP = 64


def load_module(dirpath):
    """[(vram, word)] sorted, de-duplicated, plus a vram -> (file, line) map."""
    rows = []
    meta = {}
    files = []
    for dp, _, fns in os.walk(dirpath):
        for fn in sorted(fns):
            if fn.endswith(".s"):
                files.append(os.path.join(dp, fn))
    for fp in sorted(files):
        rel = os.path.relpath(fp, ROOT)
        with open(fp, "r", errors="replace") as fh:
            for lineno, raw in enumerate(fh, 1):
                m = INSN_RE.search(raw)
                if not m:
                    continue
                rest = m.group(4).strip()
                if not rest or rest.startswith("#"):
                    continue
                v = int(m.group(2), 16)
                meta.setdefault(v, (rel, lineno))
                rows.append((v, int(m.group(3), 16)))
    rows = sorted(set(rows))
    return rows, meta


def norm(word):
    """One instruction word -> (reg/op fields, immediate_or_None)."""
    op = (word >> 26) & 0x3F
    if op in (0x02, 0x03):                     # j/jal: target shifts
        return (op << 26), None
    if op in (0x04, 0x05, 0x06, 0x07, 0x01):   # branches: offset shifts
        return ((word >> 16) << 16), None
    if op in (0x0F, 0x09, 0x0D):               # lui/addiu/ori: imm may shift
        return ((word >> 16) << 16), (word & 0xFFFF)
    return word, None


def pair_score(a_words, b_words):
    n = min(len(a_words), len(b_words))
    if n == 0:
        return 0.0
    total = 0.0
    for x, y in zip(a_words[:n], b_words[:n]):
        fx, ix = norm(x)
        fy, iy = norm(y)
        if fx == fy:
            total += 1.0 if (ix is None or ix == iy) else 0.5
    return total / n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jp", default="g3_jp")
    ap.add_argument("--eu", default="g3_eu")
    ap.add_argument("--add", action="append", default=[],
                    help="extra probe NAME=0xSTART:0xEND")
    ap.add_argument("--min-score", type=float, default=0.55)
    args = ap.parse_args()

    probes = {k: (v[0], v[1]) for k, v in DEFAULT_PROBES.items()}
    for spec in args.add:
        name, _, rng = spec.partition("=")
        start_s, _, end_s = rng.partition(":")
        probes[name.strip()] = (int(start_s, 16), int(end_s, 16))

    jp_dir = os.path.join(ROOT, "asm", args.jp, "nonmatchings")
    eu_dir = os.path.join(ROOT, "asm", args.eu, "nonmatchings")
    if not (os.path.isdir(jp_dir) and os.path.isdir(eu_dir)):
        print("audit_eu_twins: missing module dirs %s / %s" % (jp_dir, eu_dir))
        return 0

    jp, _ = load_module(jp_dir)
    eu, eu_meta = load_module(eu_dir)
    print("=== audit_eu_twins (read-only) ===")
    print("module %s -> %s: %d JP insns, %d EU insns, probes: %d"
          % (args.jp, args.eu, len(jp), len(eu), len(probes)))

    for name in sorted(probes):
        va, va_end = probes[name]
        body = [(v, w) for (v, w) in jp if va <= v < va_end][:PROBE_CAP]
        if len(body) < 4:
            print("\n[%s @0x%08X] probe too short (%d insns in [0x%08X,0x%08X))"
                  % (name, va, len(body), va, va_end))
            continue
        lead = [norm(w)[0] for _, w in body[:6]]
        lead0 = lead[0]
        hits = []
        for idx, (vram, word) in enumerate(eu):
            if norm(word)[0] != lead0:
                continue
            seq = eu[idx:idx + len(body)]
            if len(seq) < 6 or [norm(w)[0] for _, w in seq[:6]] != lead:
                continue
            score = pair_score([w for _, w in body], [w for _, w in seq])
            if score >= args.min_score:
                hits.append((score, idx, seq[-1][0]))
        hits.sort(reverse=True)
        recorded = DEFAULT_PROBES.get(name, (None, None, None))[2]
        note = ("  note: verified EU twin 0x%08X (pass-19 table)" % recorded) \
            if recorded else ""
        if hits:
            score, idx, vend = hits[0]
            v0 = eu[idx][0]
            rel, lineno = eu_meta.get(v0, ("?", 0))
            print("\n[TWIN] %s (JP 0x%08X, %d insns) -> EU 0x%08X..0x%08X (%s:%d) score %.3f%s"
                  % (name, va, len(body), v0, vend, rel, lineno, score, note))
            for score2, idx2, vend2 in hits[1:3]:
                v2 = eu[idx2][0]
                r2, l2 = eu_meta.get(v2, ("?", 0))
                print("   alt: EU 0x%08X (%s:%d) score %.3f" % (v2, r2, l2, score2))
        else:
            print("\n[MISS] %s (JP 0x%08X): no >=%.2f EU twin of the %d-insn probe (carve-seam break is a known artifact)%s"
                  % (name, va, args.min_score, len(body), note))
    return 0


if __name__ == "__main__":
    sys.exit(main())

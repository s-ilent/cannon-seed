#!/usr/bin/env python3
"""sibling_finder.py - locate recompiled twins of a landed unit elsewhere.

A landed unit (yaml `c` subsegment, verified against the oracle) proves one
compilation of a function family. The same source compiled into another
chained executable - or the same SDK function linked by a different Psy-Q
drop - selects different instructions (the parked color war: `lwc2` vs
`mtc2`), so byte matching cannot find the twins. Byte matching also cannot
see twins that sit inside `data` islands, because nothing scans them.

This tool takes the landed unit's bytes as a query and slides it over the
OTHER targets by structure, not bytes:

  1. anchor: rare aligned words of the query (rarest-first, capped) are
     located in the target payload; each hit proposes a word-aligned
     candidate start;
  2. score: both sides are disassembled word by word (capstone, lazy) and
     compared as token streams with registers masked - mnemonic sequence
     (difflib ratio), immediate-operand overlap, and literal-pool / GTE
     constant overlap;
  3. annotate: every hit above --min-score is placed in its yaml
     subsegment (is it a data island? an unlabeled asm row? already
     landed?) and checked against the SDK reports.

A proposal is a carve candidate for the landing queue, never evidence on
its own: acceptance stays `make verify`.

Usage (capstone lives in the toolchain venv, so $PY is the venv python):

    $PY tools/sibling_finder.py --src slps_00270 --at 0x800588A0 --size 0x8C
    $PY tools/sibling_finder.py --src mainmenu_eu --at 0x8006FCFC \
        --size 0x8C --min-score 0.70 --target g3_eu --target g3org_eu
"""
import argparse
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sdk_members as sm  # noqa: E402  (load_target, subsegment_kinds, ...)

REPO = sm.REPO
_NUM = re.compile(r"-?(?:0x[0-9a-f]+|\d+)")


def words(buf):
    return [int.from_bytes(buf[i:i + 4], "little")
            for i in range(0, len(buf) - 3, 4)]


def pick_needles(query, payload, want=8, max_count=64):
    """Rarest aligned query words that also occur in the payload."""
    hist = {}
    for w in words(payload):
        hist[w] = hist.get(w, 0) + 1
    cand = []
    for i, w in enumerate(words(query)):
        c = hist.get(w, 0)
        if 0 < c <= max_count and (w & 0xFFFF) or (w >> 16):
            cand.append((c, i, w))
    cand.sort()
    return cand[:want]


def candidate_starts(query, payload, needles):
    """Word-aligned starts proposed by needle hits, with needle support."""
    starts = {}
    for _c, qi, w in needles:
        wb = w.to_bytes(4, "little")
        pos = payload.find(wb)
        while pos != -1:
            if not pos & 3:
                starts.setdefault(pos - 4 * qi, set()).add(w)
            pos = payload.find(wb, pos + 1)
    return starts


def disasm_tokens(buf, base=0):
    """(mnemonic tokens, immediates, literal words) for a word stream.

    capstone is imported lazily so the offline test suite can import this
    module without the venv. Undecodable words (GTE cop2 data, literal
    pools) become token 'W' and keep their value in the word set.
    """
    import capstone
    md = capstone.Cs(capstone.CS_ARCH_MIPS,
                     capstone.CS_MODE_MIPS32 | capstone.CS_MODE_LITTLE_ENDIAN)
    mnems, imms, ws = [], [], []
    for i in range(0, len(buf) - 3, 4):
        raw = buf[i:i + 4]
        got = list(md.disasm(raw, base + i))
        if not got:
            mnems.append("W")
            ws.append(int.from_bytes(raw, "little"))
            continue
        ins = got[0]
        mnems.append(ins.mnemonic)
        for t in _NUM.findall(ins.op_str):
            try:
                imms.append(int(t, 0))
            except ValueError:
                pass
    return mnems, imms, ws


def score(query, cand):
    """Structural similarity of two (mnems, imms, words) triples."""
    qm, qi, qw = query
    cm, ci, cw = cand
    ratio = SequenceMatcher(None, qm, cm).ratio()
    parts = [0.6 * ratio]
    weight = 0.4
    if qw:
        hit = sum(1 for w in qw if w in cw)
        parts.append(weight * 0.5 * (hit / len(qw)))
        weight -= weight * 0.5
    if qi:
        cset = set(ci)
        hit = sum(1 for v in qi if v in cset)
        parts.append(weight * (hit / len(qi)))
    return sum(parts)


def region_of(target_kinds, addr):
    name = ""
    for start, k, n in target_kinds:
        if start <= addr:
            name = f"{k}:{n}"
    return name


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="target the query bytes come from")
    ap.add_argument("--at", required=True, help="VRAM address of the query unit")
    ap.add_argument("--size", required=True, help="query size in bytes")
    ap.add_argument("--target", action="append", default=None,
                    help="search only these targets (default: all but --src)")
    ap.add_argument("--min-score", type=float, default=0.75)
    ap.add_argument("--max-hits", type=int, default=6,
                    help="best N hits reported per target")
    args = ap.parse_args(argv[1:])

    loaded = sm.load_target(args.src)
    if not loaded:
        print(f"sibling_finder: no baseline image for {args.src}", file=sys.stderr)
        return 1
    payload, lo, vram = loaded
    src_anchors = sm.yaml_anchors(args.src)
    qoff = sm.name_to_raw(int(args.at, 0), src_anchors)
    if qoff is None or qoff < 0:
        print(f"sibling_finder: cannot map {args.at} through the yaml names",
              file=sys.stderr)
        return 1
    qsize = int(args.size, 0)
    query = payload[qoff:qoff + qsize]
    qtok = disasm_tokens(query)
    print(f"query {args.src} {args.at} (raw {qoff:#x}) +{qsize:#x}: "
          f"{len(words(query))} words, {len(qtok[2])} undecoded")

    targets = args.target or [p.name[len("splat."):-len(".yaml")]
                              for p in sorted((REPO / "config").glob("splat.*.yaml"))
                              if p.name[len("splat."):-len(".yaml")] != args.src]
    for t in targets:
        loaded = sm.load_target(t)
        if not loaded:
            continue
        tpayload, tlo, tvram = loaded
        anchors = sm.yaml_anchors(t)
        needles = pick_needles(query, tpayload)
        starts = candidate_starts(query, tpayload, needles)
        if not starts:
            print(f"{t:<12} no anchors (query constants absent)")
            continue
        hits = []
        slack = qsize + 0x40
        for s, support in starts.items():
            if s < 0:
                continue
            ctok = disasm_tokens(tpayload[s:s + slack])
            n = len(qtok[0])
            if len(ctok[0]) < n // 2:
                continue
            # score exactly as many instructions as the query has: extra
            # tail bytes are slack, not signal
            ctok = (ctok[0][:n], ctok[1], ctok[2])
            sc = score(qtok, ctok)
            if sc >= args.min_score:
                hits.append((sc, s, len(support)))
        hits.sort(reverse=True)
        # collapse hits inside one unit of each other, keep the best
        kept = []
        for sc, s, sup in hits:
            if kept and any(abs(s - o) < qsize // 2 for _s, o, _u in kept):
                continue
            kept.append((sc, s, sup))
        if not kept:
            print(f"{t:<12} {len(starts):>4} candidates, none >= {args.min_score}")
            continue
        kinds = sm.subsegment_kinds(t)
        known = sm.known_addresses(t)   # raw offsets
        cstarts = set()
        for off, kind, _n, nv in sm.yaml_anchors(t, with_kind=True):
            if kind == "c":
                cstarts.add(off)
        print(f"{t:<12} {len(starts):>4} candidates, {len(kept)} >= {args.min_score}:")
        for sc, s, sup in kept[:args.max_hits]:
            addr = sm.raw_to_name(s, anchors)
            reg = region_of(kinds, addr)
            note = []
            if s in cstarts:
                note.append("landed")
            if s in known:
                note.append("sdk-report")
            print(f"    {addr:#010x}  {sc:.2f}  {reg:<28}"
                  f"{'  ' + ','.join(note) if note else ''}  ({sup} anchors)")


if __name__ == "__main__":
    sys.exit(main(sys.argv))

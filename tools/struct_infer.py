#!/usr/bin/env python3
"""struct_infer.py - propose structure layouts from memory-access evidence.

Read-only. Parses the committed spimdisasm output under asm/ and infers
which registers act as struct pointers, then proposes a field map per
(function, base register) cluster. Nothing here writes files or needs a
build.

What the input covers
---------------------
Only the CARVED, still-NON-MATCHING functions live under
asm/<target>/nonmatchings/**.s (slps_00270 is the exception: its splat
asm_path is asm/nonmatchings). This is a PARTIAL slice of each target:
measured here, 115-367 .s files and ~830-2330 glabel blocks per target,
against a full image far larger. The carve grows as functions get
matched and move back into src/. So:

  * a cluster seen here is evidence of a struct, not proof of its extent;
  * a struct whose only reader is already matched does NOT appear;
  * absence of an offset is not evidence the field is absent;
  * field maps are lower bounds on the true layout.

Clustering by (function, base register) assumes one register holds one
pointer for the life of a cluster. This is wrong when a register is
reused for two different objects in one function, and when a register
holds an intermediate loaded pointer rather than the struct base. Both
cases merge or split clusters; the register-class tag (arg / saved /
temp) is printed so the reader can weigh each one.

Signedness note: the target is built -funsigned-char, so `lb` (signed)
is the minority form. `lb`/`lh` sites are the sharpest signal that a
field is a signed type (s8/s16); `lbu`/`lhu` are the unsigned default.

Scope: only the aligned scalar forms lw/lh/lhu/lb/lbu/sw/sh/sb are
collected. The carve also contains lwl/lwr/swl/swr (unaligned 4-byte),
ld/sd, and lwc2/swc2 (GTE transfers); those are real but are not field
reads of the kind this tool maps, so they are excluded rather than
misread as struct offsets.

Measured limit - embedded data. Some carved "functions" are data islands
spimdisasm decoded as code (e.g. a long run of `lb $a2,-0x300C($zero)`).
Lines inside a run of >= 4 identical non-nop encodings are dropped, and
$zero-base accesses are dropped (they reach no mapped object). These
filters are what keep the signed-byte census honest; unfiltered counts
are inflated several-fold on the G3 targets.

Usage:
  python3 tools/struct_infer.py                 # all targets
  python3 tools/struct_infer.py --target g3_jp  # one target
  python3 tools/struct_infer.py --min-fields 3  # only richer clusters
  python3 tools/struct_infer.py --json
"""
import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Order JP then EU, matching the naming in the carve.
TARGETS = ["slps_00270", "mainmenu_jp", "g3_jp", "g3org_jp",
           "sces_00269", "mainmenu_eu", "g3_eu", "g3org_eu"]

# op -> (width_bytes, signedness: "s"|"u"|None). Stores carry no sign.
OPS = {"lw": (4, None), "lh": (2, "s"), "lhu": (2, "u"),
       "lb": (1, "s"), "lbu": (1, "u"),
       "sw": (4, None), "sh": (2, None), "sb": (1, None)}

OFFSET = (r'(?:-?0x[0-9a-fA-F]+|-?[0-9]+'
          r'|%gp_rel\([^)]*\)|%lo\([^)]*\)|%hi\([^)]*\))')
# `lw $v0, 0x4($s2)` / `sw $v0, %gp_rel(D_...)($gp)` are the shapes
# collected. lwl/lwr/swl/swr, ld/sd and lwc2/swc2 exist in the carve but
# are out of scope (see docstring).
MEM = re.compile(r'\b(lw|lhu|lbu|lh|lb|sw|sh|sb)\s+\$([a-z0-9]+)\s*,'
                 r'\s*(' + OFFSET + r')\s*\(\s*\$([a-z0-9]+)\s*\)')
GLABEL = re.compile(r'^\s*glabel\s+(\S+)')
COMMENT = re.compile(r'/\*.*?\*/')

# a0-a3 are pointer args; s0-s7 are callee-saved (often a loaded base);
# v0/v1/t* are temporaries, so a "cluster" there is likelier an alias.
REG_CLASS = {}
for _r in ("a0", "a1", "a2", "a3"):
    REG_CLASS[_r] = "arg"
for _r in ("s0", "s1", "s2", "s3", "s4", "s5", "s6", "s7", "fp"):
    REG_CLASS[_r] = "saved"


def reg_class(r):
    return REG_CLASS.get(r, "temp")


def hoff(o):
    """Format a byte offset, signed."""
    if isinstance(o, int):
        return f"-0x{-o:x}" if o < 0 else f"+0x{o:x}"
    return f"+{o}"


def asm_dir(target):
    d = REPO / "asm" / target / "nonmatchings"
    if d.is_dir():
        return d
    # slps_00270's splat asm_path is asm/nonmatchings (no target dir).
    d = REPO / "asm" / "nonmatchings"
    return d if target == "slps_00270" and d.is_dir() else None


def parse_offset(tok):
    """Return ('imm', int) | ('gp'|'lo'|'hi', symbol)."""
    low = tok.lower()
    if low.startswith("%gp_rel"):
        return ("gp", tok[8:-1])
    if low.startswith("%lo"):
        return ("lo", tok[4:-1])
    if low.startswith("%hi"):
        return ("hi", tok[4:-1])
    return ("imm", int(tok, 16) if "x" in low else int(tok, 10))


ENC = re.compile(r'/\*\s*[0-9A-Fa-f]+\s+[0-9A-Fa-f]+\s+'
                 r'([0-9A-Fa-f]{8})\s*\*/')
NOP_ENC = "00000000"
DATA_RUN = 4  # >= this many identical non-nop words == embedded data


def iter_blocks(path):
    """Yield (func, lines) for each glabel block in a file."""
    func, buf = None, []
    for line in path.read_text(errors="replace").splitlines():
        m = GLABEL.match(line)
        if m:
            if func is not None:
                yield func, buf
            func, buf = m.group(1), []
        elif func is not None:
            buf.append(line)
    if func is not None:
        yield func, buf


def data_mask(buf):
    """Mark lines inside a run of >= DATA_RUN identical non-nop encodings.

    spimdisasm decodes embedded data islands as instructions when the
    carve misclassified them as code; the giveaway is a run of identical
    words (e.g. a repeating `lb $a2,-0x300C($zero)`). Such lines are not
    real accesses and must not seed a struct cluster.
    """
    encs = []
    for ln in buf:
        m = ENC.search(ln)
        encs.append(m.group(1) if m else None)
    mask = [False] * len(buf)
    i = 0
    while i < len(encs):
        e = encs[i]
        if e is None or e == NOP_ENC:
            i += 1
            continue
        j = i + 1
        while j < len(encs) and encs[j] == e:
            j += 1
        if j - i >= DATA_RUN:
            for k in range(i, j):
                mask[k] = True
        i = j
    return mask


def scan(target):
    """Parse one target's asm tree.

    Returns a dict with clusters ((func, base) -> {off: rec}), gp/lo
    symbol tallies, a per-opcode census, the lb sites, and counts of the
    lines rejected as data or $zero-base artifacts. Data islands and
    $zero-base accesses are dropped because neither is a struct access:
    the first is misdecoded bytes, the second reaches no mapped object.
    """
    d = asm_dir(target)
    res = dict(clusters=defaultdict(lambda: defaultdict(
                   lambda: dict(widths=set(), signs=set(), ops=set(),
                                reads=0, writes=0))),
               gp=defaultdict(int), lo=defaultdict(int),
               ops=defaultdict(int), lb_sites=[],
               filtered=0, zero_base=0, files=0, funcs=0)
    if d is None:
        return res
    for path in sorted(d.rglob("*.s")):
        res["files"] += 1
        for func, buf in iter_blocks(path):
            res["funcs"] += 1
            mask = data_mask(buf)
            for idx, line in enumerate(buf):
                m = MEM.search(COMMENT.sub(" ", line))
                if not m:
                    continue
                if mask[idx]:
                    res["filtered"] += 1
                    continue
                op, otok, base = m.group(1), m.group(3), m.group(4)
                if base == "zero":
                    res["zero_base"] += 1
                    continue
                width, sign = OPS[op]
                kind, off = parse_offset(otok)
                res["ops"][op] += 1
                if op in ("lb", "lbu", "lh", "lhu"):
                    cls = "gp" if (kind == "gp" or base == "gp") else \
                          ("abs" if (base == "at" or kind in ("lo", "hi"))
                           else ("stack" if base == "sp" else "ptr"))
                    if op == "lb":
                        res["lb_sites"].append((func, base, cls, off))
                if kind == "gp" or base == "gp":
                    res["gp"][off] += 1
                    continue
                if kind in ("lo", "hi") or base == "at":
                    if kind in ("lo", "hi"):
                        res["lo"][off] += 1
                    continue
                if base == "sp":
                    continue
                r = res["clusters"][(func, base)][off]
                r["off"] = off
                r["widths"].add(width)
                r["ops"].add(op)
                if sign:
                    r["signs"].add(sign)
                if op[0] == "s":
                    r["writes"] += 1
                else:
                    r["reads"] += 1
    return res


def shape_of(rec):
    """Canonical per-offset shape: (off, sorted widths, sorted signs)."""
    return (rec["off"], tuple(sorted(rec["widths"])),
            tuple(sorted(s for s in rec["signs"] if s)))


def cluster_sig(recs):
    return tuple(sorted(shape_of(r) for r in recs.values()))


def padding(offsets_sorted, sizes):
    """Byte ranges not touched by any field, given per-offset width sets."""
    gaps = []
    end = 0
    for off in offsets_sorted:
        w = max(sizes[off])
        if off > end:
            gaps.append((end, off))
        end = max(end, off + w)
    return gaps


def clusters_of(res, target, min_fields):
    """Turn a scan result into cluster dicts of >= min_fields offsets."""
    out = []
    for (func, base), recs in res["clusters"].items():
        if len(recs) < min_fields:
            continue
        offs = sorted(r["off"] for r in recs.values())
        sizes = {r["off"]: set(r["widths"]) for r in recs.values()}
        out.append(dict(target=target, func=func, base=base,
                        regclass=reg_class(base), recs=recs,
                        sig=cluster_sig(recs), gaps=padding(offs, sizes)))
    return out


def fmt_fields(recs):
    lines = []
    for off in sorted(r["off"] for r in recs.values()):
        r = recs[off]
        ws = "/".join(str(w) for w in sorted(r["widths"]))
        ss = ",".join(sorted(r["signs"])) or "-"
        note = ""
        if len(r["widths"]) > 1:
            note += " ALIAS(width)"
        if "s" in r["signs"] and "u" in r["signs"]:
            note += " ALIAS(sign)"
        lines.append(f"      {hoff(off):<7} w={ws:<3} sign={ss:<2} "
                     f"{'+'.join(sorted(r['ops']))}{note}")
    return lines


def main(argv):
    ap = argparse.ArgumentParser(prog="struct_infer.py")
    ap.add_argument("--target", action="append", default=None,
                    help="limit to target (repeatable)")
    ap.add_argument("--min-fields", type=int, default=2,
                    help="min distinct offsets to call a cluster a struct")
    ap.add_argument("--min-targets", type=int, default=2,
                    help="min targets for a shape to count as shared")
    ap.add_argument("--top", type=int, default=12,
                    help="clusters/sites to list per target")
    ap.add_argument("--all-lb", action="store_true",
                    help="print every signed-byte site")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv[1:])

    targets = args.target or TARGETS
    all_clusters, gp_by_t, lo_by_t, census, scans = [], {}, {}, {}, {}
    lb_sites = []
    for t in targets:
        res = scan(t)
        scans[t] = res
        all_clusters += clusters_of(res, t, args.min_fields)
        gp_by_t[t], lo_by_t[t] = res["gp"], res["lo"]
        census[t] = dict(files=res["files"], funcs=res["funcs"],
                         clusters=sum(1 for c in all_clusters
                                      if c["target"] == t),
                         ops=res["ops"], filtered=res["filtered"],
                         zero_base=res["zero_base"])
        for func, base, cls, off in res["lb_sites"]:
            lb_sites.append((t, func, base, cls, off))

    # shape recurrence across targets
    by_sig = defaultdict(set)
    for c in all_clusters:
        by_sig[c["sig"]].add(c["target"])
    shared = {s: ts for s, ts in by_sig.items() if len(ts) >= args.min_targets}
    # per-offset recurrence: (off,width,sign) -> targets
    off_recur = defaultdict(set)
    for c in all_clusters:
        for rec in c["recs"].values():
            for w in rec["widths"]:
                for s in (rec["signs"] or {None}):
                    off_recur[(rec["off"], w, s)].add(c["target"])

    if args.json:
        def ser(c):
            return dict(target=c["target"], func=c["func"], base=c["base"],
                        regclass=c["regclass"],
                        fields=sorted(
                            (r["off"], sorted(r["widths"]),
                             sorted(r["signs"]), sorted(r["ops"]))
                            for r in c["recs"].values()),
                        gaps=[list(g) for g in c["gaps"]])
        print(json.dumps(dict(
            targets=targets, census={t: dict(v) for t, v in census.items()},
            clusters=[ser(c) for c in all_clusters],
            lb_sites=[list(x) for x in lb_sites],
            shared_shapes=[[list(s), sorted(ts)] for s, ts in shared.items()],
            offset_recurrence=[[list(k), sorted(v)]
                               for k, v in off_recur.items()],
        ), default=list))
        return 0

    print("== struct_infer: memory-access evidence from carved asm ==")
    print("   (partial carve - field maps are lower bounds on true layout;")
    print("    data islands and $zero-base accesses are filtered out)")
    print()
    print("-- census (filtered = dropped misdecoded-data lines, "
          "zero = $zero-base lines) --")
    for t in targets:
        c = census[t]
        ops = dict(c.get("ops", {}))
        print(f"  {t:<12} files={c['files']:<4} blocks={c['funcs']:<5} "
              f"clusters>={args.min_fields}:{c['clusters']:<4} "
              f"lb={ops.get('lb', 0)} lbu={ops.get('lbu', 0)} "
              f"lh={ops.get('lh', 0)} lhu={ops.get('lhu', 0)} "
              f"lw={ops.get('lw', 0)} "
              f"gp_sym={len(gp_by_t[t])} abs_sym={len(lo_by_t[t])} "
              f"filtered={c['filtered']} zero={c['zero_base']}")

    print()
    print(f"-- signed-byte sites: {len(lb_sites)} lb total "
          f"(vs unsigned lbu elsewhere) --")
    # Group the minority signed loads so the table stays readable; print
    # every site only with --all-lb.
    grp = defaultdict(list)
    for t, func, base, cls, off in lb_sites:
        grp[(t, cls)].append((func, base, off))
    for (t, cls), sites in sorted(grp.items()):
        print(f"  {t:<12} cls={cls:<5} {len(sites)} lb")
        show = sites if args.all_lb else sites[:args.top]
        for func, base, off in show:
            print(f"      {func:<14} ${base:<3} {hoff(off)}")
        if len(sites) > len(show):
            print(f"      ... {len(sites) - len(show)} more (--all-lb)")

    print()
    print(f"-- strongest pointer clusters (>= {args.min_fields} offsets; "
          f"arg/saved first - those are true pointer bases) --")
    rank = {"arg": 0, "saved": 1, "temp": 2}
    for t in targets:
        cl = sorted([c for c in all_clusters if c["target"] == t],
                    key=lambda c: (rank[c["regclass"]], -len(c["recs"]),
                                   c["func"]))[:args.top]
        if not cl:
            continue
        print(f"  [{t}]")
        for c in cl:
            gaps = ",".join(f"{a:#x}..{b:#x}" for a, b in c["gaps"]) or "-"
            print(f"   {c['func']} base=${c['base']} ({c['regclass']}) "
                  f"fields={len(c['recs'])} pad[{gaps}]")
            for ln in fmt_fields(c["recs"]):
                print(ln)

    print()
    print(f"-- shapes recurring in >= {args.min_targets} targets "
          f"({len(shared)} shapes) --")
    sh = sorted(shared.items(),
                key=lambda kv: (-len(kv[1]), -len(kv[0])))
    for sig, ts in sh[:args.top]:
        fields = " ".join(
            f"{hoff(off)}:{'/'.join(str(w) for w in ws)}"
            f"{('/'.join(ss) if ss else '-')}"
            for off, ws, ss in sig)
        print(f"  {len(ts)}x {sorted(ts)}: {fields}")

    print()
    print("-- offset shapes recurs across targets (top) --")
    orc = sorted(off_recur.items(),
                 key=lambda kv: (-len(kv[1]), kv[0][0], kv[0][1]))
    for (off, w, s), ts in orc[:args.top]:
        print(f"  off={hoff(off)} w={w} sign={s or '-'} -> {len(ts)} "
              f"{sorted(ts)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

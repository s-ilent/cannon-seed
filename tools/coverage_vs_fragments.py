#!/usr/bin/env python3
"""coverage_vs_fragments.py - compare static fragment classification to a
runtime trace, for the ambiguous (prologue-less) code subsegments.

Static side: the fragment_report module, which classifies every prologue-less
subsegment as ORPHAN / REF'D / SHARED-TAIL / PTR-CALLED from branch and
pointer references.

Dynamic side: the COV| lines emitted by tools/pcsx_coverage.lua, which record
which entry addresses were executed and which targets the indirect dispatch
sites jumped to.

Each classification is an inference, so the value here is the disagreement:
an ORPHAN the CPU actually reaches is refuted (a reference is missing from
the static scan), a range the CPU never reaches is confirmed dead, and an
indirect target landing on a subsegment start confirms a dispatch table.

Usage: python3 tools/coverage_vs_fragments.py [TARGET] [--cov FILE]
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
VLOAD = 0x80020000

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fragment_report


def load_rows(target):
    return fragment_report.build_rows(target)[1]


def load_coverage(path):
    entered, itarget, isite, by_stage = set(), set(), {}, {}
    if not path.exists():
        return None
    for ln in path.read_text().splitlines():
        parts = ln.split("|")
        if len(parts) < 3 or parts[0] != "COV":
            continue
        tag, val = parts[1], parts[2]
        if tag == "ENTERED":
            a = int(val, 16)
            entered.add(a)
            if len(parts) >= 4 and parts[3]:
                by_stage.setdefault(parts[3], set()).add(a)
        elif tag == "ITARGET":
            itarget.add(int(val, 16))
        elif tag == "ISITE":
            isite[int(val, 16)] = int(parts[3])
    return dict(entered=entered, itarget=itarget, isite=isite, by_stage=by_stage)


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    target = args[0] if args else "slps_00270"
    cov_arg = None
    if "--cov" in argv:
        cov_arg = argv[argv.index("--cov") + 1]
    cov_path = Path(cov_arg) if cov_arg else REPO / "build" / f"coverage.{target}.txt"

    rows = load_rows(target)
    cov = load_coverage(cov_path)
    if cov is None:
        print(f"no coverage file at {cov_path}")
        print(f"run: make-like invocation with -dofile build/cov.{target}.lua "
              f"under pcsx-redux, writing COV| lines to that path")
        return 2

    # Keep only indirect targets that land inside the payload: a jr/jalr site
    # can be a BIOS veneer ($t2 = 0xA0) or a dispatcher, whose register is not a
    # code pointer. Targets outside the image are not dispatch destinations.
    size = (REPO / "baselines" / f"{target}.bin").stat().st_size - 0x800
    hi = VLOAD + size
    cov["itarget"] = {a for a in cov["itarget"] if VLOAD <= a < hi}

    # If the trace is stage-tagged (image-word verified), use only this stage's
    # hits; otherwise fall back to every recorded hit.
    hits = cov["by_stage"].get(target, cov["entered"]) if cov["by_stage"] else cov["entered"]

    print(f"== {target}: {len(rows)} prologue-less subsegs, "
          f"{len(hits)} entry addrs hit, "
          f"{len(cov['itarget'])} indirect targets ==")
    agree = refute = 0
    orphan_live = orphan_dead = 0
    for r in sorted(rows, key=lambda r: -r["size"]):
        s, e = r["s"], r["e"]
        vstart = VLOAD + s
        hit = any(vstart <= a < VLOAD + e for a in hits)
        indir = vstart in cov["itarget"]
        static_refd = bool(r["srcs"] or r["ptrs"] or r["prev_into"])
        if r["cls"] != "ORPHAN":
            verdict = "reached" if hit else "not reached in this trace"
        elif hit:
            verdict = "REFUTED: reached at runtime (static says ORPHAN)"
            refute += 1
            orphan_live += 1
        else:
            verdict = "not reached (no evidence)"
            agree += 1
            orphan_dead += 1
        if indir:
            verdict += " + indirect-entry"
        tag = "!!" if verdict.startswith("REFUTED") else "  "
        print(f"{tag} {s:#07x}-{e:#07x} {r['size']:>6}B {r['cls']:<11} "
              f"end={r['end']:<10} refs={len(r['refs'])} "
              f"jt={len(r['ptrs_into'])} :: {verdict}")
    print(f"\n{refute} static classifications refuted; "
          f"{orphan_live} ORPHANs are live, {orphan_dead} unconfirmed. "
          f"A short or non-interactive run covers only part of the code, so "
          f"'not reached' means 'no evidence', not 'dead'.")
    print("entry addrs reached: " + " ".join(f"{a:#010x}" for a in sorted(hits)))
    if cov["itarget"]:
        print("indirect targets:    " + " ".join(f"{a:#010x}" for a in sorted(cov["itarget"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

#!/usr/bin/env python3
"""gmd_anatomy.py - structural anatomy of gmd screen candidates vs retail.

Extracts the named features the probes chase (frame sp-adjusts, the walk2
fold temp+copy, the cursor giv twin, the blez slot filler, load-delay nops,
step placement) and prints a compact table plus per-candidate full diffs on
demand.  Oracle-free (uses the committed retail .s as reference).

Usage: python3 scripts/bm_unit_decode/gmd_anatomy.py [v1 v2 ... | all]
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gmd_offline_screen as g


def features(seq):
    """seq = normalized entry list (labels marked 'LABELn')."""
    insns = [e for e in seq if not e.startswith("LABEL")]
    f = {}
    f["n"] = len(insns)
    f["frame"] = insns.count("addiu$29,$29,-8") + insns.count("addiu$29,$29,8")
    f["fold_temp"] = sum(1 for e in insns if e.startswith("addiu$") and ",$4,4" in e and e != "addiu$4,$4,4")
    f["walk1"] = insns.count("addiu$4,$4,4")
    # twin: an addiu $x,$y,8 init (y != 29) before the loop label
    first_label = next((i for i, e in enumerate(seq) if e.startswith("LABEL")), len(seq))
    pre = seq[:first_label]
    f["twin8_init"] = sum(1 for e in pre if re.match(r"addiu\$\d+,\$\d+,8$", e))
    # blez slot filler = insn right after blez
    for i, e in enumerate(insns):
        if e.startswith("blez"):
            f["slot"] = insns[i + 1] if i + 1 < len(insns) else "?"
            f["post_load"] = insns[i - 1] if i >= 1 else "?"
            break
    # steps: addiu $x,$x,28 occurrences and positions (mid-body = before slt)
    slt_i = next((i for i, e in enumerate(insns) if e.startswith("slt")), len(insns))
    first_label_i = first_label
    steps_mid = [i for i, e in enumerate(insns)
                 if re.match(r"addiu\$\d+,\$\d+,28$", e) and first_label_i < i < slt_i]
    steps_tail = [i for i, e in enumerate(insns)
                  if re.match(r"addiu\$\d+,\$\d+,28$", e) and i > slt_i]
    f["steps"] = "mid=%d tail=%d" % (len(steps_mid), len(steps_tail))
    return f


def main():
    import glob
    args = sys.argv[1:]
    files = []
    if not args or args == ["all"]:
        files = sorted(glob.glob(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "gmd_v*.c")))
    else:
        d = os.path.dirname(os.path.abspath(__file__))
        files = [os.path.join(d, "gmd_%s.c" % a) for a in args]

    ref = g.parse_retail()
    refseq = [t[1] if t[0] == "i" else "LABEL%d" % t[1] for t in ref]
    print("%-10s %s" % ("RETAIL", features(refseq)))
    for c in files:
        path, r = g.compile_candidate(c)
        if path is None:
            print("%-10s COMPILE-FAIL" % os.path.basename(c)[:-2])
            continue
        got = g.parse_candidate(path)
        seq = [t[1] if t[0] == "i" else "LABEL%d" % t[1] for t in got]
        print("%-10s %s" % (os.path.basename(c)[:-2], features(seq)))


if __name__ == "__main__":
    main()

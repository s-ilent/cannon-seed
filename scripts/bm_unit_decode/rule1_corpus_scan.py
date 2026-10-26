#!/usr/bin/env python3
"""rule1_corpus_scan.py - census the epilogue shapes across all landed asm rows.

Question (LAW 5, cron-202610262304): tools/cc_post.py rule 1 (EPILOGUE DELAY
SWAP) has byte-verified variants for k = 1, 2, 3 frame reloads only.  The
block-move unit func_8002ADA0's shared epilogue (func_8002B444, pinned in
asm/nonmatchings/func_800272F8.s) reloads SIX registers (ra, s4, s3, s2,
s1, s0) and retail puts the frame release in the branch delay slot.  Before
generalizing rule 1 to k >= 4, scan every landed asm row (byte-exact ground
truth, no oracle needed) for epilogue windows and classify:

  k        = number of consecutive `lw rX, N($sp)` reloads after `lw $ra`
             (rX excludes $sp; consecutive = unbroken run)
  order    = 'swapped'  if the frame release (addiu/subu $sp,$sp,N) sits in
                        the JUMP'S DELAY SLOT (release after jr/j $ra)
             'gcc'      if the release sits BEFORE the jump (maspsx raw)
             'none'     if no frame release found in the window
  window   = [lw $ra][lw $rX]{k}[branch to $ra][release?]

Any landed row showing gcc order at k >= 2 falsifies the generalization;
any showing swapped order at k >= 4 is supporting evidence.  Run from the
repo root:  python3 scripts/bm_unit_decode/rule1_corpus_scan.py
"""
import os
import re
import sys
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CMT = re.compile(r"/\*.*?\*/")
LW_RA = re.compile(r"^\s*lw\s+\$(?:31|ra),\s*(-?0x[0-9a-fA-F]+|\d+)\(\$sp\)")
LW_SREG = re.compile(r"^\s*lw\s+\$(\w+),\s*(-?0x[0-9a-fA-F]+|\d+)\(\$sp\)")
RELEASE = re.compile(r"^\s*(?:addiu|addu|subu)\s+\$sp,\s*\$sp,\s*(-?0x[0-9a-fA-F]+|\d+)")
JUMP_RA = re.compile(r"^\s*j(?:r)?\s+\$(?:31|ra)\b")
NOP = re.compile(r"^\s*nop\b")


def strip(ln):
    return CMT.sub("", ln, count=1).rstrip() if "/*" in ln else ln


def rows():
    out = []
    for root, _dirs, files in os.walk(os.path.join(REPO, "asm")):
        for fn in sorted(files):
            if fn.endswith(".s"):
                out.append(os.path.join(root, fn))
    return out


def c_rows():
    """Set of function names compiled from C per the splat yamls."""
    names = set()
    import glob
    for ypath in glob.glob(os.path.join(REPO, "config/splat.*.yaml")):
        for ln in open(ypath, errors="replace"):
            m = re.search(r"\[\s*0x[0-9a-fA-F]+\s*,\s*c\s*,\s*(\w+)\s*\]", ln)
            if m:
                names.add(m.group(1))
    return names


def classify(raw, i):
    """Classify the epilogue window starting at the lw $ra on line i."""
    lines = [strip(x) for x in raw]
    k = 0
    j = i + 1
    while j < len(lines):
        m = LW_SREG.match(lines[j])
        if not m or m.group(1) in ("31", "ra", "29", "sp"):
            break
        k += 1
        j += 1
    # skip nothing else: next meaningful insn decides
    order, rel_at = "none", None
    for t in range(j, min(j + 4, len(lines))):
        if JUMP_RA.match(lines[t]):
            # release may sit in the delay slot (t+1) or before the jump
            for u in range(j, t):
                if RELEASE.match(lines[u]):
                    return k, "gcc", u - i
            if t + 1 < len(lines) and RELEASE.match(lines[t + 1]):
                return k, "swapped", t + 1 - i
            if t + 1 < len(lines) and NOP.match(lines[t + 1]):
                return k, "none(rel-after-nop)", t + 1 - i
            return k, "none", t - i
        if RELEASE.match(lines[t]):
            rel_at = t
    return k, "no-jump", rel_at if rel_at is not None else -1


ROW_DIR = {
    "slps_00270": "asm/nonmatchings",
    "sces_00269": "asm/sces_00269/nonmatchings",
    "mainmenu_jp": "asm/mainmenu_jp/nonmatchings",
    "mainmenu_eu": "asm/mainmenu_eu/nonmatchings",
    "g3_jp": "asm/g3_jp/nonmatchings",
    "g3_eu": "asm/g3_eu/nonmatchings",
    "g3org_jp": "asm/g3org_jp/nonmatchings",
    "g3org_eu": "asm/g3org_eu/nonmatchings",
}


def audit_c_entries():
    """Per-target audit: for every yaml c entry, classify the epilogue
    windows inside THAT target's own row and report the convention."""
    import glob
    bad, missing, good = [], 0, 0
    for ypath in sorted(glob.glob(os.path.join(REPO, "config/splat.*.yaml"))):
        target = os.path.basename(ypath)[len("splat."):-len(".yaml")]
        rowdir = ROW_DIR.get(target)
        if not rowdir:
            continue
        for ln in open(ypath, errors="replace"):
            m = re.search(r"\[\s*(0x[0-9a-fA-F]+)\s*,\s*c\s*,\s*(\w+)\s*\]", ln)
            if not m:
                continue
            va = int(m.group(1), 16) + 0x80000000
            name = m.group(2)
            path = os.path.join(REPO, rowdir, name + ".s")
            if not os.path.exists(path):
                path = os.path.join(REPO, "asm/nonmatchings", name + ".s")
            if not os.path.exists(path):
                missing += 1
                continue
            lines = open(path, errors="replace").read().splitlines()
            # locate the function's glabel and its extent from the yaml comment
            mc = re.search(r"#\s*(0x[0-9a-fA-F]+)", ln)
            ext = int(mc.group(1), 16) if mc else None
            start = 0
            for i2, l2 in enumerate(lines):
                if re.search(r"glabel\s+" + name + r"\b", l2):
                    start = i2
                    break
            seg = lines[start:] if ext is None else lines[start:start + ext // 4 * 2 + 8]
            found = 0
            for i, raw in enumerate(seg):
                if not LW_RA.match(strip(raw)):
                    continue
                k, order, _ = classify(seg, i)
                if order in ("gcc", "swapped"):
                    found += 1
                    rec = (target, name, va, order, k)
                    if order == "gcc":
                        bad.append(rec)
                    else:
                        good += 1
            if not found:
                # unit has no lw-ra epilogue (leaf/tail-call) - fine
                pass
    print()
    print(f"per-target yaml-c audit: {good} swapped epilogue window(s), "
          f"{len(bad)} gcc-order window(s), {missing} row-missing (oracle-gated) C unit(s):")
    for rec in bad[:20]:
        print(f"  {rec}")
    if not bad:
        print("  zero gcc-order epilogue windows in auditable C units - no corpus")
        print("  counterexample to the rule-1 swapped convention at any k")
    return len(bad)


def main():
    census = Counter()
    examples = {}
    cnames = c_rows()
    for path in rows():
        rel = os.path.relpath(path, REPO)
        fname = os.path.splitext(os.path.basename(path))[0]
        # a row is a C unit if its name is a yaml c entry; split fragments
        # under nonmatchings/ keep the parent name so they tag too
        tag = "c" if fname in cnames else "asm"
        lines = open(path, errors="replace").read().splitlines()
        for i, ln in enumerate(lines):
            if not LW_RA.match(strip(ln)):
                continue
            k, order, _ = classify(lines, i)
            key = (tag, k, order)
            census[key] += 1
            examples.setdefault(key, []).append(f"{rel}:{i + 1}")
    print("epilogue-window census (tag = c/asm provenance, k = reloads after lw $ra,")
    print("order = release position):")
    for (tag, k, order), n in sorted(census.items()):
        ex = examples[(tag, k, order)][0]
        more = f" (+{n - 1} more)" if n > 1 else ""
        print(f"  {tag:3s} k={k:2d}  {order:20s}  {n:4d}  e.g. {ex}{more}")
    print()
    verdict = {}
    for tag in ("c", "asm"):
        k4_gcc = [(t, k, o) for (t, k, o) in census if t == tag and k >= 4 and o == "gcc"]
        k4_swap = [(t, k, o) for (t, k, o) in census if t == tag and k >= 4 and o == "swapped"]
        ng = sum(census[x] for x in k4_gcc)
        ns = sum(census[x] for x in k4_swap)
        print(f"{tag}: k>=4 gcc-order {ng}, swapped-order {ns}")
        if k4_gcc:
            for key in sorted(k4_gcc)[:4]:
                for ex in examples[key][:3]:
                    print(f"    {key}: {ex}")
        verdict[tag] = (ng, ns)
    ng, ns = verdict["c"]
    print()
    if ng == 0:
        print("C-PROVENANCE VERDICT: zero gcc-order k>=4 windows in C units - the")
        print("rule-1 generalization to k>=4 has no counterexample in the cc_post")
        print("population and is byte-verified by the corpus (oracle still gates the land)")
    else:
        print(f"C-PROVENANCE VERDICT: {ng} gcc-order k>=4 windows in C units - blanket")
        print("generalization would mis-swap those; per-unit evidence needed")
    rc = audit_c_entries()
    return 0 if rc == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

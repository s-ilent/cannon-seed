#!/usr/bin/env python3
"""epilogue_audit.py - census the epilogue shapes the C tree ACTUALLY produces.

Companion to rule1_corpus_scan.py (cron-202610262304, LAW 5).  The retail
side says: game-code rows put the frame release in the branch delay slot at
EVERY reload count k (corpus census: 622 swapped windows, k up to 9), SDK
rows keep gcc order at every k.  tools/cc_post.py rule 1 only swaps k<=3.

This script compiles every src/*.c through the repo pipeline (tools/cc.sh,
offline - no oracle needed), reads the PRE-cc_post maspsx output, finds
every epilogue window [lw $ra][lw $sX]{k}[addu $sp,N($sp)?][j $ra] and
census k per unit.  A unit whose compiled epilogue has k >= 4 is a unit the
rule-1 generalization would CHANGE: today it assembles gcc-order and is
GREEN, so its retail bytes are gcc-order (keep-epilogue marker needed before
generalizing) unless it is game code whose retail row shows swapped (then it
is currently MISMATCHED and the generalization FIXES it - judge material).

Usage: python3 scripts/bm_unit_decode/epilogue_audit.py [srcdir]
"""
import glob
import os
import re
import subprocess
import sys
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLROOT = os.environ.get("TOOLROOT", "/home/z/my-project/tools-local/mipsel-root")

LW_RA = re.compile(r"^lw\t\$(?:31|ra),(-?0x[0-9a-fA-F]+|\d+)\(\$sp\)$")
LW_SREG = re.compile(r"^lw\t\$(\w+),(-?0x[0-9a-fA-F]+|\d+)\(\$sp\)$")
RELEASE = re.compile(r"^(?:addu|addiu)\t\$sp,\$sp,(-?0x[0-9a-fA-F]+|\d+)$")
JUMP_RA = re.compile(r"^j(?:r)?\t\$(?:31|ra)$")


def epilogues(text):
    """Yield (k, swapped, has_nop) for every epilogue window in maspsx text."""
    lines = [ln.strip() for ln in text.splitlines()]
    out = []
    for i, ln in enumerate(lines):
        if not LW_RA.match(ln):
            continue
        k = 0
        j = i + 1
        while j < len(lines):
            m = LW_SREG.match(lines[j])
            if not m or m.group(1) in ("31", "ra", "29", "sp"):
                break
            k += 1
            j += 1
        release_before = None
        jump_at = None
        for t in range(j, min(j + 3, len(lines))):
            if JUMP_RA.match(lines[t]):
                jump_at = t
                break
            if RELEASE.match(lines[t]):
                release_before = t
        if jump_at is None:
            continue
        swapped = jump_at + 1 < len(lines) and RELEASE.match(lines[jump_at + 1])
        has_nop = jump_at + 1 < len(lines) and lines[jump_at + 1] == "nop"
        out.append((k, bool(swapped), has_nop, release_before is not None))
    return out


def main():
    srcdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "src")
    env = dict(os.environ,
               LD_LIBRARY_PATH=f"{TOOLROOT}/usr/lib/x86_64-linux-gnu")
    census = Counter()
    k4plus = []
    srcs = sorted(glob.glob(os.path.join(srcdir, "*.c")))
    for src in srcs:
        name = os.path.splitext(os.path.basename(src))[0]
        base = os.path.join(REPO, "build", "judge", f"epaudit_{name}")
        os.makedirs(os.path.dirname(base), exist_ok=True)
        r = subprocess.run([f"{REPO}/tools/cc.sh", "-o", base + ".o", src],
                           cwd=REPO, capture_output=True, text=True, env=env)
        if r.returncode:
            census["COMPILE-FAIL"] += 1
            continue
        # cc.sh intermediates: <base>.gcc.s (cc1) and <base>.mas.s (maspsx,
        # pre-cc_post).  The maspsx text is what rule 1 sees.
        mas = base + ".mas.s"
        if not os.path.exists(mas):
            census["NO-INTERMEDIATE"] += 1
            continue
        wins = epilogues(open(mas, errors="replace").read())
        if not wins:
            census["no-lw-ra-epilogue"] += 1
            continue
        for (k, swapped, has_nop, rel_before) in wins:
            census[f"k={k}"] += 1
            if k >= 4:
                k4plus.append((name, k, swapped, has_nop, rel_before))
    print(f"compiled {len(srcs)} src units; epilogue-window census:")
    for key, n in sorted(census.items()):
        print(f"  {key:22s} {n:4d}")
    print()
    print(f"units producing k>=4 epilogue windows ({len(k4plus)}):")
    for (name, k, swapped, has_nop, rel_before) in sorted(k4plus):
        print(f"  {name:24s} k={k}  swapped={swapped}  nop-after-jump={has_nop}"
              f"  release-before-jump={rel_before}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

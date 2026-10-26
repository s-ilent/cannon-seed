#!/usr/bin/env python3
"""head_tail_matrix.py - prologue+tail+size read-out for one variant under
one cc1 flag regime (LAW 2 prologue interleave + LAW 5 tail deltas).

Usage: python3 scripts/bm_unit_decode/head_tail_matrix.py <variant.c> [cc1-extra-flags]
Prints: total insns, the first 16 prologue insns, and the last 42 tail insns.
"""
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLROOT = os.environ.get("TOOLROOT", "/home/z/my-project/tools-local/mipsel-root")
OBJDUMP = os.path.join(TOOLROOT, "usr/bin/mipsel-linux-gnu-objdump")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    cand = os.path.abspath(sys.argv[1])
    extra = sys.argv[2] if len(sys.argv) > 2 else ""
    base = os.path.splitext(os.path.basename(cand))[0]
    tag = re.sub(r"[^a-z0-9]+", "_", extra.strip()) or "default"
    stem = f"build/judge/htm_{base}_{tag}"
    os.makedirs(os.path.join(REPO, "build/judge"), exist_ok=True)
    env = dict(os.environ, CC1FLAGS_EXTRA=extra,
               LD_LIBRARY_PATH=f"{TOOLROOT}/usr/lib/x86_64-linux-gnu")
    r = subprocess.run([f"{REPO}/tools/cc.sh", "-o", stem + ".o", cand],
                       cwd=REPO, capture_output=True, text=True, env=env)
    if r.returncode:
        print(f"COMPILE-FAIL [{tag}]:\n{r.stderr[-800:]}")
        return 1
    r = subprocess.run([OBJDUMP, "-d", stem + ".o"], capture_output=True, text=True, env=env)
    insns = [m.group(2).split("#")[0].strip() for m in
             (re.match(r"^\s+[0-9a-f]+:\s+([0-9a-f]{8})\s+(.*)$", ln)
              for ln in r.stdout.splitlines()) if m]
    print(f"=== {base} [{extra or 'default'}]: {len(insns)} insns (retail unit = 433) ===")
    print("--- prologue (first 16) ---")
    for i, ins in enumerate(insns[:16]):
        print(f"  {i:3d} {ins}")
    print("--- tail (last 42) ---")
    for i, ins in enumerate(insns[-42:]):
        print(f"  {len(insns)-42+i:3d} {ins}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

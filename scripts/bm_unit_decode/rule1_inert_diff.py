#!/usr/bin/env python3
"""rule1_inert_diff.py - EMPIRICAL byte-inertness proof for the runbook's
Phase C patch (the rule-1 n-load generalization in tools/cc_post.py).

The analytic proof (cron-202610262304, epilogue_audit.py): the C tree
produces exactly one k>=4 epilogue (SsSeqCalledTbyT k=9) and it is
cc-post: sdk-aspsx exempt; k<=1 keeps its own rules; the k=2 units go
through the byte-verified three-load shape that the n-load form must
reproduce exactly at n=2.  This script upgrades that census to a FULL
COMPILE DIFF: every src/*.c compiles through tools/cc.sh before and
after the patch, and every object must stay byte-identical.

Usage (three passes, idempotent - re-runs skip units whose outputs exist):
    python3 scripts/bm_unit_decode/rule1_inert_diff.py pre    # before the patch
    # ... apply the runbook's Phase C patch to tools/cc_post.py ...
    python3 scripts/bm_unit_decode/rule1_inert_diff.py post   # after the patch
    python3 scripts/bm_unit_decode/rule1_inert_diff.py diff
Diff verdict: EVERY unit identical -> byte-inert empirically proven; any
DIFF -> the patch is NOT inert, do not land it (report instead).

No oracle needed (cc.sh is offline; baselines untouched).  Intermediates
live in build/judge/rule1_inert/{pre,post}/ (git-ignored).
"""
import glob
import os
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLROOT = os.environ.get("TOOLROOT", "/home/z/my-project/tools-local/mipsel-root")
BASE = os.path.join(REPO, "build", "judge", "rule1_inert")


def compile_pass(side: str) -> int:
    outdir = os.path.join(BASE, side)
    os.makedirs(outdir, exist_ok=True)
    env = dict(os.environ,
               LD_LIBRARY_PATH=f"{TOOLROOT}/usr/lib/x86_64-linux-gnu")
    srcs = sorted(glob.glob(os.path.join(REPO, "src", "*.c")))
    done = fail = skip = 0
    for src in srcs:
        name = os.path.splitext(os.path.basename(src))[0]
        want = os.path.join(outdir, name + ".o")
        if os.path.exists(want):
            skip += 1
            continue
        out = os.path.join(outdir, name + ".o.tmp")
        r = subprocess.run([f"{REPO}/tools/cc.sh", "-o", out, src],
                           cwd=REPO, capture_output=True, text=True, env=env)
        stem = out[: -len(".o.tmp")]
        if r.returncode:
            fail += 1
            # record the failure so pre/post failure sets can be compared
            with open(os.path.join(outdir, name + ".FAIL"), "w") as f:
                f.write(r.stderr[-2000:])
            continue
        # keep the post-cc_post asm next to the object (readable diff surface)
        if os.path.exists(stem + ".mas.s"):
            shutil.move(stem + ".mas.s", os.path.join(outdir, name + ".mas.s"))
        shutil.move(out, want)
        done += 1
        if done % 40 == 0:
            print(f"  [{side}] {done} compiled, {fail} failed, {skip} skipped", flush=True)
    print(f"[{side}] compiled={done} failed={fail} skipped={skip} of {len(srcs)}")
    return 0


def diff_pass() -> int:
    sides = ("pre", "post")
    outdirs = {s: os.path.join(BASE, s) for s in sides}
    for s in sides:
        if not os.path.isdir(outdirs[s]):
            print(f"FATAL: {outdirs[s]} missing - run the '{s}' pass first", file=sys.stderr)
            return 2
    pre_objs = {os.path.basename(p) for p in glob.glob(outdirs["pre"] + "/*.o")}
    post_objs = {os.path.basename(p) for p in glob.glob(outdirs["post"] + "/*.o")}
    pre_fails = {os.path.basename(p)[:-5] for p in glob.glob(outdirs["pre"] + "/*.FAIL")}
    post_fails = {os.path.basename(p)[:-5] for p in glob.glob(outdirs["post"] + "/*.FAIL")}
    ident = differ = 0
    diffs = []
    for obj in sorted(pre_objs & post_objs):
        a = open(os.path.join(outdirs["pre"], obj), "rb").read()
        b = open(os.path.join(outdirs["post"], obj), "rb").read()
        if a == b:
            ident += 1
        else:
            differ += 1
            diffs.append(obj)
    only_pre = sorted(pre_objs - post_objs)
    only_post = sorted(post_objs - pre_objs)
    fail_mismatch = sorted(pre_fails.symmetric_difference(post_fails))
    print(f"objects compared: {ident} identical, {differ} DIFFERENT")
    if diffs:
        print("DIFFERING OBJECTS (patch is NOT byte-inert):")
        for d in diffs:
            print(f"  {d}")
    if only_pre or only_post:
        print(f"one-sided objects: pre-only={only_pre} post-only={only_post}")
    if fail_mismatch:
        print(f"compile-fail sets differ pre vs post: {fail_mismatch}")
    print(f"compile failures: pre={len(pre_fails)} post={len(post_fails)}")
    if differ == 0 and not only_pre and not only_post and not fail_mismatch:
        print("VERDICT: BYTE-INERT empirically proven (every unit's object "
              "byte-identical across the patch)")
        return 0
    print("VERDICT: NOT byte-inert - do not land the patch; report")
    return 1


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "pre":
        return compile_pass("pre")
    if mode == "post":
        return compile_pass("post")
    if mode == "diff":
        return diff_pass()
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""gmd_apply_landing.py - apply (or revert) the SIX-ROW GsMapModelingData
landing as one validated command (matching lane).

Everything about this landing is proven offline (Log cron-20261028-0233):
  * gmd_v14.c is BYTE-EXACT to the committed retail 0x78 (gmd_byte_proof.py,
    30/30 words, default flags; v15 alternate);
  * all six game modules carry the body as standalone yaml rows, word-
    identical to the reference (gmd_launch_audit.py);
  * the DRY-RUN BUILD with this exact flip produced whole-image sha1s equal
    to the committed oracles on ALL SIX targets (verify's own criterion):
      g3org_jp    2b2a42250b9fe8849bbd791515ce341a678ddef0
      g3org_eu    01b37b4e01afe69acd2a46e69359dadd4a20877b
      g3_jp       994a680cd139069404e5c6d6c51d3796a728f2ec
      g3_eu       39030a759e8462575b709f77eed1050f7bbaa572
      mainmenu_jp d637286a60e36dfeee10c0441509c98b2f952d48
      mainmenu_eu f9f29eebb419b5e957ce2389d33caeedbb93685e
  * every flipped row's successor is the landed GsGetTimInfo c row, so the
    judge extent pins to exactly 0x78.

The live `make verify TARGET=<t>` x6 remains the ACCEPTANCE GATE (input
gates a3cfec70; verify 8/8 GREEN precedes any landing) - this tool only
mechanizes the tree edit so the return window executes first-shot.

Usage:
    python3 scripts/bm_unit_decode/gmd_apply_landing.py apply
    python3 scripts/bm_unit_decode/gmd_apply_landing.py revert
"""
import os
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_V14 = "scripts/bm_unit_decode/gmd_v14.c"
SRC_DST = "src/GsMapModelingData.c"

# (yaml, old row, line-ish) - old rows must occur EXACTLY once each
ROWS = [
    ("config/splat.g3org_jp.yaml",    "[0x2D248, asm, func_80053528]"),
    ("config/splat.g3org_eu.yaml",    "[0x2CB3C, asm, func_80052CEC]"),
    ("config/splat.g3_jp.yaml",       "[0x2FDAC, asm, func_8005667C]"),
    ("config/splat.g3_eu.yaml",       "[0x2F6E8, asm, func_80055E88]"),
    ("config/splat.mainmenu_jp.yaml", "[0x442C0, asm, func_8006DC40]"),
    ("config/splat.mainmenu_eu.yaml", "[0x43BC4, asm, func_8006D414]"),
]

HEADER = """/* GsMapModelingData - LIBGS SCLIB member (extent 0x78), landed as ONE source
 * across SIX placements (file offsets 0x2D248 g3org_jp, 0x2CB3C g3org_eu,
 * 0x2FDAC g3_jp, 0x2F6E8 g3_eu, 0x442C0 mainmenu_jp, 0x43BC4 mainmenu_eu;
 * true VAs 0x8004CA48 / 0x8004C33C / 0x8004F5AC / 0x8004EEE8 / 0x80063AC0 /
 * 0x800633C4 - the boots carry no copy). No cc_post marker: the DEFAULT
 * epilogue law is byte-exact for this unit (proven by the byte proof below).
 * Provenance: the addend-spelling law
 * (Log cron-20261028-0118) - the loop's addend is spelled through the fixed
 * base r so the liveness landscape snaps to retail; v14 is byte-exact to the
 * committed listing 30/30 words under default flags (gmd_byte_proof.py), the
 * six placements are word-identical (gmd_launch_audit.py), and the dry-run
 * build with this flip reproduced the committed whole-image oracle sha1 on
 * ALL SIX targets (Log cron-20261028-0233). Live verify x6 is the gate.
 *
 * Source body: scripts/bm_unit_decode/gmd_v14.c (banked leader).
 */
"""


def apply():
    # preconditions
    for path, old in ROWS:
        p = os.path.join(REPO, path)
        txt = open(p).read()
        if txt.count(old) != 1:
            sys.exit("precondition failed: %s carries %r %d times (want 1)"
                     % (path, old, txt.count(old)))
        new = old.replace(", asm,", ", c,").replace(
            old.rsplit(", ", 1)[1][:-1], "GsMapModelingData")
        if new in txt:
            sys.exit("precondition failed: %s already flipped" % path)
    v14 = os.path.join(REPO, SRC_V14)
    if not os.path.exists(v14):
        sys.exit("precondition failed: %s missing" % SRC_V14)
    if os.path.exists(os.path.join(REPO, SRC_DST)):
        sys.exit("precondition failed: %s already exists" % SRC_DST)

    body = open(v14).read()
    with open(os.path.join(REPO, SRC_DST), "w") as fh:
        fh.write(HEADER + body)
    print("wrote %s (header + v14 body)" % SRC_DST)

    for path, old in ROWS:
        p = os.path.join(REPO, path)
        txt = open(p).read()
        new = old.replace(", asm,", ", c,").replace(
            old.rsplit(", ", 1)[1][:-1], "GsMapModelingData")
        open(p, "w").write(txt.replace(old, new))
        print("flipped %s: %s -> %s" % (path, old, new))

    listings = [old.rsplit(", ", 1)[1][:-1] for _p, old in ROWS]
    r = subprocess.run(["git", "rm", "-q"] +
                       ["asm/%s/nonmatchings/%s.s" % (t, n) for t, n in [
                           ("g3org_jp", "func_80053528"),
                           ("g3org_eu", "func_80052CEC"),
                           ("g3_jp", "func_8005667C"),
                           ("g3_eu", "func_80055E88"),
                           ("mainmenu_jp", "func_8006DC40"),
                           ("mainmenu_eu", "func_8006D414")]],
                       cwd=REPO, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("git rm failed:\n%s%s" % (r.stdout, r.stderr))
    print("removed 6 dead listings: %s" % ", ".join(listings))
    print("\nNEXT (the acceptance gate, per target):")
    for t in ["g3org_jp", "g3org_eu", "g3_jp", "g3_eu",
              "mainmenu_jp", "mainmenu_eu"]:
        print("  make verify TARGET=%s" % t)


def revert():
    for path, _old in ROWS:
        subprocess.run(["git", "checkout", "HEAD", "--", path], cwd=REPO,
                       check=True)
    subprocess.run(["git", "checkout", "HEAD", "--"] +
                   ["asm/%s/nonmatchings/%s.s" % (t, n) for t, n in [
                       ("g3org_jp", "func_80053528"),
                       ("g3org_eu", "func_80052CEC"),
                       ("g3_jp", "func_8005667C"),
                       ("g3_eu", "func_80055E88"),
                       ("mainmenu_jp", "func_8006DC40"),
                       ("mainmenu_eu", "func_8006D414")]], cwd=REPO, check=True)
    dst = os.path.join(REPO, SRC_DST)
    if os.path.exists(dst):
        os.unlink(dst)
    print("reverted: 6 yamls + 6 listings restored, %s removed" % SRC_DST)


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("apply", "revert"):
        sys.exit(__doc__)
    (apply if sys.argv[1] == "apply" else revert)()

#!/usr/bin/env python3
"""wave1CC_screen.py - offline compile-side screen for the 0x1CC x20
recursive-triangle-subdivision wave (the 26th window's landing prep;
oracle-independent, the wave88_screen.py pattern).

The retail truth is the committed listings' hex comment columns (byte-true
because verify 8/8 GREEN assembles them into the witnessed image). The row
carries no absolute relocations, so ONE compiled .text serves all twenty
members: the screen compiles the template ONCE and compares its 456-byte
.text against every member listing's glabel->endlabel hex columns.

    python3 scripts/wave1CC_screen.py             # screen vs all 20 listings
    python3 scripts/wave1CC_screen.py tri_subdiv.c ...

Exit 0 = every member byte-exact.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CC = REPO / "tools" / "cc.sh"
OBJCOPY = Path("/home/z/my-project/tools-local/mipsel-root/usr/bin/mipsel-linux-gnu-objcopy")
HEXCOL = re.compile(r"/\*\s*[0-9A-Fa-f]+\s+[0-9A-Fa-f]+\s+([0-9A-Fa-f]{8})\s*\*/")
TEMPLATE = REPO / "scripts" / "wave1CC" / "tri_subdiv.c"

# the twenty wave members: (target, walk name); the sdk-tagged 0x1cc rows
# are psyq rows and are NOT part of the wave
MEMBERS = [
    ("mainmenu_eu", "func_8006E05C"),
    ("mainmenu_eu", "func_8006E84C"),
    ("mainmenu_eu", "func_8006F34C"),
    ("mainmenu_eu", "func_8006FC6C"),
    ("g3_jp", "func_8005A13C"),
    ("g3_jp", "func_8005A92C"),
    ("g3_jp", "func_8005B42C"),
    ("g3_jp", "func_8005BD4C"),
    ("g3_eu", "func_80059B80"),
    ("g3_eu", "func_8005A370"),
    ("g3_eu", "func_8005AE70"),
    ("g3_eu", "func_8005B790"),
    ("g3org_jp", "func_800575D8"),
    ("g3org_jp", "func_80057DC8"),
    ("g3org_jp", "func_800588C8"),
    ("g3org_jp", "func_800591E8"),
    ("g3org_eu", "func_80056FD4"),
    ("g3org_eu", "func_800577C4"),
    ("g3org_eu", "func_800582C4"),
    ("g3org_eu", "func_80058BE4"),
]


def retail_bytes(target, fn):
    path = REPO / "asm" / target / "nonmatchings" / f"{fn}.s"
    text = path.read_text(encoding="utf-8", errors="replace")
    # the row .s carries the whole 0x1cc row as six glabel/endlabel chunks -
    # the hex columns across the whole file ARE the retail row bytes
    raw = [bytes.fromhex(m.group(1)) for m in HEXCOL.finditer(text)]
    return path, b"".join(raw)


def compile_template():
    out_o = "/tmp/wave1CC/tri_subdiv.o"
    os.makedirs("/tmp/wave1CC", exist_ok=True)
    env = dict(os.environ)
    env["LD_LIBRARY_PATH"] = "/home/z/my-project/tools-local/mipsel-root/usr/lib/x86_64-linux-gnu"
    r = subprocess.run(["sh", str(CC), "-o", out_o, str(TEMPLATE)], cwd=str(REPO),
                       capture_output=True, text=True, env=env, timeout=180)
    return out_o, r


def main():
    args = sys.argv[1:]
    ok = True
    if not args:
        # template mode: compile once, compare vs every member listing
        out_o, r = compile_template()
        if r.returncode != 0:
            print("tri_subdiv: COMPILE-FAIL")
            print(r.stderr[-1500:])
            return 1

        dump = "/tmp/wave1CC/tri_subdiv.text"
        env2 = dict(os.environ)
        env2["LD_LIBRARY_PATH"] = "/home/z/my-project/tools-local/mipsel-root/usr/lib/x86_64-linux-gnu"
        subprocess.run([str(OBJCOPY), "--dump-section", f".text={dump}", out_o],
                       check=True, capture_output=True, env=env2)
        got = Path(dump).read_bytes()
        print(f"template .text: {len(got)} bytes (want 460 = 0x1cc; the .o's 16-byte section alignment may pad a zero tail)")
        if len(got) < 460:
            print("  text SHORT of the row extent - not screening")
            return 1

        for target, fn in MEMBERS:
            path, want = retail_bytes(target, fn)
            if len(want) != 460:
                print(f"{target} {fn}: listing extent {len(want)} != 460 - SKIP")
                ok = False
                continue
            if got[:460] == want:
                print(f"{target} {fn}: bytes=EXACT ({len(want)} bytes)")
            else:
                ok = False
                first = next((i for i in range(460) if got[i] != want[i]), None)
                w = first // 4 if first is not None else -1
                print(f"{target} {fn}: bytes=DIFF  first diff @word {w}: "
                      f"got {got[w*4:w*4+4].hex()} want {want[w*4:w*4+4].hex()}  ({path.name})")
        return 0 if ok else 1

    # staged-unit mode: compile each given unit, map its stem to its member
    # row, compare against THAT member's listing (the gen-wave-staging proof)
    by_name = {fn: (target, fn) for target, fn in MEMBERS}
    for unit in args:
        stem = Path(unit).stem
        if stem not in by_name:
            print(f"{unit}: stem {stem} is not a wave member - SKIP")
            ok = False
            continue
        target, fn = by_name[stem]
        out_o, r = compile_template_path(Path(unit))
        if r.returncode != 0:
            print(f"{stem}: COMPILE-FAIL\n{r.stderr[-600:]}")
            ok = False
            continue
        dump = out_o[:-2] + ".text"
        env2 = dict(os.environ)
        env2["LD_LIBRARY_PATH"] = "/home/z/my-project/tools-local/mipsel-root/usr/lib/x86_64-linux-gnu"
        subprocess.run([str(OBJCOPY), "--dump-section", f".text={dump}", out_o],
                       check=True, capture_output=True, env=env2)
        got = Path(dump).read_bytes()
        _, want = retail_bytes(target, fn)
        if got[:460] == want and set(got[460:]) <= {0}:
            print(f"{target} {stem}: bytes=EXACT ({len(want)} bytes, staged unit)")
        else:
            ok = False
            first = next((i for i in range(min(len(got), len(want))) if got[i] != want[i]), None)
            if first is None:
                print(f"{target} {stem}: bytes=DIFF (length/zero-tail)")
            else:
                w = first // 4
                print(f"{target} {stem}: bytes=DIFF  first diff @word {w}: "
                      f"got {got[w*4:w*4+4].hex()} want {want[w*4:w*4+4].hex()}")
    return 0 if ok else 1


def compile_template_path(cfile):
    out_o = "/tmp/wave1CC/" + Path(cfile).stem + ".o"
    os.makedirs("/tmp/wave1CC", exist_ok=True)
    env = dict(os.environ)
    env["LD_LIBRARY_PATH"] = "/home/z/my-project/tools-local/mipsel-root/usr/lib/x86_64-linux-gnu"
    r = subprocess.run(["sh", str(CC), "-o", out_o, str(cfile)], cwd=str(REPO),
                       capture_output=True, text=True, env=env, timeout=180)
    return out_o, r


if __name__ == "__main__":
    sys.exit(main())

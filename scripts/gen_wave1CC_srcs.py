#!/usr/bin/env python3
"""gen_wave1CC_srcs.py - emit the twenty per-row src units for the 0x1CC
recursive-triangle-subdivision own-row wave (sha1 28494af42860, 460 bytes
x 20; the 26th window's landing prep, decode banked in docs/TASKS.md
window cron-202610292127).

The wave104 one-mention law + the row-name==unit-name spelling law: every
yaml row gets its own src/<walk-name>.c, the .globl + label named exactly
the row name, the bytes byte-identical to the wave template
(scripts/wave1CC/tri_subdiv.c - the hand-asm unit, screens bytes=EXACT
offline x20 against every member's committed listing, this window). The
five interior chunk labels are row-local (.L labels in the template;
zero exterior references verified across the eight trees). No provenance
injection: the only placeholder mention a unit carries is its own
definition (headers name no siblings; identities live in the yaml + the
landing commit). mainmenu_jp/sces/slps carry no member.

    python3 scripts/gen_wave1CC_srcs.py              # emit into src/
    python3 scripts/gen_wave1CC_srcs.py --staging D  # emit into D (tests)

Landing order and gates live in scripts/land_wave1CC.sh (the wave-104
surgery shape: per-target flip + listing delete + make verify, honest
revert; the five landed targets last-to-first with slps-style care).
Run this gen BEFORE that script; ratchets move 713 -> 733 in the landing
commit (20 definitions x 1 mention - recompute the raise from the tree in
landing order, the twentieth-return NEXT 1 arithmetic note). THE LANDING
COMMIT WAITS FOR THE WITNESS per the INPUT GATES - the witness is UP as
of this window (the 22nd production return, 8/8 STRICT ~21:44Z), so the
next window's landing can go straight to the flips.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
STAGE = REPO / "scripts" / "wave1CC"

WAVE = [
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
TMPL_LABEL = "func_8005A13C"


def unit_text(tmpl_text: str, fn: str) -> str:
    for form in (f".globl {TMPL_LABEL}", f"{TMPL_LABEL}:"):
        if tmpl_text.count(form) != 1:
            raise SystemExit(f"{form!r}: hit {tmpl_text.count(form)} times, want 1")
    body = tmpl_text.replace(f".globl {TMPL_LABEL}", f".globl {fn}")
    body = body.replace(f"{TMPL_LABEL}:", f"{fn}:")
    return body


def main() -> int:
    argv = sys.argv[1:]
    staging = None
    if argv and argv[0] == "--staging":
        staging = Path(argv[1])
        argv = argv[2:]
    outdir = staging if staging else REPO / "src"
    if staging:
        outdir.mkdir(parents=True, exist_ok=True)
    text = (STAGE / "tri_subdiv.c").read_text()
    total = 0
    for target, fn in WAVE:
        out = outdir / f"{fn}.c"
        if out.exists() and not staging:
            raise SystemExit(f"refusing to overwrite existing {out}")
        out.write_text(unit_text(text, fn))
        total += 1
    print(f"emitted {total} units into {outdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

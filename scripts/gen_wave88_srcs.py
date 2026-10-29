#!/usr/bin/env python3
"""gen_wave88_srcs.py - emit the four per-row src units for the memmove
own-row wave (0x90 row = 0x88 function + 2 zero tail words; 20th-return
NEXT 3, the psyq-decode class).

The memclr one-src-unit-per-row law + the row-name==unit-name spelling law:
every yaml row gets its own src/<walk-name>.c, the .globl + label named
exactly the row name, the bytes byte-identical to the wave template
(scripts/wave88/memmove.c - the hand-asm unit, screens bytes=EXACT offline,
window cron-202610291255). The decode comment keeps the psyq identity;
only the .globl/label lines carry the walk name (string-anchored: each
spells exactly once inside the __asm__ block). Four targets pin memmove in
symbols ("pinned member row") - the pins stay; they are the identity alias
for the landed rows (the SetVideoMode sdk-member-on-matched-c-row
precedent).

    python3 scripts/gen_wave88_srcs.py              # emit into src/
    python3 scripts/gen_wave88_srcs.py --staging D  # emit into D (tests)

Landing order and gates live in scripts/land_wave88.sh (the wave-104
surgery shape: per-target flip + listing delete + make verify, slps LAST,
revert on any failure). Run this gen BEFORE that script; ratchets move
691 -> 695 in the landing commit when it follows the 10C wave (recompute
the raise from the tree in landing order - the twentieth-return NEXT 1
arithmetic note). THE LANDING COMMIT WAITS FOR THE WITNESS per the INPUT
GATES (the eighteenth return's NEXT 3 law) - this gen + the offline
screens are the Law Zero offline half.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
STAGE = REPO / "scripts" / "wave88"

WAVE = [
    ("slps_00270", "func_80030D90"),
    ("mainmenu_jp", "func_8006661C"),
    ("g3_jp", "func_8004EF2C"),
    ("g3org_jp", "func_8004BDD8"),
]
TMPL_LABEL = "func_80030D90"


def unit_text(tmpl_text: str, fn: str) -> str:
    for form in (f".globl {TMPL_LABEL}", f"{TMPL_LABEL}:"):
        if tmpl_text.count(form) != 1:
            raise SystemExit(f"{form!r}: hit {tmpl_text.count(form)} times, want 1")
    body = tmpl_text.replace(f".globl {TMPL_LABEL}", f".globl {fn}")
    body = body.replace(f"{TMPL_LABEL}:", f"{fn}:")
    marker = " */\n"
    idx = body.index(marker)
    # No per-unit provenance injection: the wave104 law holds - the only
    # placeholder mention a unit carries is its own definition (headers name
    # no siblings; identities live in the yaml + the landing commit).
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
    text = (STAGE / "memmove.c").read_text()
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

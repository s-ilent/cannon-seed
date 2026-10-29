#!/usr/bin/env python3
"""gen_wave10C_srcs.py - emit the five per-row src units for the
MulMatrix (x3) / MulMatrix2 (x2) 0x10C own-row waves (20th-return NEXT 3,
the psyq-decode class).

The memclr one-src-unit-per-row law + the row-name==unit-name spelling law:
every yaml row gets its own src/<walk-name>.c, the FUNCTION named exactly
the row name, the body byte-identical to the wave template
(scripts/wave10C/MulMatrix.c + MulMatrix2.c - both screen bytes=EXACT
offline, window cron-202610291255). The decode comments keep the psyq
identities; only the definition line carries the walk name (line-anchored
definition-only rename - the comments' prototype lines spell the psyq
signatures and must keep them). Two targets pin the psyq names in symbols
(slps/g3_eu, "pinned member row") - the pins stay; they are the identity
alias for the landed rows (the SetVideoMode sdk-member-on-matched-c-row
precedent).

    python3 scripts/gen_wave10C_srcs.py              # emit into src/
    python3 scripts/gen_wave10C_srcs.py --staging D  # emit into D (tests)

Landing order and gates live in scripts/land_wave10C.sh (the wave-104
surgery shape: per-target flip + listing delete + make verify, slps LAST,
revert on any failure). Run this gen BEFORE that script; ratchets move
686 -> 691 in the landing commit (5 definitions, one mention per file,
headers name no siblings) with the provenance entry. THE LANDING COMMIT
WAITS FOR THE WITNESS per the INPUT GATES (the eighteenth return's NEXT 3
law) - this gen + the offline screens are the Law Zero offline half.
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
STAGE = REPO / "scripts" / "wave10C"

WAVE_MM = [
    ("slps_00270", "func_80037BD8"),
    ("mainmenu_eu", "func_8005DDBC"),
    ("g3_eu", "func_8004FCA0"),
]
WAVE_MM2 = [
    ("slps_00270", "func_80037CE4"),
    ("g3_eu", "func_8004FDAC"),
]
SZ = "0x10C"


def unit_text(tmpl_text: str, fn: str, tmpl_name: str) -> str:
    # rename ONLY the definition line (line-anchored - the decode comment's
    # prototype line spells the psyq signature and must keep the psyq name)
    pat = re.compile(r"^(long \*)" + re.escape(tmpl_name) + r"\(", re.M)
    body, n = pat.subn(rf"\g<1>{fn}(", tmpl_text)
    if n != 1:
        raise SystemExit(f"{tmpl_name}: definition rename hit {n} times, want 1")
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
    total = 0
    for tmpl_name, wave in (("MulMatrix", WAVE_MM), ("MulMatrix2", WAVE_MM2)):
        text = (STAGE / f"{tmpl_name}.c").read_text()
        for target, fn in wave:
            out = outdir / f"{fn}.c"
            if out.exists() and not staging:
                raise SystemExit(f"refusing to overwrite existing {out}")
            out.write_text(unit_text(text, fn, tmpl_name))
            total += 1
    print(f"emitted {total} units into {outdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

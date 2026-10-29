#!/usr/bin/env python3
"""gen_waveC8_srcs.py - emit the eight per-row src units for the
select_max_param own-row wave (0xC8, one member per target).

The memclr one-src-unit-per-row law + the row-name==unit-name spelling law:
every yaml row gets its own src/<walk-name>.c, the FUNCTION named exactly
the row name, the body byte-identical to the wave template
(scripts/waveC8/select_max_param.c - screens bytes=EXACT offline, window
cron-202610291140). The decode comment keeps the psyq identity; only the
definition line carries the walk name (a blanket replace would corrupt the
decode comment's cross-references). Three targets pin the psyq name in
symbols (slps/g3org_jp/mainmenu_jp, "pinned member row") - the pins stay;
they are the identity alias for the landed rows (the SetVideoMode
sdk-member-on-matched-c-row precedent).

    python3 scripts/gen_waveC8_srcs.py              # emit into src/
    python3 scripts/gen_waveC8_srcs.py --staging D  # emit into D (tests)

Landing order and gates live in scripts/land_waveC8.sh (the wave-104
surgery shape: per-target flip + listing delete + make verify, slps LAST,
revert on any failure). Run this gen BEFORE that script; ratchets move
664 -> 672 in the landing commit (8 definitions, one mention per file,
headers name no siblings) with the provenance entry. THE LANDING COMMIT
WAITS FOR THE WITNESS per the INPUT GATES (the eighteenth return's NEXT 3
law) - this gen + the offline screens are the Law Zero offline half.
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
STAGE = REPO / "scripts" / "waveC8"

WAVE = [
    ("slps_00270", "func_80036D04"),
    ("sces_00269", "func_8003384C"),
    ("mainmenu_jp", "func_8006E9BC"),
    ("mainmenu_eu", "func_80064010"),
    ("g3_jp", "func_800501F8"),
    ("g3_eu", "func_8004FB34"),
    ("g3org_jp", "func_800542A4"),
    ("g3org_eu", "func_8004CF88"),
]
TMPL_NAME = "select_max_param"
SZ = "0xC8"


def unit_text(tmpl_text: str, target: str, fn: str) -> str:
    # rename ONLY the definition line (line-anchored - the decode comment's
    # prototype line spells the same signature and must keep the psyq name);
    # the decode comment keeps the psyq identity
    pat = re.compile(r"^(int )" + re.escape(TMPL_NAME) + r"\(", re.M)
    body, n = pat.subn(rf"\g<1>{fn}(", tmpl_text)
    if n != 1:
        raise SystemExit(f"{TMPL_NAME}: definition rename hit {n} times, want 1")
    marker = " */\n"
    idx = body.index(marker)
    provenance = (f" * This unit: {target} row {fn}, the {SZ} member of its wave\n"
                  f" * (row-name==unit-name, one-src-unit-per-row).\n")
    return body[:idx] + provenance + body[idx:]


def main() -> int:
    argv = sys.argv[1:]
    staging = None
    if argv and argv[0] == "--staging":
        staging = Path(argv[1])
        argv = argv[2:]
    outdir = staging if staging else REPO / "src"
    if staging:
        outdir.mkdir(parents=True, exist_ok=True)
    text = (STAGE / f"{TMPL_NAME}.c").read_text()
    total = 0
    for target, fn in WAVE:
        out = outdir / f"{fn}.c"
        if out.exists() and not staging:
            raise SystemExit(f"refusing to overwrite existing {out}")
        out.write_text(unit_text(text, target, fn))
        total += 1
    print(f"emitted {total} units into {outdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

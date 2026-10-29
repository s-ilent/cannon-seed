#!/usr/bin/env python3
"""gen_waveE8E4_srcs.py - emit the fourteen per-row src units for the
MulRotMatrix (0xE8) / MulRotMatrix0 (0xE4) own-row waves.

The memclr one-src-unit-per-row law + the row-name==unit-name spelling law:
every yaml row gets its own src/<walk-name>.c, the FUNCTION named exactly
the row name, every body byte-identical to its wave template
(scripts/waveE8E4/MulRotMatrix.c and MulRotMatrix0.c - both screens
shape=OK bytes=EXACT offline, window cron-202610291025). The decode
comment keeps the psyq identity; only the definition line carries the
walk name (a blanket replace would corrupt the cross-references).

    python3 scripts/gen_waveE8E4_srcs.py              # emit into src/
    python3 scripts/gen_waveE8E4_srcs.py --staging D  # emit into D (tests)

Landing order and gates live in scripts/land_waveE8E4.sh (the wave-104
surgery shape: per-target flip + listing delete + make verify, slps LAST,
revert on any failure). Run this gen BEFORE that script; ratchets move
664 -> 678 in the landing commit (14 definitions, one mention per file,
headers name no siblings) with the provenance entry.
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
STAGE = REPO / "scripts" / "waveE8E4"

WAVE_E8 = [
    ("slps_00270", "func_80034328"),
    ("sces_00269", "func_80033DF0"),
    ("mainmenu_eu", "func_8005D6EC"),
    ("g3_jp", "func_800497F8"),
    ("g3_eu", "func_80049210"),
    ("g3org_jp", "func_80046C94"),
    ("g3org_eu", "func_80046664"),
]
WAVE_E4 = [
    ("slps_00270", "func_80034244"),
    ("sces_00269", "func_80033D0C"),
    ("mainmenu_eu", "func_8005D608"),
    ("g3_jp", "func_80049714"),
    ("g3_eu", "func_8004912C"),
    ("g3org_jp", "func_80046BB0"),
    ("g3org_eu", "func_80046580"),
]
TEMPLATES = {
    "MulRotMatrix": ("MulRotMatrix.c", WAVE_E8, "0xE8"),
    "MulRotMatrix0": ("MulRotMatrix0.c", WAVE_E4, "0xE4"),
}


def unit_text(tmpl_name: str, tmpl_text: str, target: str, fn: str, sz: str) -> str:
    # rename ONLY the definition line; the decode comment keeps the psyq name
    pat = re.compile(r"(long \*)" + re.escape(tmpl_name) + r"\(")
    body, n = pat.subn(rf"\g<1>{fn}(", tmpl_text)
    if n != 1:
        raise SystemExit(f"{tmpl_name}: definition rename hit {n} times, want 1")
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
    for tmpl_name, (tpath, wave, sz) in TEMPLATES.items():
        text = (STAGE / tpath).read_text()
        for target, fn in wave:
            out = outdir / f"{fn}.c"
            if out.exists() and not staging:
                raise SystemExit(f"refusing to overwrite existing {out}")
            out.write_text(unit_text(tmpl_name, text, target, fn, sz))
            total += 1
    print(f"emitted {total} units into {outdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

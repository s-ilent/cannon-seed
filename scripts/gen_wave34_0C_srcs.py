#!/usr/bin/env python3
"""gen_wave34_0C_srcs.py - emit the fourteen per-row src units for the two
fresh x8 own-row waves (the eighteenth return's phase F items; decodes
pre-proven offline in window cron-202610291410):

  wave34 (0x34): the word-copy loop - seven own-row members, one per game
  target except mainmenu_jp (the parent-bound interior at
  func_80085B5C +0x168 lands with its parent row, never alone).
  Template scripts/wave34_0C/wave34.c screens bytes=EXACT (13 words).

  wave0C (0xC): the halfword-load thunk - seven own-row members, same
  shape (the eighth is the parent-bound interior at func_8007FFAC +0x1BC).
  Template scripts/wave34_0C/wave0C.c screens bytes=EXACT (3 words).

The memclr one-src-unit-per-row law + the row-name==unit-name spelling
law: every yaml row gets its own src/<walk-name>.c, the FUNCTION named
exactly the row name, the body byte-identical to the wave template. No
psyq pin exists on either wave (checked: curated = none everywhere) - the
units land under their walk names.

    python3 scripts/gen_wave34_0C_srcs.py              # emit into src/
    python3 scripts/gen_wave34_0C_srcs.py --staging D  # emit into D (tests)

Landing order and gates live in scripts/land_wave34_0C.sh (the wave-104
surgery shape: per-target flip + listing delete + make verify, slps LAST,
revert on any failure). Run this gen BEFORE that script; ratchets move
+7 (wave34) and +7 (wave0C) from the tree's current count in the landing
commit (one raise per wave, definitions one mention per file, headers
name no siblings) with the provenance entries. THE LANDING COMMITS WAIT
FOR THE WITNESS per the INPUT GATES (the eighteenth return's NEXT 3 law)
- this gen + the offline screens are the Law Zero offline half.
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
STAGE = REPO / "scripts" / "wave34_0C"

WAVES = [
    ("wave34", "void", [
        ("slps_00270", "func_8003C8F8"),
        ("sces_00269", "func_8003C6EC"),
        ("mainmenu_eu", "func_800792C0"),
        ("g3_jp", "func_8006334C"),
        ("g3_eu", "func_80063CDC"),
        ("g3org_jp", "func_800607E8"),
        ("g3org_eu", "func_80061130"),
    ]),
    ("wave0C", "int", [
        ("slps_00270", "func_80037BF4"),
        ("sces_00269", "func_800377A8"),
        ("mainmenu_eu", "func_80074100"),
        ("g3_jp", "func_8005E648"),
        ("g3_eu", "func_8005ED98"),
        ("g3org_jp", "func_8005BAE4"),
        ("g3org_eu", "func_8005C1EC"),
    ]),
]
SIZES = {"wave34": "0x34", "wave0C": "0xC"}


def unit_text(tmpl_text: str, tmpl_name: str, ret: str,
              target: str, fn: str) -> str:
    # rename ONLY the definition line (line-anchored - the decode comment's
    # prototype line spells the same signature and must keep the template
    # name); the decode comment keeps the wave identity
    pat = re.compile(r"^(%s )" % re.escape(ret) + re.escape(tmpl_name) + r"\(",
                     re.M)
    body, n = pat.subn(rf"\g<1>{fn}(", tmpl_text)
    if n != 1:
        raise SystemExit(f"{tmpl_name}: definition rename hit {n} times, want 1")
    marker = " */\n"
    idx = body.index(marker)
    provenance = (f" * This unit: {target} row {fn}, the {SIZES[tmpl_name]} member of its wave\n"
                  f" (row-name==unit-name, one-src-unit-per-row).\n")
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
    total = 0
    for tmpl_name, ret, members in WAVES:
        text = (STAGE / f"{tmpl_name}.c").read_text()
        for target, fn in members:
            out = outdir / f"{fn}.c"
            if out.exists() and not staging:
                raise SystemExit(f"refusing to overwrite existing {out}")
            out.write_text(unit_text(text, tmpl_name, ret, target, fn))
            total += 1
    print(f"emitted {total} units into {outdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""tools/gen_yamls.py — emit splat yaml templates for targets that lack one.

Fills every fact from measured sources only: sizes from the baselines on
disk, pc0/t_addr/marks from config/exe.json, SHA-1 from config/sha1/.
Does NOT generate subsegments — that is `make scan`'s job. Idempotent:
refuses to overwrite an existing yaml.

Usage: python3 tools/gen_yamls.py <target> [<target> ...]
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

DESC = {
    "slps_00270": ("Japan boot executable", "SLPS_002.70 (SLPS-00270)", "SLPS disc"),
    "sces_00269": ("Europe boot executable", "SCES_002.69 (SCES-00269)", "SCES disc"),
    "mainmenu_jp": ("Japan main menu executable", "MAINMENU.EXE", "SLPS disc"),
    "mainmenu_eu": ("Europe main menu executable", "MAINMENU.EXE", "SCES disc"),
    "g3_jp": ("Japan game executable", "DRAGOON/G3.EXE", "SLPS disc"),
    "g3_eu": ("Europe game executable", "DRAGOON/G3.EXE", "SCES disc"),
    "g3org_jp": ("Japan linker-variant executable", "GOURB/G3ORG.EXE", "SLPS disc"),
    "g3org_eu": ("Europe linker-variant executable", "GOURB/G3ORG.EXE", "SCES disc"),
}

TEMPLATE = """\
# =============================================================================
# config/splat.{target}.yaml — {desc}
#
# {orig}, {disc}: {fsize:,} bytes on disc, {psize:,}-byte payload.
# SHA-1: {sha1} (config/sha1/{target}.sha1)
#
# STATUS: header facts measured (docs/LOADMAP.md, config/exe.json):
# payload loads at t_addr 0x80020000, entry pc0 = {pc0}.
# Subsegments below are the deterministic scan-v2 bootstrap
# (tools/scan_functions.py); re-run `make scan TARGET={target}` after any
# layout discovery, then re-split.
#
# asm_path is PER TARGET: every address in this file is valid only for
# this revision, so its split must never mix with another target's.
# =============================================================================

options:
  basename: {target}
  base_path: ..
  target_path: baselines/{target}.bin
  build_path: build
  asm_path: asm/{target}/nonmatchings
  asset_path: assets
  symbol_addrs_path:
    - config/symbols.{target}.txt
  ld_script_path: build/{target}.ld
  # auto symbol lists are per-target build artifacts, not shared state
  undefined_funcs_auto_path: build/{target}.undefined_funcs_auto.txt
  undefined_syms_auto_path: build/{target}.undefined_syms_auto.txt

  compiler: GCC            # FILL: pin exact revision (docs/TOOLCHAIN.md —
                           # Psy-Q kernel strings date the SDK to 1995-10;
                           # GCC 2.6.3 is the working hypothesis)
  platform: psx
  endianness: little

  # FILL: compiler flags once identified from the toolchain fingerprint
  # (candidates: -mips1 -mcpu=3000 -O2/-O3 -G0/-G4 -funsigned-char)

  create_undefined_syms_auto: true
  auto_link_sections: []

segments:
  - name: payload
    type: code
    start: 0x800
    vram: 0x80020000
    subsegments:
    # BEGIN GENERATED SUBSEGMENTS (tools/scan_functions.py - make scan)
    # END GENERATED SUBSEGMENTS
  - [0x{fsize:X}]
"""


def main(argv):
    if len(argv) < 2:
        raise SystemExit(__doc__)
    exe = json.loads((REPO / "config" / "exe.json").read_text())
    for target in argv[1:]:
        out = REPO / "config" / f"splat.{target}.yaml"
        if out.exists():
            print(f"skip {target}: {out.name} already exists")
            continue
        if target not in exe or target not in DESC:
            raise SystemExit(f"unknown target {target} (not in exe.json/DESC)")
        blob_path = REPO / "baselines" / f"{target}.bin"
        if not blob_path.exists():
            raise SystemExit(f"missing baseline {blob_path}")
        sha1 = (REPO / "config" / "sha1" / f"{target}.sha1").read_text()
        sha1 = [l for l in sha1.splitlines() if l.strip() and not l.strip().startswith("#")][0].split()[0].lower()
        fsize = blob_path.stat().st_size
        text = TEMPLATE.format(
            target=target,
            desc=DESC[target][0],
            orig=DESC[target][1],
            disc=DESC[target][2],
            fsize=fsize,
            psize=fsize - 0x800,
            sha1=sha1,
            pc0=exe[target]["pc0"],
        )
        out.write_text(text)
        print(f"wrote {out.name} ({fsize:,} B image, pc0 {exe[target]['pc0']})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

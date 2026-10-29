#!/usr/bin/env bash
# land_wave10C.sh - the MulMatrix (x3) / MulMatrix2 (x2) 0x10C wave landing
# (20th-return NEXT 3; decode pre-proven offline in window cron-202610291255:
# both templates screen bytes=EXACT vs the committed slps listings (67 words
# each, zero relocations), wave10C_check.py proves the retail rows
# byte-identical (x3 / x2) via the listing hex columns, and the gen'd units
# are byte-identical to the templates modulo the row-name definition).
#
# RUNS IN A RETURN WINDOW with witness 8/8 (the INPUT GATES own the landing
# commit; the offline window that banked this script could not run it).
# Run gen_wave10C_srcs.py FIRST (it emits the five src/ units).
#
# Per target: flip the yaml row [off, asm, N] -> [off, c,   N] (aligned
# spelling), delete the listing (slps uses the flat asm/nonmatchings path),
# then `make verify TARGET=<t>`. ANY verify failure reverts that target's
# edits (unverified bytes never land). mainmenu_eu first (one row), g3_eu
# second (two rows), slps LAST (the flat-path listing + the gp-window
# first-shot risk). After landing: judge_unit MulMatrix (g3_eu carrier)
# + MulMatrix2 both regimes and spot-judge the remaining three members,
# ratchets 664 -> 669 (5 definitions, one mention per file, headers name no
# siblings - raise + provenance entry in the same commit), suite,
# clean_stale_asm.
#
# Run from the repo root:  sh scripts/land_wave10C.sh
set -u

# target -> "off:name" pairs (MulMatrix first, then MulMatrix2)
ROWS_mm_slps_00270="0x151F8:func_80037BD8"
ROWS_mm_mainmenu_eu="0x3E5BC:func_8005DDBC"
ROWS_mm_g3_eu="0x2A0E0:func_8004FCA0"
ROWS_mm2_slps_00270="0x15304:func_80037CE4"
ROWS_mm2_g3_eu="0x2A1EC:func_8004FDAC"

TARGETS="${*:-mainmenu_eu g3_eu slps_00270}"
FAILED=""

for t in $TARGETS; do
  echo "=== $t: landing MulMatrix/MulMatrix2"
  yaml="config/splat.$t.yaml"
  if [ "$t" = "slps_00270" ]; then ldir="asm/nonmatchings"; else ldir="asm/$t/nonmatchings"; fi

  rows_var="ROWS_mm_$t"; rows="${!rows_var:-}"
  rows_var="ROWS_mm2_$t"; rows2="${!rows_var:-}"
  rows="$rows $rows2"

  ok=1
  for row in $rows; do
    off="${row%%:*}"; fn="${row##*:}"
    [ -n "$off" ] || continue
    grep -q "\[${off}, asm, ${fn}\]" "$yaml" || { echo "  RECIPE MISS: [${off}, asm, ${fn}]"; ok=0; continue; }
    sed -i "s|\[${off}, asm, ${fn}\] \+#|[${off}, c,   ${fn}]   #|" "$yaml"
    rm -f "$ldir/$fn.s"
  done
  [ "$ok" = 1 ] || { git checkout -- "$yaml"; FAILED="$FAILED $t(recipe)"; continue; }

  if TARGET="$t" ./tools/verify.sh "$t"; then
    echo "  $t: verify GREEN"
  else
    echo "  $t: verify FAILED - reverting target edits"
    git checkout -- "$yaml"
    for row in $rows; do
      off="${row%%:*}"; fn="${row##*:}"
      [ -n "$off" ] || continue
      git checkout -- "$ldir/$fn.s" 2>/dev/null
      rm -f "src/$fn.c"
    done
    FAILED="$FAILED $t"
  fi
done

echo
if [ -n "$FAILED" ]; then
  echo "LANDING INCOMPLETE, failed targets:$FAILED"
  exit 1
fi
echo "LANDING COMPLETE: next -> judge_unit MulMatrix + MulMatrix2 (both regimes) on the live oracle, spot-judge the three twins, ratchets 664->669, suite, clean_stale_asm"

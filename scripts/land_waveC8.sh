#!/usr/bin/env bash
# land_waveC8.sh - the select_max_param (0xC8) x8 own-row wave landing
# (eighteenth-return NEXT 2; decode pre-proven offline in window
# cron-202610291140: the template screens bytes=EXACT vs the committed slps
# listing (50 words, zero relocations), waveC8_check.py proves the eight
# retail rows byte-identical x8 via the listing hex columns, and the eight
# gen'd units are byte-identical to the template modulo the row-name
# definition).
#
# RUNS IN A RETURN WINDOW with witness 8/8 (the INPUT GATES own the landing
# commit; the offline window that banked this script could not run it).
# Run gen_waveC8_srcs.py FIRST (it emits the eight src/ units).
#
# Per target: flip the yaml row [off, asm, N] -> [off, c,   N] (aligned
# spelling), delete the listing (slps uses the flat asm/nonmatchings path),
# then `make verify TARGET=<t>`. ANY verify failure reverts that target's
# edits (unverified bytes never land). slps runs LAST (the flat-path
# listing + the gp-window first-shot risk). After landing: judge_unit x8 on
# the live oracle (the psyq identity is select_max_param - the judge
# baselines carry it on the pinned targets), ratchets 664 -> 672 (8
# definitions, one mention per file, headers name no siblings - raise +
# provenance entry in the same commit), suite, clean_stale_asm.
#
# Run from the repo root:  sh scripts/land_waveC8.sh
set -u

declare -A C8_OFF=( [slps_00270]=0x14584 [sces_00269]=0x1404C [mainmenu_jp]=0x44F0C [mainmenu_eu]=0x44810 [g3_jp]=0x309F8 [g3_eu]=0x30334 [g3org_jp]=0x2DE94 [g3org_eu]=0x2D788 )
declare -A C8_NAME=( [slps_00270]=func_80036D04 [sces_00269]=func_8003384C [mainmenu_jp]=func_8006E9BC [mainmenu_eu]=func_80064010 [g3_jp]=func_800501F8 [g3_eu]=func_8004FB34 [g3org_jp]=func_800542A4 [g3org_eu]=func_8004CF88 )

TARGETS="${*:-g3_jp g3_eu g3org_jp g3org_eu sces_00269 mainmenu_eu mainmenu_jp slps_00270}"
FAILED=""

for t in $TARGETS; do
  echo "=== $t: landing select_max_param"
  yaml="config/splat.$t.yaml"
  off="${C8_OFF[$t]}"; fn="${C8_NAME[$t]}"
  if [ "$t" = "slps_00270" ]; then ldir="asm/nonmatchings"; else ldir="asm/$t/nonmatchings"; fi

  grep -q "\[${off}, asm, ${fn}\]" "$yaml" || { echo "  RECIPE MISS: [${off}, asm, ${fn}]"; FAILED="$FAILED $t(recipe)"; continue; }
  sed -i "s|\[${off}, asm, ${fn}\] \+#|[${off}, c,   ${fn}]   #|" "$yaml"
  rm -f "$ldir/$fn.s"

  if TARGET="$t" ./tools/verify.sh "$t"; then
    echo "  $t: verify GREEN"
  else
    echo "  $t: verify FAILED - reverting target edits"
    git checkout -- "$yaml"
    git checkout -- "$ldir/$fn.s" 2>/dev/null
    rm -f "src/$fn.c"
    FAILED="$FAILED $t"
  fi
done

echo
if [ -n "$FAILED" ]; then
  echo "LANDING INCOMPLETE, failed targets:$FAILED"
  exit 1
fi
echo "LANDING COMPLETE: next -> judge_unit x8, ratchets 664->672, suite, clean_stale_asm"

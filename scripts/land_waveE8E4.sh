#!/usr/bin/env bash
# land_waveE8E4.sh - the MulRotMatrix (0xE8) / MulRotMatrix0 (0xE4) x7
# own-row wave landing (eighteenth-return NEXT 1; decode pre-proven offline
# in window cron-202610291025: both templates shape=OK bytes=EXACT vs the
# committed slps listings, and the fourteen gen'd units are byte-identical
# to the templates modulo the row-name definition).
#
# RUNS IN A RETURN WINDOW with witness 8/8 (the INPUT GATES own the landing
# commit; the offline window that banked this script could not run it).
# Run gen_waveE8E4_srcs.py FIRST (it emits the fourteen src/ units).
#
# Per target: flip the two yaml rows [off, asm, N] -> [off, c,   N]
# (aligned spelling), delete the two listings (slps uses the flat
# asm/nonmatchings path), then `make verify TARGET=<t>`. ANY verify failure
# reverts that target's edits (unverified bytes never land). slps runs LAST
# (the flat-path listing + the gp-window first-shot risk). After landing:
# judge_unit x14 on the live oracle, ratchets 664 -> 678 (14 definitions,
# one mention per file, headers name no siblings - raise + provenance entry
# in the same commit), suite, clean_stale_asm.
#
# Run from the repo root:  sh scripts/land_waveE8E4.sh
set -u

declare -A E8_OFF=( [sces_00269]=0x145F0 [mainmenu_eu]=0x3DEEC [g3_jp]=0x29FF8 [g3_eu]=0x29A10 [g3org_jp]=0x27494 [g3org_eu]=0x26E64 [slps_00270]=0x14B28 )
declare -A E8_NAME=( [sces_00269]=func_80033DF0 [mainmenu_eu]=func_8005D6EC [g3_jp]=func_800497F8 [g3_eu]=func_80049210 [g3org_jp]=func_80046C94 [g3org_eu]=func_80046664 [slps_00270]=func_80034328 )
declare -A E4_OFF=( [sces_00269]=0x1450C [mainmenu_eu]=0x3DE08 [g3_jp]=0x29F14 [g3_eu]=0x2992C [g3org_jp]=0x273B0 [g3org_eu]=0x26D80 [slps_00270]=0x14A44 )
declare -A E4_NAME=( [sces_00269]=func_80033D0C [mainmenu_eu]=func_8005D608 [g3_jp]=func_80049714 [g3_eu]=func_8004912C [g3org_jp]=func_80046BB0 [g3org_eu]=func_80046580 [slps_00270]=func_80034244 )

TARGETS="${*:-g3_jp g3_eu g3org_jp g3org_eu sces_00269 mainmenu_eu slps_00270}"
FAILED=""

for t in $TARGETS; do
  echo "=== $t: landing MulRotMatrix0 + MulRotMatrix"
  yaml="config/splat.$t.yaml"
  e8off="${E8_OFF[$t]}"; e8="${E8_NAME[$t]}"
  e4off="${E4_OFF[$t]}"; e4="${E4_NAME[$t]}"
  if [ "$t" = "slps_00270" ]; then ldir="asm/nonmatchings"; else ldir="asm/$t/nonmatchings"; fi

  flip() { # off name -> edits yaml in place, returns 0 on success
    grep -q "\[${1}, asm, ${2}\]" "$yaml" || { echo "  RECIPE MISS: [${1}, asm, ${2}]"; return 1; }
    sed -i "s|\[${1}, asm, ${2}\] \+#|\[${1}, c,   ${2}]   #|" "$yaml"
  }
  flip "$e4off" "$e4" && flip "$e8off" "$e8" || { FAILED="$FAILED $t(recipe)"; git checkout -- "$yaml"; continue; }
  rm -f "$ldir/$e4.s" "$ldir/$e8.s"

  if TARGET="$t" ./tools/verify.sh "$t"; then
    echo "  $t: verify GREEN"
  else
    echo "  $t: verify FAILED - reverting target edits"
    git checkout -- "$yaml"
    git checkout -- "$ldir/$e4.s" "$ldir/$e8.s" 2>/dev/null
    rm -f "src/$e4.c" "src/$e8.c"
    FAILED="$FAILED $t"
  fi
done

echo
if [ -n "$FAILED" ]; then
  echo "LANDING INCOMPLETE, failed targets:$FAILED"
  exit 1
fi
echo "LANDING COMPLETE x${TARGETS%% *}: next -> judge_unit x14, ratchets 664->678, suite, clean_stale_asm"

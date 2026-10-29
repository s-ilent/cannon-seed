#!/bin/bash
# land_wave34_0C.sh - the two fresh x8 own-row waves landing (the eighteenth
# return's phase F items; decodes pre-proven offline in window
# cron-202610291410: both templates screen bytes=EXACT vs the committed slps
# listings (13 / 3 words, zero relocations), wave34_0C_check.py proves the
# seven retail rows byte-identical x7 per wave via the listing hex columns
# and reports the parent-bound mainmenu_jp interiors (func_80085B5C +0x168,
# func_8007FFAC +0x1BC - they land with their parent rows, never alone),
# and the fourteen gen'd units are byte-identical to the templates modulo
# the row-name definitions).
#
# RUNS IN A RETURN WINDOW with witness 8/8 (the INPUT GATES own the landing
# commits; the offline window that banked this script could not run it).
# Run gen_wave34_0C_srcs.py FIRST (it emits the fourteen src/ units).
#
# Per target per wave: flip the yaml row [off, asm, N] -> [off, c,   N]
# (aligned spelling), delete the listing (slps uses the flat
# asm/nonmatchings path), then `./tools/verify.sh <t>`. ANY verify failure
# reverts that target's edits (unverified bytes never land). slps runs LAST
# in each wave (the flat-path listing + the gp-window first-shot risk).
# After landing: judge_unit x7 per wave on the live oracle, ratchets +7 per
# wave from the tree's CURRENT count (recompute in landing order - the
# banked E8E4/C8/10C/88 waves may land before this script), suite,
# clean_stale_asm.
#
# Run from the repo root:  sh scripts/land_wave34_0C.sh
set -u

declare -A W34_OFF=( [slps_00270]=0x1D0F8 [sces_00269]=0x1CEEC [mainmenu_eu]=0x59AC0 [g3_jp]=0x43B4C [g3_eu]=0x444DC [g3org_jp]=0x40FE8 [g3org_eu]=0x41930 )
declare -A W34_NAME=( [slps_00270]=func_8003C8F8 [sces_00269]=func_8003C6EC [mainmenu_eu]=func_800792C0 [g3_jp]=func_8006334C [g3_eu]=func_80063CDC [g3org_jp]=func_800607E8 [g3org_eu]=func_80061130 )
declare -A W0C_OFF=( [slps_00270]=0x183F4 [sces_00269]=0x17FA8 [mainmenu_eu]=0x54900 [g3_jp]=0x3EE48 [g3_eu]=0x3F598 [g3org_jp]=0x3C2E4 [g3org_eu]=0x3C9EC )
declare -A W0C_NAME=( [slps_00270]=func_80037BF4 [sces_00269]=func_800377A8 [mainmenu_eu]=func_80074100 [g3_jp]=func_8005E648 [g3_eu]=func_8005ED98 [g3org_jp]=func_8005BAE4 [g3org_eu]=func_8005C1EC )

land_wave() {
  local tag="$1"; shift
  local -a ts=("$@")
  local -n OFF="${tag}_OFF"
  local -n NAME="${tag}_NAME"
  local FAILED=""
  for t in "${ts[@]}"; do
    echo "=== $t: landing ${tag} (${NAME[$t]})"
    local yaml="config/splat.$t.yaml"
    local off="${OFF[$t]}"; local fn="${NAME[$t]}"
    local ldir="asm/$t/nonmatchings"
    if [ "$t" = "slps_00270" ]; then ldir="asm/nonmatchings"; fi

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
  if [ -n "$FAILED" ]; then
    echo "WAVE ${tag} INCOMPLETE, failed targets:$FAILED"
    return 1
  fi
  echo "WAVE ${tag} COMPLETE"
  return 0
}

# per wave: non-slps first, slps LAST
ORDER="g3_jp g3_eu g3org_jp g3org_eu sces_00269 mainmenu_eu slps_00270"
RC=0
land_wave W34 $ORDER || RC=1
land_wave W0C $ORDER || RC=1

echo
if [ "$RC" -ne 0 ]; then
  echo "LANDING INCOMPLETE (see per-wave lines above)"
  exit 1
fi
echo "LANDING COMPLETE: next -> judge_unit x7 per wave, ratchets +7 per wave from the tree's count, suite, clean_stale_asm"

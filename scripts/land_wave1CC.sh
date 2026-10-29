#!/usr/bin/env bash
# land_wave1CC.sh - the 0x1CC recursive-triangle-subdivision x20 own-row
# wave landing (the 27th window's NEXT 1; decode + landing prep banked in
# the 26th window cron-202610292127: ONE hand-asm template
# scripts/wave1CC/tri_subdiv.c screens bytes=EXACT x20 against every
# member's committed listing, zero absolute relocations, five interior
# chunk labels row-local with zero exterior references).
#
# RUNS IN A RETURN WINDOW with witness 8/8 (the INPUT GATES own the
# landing commit). Run gen_wave1CC_srcs.py FIRST (it emits the twenty
# src units - eighteen flat + TWO PER-TARGET, see below).
#
# CROSS-TARGET WALK-NAME COLLISIONS (this window's discovery): two of the
# twenty walk names are already TRACKED flat src units of OTHER targets'
# landed rows - src/func_8006F34C.c is g3_jp's landed 0x10 sdk row
# (a29e899d, _spu_getInTransfer) and src/func_8005AE70.c is mainmenu_eu's
# landed 0x30 row (08388577). One flat file cannot serve two builds, so
# those two members land PER-TARGET at src/<target>/<fn>.c and
# tools/build.sh + tools/judge_unit.py prefer src/$TARGET/$name.c when
# present (byte-inert where unused: mainmenu_jp verified GREEN + suite
# 85/85 on the patched pipeline BEFORE any flip).
#
# Per target: flip the four yaml rows [off, asm, N] -> [off, c,   N]
# (aligned spelling), delete the four listings, then
# TARGET=$t ./tools/verify.sh "$t". ANY verify failure reverts that
# target's edits (unverified bytes never land). Landing order keeps the
# two collision targets LAST: g3org_jp g3org_eu g3_jp mainmenu_eu g3_eu.
# After landing: judge_unit x20 on the live oracle, ratchets recomputed
# from the tree (the banked +20 assumed the C one-mention form; the bare
# file-scope __asm__ unit is the wave88 two-mention .globl+label form ->
# +40 expected, 713->753, the wave88 expectation-vs-tree lesson again),
# suite, clean_stale_asm.
#
# Run from the repo root:  sh scripts/land_wave1CC.sh
set -u

declare -A M_OFF=(
  [mainmenu_eu]="0x4E85C:func_8006E05C 0x4F04C:func_8006E84C 0x4FB4C:func_8006F34C 0x5046C:func_8006FC6C"
  [g3_jp]="0x3A93C:func_8005A13C 0x3B12C:func_8005A92C 0x3BC2C:func_8005B42C 0x3C54C:func_8005BD4C"
  [g3_eu]="0x3A380:func_80059B80 0x3AB70:func_8005A370 0x3B670:func_8005AE70 0x3BF90:func_8005B790"
  [g3org_jp]="0x37DD8:func_800575D8 0x385C8:func_80057DC8 0x390C8:func_800588C8 0x399E8:func_800591E8"
  [g3org_eu]="0x377D4:func_80056FD4 0x37FC4:func_800577C4 0x38AC4:func_800582C4 0x393E4:func_80058BE4"
)

TARGETS="${*:-g3org_jp g3org_eu g3_jp mainmenu_eu g3_eu}"
FAILED=""

for t in $TARGETS; do
  echo "=== $t: landing the 0x1CC x4"
  yaml="config/splat.$t.yaml"
  ldir="asm/$t/nonmatchings"
  flipped=0
  for pair in ${M_OFF[$t]}; do
    off="${pair%%:*}"; fn="${pair##*:}"
    if ! grep -q "\[${off}, asm, ${fn}\]" "$yaml"; then
      echo "  RECIPE MISS: [${off}, asm, ${fn}]"
      FAILED="$FAILED $t(recipe)"
      break
    fi
    sed -i "s|\[${off}, asm, ${fn}\] \+#|[${off}, c,   ${fn}]   #|" "$yaml"
    if ! grep -qE "\[${off}, c, +${fn}\]" "$yaml"; then
      echo "  SED MISS: ${off} ${fn} did not flip"
      git checkout -- "$yaml"
      FAILED="$FAILED $t(sed)"
      break
    fi
    rm -f "$ldir/$fn.s"
    flipped=$((flipped + 1))
  done
  [ "$flipped" -eq 4 ] || { echo "  $t: flip incomplete ($flipped/4)"; continue; }

  if TARGET="$t" ./tools/verify.sh "$t"; then
    echo "  $t: verify GREEN"
  else
    echo "  $t: verify FAILED - reverting target edits"
    git checkout -- "$yaml"
    for pair in ${M_OFF[$t]}; do
      fn="${pair##*:}"
      git checkout -- "$ldir/$fn.s" 2>/dev/null
      rm -f "src/$fn.c" "src/$t/$fn.c"
    done
    rmdir "src/$t" 2>/dev/null
    FAILED="$FAILED $t"
  fi
done

echo
if [ -n "$FAILED" ]; then
  echo "LANDING INCOMPLETE, failed targets:$FAILED"
  exit 1
fi
echo "LANDING COMPLETE: next -> judge_unit x20 (five targets x4), ratchets recompute from the tree, suite, clean_stale_asm"

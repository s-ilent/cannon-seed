#!/usr/bin/env bash
# land_wave88.sh - the memmove (0x90) x4 own-row wave landing (20th-return
# NEXT 3; decode pre-proven offline in window cron-202610291255: the
# hand-asm template screens bytes=EXACT vs the committed slps listing (36
# words incl. the 2 zero tail words, zero relocations), wave88_check.py /
# wave10C_check.py prove the four retail rows byte-identical x4 via the
# listing hex columns, and the gen'd units are byte-identical to the
# template modulo the .globl/label row name).
#
# RUNS IN A RETURN WINDOW with witness 8/8 (the INPUT GATES own the landing
# commit; the offline window that banked this script could not run it).
# Run gen_wave88_srcs.py FIRST (it emits the four src/ units).
#
# Per target: flip the yaml row [off, asm, N] -> [off, c,   N] (aligned
# spelling), delete the listing (slps uses the flat asm/nonmatchings path),
# then `make verify TARGET=<t>`. ANY verify failure reverts that target's
# edits (unverified bytes never land). g3org_jp, g3_jp, mainmenu_jp in that
# order, slps LAST (the flat-path listing + the gp-window first-shot risk).
# After landing: judge_unit memmove both regimes on the live oracle (the
# psyq identity is memmove - all four targets carry the curated pin),
# ratchets 664 -> 673 IF the 10C wave did not land first (its own note
# moves 664 -> 669; recompute this raise from the tree), suite,
# clean_stale_asm.
#
# Run from the repo root:  sh scripts/land_wave88.sh
set -u

declare -A MM_OFF=( [slps_00270]=0xF1F0 [mainmenu_jp]=0x3DC0C [g3_jp]=0x295CC [g3org_jp]=0x26A68 )
declare -A MM_NAME=( [slps_00270]=func_80030D90 [mainmenu_jp]=func_8006661C [g3_jp]=func_8004EF2C [g3org_jp]=func_8004BDD8 )

TARGETS="${*:-g3org_jp g3_jp mainmenu_jp slps_00270}"
FAILED=""

for t in $TARGETS; do
  echo "=== $t: landing memmove"
  yaml="config/splat.$t.yaml"
  off="${MM_OFF[$t]}"; fn="${MM_NAME[$t]}"
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
echo "LANDING COMPLETE: next -> judge_unit memmove both regimes on the live oracle, ratchets (recompute from the tree), suite, clean_stale_asm"

#!/usr/bin/env bash
# land_transposematrix.sh - execute the TransposeMatrix x6 whole-row flip
# (window cron-202610252019; src/TransposeMatrix.c word-proven 20/20 at
# all six sites by scripts/prove_transposematrix.py).
# Per target: flip the row asm->c with the curated name, delete the old
# .s, make verify. ANY verify failure reverts that target's edits
# (unverified bytes never land) and reports. Run from the repo root with
# the witness 8/8.
set -u

declare -A ROWS=(
  [slps_00270]="0x14668, func_80036DE8"
  [sces_00269]="0x14130, func_800368B0"
  [g3_jp]="0x30ADC, func_8005760C"
  [g3_eu]="0x30418, func_80056E18"
  [g3org_jp]="0x2DF78, func_80054388"
  [g3org_eu]="0x2D86C, func_80053C7C"
)

TARGETS="${*:-slps_00270 sces_00269 g3_jp g3_eu g3org_jp g3org_eu}"
FAILED=""
for t in $TARGETS; do
  echo "=== $t: flipping 1 row"
  git checkout -- "config/splat.$t.yaml" 2>/dev/null
  ok=1
  while IFS= read -r row; do
    [ -z "$row" ] && continue
    off="${row%%, *}"
    name="${row##*, }"
    line=$(rg -n "^\s*- \[${off}, asm, ${name}\]" "config/splat.$t.yaml" | head -1 | cut -d: -f1)
    if [ -z "$line" ]; then
      echo "  RECIPE MISS: - [${off}, asm, ${name}] not found in splat.$t.yaml"
      ok=0; break
    fi
    sed -i "${line}s/, asm, ${name}\]/, c, TransposeMatrix]/" "config/splat.$t.yaml"
    sfile="asm/$t/nonmatchings/${name}.s"
    [ "$t" = "slps_00270" ] && sfile="asm/nonmatchings/${name}.s"
    if [ -f "$sfile" ]; then rm "$sfile"; echo "  flipped ${off} ${name} -> TransposeMatrix (+ removed $(basename "$sfile"))"; else
      echo "  flipped ${off} ${name} -> TransposeMatrix (.s not present)"; fi
  done <<< "${ROWS[$t]}"
  if [ "$ok" -eq 0 ]; then
    git checkout -- "config/splat.$t.yaml"; FAILED="$FAILED $t(recipe)"; continue
  fi
  if make verify TARGET="$t" >/tmp/verify_$t.log 2>&1; then
    echo "  $t: GREEN"
  else
    echo "  $t: VERIFY FAIL - reverting"
    git checkout -- "config/splat.$t.yaml"
    case "$t" in
      slps_00270) git checkout -- "asm/nonmatchings/func_80036DE8.s" 2>/dev/null;;
      *) git checkout -- "asm/$t/nonmatchings/${ROWS[$t]##*, }.s" 2>/dev/null;;
    esac
    FAILED="$FAILED $t(verify)"
    tail -5 /tmp/verify_$t.log
  fi
done

echo
if [ -n "$FAILED" ]; then
  echo "FAILED:${FAILED}"
  exit 1
fi
echo "ALL TARGETS GREEN"

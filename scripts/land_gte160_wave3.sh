#!/usr/bin/env bash
# land_gte160_wave3.sh - the 0x160 GTE transform host's cross-target copies
# (twelfth-return NEXT item 1). The g3_eu func_80048EC0 whole-row landing
# (05d05573) has six byte-identical EXACT-EXTENT copies across the other
# game/boot targets (byte-search over the fresh per-sector extracts, one hit
# per target): sces_00269 func_80033AA0, mainmenu_eu func_8005D39C,
# g3org_eu func_80046314, slps_00270 func_80033FD8, g3_jp func_800494A8,
# g3org_jp func_80046944 - all "# 0x160 sdk" rows, all 352 bytes equal.
# Per target: one-line yaml flip [off, asm, NAME] -> [off, c, func_80048EC0],
# delete the row's .s listing (slps uses the flat asm/nonmatchings path),
# make verify. ANY verify failure reverts that target's edits (unverified
# bytes never land). slps runs LAST (the gp-window first-shot risk).
# mainmenu_jp's copy is NOT here: it sits INSIDE the 0x520 data row
# data_80066CF4 at +8 (0x3E1BC) - a re-carve candidate with its own
# evidence pass, not a clean flip. Run from the repo root, witness 8/8.
set -u

NEW=func_80048EC0
declare -A ROWS=(
  [sces_00269]="0x142A0, func_80033AA0"
  [mainmenu_eu]="0x3DB9C, func_8005D39C"
  [g3org_eu]="0x26B14, func_80046314"
  [g3_jp]="0x29CA8, func_800494A8"
  [g3org_jp]="0x27144, func_80046944"
  [slps_00270]="0x147D8, func_80033FD8"
)

TARGETS="${*:-g3_jp g3org_eu g3org_jp sces_00269 mainmenu_eu slps_00270}"
FAILED=""
for t in $TARGETS; do
  echo "=== $t: flipping 1 row to ${NEW}"
  git checkout -- "config/splat.$t.yaml" 2>/dev/null
  ok=1
  row=$(echo "${ROWS[$t]}" | head -1)
  off="${row%%, *}"
  name="${row##*, }"
  line=$(grep -n "^\s*- \[${off}, asm, ${name}\]" "config/splat.$t.yaml" | head -1 | cut -d: -f1)
  if [ -z "$line" ]; then
    echo "  RECIPE MISS: - [${off}, asm, ${name}] not found in splat.$t.yaml"
    FAILED="$FAILED $t(recipe)"; continue
  fi
  sed -i "${line}s/- \[${off}, asm, ${name}\]/- [${off}, c,   ${NEW}]/" "config/splat.$t.yaml"
  if ! grep -q "^\s*- \[${off}, c,   ${NEW}\]" "config/splat.$t.yaml"; then
    echo "  FLIP MISS: sed did not produce the c row"; git checkout -- "config/splat.$t.yaml"
    FAILED="$FAILED $t(flip)"; continue
  fi
  sfile="asm/$t/nonmatchings/${name}.s"
  [ -f "$sfile" ] || sfile="asm/nonmatchings/${name}.s"
  if [ -f "$sfile" ]; then rm "$sfile"; echo "  flipped ${off} ${name} -> ${NEW} (+ removed ${sfile})"; else
    echo "  flipped ${off} ${name} -> ${NEW} (.s not present - clean_stale_asm will sweep)"; fi
  if make verify TARGET="$t" >/tmp/verify_w3_$t.log 2>&1; then
    echo "  VERIFY GREEN: $t"
  else
    echo "  VERIFY FAILED: $t - reverting (tail below)"
    tail -8 /tmp/verify_w3_$t.log
    git checkout -- "config/splat.$t.yaml"
    git checkout -- "asm/$t/nonmatchings/" 2>/dev/null
    git checkout -- "asm/nonmatchings/" 2>/dev/null
    FAILED="$FAILED $t(verify)"
  fi
done
echo "=== LANDED (revert-free) except:${FAILED:- none}"

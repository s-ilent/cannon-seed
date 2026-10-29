#!/usr/bin/env bash
# land_gte110_wave4.sh - the 0x110 GTE rotation-matrix composer's seven
# staged merges (thirteenth-return NEXT item 1). The g3_eu whole-row merge
# (41c2e54a) turned [0x29AF8 0xe0 asm func_800492F8] + [0x29BD8 0x30 c
# func_8005DED4] into one [0x29AF8 0x110 c func_800492F8]; the full 0x110
# needle hits EXACTLY ONCE in every other baseline (wave-4 pre-check,
# cron-20261028-2311): sces_00269 0x146D8, g3org_eu 0x26F4C, slps_00270
# 0x14C10, g3_jp 0x2A0E0, g3org_jp 0x2757C, mainmenu_eu 0x3DFD4,
# mainmenu_jp 0x3E5F4.
# NOT in this script (both held on purpose):
#   - mainmenu_eu: REAL NAME COLLISION - symbols.mainmenu_eu.txt line 1991
#     already labels VA 0x800492F8 (off 0x29AF8, branch target) as
#     func_800492F8; flipping the 0x3DFD4 row to that name would put the
#     name on a second VA (wave-2's E3DC decision class). Stays asm.
#   - mainmenu_jp: the head 0xe0 sits INSIDE the 0x520 data row
#     data_80066CF4 (0x3E1B4..0x3E6D4) - needs the parked re-carve
#     evidence pass, not a row flip.
# Per target: replace the [off, asm, HEAD] row with [off, c, func_800492F8]
# # 0x110 sdk, DELETE the [off+0xe0, c, func_8005DED4] tail row, delete the
# head's .s listing (slps uses the flat asm/nonmatchings path), make verify.
# ANY verify failure reverts that target's edits (unverified bytes never
# land). slps runs LAST (the gp-window first-shot risk). Run from the repo
# root, witness 8/8. After landing: judge_unit per target, ratchets, suite.
set -u

NEW=func_800492F8
declare -A HEAD_OFF=(
  [sces_00269]="0x146D8"
  [g3org_eu]="0x26F4C"
  [g3_jp]="0x2A0E0"
  [g3org_jp]="0x2757C"
  [slps_00270]="0x14C10"
)
declare -A HEAD_NAME=(
  [sces_00269]="func_80033ED8"
  [g3org_eu]="func_8004674C"
  [g3_jp]="func_800498E0"
  [g3org_jp]="func_80046D7C"
  [slps_00270]="func_80034410"
)
declare -A TAIL_OFF=(
  [sces_00269]="0x147B8"
  [g3org_eu]="0x2702C"
  [g3_jp]="0x2A1C0"
  [g3org_jp]="0x2765C"
  [slps_00270]="0x14CF0"
)

TARGETS="${*:-g3_jp g3org_eu g3org_jp sces_00269 slps_00270}"
FAILED=""
for t in $TARGETS; do
  echo "=== $t: merging 0x110 rows into ${NEW}"
  git checkout -- "config/splat.$t.yaml" 2>/dev/null
  off="${HEAD_OFF[$t]}"; head="${HEAD_NAME[$t]}"; tail="${TAIL_OFF[$t]}"
  yaml="config/splat.$t.yaml"
  hline=$(grep -n "^\s*- \[${off}, asm, ${head}\]" "$yaml" | head -1 | cut -d: -f1)
  if [ -z "$hline" ]; then
    echo "  RECIPE MISS: - [${off}, asm, ${head}] not found"; FAILED="$FAILED $t(recipe)"; continue
  fi
  tline=$(grep -n "^\s*- \[${tail}, c, func_8005DED4\]" "$yaml" | head -1 | cut -d: -f1)
  if [ -z "$tline" ]; then
    echo "  RECIPE MISS: - [${tail}, c, func_8005DED4] not found"; FAILED="$FAILED $t(tail)"; continue
  fi
  sed -i "${hline}s|- \[${off}, asm, ${head}\].*|- [${off}, c,   ${NEW}]   # 0x110 sdk|" "$yaml"
  sed -i "${tline}d" "$yaml"
  if ! grep -q "^\s*- \[${off}, c,   ${NEW}\]   # 0x110 sdk" "$yaml"; then
    echo "  FLIP MISS: sed did not produce the merged row"; git checkout -- "$yaml"
    FAILED="$FAILED $t(flip)"; continue
  fi
  sfile="asm/$t/nonmatchings/${head}.s"
  [ -f "$sfile" ] || sfile="asm/nonmatchings/${head}.s"
  if [ -f "$sfile" ]; then rm "$sfile"; echo "  merged ${off}+${tail} -> ${NEW} (removed ${sfile})"; else
    echo "  merged ${off}+${tail} -> ${NEW} (.s not present - clean_stale_asm will sweep)"; fi
  if make verify TARGET="$t" >/tmp/verify_w4_$t.log 2>&1; then
    echo "  VERIFY GREEN: $t"
  else
    echo "  VERIFY FAILED: $t - reverting (tail below)"
    tail -8 /tmp/verify_w4_$t.log
    git checkout -- "$yaml"
    git checkout -- "asm/$t/nonmatchings/" 2>/dev/null
    git checkout -- "asm/nonmatchings/" 2>/dev/null
    FAILED="$FAILED $t(verify)"
  fi
done
echo "=== LANDED (revert-free) except:${FAILED:- none}"

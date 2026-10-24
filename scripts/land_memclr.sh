#!/usr/bin/env bash
# land_memclr.sh - execute the staged memclr family flip (window banked
# recipes; 12 build-inert src units, one-line yaml asm->c flip per row).
# Per target: flip both rows, delete the two .s files, make verify.
# ANY verify failure reverts that target's edits (unverified bytes never
# land) and reports. Run from the repo root with the witness 8/8.
set -u

declare -A ROWS=(
  [g3_eu]="0x2B1F8, func_8004A9F8
0x2B324, func_80051144"
  [sces_00269]="0xF83C, func_8002F03C
0xF584, func_80031124"
  [g3_jp]="0x2B500, func_80051320
0x2B994, func_800518E4"
  [g3org_eu]="0x28394, func_8004DA94
0x28778, func_8004DE78"
  [g3org_jp]="0x2899C, func_8004E1CC
0x28E30, func_8004E660"
  [mainmenu_eu]="0x3F41C, func_800681BC
0x3F800, func_800686D0"
  [mainmenu_jp]="0x3FA14, func_800688E4
0x3FEA8, func_80068D78"
)

TARGETS="${*:-g3_eu sces_00269 g3_jp g3org_eu g3org_jp mainmenu_eu mainmenu_jp}"
FAILED=""
for t in $TARGETS; do
  echo "=== $t: flipping 2 rows"
  # snapshot for revert
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
    sed -i "${line}s/, asm, /, c,   /" "config/splat.$t.yaml"
    sfile="asm/$t/nonmatchings/${name}.s"
    if [ -f "$sfile" ]; then rm "$sfile"; echo "  flipped ${off} ${name} (+ removed $(basename "$sfile"))"; else
      echo "  flipped ${off} ${name} (.s not present - clean_stale_asm will sweep)"; fi
  done <<< "${ROWS[$t]}"
  if [ "$ok" -eq 0 ]; then
    git checkout -- "config/splat.$t.yaml"; FAILED="$FAILED $t(recipe)"; continue
  fi
  if make verify TARGET="$t" >/tmp/verify_$t.log 2>&1; then
    echo "  VERIFY GREEN: $t"
  else
    echo "  VERIFY FAILED: $t - reverting (tail below)"
    tail -8 /tmp/verify_$t.log
    git checkout -- "config/splat.$t.yaml"
    # restore any deleted .s from HEAD
    git checkout -- "asm/$t/nonmatchings/" 2>/dev/null
    FAILED="$FAILED $t(verify)"
  fi
done
echo "=== LANDED (revert-free) except:${FAILED:- none}"

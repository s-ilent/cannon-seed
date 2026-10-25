#!/usr/bin/env bash
# land_libsn_hosts.sh - execute the LIBSN host-call wave (window
# cron-202610252019; src/PCopen.c / src/PClseek.c / src/_SN_write.c
# word-proven at all ten sites by scripts/prove_libsn_hosts.py).
# Per target: flip the rows asm->c with the curated names, delete the
# old .s files, make verify. ANY verify failure reverts that target's
# edits (unverified bytes never land) and reports. Run from the repo
# root with the witness 8/8.
set -u

declare -A ROWS=(
  [g3_jp]="0x2969C, func_8004EFFC, PCopen
0x296BC, func_8004F01C, PClseek
0x297B0, func_8004F110, _SN_write"
  [g3_eu]="0x290B4, func_8004EA14, PCopen
0x290D4, func_8004EA34, PClseek
0x291C8, func_8004EB28, _SN_write"
  [g3org_jp]="0x26B38, func_8004BEA8, PCopen
0x26C4C, func_8004BFBC, _SN_write"
  [g3org_eu]="0x26508, func_8004B748, PCopen
0x2661C, func_8004B85C, _SN_write"
)

TARGETS="${*:-g3_jp g3_eu g3org_jp g3org_eu}"
FAILED=""
for t in $TARGETS; do
  echo "=== $t: flipping rows"
  git checkout -- "config/splat.$t.yaml" 2>/dev/null
  ok=1
  removed=""
  while IFS= read -r row; do
    [ -z "$row" ] && continue
    off="$(echo "$row" | cut -d, -f1)"
    name="$(echo "$row" | cut -d, -f2 | sed 's/^ *//')"
    cur="$(echo "$row" | cut -d, -f3 | sed 's/^ *//')"
    line=$(rg -n "^\s*- \[${off}, asm, ${name}\]" "config/splat.$t.yaml" | head -1 | cut -d: -f1)
    if [ -z "$line" ]; then
      echo "  RECIPE MISS: - [${off}, asm, ${name}] not found in splat.$t.yaml"
      ok=0; break
    fi
    sed -i "${line}s/, asm, ${name}\]/, c, ${cur}]/" "config/splat.$t.yaml"
    sfile="asm/$t/nonmatchings/${name}.s"
    if [ -f "$sfile" ]; then rm "$sfile"; removed="$removed $sfile"
      echo "  flipped ${off} ${name} -> ${cur} (+ removed $(basename "$sfile"))"
    else
      echo "  flipped ${off} ${name} -> ${cur} (.s not present)"
    fi
  done <<< "${ROWS[$t]}"
  if [ "$ok" -eq 0 ]; then
    git checkout -- "config/splat.$t.yaml"; FAILED="$FAILED $t(recipe)"; continue
  fi
  if make verify TARGET="$t" >/tmp/verify_$t.log 2>&1; then
    echo "  $t: GREEN"
  else
    echo "  $t: VERIFY FAIL - reverting"
    git checkout -- "config/splat.$t.yaml"
    for f in $removed; do git checkout -- "$f" 2>/dev/null; done
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

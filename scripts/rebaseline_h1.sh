#!/bin/sh
# rebaseline_h1.sh - the word_diff -G0 fix's H.1 re-baseline (runbook H.1,
# cron-202611052113). Rebuilds each anchor draft's .mas.s through the real
# cc.sh -S pipeline (STOP_AT_ASM, knob-alive unit flags), then word_diffs it
# under the FIXED instrument (-G0, mirroring cc.sh's as step) and mini-links
# the SIZE. Output = one verdict line per anchor; the runbook H.1 ladder and
# the twin table get the new aligned counts.
#
# Usage: sh scripts/rebaseline_h1.sh [draftN ...]   (default: the full set)
set -e
cd "$(dirname "$0")/.."
LD_PATH="${TOOLROOT:-/home/z/my-project/tools-local/mipsel-root}/usr/lib/x86_64-linux-gnu"
ROW="asm/g3org_jp/nonmatchings/func_80068064.s"
VA0=0x80068064; VA1=0x800684AC

d="${1:-all}"
if [ "$d" = all ]; then
  set -- 20 38 46 47 53 57 59
fi

for n in "$@"; do
  src="probes/gcc263/SsVabOpenHeadWithMode_draft${n}.c"
  [ -f "$src" ] || { echo "draft$n: MISSING $src"; continue; }
  STOP_AT_ASM=1 MASPSX_UNIT_FLAGS="--addiu-at on" \
    tools/cc.sh -o "/tmp/wd${n}.o" "$src" 2>/dev/null
  echo "=== draft${n}"
  LD_LIBRARY_PATH="$LD_PATH" python3 scripts/word_diff.py \
    "/tmp/wd${n}.mas.s" "$ROW" "$VA0" "$VA1" 2>&1 | head -2
  python3 tools/minilink.py g3org_jp SsVabOpenHeadWithMode "$src" 48864 2>&1 | tail -1
done
echo "=== H.1 re-baseline done"

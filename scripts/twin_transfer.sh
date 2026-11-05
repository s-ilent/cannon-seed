#!/bin/sh
# twin_transfer.sh - the region-twin transfer wave runner (runbook, twin-prep
# step 2, cron-202611051843). Per twin: minilink the parked form against the
# twin's own symbols at the twin's rom offset, then word_diff the fresh
# build/judge/<unit>.mas.s against the twin's own row over VA..VA+0x448.
# minilink OVERWRITES the shared work dir each run, so the word_diff MUST
# follow its minilink immediately - never batch the minilinks first.
#
# Usage: sh scripts/twin_transfer.sh <draft-file> <unit-name>
# (defaults: the d53 parked form, SsVabOpenHeadWithMode)
set -e
cd "$(dirname "$0")/.."
LD_PATH="${TOOLROOT:-/home/z/my-project/tools-local/mipsel-root}/usr/lib/x86_64-linux-gnu"
DRAFT="${1:-probes/gcc263/SsVabOpenHeadWithMode_draft53.c}"
UNIT="${2:-SsVabOpenHeadWithMode}"
MAS="build/judge/${UNIT}.mas.s"

# target  rom_hex  row-file                                      va          end-va
run_twin() {
  tgt="$1"; rom="$2"; row="$3"; va="$4"; end="$5"
  echo "=== $tgt rom 0x$rom row $row"
  python3 tools/minilink.py "$tgt" "$UNIT" "$DRAFT" "$rom" 2>&1 | tail -1
  LD_LIBRARY_PATH="$LD_PATH" python3 scripts/word_diff.py "$MAS" "$row" "$va" "$end" 2>&1 | head -2
}

run_twin g3org_eu    493D4 asm/g3org_eu/nonmatchings/func_80068BD4.s    0x80068BD4 0x8006901C
run_twin g3_jp       4B3C8 asm/g3_jp/nonmatchings/func_8006ABC8.s       0x8006ABC8 0x8006B010
run_twin g3_eu       4BF80 asm/g3_eu/nonmatchings/func_8006B780.s       0x8006B780 0x8006BBC8
run_twin mainmenu_eu 61564 asm/mainmenu_eu/nonmatchings/func_80080D64.s 0x80080D64 0x800811AC
run_twin sces_00269  24990 asm/sces_00269/nonmatchings/func_80049840.s  0x80044190 0x800445D8
# mainmenu_jp (0x609E4, interior of func_8008E714.s) and slps_00270
# (0x24974, asm/nonmatchings/func_80049824.s) were measured in the step-1
# window; extend the list if the parked form changes.
echo "=== twin wave done"

#!/bin/sh
# probe787_flags.sh - the func_80078724 (CdGetToc2) retail flag-set probe.
#
# The cron-202611030028 window REFINED the banked -O1 finding: the decode
# block's allocation (pins a0/a1, hi nibbles in v-regs with the v1/v0 swap,
# the x10 chain of the last decode in v1 so its final addu can ride the
# verbose-guard bnez delay) is reproduced NOT by plain -O1 but by
# -O2 -fno-strength-reduce (measured: the 63-word decode gap closes to a
# handful of words; the loop call block's hoisted arg setup is also -O2
# native). Plain -O2 differs by the loop-carried {min,max} strength-reduced
# basis (the 1358 window's SIZE +24 measurement) — so the loop discriminator
# is the strength-reduction pass, not the -O level. Residual at -O2-fnsr:
# the rp/track s-reg pair swap, the lo2 andi destination (dead-pin reuse
# vs the pin itself), and a few sched1 store/sink placements.
#
# Usage: sh scripts/probe787_flags.sh            # run the flag matrix
# The script flips the yaml row to c for the judge and RESTORES it after;
# it never leaves the tree dirty (the row stays asm until the ladder lands).
set -e
cd "$(dirname "$0")/.."
YAML=config/splat.mainmenu_eu.yaml
restore() { git checkout -- "$YAML" 2>/dev/null || true; }
trap restore EXIT
# the judge needs a c row; flip it for the probe (restored on exit)
python3 - <<'EOF'
import re
p = "config/splat.mainmenu_eu.yaml"
s = open(p).read()
s2 = s.replace("- [0x58F24, asm, func_80078724]", "- [0x58F24, c,   func_80078724]")
assert s2 != s, "asm row not found"
open(p, "w").write(s2)
EOF

judge_with() {
    desc="$1"; shift
    cp scripts/deferred_func_80078724.c src/mainmenu_eu/func_80078724.c
    # flag set is passed through the environment (CC1FLAGS_EXTRA probe hook)
    env "$@" python3 tools/judge_unit.py mainmenu_eu func_80078724 2>&1 | head -1 \
        | sed "s/^/[$desc] /"
    rm -f src/mainmenu_eu/func_80078724.c
}

# -O1 (the banked 1358 baseline)
sed 's/cc-post: cc1-O1/cc-post: cc1-O1/' scripts/deferred_func_80078724.c \
    > src/mainmenu_eu/func_80078724.c
python3 tools/judge_unit.py mainmenu_eu func_80078724 2>&1 | head -1 | sed 's/^/[-O1 as banked] /'
rm -f src/mainmenu_eu/func_80078724.c

# -O2 plain (the 1358 window's SIZE +24 measurement); rule 11's prologue
# anchor is -O1-shaped — at -O2 the hoist is native, so the marker comes off
sed -e 's/cc-post: cc1-O1/cc-post: off1/' \
    -e 's/cc-post: prologue-param-first/cc-post: off2/' \
    scripts/deferred_func_80078724.c > src/mainmenu_eu/func_80078724.c
python3 tools/judge_unit.py mainmenu_eu func_80078724 2>&1 | head -1 | sed 's/^/[-O2 plain] /'
rm -f src/mainmenu_eu/func_80078724.c

# -O2 -fno-strength-reduce (the refined hypothesis)
sed -e 's/cc-post: cc1-O1/cc-post: off1/' \
    -e 's/cc-post: prologue-param-first/cc-post: off2/' \
    scripts/deferred_func_80078724.c > src/mainmenu_eu/func_80078724.c
CC1FLAGS_EXTRA="-fno-strength-reduce" \
    python3 tools/judge_unit.py mainmenu_eu func_80078724 2>&1 | head -1 \
    | sed 's/^/[-O2 -fno-strength-reduce] /'
rm -f src/mainmenu_eu/func_80078724.c
echo "probe done (yaml restored, scratch removed)"

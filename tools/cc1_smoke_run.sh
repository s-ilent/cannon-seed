#!/bin/sh
# Run the cc1 modified-compiler mechanism smoke (probes/gcc263/cc1_smoke*.c)
# stock vs patched and report the two gates:
#
#   RENDER GATE  - stock .gcc.s == patched .gcc.s (combine folds the pair
#                  away; the pipeline output is unchanged)
#   TALLY GATE   - the patched .flow shows the extra register reads the
#                  guards let survive cse2 (the store-consumer shape is
#                  the milestone-3 target; the register-consumer shape is
#                  EXPECTED to show no delta - value forwarding eats it)
#
# Usage: sh tools/cc1_smoke_run.sh [smoke-stem ...]
#        (default: cc1_smoke1 cc1_smoke2)

set -e
REPO="$(cd "$(dirname "$0")/.." && pwd)"
SELF="${GCCDIR_SELF:-/home/z/my-project/tools-local/gcc-2.6.3-src/gcc-2.6.3}"
WORK="${SMOKE_WORK:-/home/z/my-project/probe-work/cc1-smoke}"
STEMS="${*:-cc1_smoke1 cc1_smoke2}"

rm -rf "$WORK"
mkdir -p "$WORK/stock" "$WORK/patched"

for stem in $STEMS; do
    ( cd "$WORK/stock" && \
      CC1FLAGS_EXTRA=-da \
      sh "$REPO/tools/cc.sh" -S -o "$stem.o" "$REPO/probes/gcc263/$stem.c" >/dev/null )
    ( cd "$WORK/patched" && \
      QEMU=/usr/bin/env GCCDIR="$SELF" CC1FLAGS_EXTRA=-da \
      sh "$REPO/tools/cc.sh" -S -o "$stem.o" "$REPO/probes/gcc263/$stem.c" >/dev/null )

    echo "=== $stem ==="
    if diff -q "$WORK/stock/$stem.gcc.s" "$WORK/patched/$stem.gcc.s" >/dev/null; then
        echo "  RENDER GATE: PASS (byte-identical)"
    else
        echo "  RENDER GATE: FAIL - render changed:"
        diff "$WORK/stock/$stem.gcc.s" "$WORK/patched/$stem.gcc.s" | head -12
    fi

    # the .flow register-usage table: "Register NNN used X times across Y insns"
    if [ -f "$WORK/stock/$stem.c.flow" ] && [ -f "$WORK/patched/$stem.c.flow" ]; then
        if diff -q "$WORK/stock/$stem.c.flow" "$WORK/patched/$stem.c.flow" >/dev/null; then
            echo "  TALLY GATE:   no .flow delta (the +1 read did NOT survive cse2)"
        else
            echo "  TALLY GATE:   .flow delta (reads survived cse2):"
            diff "$WORK/stock/$stem.c.flow" "$WORK/patched/$stem.c.flow" \
                | grep -E '^[<>].*Register' | head -12
        fi
    else
        echo "  TALLY GATE:   .flow dumps missing:"
        ls "$WORK/stock" "$WORK/patched" | sed 's/^/    /'
    fi
done
echo "[smoke] artifacts in $WORK/{stock,patched}"

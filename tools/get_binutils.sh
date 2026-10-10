#!/usr/bin/env bash
# =============================================================================
# tools/get_binutils.sh — reproducible no-root mipsel binutils bring-up.
#
# The matching pipeline needs a MIPS as/ld/objcopy. This sandbox has no
# root and no apt, so we extract the Debian buster mipsel-cross binutils
# (2.31.1-16, the version the round-trip oracle is proven against) into
# tools-local/mipsel-root with `dpkg -x`. Idempotent: re-running is a
# no-op when the assembler already works.
#
# Verified pair: maspsx output + GNU as 2.31.1 -> byte-exact slps_00270
# and sces_00269 round-trips (see docs/TOOLCHAIN.md).
# =============================================================================
set -eu

REPO="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="${TOOLROOT:-/home/z/my-project/tools-local/mipsel-root}"
AS="$ROOT/usr/bin/mipsel-linux-gnu-as"
DEBDIR="$REPO/../tools-local/deb"
MIRROR="https://archive.debian.org/debian/pool/main/b/binutils"
AS_VERSION_WANT="2.31.1"

export LD_LIBRARY_PATH="$ROOT/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

if [ -x "$AS" ] && "$AS" --version 2>/dev/null | grep -q "$AS_VERSION_WANT"; then
    echo "get_binutils: OK — $($AS --version | head -1) at $AS"
    exit 0
fi

echo "get_binutils: fetching Debian buster binutils 2.31.1-16 (amd64 host, mipsel target)"
mkdir -p "$DEBDIR" "$ROOT"
cd "$DEBDIR"
for deb in \
    binutils-mipsel-linux-gnu_2.31.1-16_amd64.deb \
    libbinutils_2.31.1-16_amd64.deb; do
    if [ ! -f "$deb" ]; then
        # archive.debian.org serves buster only over plain http on some
        # mirrors; try https first, fall back to http.
        curl -fsSL -o "$deb" "$MIRROR/$deb" \
            || curl -fsSL -o "$deb" "${MIRROR/https:/http:}/$deb"
    fi
    dpkg -x "$deb" "$ROOT"
done

"$AS" --version | head -1
echo "get_binutils: installed into $ROOT"
echo "get_binutils: note — tools/build.sh already sets LD_LIBRARY_PATH for these binaries"

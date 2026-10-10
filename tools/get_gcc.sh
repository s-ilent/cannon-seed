#!/bin/sh
# Fetch the Psy-Q-era compiler and a user-mode emulator for it.
#
# The PS1 compiler of record (docs/TOOLCHAIN.md) is GCC 2.6.3 as shipped
# with the October-1995 Psy-Q SDK. Prebuilt Linux binaries come from the
# decompals/old-gcc release set (same source decomp.me builds its PSX
# images from). Those binaries are 32-bit i386, and this sandbox's
# seccomp allowlist only accepts x86-64 syscall numbers (i386 processes
# die instantly with SIGSYS / "Bad system call"), so we also fetch
# qemu-i386 (static, x86-64) to translate the guest syscalls in
# userspace. qemu itself is an amd64 binary making ordinary syscalls,
# which the allowlist accepts.
#
# No root required: everything lands in /home/z/my-project/tools-local/
# (outside the repo, survives re-provisions). Re-run any time; idempotent.
#
# Usage: sh tools/get_gcc.sh

set -e

REPO="$(cd "$(dirname "$0")/.." && pwd)"
TOOLROOT="/home/z/my-project/tools-local"
QEMU="$TOOLROOT/qemu-root/usr/bin/qemu-i386-static"
GCCDIR="$TOOLROOT/gcc-2.6.3-psx"

GCC_URL="https://github.com/decompals/old-gcc/releases/download/0.12/gcc-2.6.3-psx.tar.gz"
# bullseye-era qemu-user-static ships REAL static binaries; trixie's
# package only contains symlinks into qemu-user (dynamic), and this
# sandbox refuses symlinks.
QEMU_URL="http://deb.debian.org/debian/pool/main/q/qemu/qemu-user-static_5.2+dfsg-11+deb11u3_amd64.deb"

mkdir -p "$TOOLROOT"

if [ -x "$QEMU" ]; then
    echo "[get_gcc] qemu-i386-static present"
else
    echo "[get_gcc] fetching qemu-user-static (bullseye, static)..."
    TMP="$(mktemp -d)"
    curl -sL --max-time 300 -o "$TMP/qus.deb" "$QEMU_URL"
    dpkg -x "$TMP/qus.deb" "$TOOLROOT/qemu-root"
    rm -rf "$TMP"
    [ -x "$QEMU" ] || { echo "FATAL: qemu-i386-static not found after extract" >&2; exit 1; }
fi

if [ -x "$GCCDIR/cc1" ]; then
    echo "[get_gcc] gcc-2.6.3-psx present"
else
    echo "[get_gcc] fetching gcc-2.6.3-psx (decompals/old-gcc 0.12)..."
    TMP="$(mktemp -d)"
    curl -sL --max-time 300 -o "$TMP/gcc.tgz" "$GCC_URL"
    mkdir -p "$GCCDIR"
    tar xzf "$TMP/gcc.tgz" -C "$GCCDIR"
    rm -rf "$TMP"
    chmod +x "$GCCDIR"/*
fi

# Smoke: the banner line proves we have the Sony PSX build, not a
# generic mips gcc.
BANNER="$("$QEMU" "$GCCDIR/cc1" -quiet </dev/null 2>/dev/null | grep -m1 "Sony Playstation" || true)"
if [ -z "$BANNER" ]; then
    echo "FATAL: cc1 did not emit the Sony Playstation banner under qemu" >&2
    exit 1
fi
echo "[get_gcc] ok: $BANNER"

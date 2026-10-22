#!/bin/sh
# Build a modified-cc1-capable GCC 2.6.3 PSX cross-compiler from source.
#
# Why: the color-war probe (probes/gcc263/GsTMDdivG4LFG.c STATUS blocks,
# windows cron-20261021-2213 .. cron-20261022-0043) needs cc1 patches that
# suppress the self-kill fold at the tree and cse levels while keeping
# combine's - the experiment no stock binary can run.
#
# Recipe: decompals/old-gcc gcc-2.6.3-psx.Dockerfile (the same source the
# decompals release binaries build from), with the two sandbox adaptations
# the cron-20261022-0043 record documented:
#   1. no multilib on this 64-bit host: -m32/-march=i686 dropped,
#      -fcommon added;
#   2. gcc.c hardcodes sys_errlist/sys_nerr (gone from modern glibc):
#      switched to strerror(errno).
# The stock tarball is fetched at the sha256 the 2213 record pinned.
#
# Equivalence gate (run separately, see probe STATUS): the self-built cc1
# renders the committed G probe byte-identical to the decompals binary.
#
# Usage: sh tools/build_cc1_263.sh          (idempotent; skips if cc1 exists)
#        GCCSRC=/path override the work root (default tools-local/gcc-2.6.3-src)

set -e

REPO="$(cd "$(dirname "$0")/.." && pwd)"
TOOLROOT="${TOOLROOT:-/home/z/my-project/tools-local}"
GCCSRC="${GCCSRC:-$TOOLROOT/gcc-2.6.3-src}"
TARBALL_SHA256="71f673849f4dc7f20aba6ba1ecb6221c6704ef3152779aef15602e974ae3c140"
TARBALL_URL="https://gcc.gnu.org/pub/gcc/old-releases/gcc-2/gcc-2.6.3.tar.bz2"
RECIPE="$TOOLROOT/old-gcc-src"

if [ -x "$GCCSRC/gcc-2.6.3/cc1" ]; then
    echo "[build_cc1] cc1 already built at $GCCSRC/gcc-2.6.3/cc1 - nothing to do"
    exit 0
fi

mkdir -p "$GCCSRC"

# --- 1. stock tarball at the pinned hash -----------------------------
if [ ! -f "$GCCSRC/gcc-2.6.3.tar.bz2" ]; then
    echo "[build_cc1] fetching gcc-2.6.3.tar.bz2..."
    curl -fsSL -o "$GCCSRC/gcc-2.6.3.tar.bz2" "$TARBALL_URL"
fi
got="$(sha256sum "$GCCSRC/gcc-2.6.3.tar.bz2" | cut -d' ' -f1)"
if [ "$got" != "$TARBALL_SHA256" ]; then
    echo "[build_cc1] FATAL: tarball sha256 $got != pinned $TARBALL_SHA256" >&2
    exit 1
fi
echo "[build_cc1] tarball hash OK"

# --- 2. recipe repo (the exact patch set) ----------------------------
if [ ! -f "$RECIPE/gcc-2.6.3-psx.Dockerfile" ]; then
    echo "[build_cc1] cloning decompals/old-gcc recipe..."
    rm -rf "$RECIPE"
    git clone --depth 1 https://github.com/decompals/old-gcc.git "$RECIPE"
fi

# --- 3. extract + patch ----------------------------------------------
cd "$GCCSRC"
if [ ! -d gcc-2.6.3 ]; then
    tar xjf gcc-2.6.3.tar.bz2
fi
cd gcc-2.6.3
# the 1994 archive ships read-only modes; sed -i / patch need write
chmod -R u+w .

if [ ! -f .patched ]; then
    echo "[build_cc1] applying the decompals patch set..."
    sed -i -- 's/include <varargs.h>/include <stdarg.h>/g' *.c
    patch -su -p1 obstack.h -i "$RECIPE/patches/obstack-2.7.2.h.patch"
    patch -su -p1 sdbout.c -i "$RECIPE/patches/sdbout-2.6.3.c.patch"
    patch -su -p1 cp/g++.c -i "$RECIPE/patches/g++-2.6.3.c.patch"
    patch -su -p1 < "$RECIPE/patches/psx-2.5.7.patch"
    touch -c cp/parse.y cp/parse.h cp/parse.c
    touch insn-config.h

    # sandbox adaptation 2: gcc.c sys_errlist/sys_nerr -> strerror
    # (modern glibc dropped the compat arrays; HAVE_STRERROR is already
    # on the build line, so route the messages through strerror(3))
    python3 - "$RECIPE" <<'EOF'
import sys, re
recipe = sys.argv[1]
src = open('gcc.c').read()
if 'MODIFIED-CC1 strerror adaptation' not in src:
    # drop the hardcoded externs and every sys_errlist/sys_nerr use
    src = src.replace('extern char *sys_errlist[];', '/* MODIFIED-CC1 strerror adaptation */')
    src = src.replace('extern int sys_nerr;', '')
    src = re.sub(r'\bsys_errlist\s*\[\s*errno\s*\]', 'strerror (errno)', src)
    src = re.sub(r'\bsys_nerr\b', '1', src)
    if '#include <string.h>' not in src:
        src = src.replace('#include <errno.h>', '#include <errno.h>\n#include <string.h>', 1)
    open('gcc.c', 'w').write(src)
    print('[build_cc1] gcc.c strerror adaptation applied')
else:
    print('[build_cc1] gcc.c adaptation already present')
EOF
    touch .patched
fi

# --- 4. configure + build ---------------------------------------------
if [ ! -f config.status ]; then
    ./configure --target=mips-sony-psx \
        --prefix=/opt/cross \
        --with-endian-little \
        --with-gnu-as \
        --host=i386-pc-linux \
        --build=i386-pc-linux
fi

echo "[build_cc1] building cpp cc1 xgcc (this is the ~5 min step)..."
make --jobs "$(nproc)" cpp cc1 xgcc \
    CFLAGS="-std=gnu89 -static -fcommon -Dbsd4_4 -Dmips -DHAVE_STRERROR"

echo "[build_cc1] done: $GCCSRC/gcc-2.6.3/{cc1,cpp,xgcc}"
echo "[build_cc1] equivalence gate: render a committed probe with"
echo "[build_cc1]   QEMU=/usr/bin/env GCCDIR=$GCCSRC/gcc-2.6.3 sh tools/cc.sh -S -o /tmp/gate.o probes/gcc263/GsTMDdivG4LFG.c"
echo "[build_cc1] and diff the .gcc.s against the decompals render."

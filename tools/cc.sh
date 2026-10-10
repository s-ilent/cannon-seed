#!/bin/sh
# Compile one C file with the Psy-Q-era compiler (GCC 2.6.3 PSX) and
# assemble it to a .o with the repo's pinned binutils — the same
# front-end/back-end pair that produced the retail binaries.
#
#   tools/cc.sh -o out.o file.c
#
# Pipeline: cc1 (i386, run under qemu-i386) emits ASPSX-syntax MIPS asm;
# maspsx rewrites it to GNU-as syntax; our mipsel as 2.31.1 assembles.
# Intermediate .s files are kept next to the output for diffing.
#
# Flag set is the working hypothesis from docs/TOOLCHAIN.md:
#   -mips1  MIPS1 ISA (measured: mult/mflo, no MIPS32 mul)
#   -O2     optimization level (hypothesis; probes must confirm)
#   -G0     no small-data (%gp_rel never appears in the matched asm)
#   -funsigned-char  plain char is unsigned (lbu 184 vs lb 13)
#   -fno-builtin     no libc call substitution (libgcc calls: zero)
#
# Env overrides: QEMU, GCCDIR, MASPSX, TOOLROOT (binutils root).

set -e

REPO="$(cd "$(dirname "$0")/.." && pwd)"
TOOLROOT="${TOOLROOT:-/home/z/my-project/tools-local}"
QEMU="${QEMU:-$TOOLROOT/qemu-root/usr/bin/qemu-i386-static}"
GCCDIR="${GCCDIR:-$TOOLROOT/gcc-2.6.3-psx}"
MASPSX="${MASPSX:-/home/z/my-project/tools-src/maspsx/maspsx.py}"

AS="$TOOLROOT/mipsel-root/usr/bin/mipsel-linux-gnu-as"
export LD_LIBRARY_PATH="$TOOLROOT/mipsel-root/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

[ -x "$QEMU" ] || { echo "cc.sh: qemu missing — run tools/get_gcc.sh" >&2; exit 1; }
[ -x "$GCCDIR/cc1" ] || { echo "cc.sh: cc1 missing — run tools/get_gcc.sh" >&2; exit 1; }
[ -f "$MASPSX" ] || { echo "cc.sh: maspsx missing — clone tools-src/maspsx (see rehydrate.sh)" >&2; exit 1; }
[ -x "$AS" ] || { echo "cc.sh: mipsel as missing — run tools/get_binutils.sh" >&2; exit 1; }

# --- parse arguments -------------------------------------------------
OUT=""
INCS=""
SOURCES=""
STOP_AT_ASM=0
while [ $# -gt 0 ]; do
    case "$1" in
        -o) OUT="$2"; shift 2 ;;
        -I) INCS="$INCS -I$2"; shift 2 ;;
        -I*) INCS="$INCS $1"; shift ;;
        -S) STOP_AT_ASM=1; shift ;;
        *) SOURCES="$SOURCES $1"; shift ;;
    esac
done
[ -n "$OUT" ] || OUT="a.out"
[ -n "$SOURCES" ] || { echo "cc.sh: no input file" >&2; exit 1; }

# one source per invocation (functions are compiled per-file anyway)
SRC=$(echo $SOURCES)
BASE="$(basename "$SRC" .c)"
STEM="${OUT%.o}"

CC1FLAGS="-quiet -mips1 -O2 -G0 -funsigned-char -fno-builtin $INCS"

# The Psy-Q cc1 wants preprocessed input (it rejects unstripped
# comments), so run the bundled cpp first — same as the original
# Psy-Q driver did.
"$QEMU" "$GCCDIR/cpp" $INCS "$SRC" -o "$STEM.i"
"$QEMU" "$GCCDIR/cc1" $CC1FLAGS "$STEM.i" -o "$STEM.gcc.s"

# maspsx reads its input from stdin when stdin is not a tty (which is
# always the case here), so pipe the cc1 output into it. --expand-div
# reproduces the ASPSX assembler's div/divu macro expansion (break 7 /
# break 6 trap guards) that the retail binaries contain; the retail
# disassembly shows exactly this sequence (e.g. func_80028B8C.s).
python3 "$MASPSX" --expand-div < "$STEM.gcc.s" > "$STEM.mas.s"

if [ "$STOP_AT_ASM" = 1 ]; then
    # Hand the .mas.s to the caller (tools/build.sh rewrites the section
    # name to .r_<rom> and assembles with its own flags — it must, because
    # gas pads the default .text section to 16 bytes on MIPS, while a
    # fresh .section name carries no default padding).
    echo "cc.sh: $SRC -> $STEM.mas.s (-S: assembly left to caller)"
    exit 0
fi

"$AS" -march=mips64 -mabi=32 -EL -G0 -I "$REPO/include" -o "$OUT" "$STEM.mas.s"
echo "cc.sh: $SRC -> $OUT (intermediates: $STEM.gcc.s, $STEM.mas.s)"

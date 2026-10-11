#!/usr/bin/env bash
# =============================================================================
# tools/permuter/compile.sh — compile ONE C file with the pinned toolchain,
# in the form decomp-permuter expects.
#
#     compile.sh <input.c> -o <output.o>
#
# This is the permuter-side twin of tools/cc.sh: the same stages
# (cpp -> cc1 -> maspsx --expand-div -> cc_post fixups -> mipsel as), but it
# stops at the relocatable .o the permuter disassembles instead of handing
# back the staged .mas.s that build.sh rewrites into a .r_<rom> section.
#
# Overridable, so one file works in the sandbox and on a developer host:
#
#   TOOLROOT   root holding gcc-2.6.3-psx/ and mipsel-root/
#              (default: the sandbox's /home/z/my-project/tools-local)
#   MASPSX     path to maspsx.py
#   QEMU       runner for the static i386 cc1/cpp. In the sandbox this is
#              qemu-i386-static (see tools/get_gcc.sh for why seccomp forces
#              the indirection); on a normal host point it at a shim that
#              just execs its argument, and the compiler runs natively.
#   PYTHON     interpreter for the python stage scripts
# =============================================================================
set -euo pipefail

REPO="${REPO:-$(cd "$(dirname "$0")/../.." && pwd)}"
TOOLROOT="${TOOLROOT:-/home/z/my-project/tools-local}"
MASPSX="${MASPSX:-/home/z/my-project/tools-src/maspsx/maspsx.py}"
QEMU="${QEMU:-$TOOLROOT/qemu-root/usr/bin/qemu-i386-static}"
GCCDIR="${GCCDIR:-$TOOLROOT/gcc-2.6.3-psx}"
AS="$TOOLROOT/mipsel-root/usr/bin/mipsel-linux-gnu-as"
PYTHON="${PYTHON:-python3}"

export LD_LIBRARY_PATH="$TOOLROOT/mipsel-root/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

src=""; out=""
while [ $# -gt 0 ]; do
    case "$1" in
        -o) out="$2"; shift 2 ;;
        *)  src="$1"; shift ;;
    esac
done
[ -n "$src" ] || { echo "permuter/compile.sh: no input file" >&2; exit 2; }
[ -n "$out" ] || out="${src%.c}.o"
[ -x "$AS" ] || { echo "permuter/compile.sh: mipsel as missing at $AS" >&2; exit 2; }
[ -x "$QEMU" ] || { echo "permuter/compile.sh: runner missing at $QEMU" >&2; exit 2; }

stem="${out%.o}"

# cpp first: Psy-Q cc1 wants preprocessed input (it rejects raw comments).
"$QEMU" "$GCCDIR/cpp" -I "$REPO/include" "$src" -o "$stem.i"
# -I is omitted here deliberately: cc1's option parser rejects it, and the
# include path was already expanded by cpp above.
"$QEMU" "$GCCDIR/cc1" -quiet -mips1 -O2 -G8 -funsigned-char -fno-builtin \
    "$stem.i" -o "$stem.gcc.s"
"$PYTHON" "$MASPSX" --expand-div < "$stem.gcc.s" > "$stem.mas.s"
"$PYTHON" "$REPO/tools/cc_post.py" "$stem.mas.s"
"$AS" -march=mips64 -mabi=32 -EL -G0 -I "$REPO/include" -o "$out" "$stem.mas.s"

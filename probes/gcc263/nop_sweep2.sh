#!/bin/sh
# nop_sweep2.sh — final two hypotheses:
#   1. cc1plus (C++) instead of cc1
#   2. symbol defined in the same TU (.sdata/.data definition, not .extern)
set -u
TOOLROOT=/home/z/my-project/tools-local
QEMU=$TOOLROOT/qemu-root/usr/bin/qemu-i386-static
GCCDIR=$TOOLROOT/gcc-2.6.3-psx
WORK=/home/z/my-project/scripts/nop_sweep_work
mkdir -p "$WORK"

cat > "$WORK/c_plain.c" <<'EOF'
extern unsigned int D_80063268;
void probe_f(void) { D_80063268 = 0; }
EOF
cat > "$WORK/c_volatile.c" <<'EOF'
extern volatile unsigned int D_80063268;
void probe_f(void) { D_80063268 = 0; }
EOF
cat > "$WORK/c_def.c" <<'EOF'
unsigned int D_80063268 = 5;
void probe_f(void) { D_80063268 = 0; }
EOF

detect() {
    if awk '/^probe_f:/{f=1;n=0;next} f&&/^\s*nop\s*$/{print "HIT"; exit} f&&/^\s*[a-z]/{n++; if(n>1) exit}' "$WORK/p2.s" | grep -q HIT; then
        echo "ENTRYNOP $1"
    fi
}

echo "=== cc1plus ==="
for src in c_plain c_volatile c_def; do
    "$QEMU" "$GCCDIR/cpp" "$WORK/$src.c" -o "$WORK/p2.i" 2>/dev/null || { echo "CPPFAIL $src"; continue; }
    for extra in "" "-fvolatile" "-fvolatile-global" "-O0" "-O1" "-O3" "-G0"; do
        "$QEMU" "$GCCDIR/cc1plus" -quiet -mips1 -O2 -G8 -funsigned-char -fno-builtin $extra "$WORK/p2.i" -o "$WORK/p2.s" 2>"$WORK/err2.txt" || { echo "CXX1FAIL $src $extra :: $(head -1 $WORK/err2.txt | head -c 90)"; continue; }
        detect "cc1plus $src $extra"
    done
done

echo "=== cc1 defined-symbol (with .sdata emission) ==="
for extra in "" "-fvolatile" "-fvolatile-global" "-O0" "-O1" "-O3" "-G0" "-G4"; do
    "$QEMU" "$GCCDIR/cpp" "$WORK/c_def.c" -o "$WORK/p2.i" 2>/dev/null
    "$QEMU" "$GCCDIR/cc1" -quiet -mips1 -O2 -G8 -funsigned-char -fno-builtin $extra "$WORK/p2.i" -o "$WORK/p2.s" 2>/dev/null || { echo "CC1FAIL def $extra"; continue; }
    detect "cc1 def $extra"
done

echo "=== also: what does the .s around probe_f look like (def, base flags) ==="
sed -n '1,40p' "$WORK/p2.s" 2>/dev/null | grep -A6 -B1 "probe_f\|D_80063268" | head -25
echo "=== done ==="

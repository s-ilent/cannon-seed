#!/bin/sh
# nop_sweep.sh — sweep cc1 2.6.3-psx flag x source matrix looking for any
# combination that emits a leading `nop` on a store-to-global leaf function
# (the func_80025AE0 / func_8002A0DC retail shape: nop; sw/sh $zero,off($gp); jr $ra; nop).
#
# Detection: in cc1's raw output, the function label followed within 2 lines
# by a bare `nop`. Record every hit with its flags + source variant.
set -u

REPO=/home/z/my-project/cannon-seed
TOOLROOT=/home/z/my-project/tools-local
QEMU=$TOOLROOT/qemu-root/usr/bin/qemu-i386-static
GCCDIR=$TOOLROOT/gcc-2.6.3-psx
WORK=/home/z/my-project/scripts/nop_sweep_work
mkdir -p "$WORK"

# --- source variants ---------------------------------------------------
cat > "$WORK/s_plain.c" <<'EOF'
extern unsigned int D_80063268;
void probe_f(void) { D_80063268 = 0; }
EOF
cat > "$WORK/s_volatile.c" <<'EOF'
extern volatile unsigned int D_80063268;
void probe_f(void) { D_80063268 = 0; }
EOF
cat > "$WORK/s_short.c" <<'EOF'
extern unsigned short D_80063294;
void probe_f(void) { D_80063294 = 0; }
EOF
cat > "$WORK/s_static.c" <<'EOF'
static unsigned int D_80063268;
void probe_f(void) { D_80063268 = 0; }
EOF
cat > "$WORK/s_param.c" <<'EOF'
extern unsigned int D_80063268;
void probe_f(int unused_a) { D_80063268 = 0; }
EOF
cat > "$WORK/s_kr.c" <<'EOF'
extern unsigned int D_80063268;
void probe_f();
void probe_f() { D_80063268 = 0; }
EOF
cat > "$WORK/s_two.c" <<'EOF'
extern unsigned int D_80063268;
void probe_other(void) { D_80063268 = 7; }
void probe_f(void) { D_80063268 = 0; }
EOF
cat > "$WORK/s_twoafter.c" <<'EOF'
extern unsigned int D_80063268;
void probe_f(void) { D_80063268 = 0; }
void probe_other(void) { D_80063268 = 7; }
EOF

BASE="-mips1 -O2 -G8 -funsigned-char -fno-builtin"

FLAGS=""
for f in -fvolatile -fvolatile-global -fdefer-pop -fforce-addr -fforce-mem \
         -ffloat-store -ffast-math -fcaller-saves -fno-caller-saves \
         -fcse-follow-jumps -fcse-skip-blocks -fexpensive-optimizations \
         -finline-functions -fkeep-inline-functions -fomit-frame-pointer \
         -fno-omit-frame-pointer -fpeephole -fno-peephole \
         -frerun-cse-after-loop -fschedule-insns -fno-schedule-insns \
         -fschedule-insns2 -fno-schedule-insns2 -fstrength-reduce \
         -fthread-jumps -funroll-loops -fcommon -fno-common \
         -fembedded-data -fno-embedded-data -mgpopt -mno-gpopt \
         -mrnames -mno-rnames -mabicalls -mno-abicalls -mdivide -mbreaks; do
    FLAGS="$FLAGS $f"
done

run_one() {
    srcfile="$1"; tag="$2"; shift 2
    "$QEMU" "$GCCDIR/cpp" "$srcfile" -o "$WORK/p.i" 2>"$WORK/err.txt" || { echo "CPPFAIL $tag"; return; }
    "$QEMU" "$GCCDIR/cc1" -quiet -mips1 -G8 -funsigned-char -fno-builtin "$@" "$WORK/p.i" -o "$WORK/p.s" 2>"$WORK/err.txt" || { echo "CC1FAIL $tag :: $(tail -1 $WORK/err.txt | head -c 100)"; return; }
    # detect: label 'probe_f:' then nop within the next 2 lines
    if awk '/^probe_f:/{f=1;n=0;next} f&&/^\s*nop\s*$/{print "HIT"; exit} f&&/^\s*[a-z]/{n++; if(n>1) exit}' "$WORK/p.s" | grep -q HIT; then
        echo "ENTRYNOP $tag"
    fi
}

echo "=== sweep: source variants x single extra flags (base -O2 -G8) ==="
for src in s_plain s_volatile s_short s_static s_param s_kr s_two s_twoafter; do
    run_one "$WORK/$src.c" "$src BASE" || true
    for f in $FLAGS; do
        run_one "$WORK/$src.c" "$src $f" "$f" || true
    done
done

echo "=== sweep: optimization levels (s_plain) ==="
for opt in -O0 -O1 -O2 -O3; do
    for g in -G0 -G4 -G8; do
        run_one "$WORK/s_plain.c" "s_plain $opt $g" $opt $g || true
        run_one "$WORK/s_volatile.c" "s_volatile $opt $g" $opt $g || true
    done
done

echo "=== sweep: isa/cpu variants (s_plain, -O2 -G8) ==="
for m in -mips2 -mfp64 -mgas -mno-gas -mcpu=r3000 -mcpu=r4400 -m4650 -m3900; do
    run_one "$WORK/s_plain.c" "s_plain $m" "$m" || true
done

echo "=== sweep done ==="

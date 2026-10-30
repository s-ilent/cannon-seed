/* Real-decompiled-C game function #15 candidate - ROUND-5 STATE
 * (cron-20261030-2151 window, 2026-10-30). Supersedes the round-4 switch
 * draft (deferred_func_80052038.c, judge 1988/2032 DIFF 405/497).
 *
 * ROUND-5 BREAKTHROUGH - THE DISPATCH STRUCTURAL ITEM IS CLOSED OFFLINE:
 * - ROOT CAUSE of the fold-vs-at-split dispatch diff: cc1 emits the
 *   sym($reg) addressing MACRO (`lw $2,$L39($2)` raw) and the EXPANSION
 *   belongs to the assembler. maspsx's default expansion is the FOLD
 *   (lui $at,%hi; addu $at,$at,$idx; lw %lo($at), 3 insns); the ORIGINAL
 *   aspsx (< 2.30) expanded it as the AT-SPLIT (lui $at,%hi; addiu
 *   $at,$at,%lo; addu $at,$at,$idx; lw 0x0($at), 4 insns) - exactly every
 *   retail jtbl dispatch (func_80052038/22B5C/50898 verified identical).
 *   maspsx already carried the knob: addiu_at=True for aspsx < 2.30.
 * - THE PATCH: tools/maspsx_delay_slot.patch regrown with addiu_at=True
 *   in the base config (single knob; the version flag also flips
 *   nop_at_expansion/nop_mflo_mfhi which we do NOT want) + rehydrate now
 *   RESETS the clone before applying so regrown patches never skip hunks.
 * - THE DISPATCH: the switch is replaced by a computed-goto over the
 *   COMMITTED extern row jtbl_80021B10 (30 entries, 14 default-filled):
 *       ix = (long)code - 0x20;
 *       if ((unsigned long)ix < 0x1E) goto *((void **)jtbl_80021B10)[ix];
 *   which removes the C-unit .rodata orphan table entirely AND under
 *   addiu_at emits the retail 4-insn at-split THROUGH $at with the
 *   register roles intact (andi $5/$a1 code, addu $3/$v1 ix, sltiu+sll
 *   $2/$v0, la $at, lw $2, j $2) - probe_52038_goto3 vs retail: FORM
 *   IDENTICAL. `goto *(elem_address)` (no deref) emits NO load at all;
 *   the deref form `*((void **)jtbl)[ix]` is the retail semantics.
 * - LABEL LIVENESS: gcc 2.6.3 DCEs every case label only jumped to via
 *   the extern table (dead `keep = &&L` assignments do NOT preserve
 *   them). ZERO-COST FIX: two 8-input input-only asms with "i"
 *   constraints (__asm__ ("" : : "i"(&&L_0x20), ...) x2 - gcc 2.6.3
 *   caps asm at 10 operands) - the label refs survive as immediates,
 *   no register moves, no emitted insns, labels preserved.
 * - CASE BODIES: under addiu_at the flag-path tbl-pin + statement-
 *   barrier workarounds are WRONG (they emit the la into the pinned $2
 *   where retail uses $at) - dropped in favor of the PLAIN sym($reg)
 *   forms which maspsx now expands to the retail at-split natively.
 *   The no-flag two-index forms dropped the tbl-assign too.
 * - OFFLINE PROOF: scripts/word_diff.py (assemble + objdump + byteswap
 *   + difflib vs the retail word stream) is the new offline judge
 *   proxy; the dispatch + pre-dispatch words are retail-exact. The
 *   remaining deltas (case bodies, mode chain, a1v/a2v nits) need the
 *   LIVE judge - next window on the witnessed oracle: stage v2 into
 *   src/func_80052038.c, flip the yaml row, build g3_eu, judge.
 *
 * cc-post: keep-epilogue
 */
typedef long (*StdFn)(long *, long, long, long, long, long, long, long *);
typedef long (*AltFn)(long *, long, long, long, long, long, long *);

extern long D_80147E20;
extern long D_80147E24;
extern long D_80164268;
extern long D_801727D4;
extern long D_80171E04;
extern long D_8016AF90;
extern long D_8016AFA4;
extern long D_8016AB6C;
extern long GsSetLightMode_lmode;
extern long jtbl_80021B10[];
extern long D_80098998[];
extern long D_800989B0[];
extern long D_800989B8[];
extern long D_800989D0[];
extern long D_800989D8[];
extern long D_800989F0[];
extern long D_800989F8[];
extern long D_80098A10[];
extern long D_80098A18[];
extern long D_80098A30[];
extern long D_80098A38[];
extern long D_80098A50[];
extern long D_80098A58[];
extern long D_80098A70[];
extern long D_80098A78[];
extern long D_80098A90[];
extern long D_80098A98[];
extern long D_80098AA4[];
extern char D_80021AF0[];
extern int printf();

void func_80052038(long *ctrlp, long a1p, long a2p, long *recp)
{
    register long *ctrl asm("$4");
    register unsigned char *s0 asm("$16");
    register long s1 asm("$17");
    register long s2 asm("$18");
    register long *rec asm("$19");
    register long a1 asm("$20");
    register long a2 asm("$21");
    register long s6v asm("$22");
    register long s7 asm("$23");
    long fpv;
    long t0;
    long mid;
    register long a1v asm("$5");
    long a2v;
    long t9;
    long mode;
    long *state;
    long ix;

    a1 = a1p;
    a2 = a2p;
    rec = recp;
    ctrl = ctrlp;

    if (*ctrl >= 0) {
        long f1;
        long f2;
        long f3;
        long f5;
        f1 = (long)((*(unsigned long *)ctrl >> 3) & 3);
        f2 = (long)((*(volatile unsigned long *)ctrl >> 5) & 1);
        D_80147E24 = f1;
        f3 = (long)((*(unsigned long *)ctrl >> 6) & 1);
        D_80164268 = f2;
        t9 = *(unsigned long *)ctrl >> 9;
        __asm__ ("" : "=r"(t9) : "0"(t9));
        D_80147E20 = f3;
        f5 = (long)((*(unsigned long *)ctrl >> 30) & 1);
        D_801727D4 = t9 & 7;
        a1v = t9 & 7;
        D_80171E04 = f5;
        if (a1v != 0) {
            long r1;
            long r2;
            a2v = 1;
            r1 = D_8016AF90;
            r2 = D_8016AFA4;
            rec[0] = a1v;
            rec[1] = r1;
            rec[2] = r2;
        } else {
            a2v = 0;
        }
        if (D_80147E20 == 1) {
            mode = 2;
        } else {
            long tmp = D_80164268;
            if (tmp != 0) {
                if (tmp == 1 && D_80147E24 == 1) {
                    mode = 1;
                } else {
                    mode = 0;
                }
            } else {
                if (GsSetLightMode_lmode == 1) {
                    mode = 1;
                } else {
                    mode = 0;
                }
            }
        }
        state = (long *)ctrlp[2];
        s0 = (unsigned char *)state[4];
        s1 = state[5];
        s2 = state[0];
        s7 = state[2];
        if (s1 == 0) {
            return;
        }
        s6v = mode << 2;
        t0 = a2v * 12;
        fpv = a2v << 2;
        __asm__ ("" : : "i"(&&L_0x20), "i"(&&L_0x21), "i"(&&L_0x24), "i"(&&L_0x25), "i"(&&L_0x28), "i"(&&L_0x29), "i"(&&L_0x2C), "i"(&&L_0x2D));
        __asm__ ("" : : "i"(&&L_0x30), "i"(&&L_0x31), "i"(&&L_0x34), "i"(&&L_0x35), "i"(&&L_0x38), "i"(&&L_0x39), "i"(&&L_0x3C), "i"(&&L_0x3D));
        do {
            unsigned int code = (unsigned int)s0[3] & 0xFD;
            ix = (long)code - 0x20;
            if ((unsigned long)ix < 0x1E)
                goto *((void **)jtbl_80021B10)[ix];
            printf(D_80021AF0, code, s0);
            goto L_next;
        L_0x20:
                if (*(unsigned short *)(s0 + 2) & 4) {
                    D_8016AB6C = ((StdFn) * (long *)(s6v + (char *)D_80098A98))(
                        (long *)s0, s2, s7, D_8016AB6C,
                        *(unsigned short *)s0, a2, a1, rec);
                    s1 -= *(unsigned short *)s0;
                    s0 += *(unsigned short *)s0 * 24;
                } else {
                    D_8016AB6C = ((StdFn) * (long *)(s6v + (t0 + (char *)D_80098998)))(
                        (long *)s0, s2, s7, D_8016AB6C,
                        *(unsigned short *)s0, a2, a1, rec);
                    s1 -= *(unsigned short *)s0;
                    s0 += *(unsigned short *)s0 * 16;
                    goto L_next;
        L_0x24:
                D_8016AB6C = ((StdFn) * (long *)(s6v + (t0 + (char *)D_800989D8)))(
                    (long *)s0, s2, s7, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 24;
                goto L_next;
        L_0x30:
                if (*(unsigned short *)(s0 + 2) & 4) {
                    D_8016AB6C = ((StdFn) * (long *)(s6v + (char *)D_80098AA4))(
                        (long *)s0, s2, s7, D_8016AB6C,
                        *(unsigned short *)s0, a2, a1, rec);
                    s1 -= *(unsigned short *)s0;
                    s0 += *(unsigned short *)s0 * 28;
                } else {
                    D_8016AB6C = ((StdFn) * (long *)(s6v + (t0 + (char *)D_800989B8)))(
                        (long *)s0, s2, s7, D_8016AB6C,
                        *(unsigned short *)s0, a2, a1, rec);
                    s1 -= *(unsigned short *)s0;
                    s0 += *(unsigned short *)s0 * 20;
                }
                goto L_next;
        L_0x34:
                D_8016AB6C = ((StdFn) * (long *)(s6v + (t0 + (char *)D_800989F8)))(
                    (long *)s0, s2, s7, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 28;
                goto L_next;
        L_0x28:
                D_8016AB6C = ((StdFn) * (long *)(s6v + (t0 + (char *)D_80098A18)))(
                    (long *)s0, s2, s7, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 20;
                goto L_next;
        L_0x2C:
                D_8016AB6C = ((StdFn) * (long *)(s6v + (t0 + (char *)D_80098A58)))(
                    (long *)s0, s2, s7, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 32;
                goto L_next;
        L_0x38:
                D_8016AB6C = ((StdFn) * (long *)(s6v + (t0 + (char *)D_80098A38)))(
                    (long *)s0, s2, s7, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 24;
                goto L_next;
        L_0x3C:
                D_8016AB6C = ((StdFn) * (long *)(s6v + (t0 + (char *)D_80098A78)))(
                    (long *)s0, s2, s7, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 36;
                goto L_next;
        L_0x21:
                D_8016AB6C = ((AltFn) * (long **)((char *)D_800989B0 + fpv))(
                    (long *)s0, s2, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 16;
                goto L_next;
        L_0x29:
                D_8016AB6C = ((AltFn) * (long **)((char *)D_80098A30 + fpv))(
                    (long *)s0, s2, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 16;
                goto L_next;
        L_0x31:
                D_8016AB6C = ((AltFn) * (long **)((char *)D_800989D0 + fpv))(
                    (long *)s0, s2, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 24;
                goto L_next;
        L_0x25:
                D_8016AB6C = ((AltFn) * (long **)((char *)D_800989F0 + fpv))(
                    (long *)s0, s2, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 28;
                goto L_next;
        L_0x35:
                D_8016AB6C = ((AltFn) * (long **)((char *)D_80098A10 + fpv))(
                    (long *)s0, s2, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 36;
                goto L_next;
        L_0x39:
                D_8016AB6C = ((AltFn) * (long **)((char *)D_80098A50 + fpv))(
                    (long *)s0, s2, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 28;
                goto L_next;
        L_0x2D:
                D_8016AB6C = ((AltFn) * (long **)((char *)D_80098A70 + fpv))(
                    (long *)s0, s2, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 32;
                goto L_next;
        L_0x3D:
                D_8016AB6C = ((AltFn) * (long **)((char *)D_80098A90 + fpv))(
                    (long *)s0, s2, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 44;
                goto L_next;
                printf(D_80021AF0, code, s0);
                goto L_next;
            }
            L_next:
            ;
        } while (s1 != 0);
    }
}

/* Real-decompiled-C game function #15 candidate - ROUND-6 STATE (the
 * cron-20261030-2306 window). THE LANDING COMBINATION banked by the
 * window-36 post-mortem: v2 dispatch + round-4 case bodies + addiu_at.
 *
 * - DISPATCH from deferred_func_80052038_v2.c (round-5): computed-goto
 *   over the COMMITTED extern row jtbl_80021B10 (removes the C-unit
 *   .rodata orphan), guarded ix = (long)code - 0x20;
 *   if ((unsigned long)ix < 0x1E) goto *((void **)jtbl_80021B10)[ix];
 *   the two zero-cost 8-input "i"-constraint label-liveness asms keep
 *   the case labels alive (gcc 2.6.3 DCEs labels only reached via the
 *   extern table; dead keep-assignments do NOT). Under the addiu_at
 *   maspsx flip this emits the retail 4-insn at-split THROUGH $at with
 *   the register roles intact (judge-proven retail-exact in round 5).
 * - CASE BODIES from deferred_func_80052038.c (round-4 state): the
 *   round-5 judge REGRESSED (SIZE 2228/2032, DIFF 444/508 vs the
 *   round-4 baseline 1988, 405/497) because addiu_at only replaces the
 *   tbl-pin workarounds for the SINGLE-INDEX forms. Restored here:
 *   (a) the two flag paths (0x20/0x30 flag arm) keep the round-3/4
 *   tbl-pin + statement-barrier form (tbl = D_xxx; __asm__("" :: "r"(tbl));
 *   *(long *)(s6v + (char *)tbl)) - the barrier forces the la to
 *   complete before the index addu; (b) the eight no-flag StdFn cases
 *   keep the round-2/4 inline tbl-assign pin
 *   (*(long *)(s6v + (t0 + (char *)(tbl = D_xxx)))) - the base-pointer
 *   local pinned to $2 reproduces the 5-insn retail la-in-$v0 form.
 *   The eight AltFn cases stay the plain fpv form (retail-correct
 *   natively under addiu_at, per the round-4 fpv-everywhere closure).
 * - DECLARATIONS: v2's set + register long tbl asm("$2") from round 4
 *   (round-4 relative order kept: fpv, t0, tbl, mid, a1v, ...).
 *
 * Judge history: round-2 1944 (DIFF 436/486) -> round-3 1988 (405/497)
 * -> round-4 1988 (405/497, case-ground-truth banked, V2/V3 levers dead)
 * -> round-5 v2 dispatch 2228 (444/508 REGRESSION, case bodies at fault).
 * This file is the next landing attempt: stage into src/func_80052038.c,
 * flip the g3_eu yaml row to [0x32838, c, func_80052038], build g3_eu,
 * judge live (witness 8/8), then the whole-image verify gates the
 * addiu_at flip against the landed set before any commit.
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
    register long tbl asm("$2");
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
                    tbl = D_80098A98;
                __asm__ ("" : : "r"(tbl));
                D_8016AB6C = ((StdFn) * (long *)(s6v + (char *)tbl))(
                        (long *)s0, s2, s7, D_8016AB6C,
                        *(unsigned short *)s0, a2, a1, rec);
                    s1 -= *(unsigned short *)s0;
                    s0 += *(unsigned short *)s0 * 24;
                } else {
                    D_8016AB6C = ((StdFn) * (long *)(s6v + (t0 + (char *)(tbl = D_80098998))))(
                        (long *)s0, s2, s7, D_8016AB6C,
                        *(unsigned short *)s0, a2, a1, rec);
                    s1 -= *(unsigned short *)s0;
                    s0 += *(unsigned short *)s0 * 16;
                    goto L_next;
        L_0x24:
                D_8016AB6C = ((StdFn) * (long *)(s6v + (t0 + (char *)(tbl = D_800989D8))))(
                    (long *)s0, s2, s7, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 24;
                goto L_next;
        L_0x30:
                if (*(unsigned short *)(s0 + 2) & 4) {
                    tbl = D_80098AA4;
                __asm__ ("" : : "r"(tbl));
                D_8016AB6C = ((StdFn) * (long *)(s6v + (char *)tbl))(
                        (long *)s0, s2, s7, D_8016AB6C,
                        *(unsigned short *)s0, a2, a1, rec);
                    s1 -= *(unsigned short *)s0;
                    s0 += *(unsigned short *)s0 * 28;
                } else {
                    D_8016AB6C = ((StdFn) * (long *)(s6v + (t0 + (char *)(tbl = D_800989B8))))(
                        (long *)s0, s2, s7, D_8016AB6C,
                        *(unsigned short *)s0, a2, a1, rec);
                    s1 -= *(unsigned short *)s0;
                    s0 += *(unsigned short *)s0 * 20;
                }
                goto L_next;
        L_0x34:
                D_8016AB6C = ((StdFn) * (long *)(s6v + (t0 + (char *)(tbl = D_800989F8))))(
                    (long *)s0, s2, s7, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 28;
                goto L_next;
        L_0x28:
                D_8016AB6C = ((StdFn) * (long *)(s6v + (t0 + (char *)(tbl = D_80098A18))))(
                    (long *)s0, s2, s7, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 20;
                goto L_next;
        L_0x2C:
                D_8016AB6C = ((StdFn) * (long *)(s6v + (t0 + (char *)(tbl = D_80098A58))))(
                    (long *)s0, s2, s7, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 32;
                goto L_next;
        L_0x38:
                D_8016AB6C = ((StdFn) * (long *)(s6v + (t0 + (char *)(tbl = D_80098A38))))(
                    (long *)s0, s2, s7, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 24;
                goto L_next;
        L_0x3C:
                D_8016AB6C = ((StdFn) * (long *)(s6v + (t0 + (char *)(tbl = D_80098A78))))(
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
            }
            L_next:
            ;
        } while (s1 != 0);
    }
}

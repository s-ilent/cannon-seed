/* Real-decompiled-C game function #15 candidate - ROUND-12 / LANDING
 * SOURCE (the cron-20261031-0251 window). Body = v11 (levers A+C) with
 * rec UNPINNED (plain long *rec). LIVE JUDGE: EXACT (2032 bytes, 0.4s) -
 * func_80052038 matches retail byte-for-byte. The unpin is what closes
 * the last word: with rec pinned to $19, fwprop rewrote rec[0]'s BARE
 * rec address use (offset 0 folds to *rec) into the incoming recp
 * pseudo ($a3), so the store went out sw $a1,0($a3) vs retail's
 * sw $a1,0($s3); rec[1]/rec[2] were safe because rec+4/rec+8 are not
 * bare uses. Unpinned, gcc 2.6.3's local-alloc assigns rec's pseudo to
 * $19 NATURALLY (its life spans the case-body calls, so it needs a
 * callee-saved reg) and the copy-prop artifact vanishes - all three
 * rec stores emit through $s3 and the bltz-delay move s3,a3 stays.
 * The round-11 levers that carried this home (both judge-proven on the
 * live oracle this window):
 * (A) t9 liveness: __asm__("" : : "r"(t9)) after a1v = t9 & 7 keeps t9
 *     live PAST a1v's definition, so the t9 chain (lw/srl) cannot
 *     coalesce into a1v's $5 pin - retail holds it in $v1 (row
 *     800520A8/BC lw $v1 / srl $v1,$v1,9) and materializes a1v =
 *     andi $a1,$v1,7 (row 800520C0). No code emitted.
 * (C) else-arm a1v opaque redefinition (__asm__("" : "=r"(a1v) :
 *     "0"(a1v))) kills the else arm's a1v==0 knowledge, so a2v = 0
 *     emits move a2,zero (retail 80052104 addu $a2,$zero,$zero) instead
 *     of move a2,a1. No code emitted.
 * And the round-9/10/11 ladder this sits on: computed-goto dispatch over
 * the committed jtbl_80021B10 row under --addiu-at on (per-target
 * maspsx_flags.txt, g3_eu only), printf-LAST default block (cross-
 * jumping fires, stub merge closed), $2-pinned two-index no-flag table
 * loads with the s6v-then-t0 sum order, goto/shared-block mode chain
 * with the FALL-THROUGH lmode join (retail 8005213C falls into the
 * shared tmp!=1 check at 80052144) and the SHARED compare constant
 * materialized once into the dead a1v register (a1v = 1 before the
 * chain, retail's ori $a1,$zero,0x1 at 80052110) with the f1 compare
 * expressed as D_80147E24 != tmp (retail's bne $v0,$v1 at 80052158).
 * Dead ends banked this window: lever B (opaque "=r"(rec) redefine)
 * fixes the store base but reshuffles the whole prologue save/move
 * order (6-40 diffs, v9/v10/v13); input-only volatile asm does NOT
 * block the forwarding (v12); B2 (asm-as-definition at entry) worse.
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
    long *rec;
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
    register long *tbl asm("$2");

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
        /* LEVER A: the read keeps t9 live PAST a1v's definition, so gcc
         * cannot coalesce the t9 chain (lw/srl) into a1v's $5 pin -
         * retail holds it in $v1 (row 800520A8/BC: lw $v1 / srl $v1,$v1,9)
         * and materializes a1v = andi $a1,$v1,7. No code emitted. */
        __asm__ ("" : : "r"(t9));
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
            /* LEVER C: opaque redefinition of a1v kills the else-arm's
             * a1v==0 knowledge, so a2v = 0 emits move a2,zero (retail row
             * 80052104: addu $a2,$zero,$zero) instead of move a2,a1. */
            __asm__ ("" : "=r"(a1v) : "0"(a1v));
            a2v = 0;
        }
        a1v = 1;
        if (D_80147E20 == a1v) {
            mode = 2;
        } else {
            long tmp = D_80164268;
            if (tmp != 0) goto L_mode_shared;
            if (GsSetLightMode_lmode == a1v) goto L_mode_one;
            /* fall through: lmode != 1 enters the shared check with tmp==0,
             * whose (tmp != 1) compare then sends it to mode=0 (retail's
             * 8005213C fall-through into 80052144). */
        L_mode_shared:
            if (tmp != a1v) goto L_mode_zero;
            if (D_80147E24 != tmp) goto L_mode_zero;
        L_mode_one:
            mode = 1;
            goto L_mode_done;
        L_mode_zero:
            mode = 0;
        L_mode_done:
            ;
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
            goto L_default;
        L_0x20:
                if (*(unsigned short *)(s0 + 2) & 4) {
                    D_8016AB6C = ((StdFn) * (long *)(s6v + (char *)D_80098A98))(
                        (long *)s0, s2, s7, D_8016AB6C,
                        *(unsigned short *)s0, a2, a1, rec);
                    s1 -= *(unsigned short *)s0;
                    s0 += *(unsigned short *)s0 * 24;
                } else {
                    tbl = (long *)((char *)D_80098998 + s6v + t0); D_8016AB6C = ((StdFn) *(long *)tbl)(
                        (long *)s0, s2, s7, D_8016AB6C,
                        *(unsigned short *)s0, a2, a1, rec);
                    s1 -= *(unsigned short *)s0;
                    s0 += *(unsigned short *)s0 * 16;
                    goto L_next;
        L_0x24:
                tbl = (long *)((char *)D_800989D8 + s6v + t0); D_8016AB6C = ((StdFn) *(long *)tbl)(
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
                    tbl = (long *)((char *)D_800989B8 + s6v + t0); D_8016AB6C = ((StdFn) *(long *)tbl)(
                        (long *)s0, s2, s7, D_8016AB6C,
                        *(unsigned short *)s0, a2, a1, rec);
                    s1 -= *(unsigned short *)s0;
                    s0 += *(unsigned short *)s0 * 20;
                }
                goto L_next;
        L_0x34:
                tbl = (long *)((char *)D_800989F8 + s6v + t0); D_8016AB6C = ((StdFn) *(long *)tbl)(
                    (long *)s0, s2, s7, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 28;
                goto L_next;
        L_0x28:
                tbl = (long *)((char *)D_80098A18 + s6v + t0); D_8016AB6C = ((StdFn) *(long *)tbl)(
                    (long *)s0, s2, s7, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 20;
                goto L_next;
        L_0x2C:
                tbl = (long *)((char *)D_80098A58 + s6v + t0); D_8016AB6C = ((StdFn) *(long *)tbl)(
                    (long *)s0, s2, s7, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 32;
                goto L_next;
        L_0x38:
                tbl = (long *)((char *)D_80098A38 + s6v + t0); D_8016AB6C = ((StdFn) *(long *)tbl)(
                    (long *)s0, s2, s7, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 24;
                goto L_next;
        L_0x3C:
                tbl = (long *)((char *)D_80098A78 + s6v + t0); D_8016AB6C = ((StdFn) *(long *)tbl)(
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
        L_default:
                printf(D_80021AF0, code, s0);
                goto L_next;
            }
            L_next:
            ;
        } while (s1 != 0);
    }
}

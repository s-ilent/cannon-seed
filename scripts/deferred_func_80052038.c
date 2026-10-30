/* Real-decompiled-C game function #15 candidate (window 34 decode; round-1
 * landing attempt 2026-10-30, this window, witness 8/8 restored at 13:20Z on
 * Silent's fresh 11:42 UTC CDN links).
 *
 * ROUND-1 STATUS: judge reached SIZE built 1932 vs row 2032 (84 B / 21 insns
 * short) with the head + prologue + save-slot layout EXACT; the case bodies
 * compile and the stub-merge shape is close but not yet byte-exact. The full
 * C below compiles clean and is the resume point - iterate judge_unit from
 * here, do NOT restart the decode.
 *
 * ROUND-1 FINDINGS (all judge-proven against the live oracle):
 * - HEAD CONDITION: the 80052074 branch is bltz $v0 -> the epilogue, i.e.
 *   the body runs when ctrl[0] >= 0 - the if (*ctrl >= 0) form is correct.
 * - THE FIVE HEAD RELOADS INTERLEAVE (retail: load(N) slides up between
 *   srl(N-1) and andi(N-1), never crossing a store). Plain C reproduces the
 *   five reloads but NOT the interleave (probe scripts/probe_head_reload.c
 *   variants A/B and probe_head_reload2.c D/E/F all stay sequenced). The
 *   load-hoist needs the SOFTWARE-PIPELINED statement order used below
 *   (each field's load precedes the previous field's store; the scheduler
 *   then interleaves without crossing a store). C89: declarations first,
 *   assignments in pipeline order.
 * - HEAD SHIFTS ARE UNSIGNED (srl not sra): read via
 *   *(unsigned long *)ctrl.
 * - THE HEAD-FIELD TARGETS ARE SCALAR EXTERNS: `extern long D_80147E24;`
 *   + bare-name stores give the retail lui $at/%hi + sw %lo form; the
 *   array-extern form (D_80147E24[0]) makes gcc cache the address in a
 *   call-clobbered reg (la $9) - wrong. Same for D_80164268/D_80147E20/
 *   D_801727D4/D_80171E04/D_8016AB6C/D_8016AF90/D_8016AFA4/
 *   GsSetLightMode_lmode (fused-pair loads for the reads).
 * - PARAM PINS: retail holds a1 -> $20 (s4), a2 -> $21 (s5), rec -> $19
 *   (s3); the register-var pins reproduce the save-slot layout exactly
 *   (0x38/0x3C/0x34) when the initializers run in the order a1, a2, rec.
 * - PIN WARNING: pinning fpv (a2v*4) to $30 makes gcc COALESCE the spilled
 *   t0 (a2v*12) into $fp and emits a dead duplicate sll - WRONG ADDRESSES
 *   in the 6-entry grid cases. fpv must stay UNPINNED; gcc then spills t0
 *   to 0x20(sp) (vars=8, frame 0x50, all ten save slots == retail) and
 *   allocates fp naturally.
 * - CALL TYPES: two typedefs - StdFn 8 args (op, s2, s7, D_8016AB6C, len,
 *   a2, a1, rec) and AltFn 7 args (op, s2, D_8016AB6C, len, a2, a1, rec);
 *   both end in long* - the unprototyped-int tail made gcc warn.
 * - ADVANCE CORRECTIONS over the window-34 case map (asm truth):
 *   0x28 = x20 (sll,addu -> j 27D0 <<2), NOT x36; 0x30-clear = x20, NOT
 *   x28; 0x2D falls INTO the 274C stub = x32 (no inline chain); 0x29 and
 *   0x31 fall through the 2590/25EC merge points (a1 = s2 rides inside
 *   the stub). x16/x24/x32 tail-merge into 80052594/25EC/274C; x20/x28/
 *   x36/x44 stay inline over the shared 27CC/27D0 chain.
 * - gcc lowers `switch (code)` (16 cases 0x20..0x3D, step-4 pattern) to
 *   the exact sltiu/jtbl form with the 14 default-filled dead slots.
 *
 * REMAINING ROUND-2 WORK: (1) case-body pass - the judge diff after the
 * pipelined head lands; expected deltas are the table-address addu operand
 * order and the per-case arg-store order; (2) the stub merge - if gcc
 * merges the x20/x28 groups retail left inline, differentiate the advance
 * text; (3) the loop-head t0/fpv/s6 emission order.
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

void func_80052038(long *ctrl, long a1p, long a2p, long *recp)
{
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
    long a1v;
    long a2v;
    long mode;
    long *state;

    a1 = a1p;
    a2 = a2p;
    rec = recp;

    if (*ctrl >= 0) {
        long f1;
        long f2;
        long f3;
        long f5;
        f1 = (long)((*(unsigned long *)ctrl >> 3) & 3);
        f2 = (long)((*(unsigned long *)ctrl >> 5) & 1);
        D_80147E24 = f1;
        f3 = (long)((*(unsigned long *)ctrl >> 6) & 1);
        D_80164268 = f2;
        a1v = (*(unsigned long *)ctrl >> 9) & 7;
        D_80147E20 = f3;
        f5 = (long)((*(unsigned long *)ctrl >> 30) & 1);
        D_801727D4 = a1v;
        D_80171E04 = f5;
        a2v = (a1v != 0);
        if (a1v != 0) {
            rec[0] = a1v;
            rec[1] = D_8016AF90;
            rec[2] = D_8016AFA4;
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
                mode = (GsSetLightMode_lmode == 1);
            }
        }
        state = (long *)ctrl[2];
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
        do {
            unsigned int code = (unsigned int)s0[3] & 0xFD;
            switch (code) {
            case 0x20:
                if (*(unsigned short *)(s0 + 2) & 4) {
                    D_8016AB6C = ((StdFn) * (long **)((char *)D_80098A98 + s6v))(
                        (long *)s0, s2, s7, D_8016AB6C,
                        *(unsigned short *)s0, a2, a1, rec);
                    s1 -= *(unsigned short *)s0;
                    s0 += *(unsigned short *)s0 * 24;
                } else {
                    D_8016AB6C = ((StdFn) * (long **)((char *)D_80098998 + t0 + s6v))(
                        (long *)s0, s2, s7, D_8016AB6C,
                        *(unsigned short *)s0, a2, a1, rec);
                    s1 -= *(unsigned short *)s0;
                    s0 += *(unsigned short *)s0 * 16;
                }
                break;
            case 0x24:
                D_8016AB6C = ((StdFn) * (long **)((char *)D_800989D8 + t0 + s6v))(
                    (long *)s0, s2, s7, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 24;
                break;
            case 0x30:
                if (*(unsigned short *)(s0 + 2) & 4) {
                    D_8016AB6C = ((StdFn) * (long **)((char *)D_80098AA4 + s6v))(
                        (long *)s0, s2, s7, D_8016AB6C,
                        *(unsigned short *)s0, a2, a1, rec);
                    s1 -= *(unsigned short *)s0;
                    s0 += *(unsigned short *)s0 * 28;
                } else {
                    D_8016AB6C = ((StdFn) * (long **)((char *)D_800989B8 + t0 + s6v))(
                        (long *)s0, s2, s7, D_8016AB6C,
                        *(unsigned short *)s0, a2, a1, rec);
                    s1 -= *(unsigned short *)s0;
                    s0 += *(unsigned short *)s0 * 20;
                }
                break;
            case 0x34:
                D_8016AB6C = ((StdFn) * (long **)((char *)D_800989F8 + t0 + s6v))(
                    (long *)s0, s2, s7, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 28;
                break;
            case 0x28:
                D_8016AB6C = ((StdFn) * (long **)((char *)D_80098A18 + t0 + s6v))(
                    (long *)s0, s2, s7, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 20;
                break;
            case 0x2C:
                D_8016AB6C = ((StdFn) * (long **)((char *)D_80098A58 + t0 + s6v))(
                    (long *)s0, s2, s7, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 32;
                break;
            case 0x38:
                D_8016AB6C = ((StdFn) * (long **)((char *)D_80098A38 + t0 + s6v))(
                    (long *)s0, s2, s7, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 24;
                break;
            case 0x3C:
                D_8016AB6C = ((StdFn) * (long **)((char *)D_80098A78 + t0 + s6v))(
                    (long *)s0, s2, s7, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 36;
                break;
            case 0x21:
                D_8016AB6C = ((AltFn) * (long **)((char *)D_800989B0 + fpv))(
                    (long *)s0, s2, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 16;
                break;
            case 0x29:
                D_8016AB6C = ((AltFn) * (long **)((char *)D_80098A30 + fpv))(
                    (long *)s0, s2, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 16;
                break;
            case 0x31:
                D_8016AB6C = ((AltFn) * (long **)((char *)D_800989D0 + fpv))(
                    (long *)s0, s2, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 24;
                break;
            case 0x25:
                D_8016AB6C = ((AltFn) * (long **)((char *)D_800989F0 + fpv))(
                    (long *)s0, s2, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 28;
                break;
            case 0x35:
                D_8016AB6C = ((AltFn) * (long **)((char *)D_80098A10 + fpv))(
                    (long *)s0, s2, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 36;
                break;
            case 0x39:
                D_8016AB6C = ((AltFn) * (long **)((char *)D_80098A50 + fpv))(
                    (long *)s0, s2, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 28;
                break;
            case 0x2D:
                D_8016AB6C = ((AltFn) * (long **)((char *)D_80098A70 + fpv))(
                    (long *)s0, s2, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 32;
                break;
            case 0x3D:
                D_8016AB6C = ((AltFn) * (long **)((char *)D_80098A90 + fpv))(
                    (long *)s0, s2, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 44;
                break;
            default:
                printf(D_80021AF0, code, s0);
                break;
            }
        } while (s1 != 0);
    }
}

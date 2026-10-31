/* Real-decompiled-C game function #15 candidate - ROUND-11 SCREEN (the
 * cron-20261031-0251 window). Body = v7 (round-10 goto/shared-block mode
 * chain) with BOTH round-11 resume levers applied:
 * (1) FALL-THROUGH JOIN: the tmp!=0 path enters the shared (tmp != 1)
 *     check via goto L_mode_shared, the lmode!=1 path FALLS THROUGH into
 *     it (source order: lmode check first, shared check after, no goto to
 *     a separate zero block) - retail 8005213C falls into 80052144, whose
 *     (tmp != 1) compare takes the tmp==0 fall-through to mode=0 with no
 *     extra branch, killing the built chain's extra j/nop join pair;
 * (2) SHARED COMPARE REGISTER: a1v = 1 reuses the dead $5 pin (a1v died
 *     at the rec[] stores) for the constant, materialized once before the
 *     chain and shared by the D_80147E20==1, lmode==1 and tmp!=1 compares
 *     - retail's ori $a1,$zero,0x1 at 80052110 (round-10 finding (b));
 *     the f1 compare is expressed as D_80147E24 != tmp so the comparand
 *     is tmp's register ($v1) exactly like retail's bne $v0,$v1 at
 *     80052158 (semantically identical: tmp==1 is proven at that point).
 * PROBE RECORD. Judge result banked below after the live run. (v8 judge: DIFF 5/508 at SIZE == 2032 - mode chain, stub merges, dispatch, all case bodies EXACT.)
 *
 * --- ROUND-10 STATE BELOW (cron-20261031-0136 window) --------------------
 * with ONLY the mode chain rewritten as the goto/shared-block form:
 * tmp!=1 -> L_mode_zero, f1!=1 -> L_mode_zero, lmode!=1 -> L_mode_zero,
 * explicit L_mode_one (mode=1; goto L_mode_done) / L_mode_zero (mode=0)
 * blocks. PROBE RECORD, not a landing candidate. LIVE JUDGE: SIZE 2036 vs
 * row 2032 (+4: the mode chain now matches retail's LENGTH - the
 * round-4-era length regression is gone), aligned 470/508 vs v6's
 * 468/508 (+2 only: the branch skeleton gained the delay-slot
 * assignments - addu $3,$0,$zero rides the bne delay and ori $3,$zero,1
 * the j delay, so round-4's "gcc delay-fills the arms" blocker is DEAD
 * under the printf-last shape - but the built chain still (a) spends an
 * extra j $L43 + nop pair on the join where retail FALLS THROUGH from
 * the D_80147E24 load into the shared compare, and (b) materializes the
 * compare-constant 1 into a temp $3 (ori $3,$zero,1) where retail
 * reuses a register that already holds 1 for BOTH compares ($a1 in the
 * row at 8005213C/44 - the round-4 "f1-vs-tmp register compare" note).
 * ROUND-11 RESUME: (1) drop the explicit goto to L_mode_one so the
 * f1==1 path falls through into the shared compare exactly like
 * retail; (2) find the source form that keeps the constant 1 in a
 * register the compares share (candidate: compare against a1v/state
 * words rather than literals, or a single if-ladder without the early
 * goto); then re-judge. The v6 la-chain state is UNTOUCHED here - the
 * two-index sites still carry the round-9 pinned form.
 *
 * --- ROUND-9 STATE BELOW (cron-20261031-0136 window, judge-proven) ----
 * Supersedes v3 (the banked
 * cron-20261031-0136 window, judge-proven on the live oracle). V6 = v4's
 * body with the eight two-index no-flag StdFn sites rewritten through a
 * $2-pinned local that materializes the FULL sum symbol-first-then-s6-then-t0:
 *   register long *tbl asm("$2");
 *   tbl = (long *)((char *)D_x + s6v + t0); ... *(long *)tbl ...
 * LIVE JUDGE: SIZE 2016 vs row 2032 (unchanged - both forms are 5 insns),
 * aligned 468/508 vs v4's 428/508: the la-chain delta CLOSED (+40 words =
 * exactly the predicted 5 words x 8 cases). Built chain (0x20-else class):
 *   la $2,D_x; addu $2,$8,$2; addu $2,$22,$2; lw $2,0($2)  ==  retail
 *   lui/addiu $v0; addu $v0,$t0,$v0; addu $v0,$s6,$v0; lw $v0,0($v0)
 * (row 80052248..58) - operand patterns AND addition order both match;
 * the sum-order swap (s6v before t0) was the key, the round-8 screen's
 * t0-then-s6v order built s6-first. The $2 pin does NOT disturb the
 * dispatch (its own $2 use is disjoint program points; screen + judge
 * confirm the dispatch bytes) nor the single-index at-split forms.
 * REMAINING 40 words / 28 blocks: (1) ~10 single-word stub-jump offsets -
 * built tail-js land 0x10 (4 insns) EARLIER into each shared stub than
 * retail (j 80052584 vs j func_80052594, j 800525dc vs 525EC, j 800527bc
 * vs 27CC, j 800527c0 vs 27D0, ...) - gcc shares 4 more leading insns
 * than retail's merge points; (2) the mode-chain replace block
 * (~0x80052130, ~12 retail words, xori/sltiu if-conversion vs retail's
 * branch form); (3) the head register nits (0x80052074 DB01 vs DF01,
 * 0x800520A8 lw $5 vs $3, ...). Landing still waits per the gates (not
 * EXACT); staging was staged, judged and REVERTED this window.
 *
 * --- ROUND-7 STATE BELOW (cron-20261030-2306 window, judge-proven) ----
 * Supersedes v3 (the banked
 * cron-20261030-2306 window, judge-proven). Supersedes v3 (the banked
 * window-36 combination v2-dispatch + round-4 case bodies + tbl pin),
 * which the live judge REGRESSED: SIZE 2236/2032 DIFF 450/508 vs v2's
 * 2228/444. v3's tbl=$2 pin is WRONG under the computed-goto dispatch -
 * the dispatch itself occupies $2 (sltiu+sll/lw/j), so the pinned la
 * lands in $v0 where the single-index retail form is la-in-$at, plus a
 * duplicate move a0,s0 scheduling artifact; the round-5 plain forms
 * were already retail-correct for the single-index shapes under
 * addiu_at. V4 = plain bodies everywhere (no tbl pin, no barrier) +
 * the default printf block moved to SOURCE-LAST (L_default before
 * L_next) - built placed it early (+2 insns: the extra j/nop pair to
 * the loop-back); retail has it last, falling through to the loop
 * back-edge (bnez $s1 after the printf return).
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
 * - CASE BODIES: v3's live judge DISPROVED the round-4 body restore -
 *   the round-5 judge REGRESSION (SIZE 2228/2032, DIFF 444/508) was NOT
 *   the missing pins: under the computed-goto dispatch the plain forms
 *   are correct for every case class (the single-index loads ride the
 *   addiu_at at-split natively; the two-index no-flag forms give the
 *   same 5-insn count). v3's restored tbl=$2 pin CONFLICTED with the
 *   dispatch's own $2 use: the pinned la landed in $v0 where retail is
 *   la-in-$at, plus a duplicate move a0,s0 scheduling artifact (+8 B,
 *   DIFF 450). V4 keeps the round-5 plain bodies everywhere.
 * - DECLARATIONS: v2's set exactly (fpv, t0, mid, a1v, a2v, t9, mode,
 *   state, ix) - no tbl pin.
 *
 * Judge history: round-2 1944 (436/486) -> round-4 switch 1988 (405/497,
 * orphan .rodata table blocks landing) -> round-5 goto+plain 2228 (444/508)
 * -> round-6 goto+pins 2236 (450/508, pin conflicts with dispatch $2).
 * Remaining deltas after v4 (all mapped via scripts/linked_sidediff.py on
 * the mini-linked judge .elf): (1) the stub-merge/tail-sharing item ~+35
 * words - retail TAIL-JUMPS same-stride cases into shared stubs
 * (x16/x24/x32 full stubs 80052594/25EC/274C; the rest share the 27CC/27D0
 * call chain) while gcc 2.6.3 inline-expands every case tail; (2) the mode
 * chain ~+6 words (gcc if-converts with xori, retail keeps the branch form
 * with shared mode=1/0 blocks); (3) the known register nits (a1v
 * lw/srl-into-$5 vs retail $3, rec[0] base $7 vs $s3, a2v move a2,a1 vs
 * move a2,zero, mode-temp $v0 vs $v1). Next levers: express the tails so
 * gcc 2.6.3 cross-jumping fires (identical trailing statement sequences
 * per stride group), or accept inline tails; the mode-chain goto-form
 * probe v5/v6 shapes (banked round-4).
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
    register long *tbl asm("$2");

    a1 = a1p;
    a2 = a2p;
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
            /* LEVER B25: the asm IS rec's only definition - recp's value
             * must land in rec's $19 pin here, and the output makes rec
             * opaque past it, so rec[0]'s bare-rec address use cannot be
             * forwarded to the incoming $a3. The move $19,$7 stays
             * schedulable into the bltz delay slot (retail 80052078). */
            __asm__ ("" : "=r"(rec) : "0"(recp));
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

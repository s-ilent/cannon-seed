/* ROUND-5 DRAFT - JUDGED ON THE LIVE ORACLE (cron-20261031-0851 window):
 * SIZE built 1424 = row 1424 (EXACT LENGTH), aligned 351/356, DIFF 6 words.
 * Two lever applications on top of r4:
 *  1. The b20 pin (v5 asm("$5")) HOLDS in the full context: c5 emits its
 *     full 9-word chain (lui/lw/nop/beqz/ori/beq/ori/j/ori), c0 stays
 *     retail-exact in $3, and the ~20 downstream j-target shifts of the
 *     r3 map auto-resolved as predicted once the first cluster reached
 *     full length.
 *  2. NEW LAW - the label-barrier asm must sit BEFORE the >= 6 check:
 *     retail fills the first beqz's delay slot with the dispatch's own
 *     sltiu (row 8006AFB8/BC); the r4 position (asm BETWEEN the two
 *     range checks) is a scheduling barrier and the built emitted a nop
 *     instead - that ONE +1 word shifted every downstream j/jal target
 *     and both InterruptCallback %lo immediates by 4 (the r5 first
 *     judge: SIZE 1428, DIFF 336; after the move: SIZE 1424, DIFF 6).
 * The remaining 6 words:
 *  a. c5's four reg-field words - lui/lw/beqz/beq encode $5 where retail
 *     carries $v1 (the pin's structural cost; v5 pinned to $3 itself
 *     re-merges per b21, so 4 is the current floor).
 *  b. func_8006B0F0's prologue: retail schedules the pinned-counter init
 *     ori $v0,0x3E7 BEFORE the ra save (row 8006B0F4), the built after
 *     it (same encoding, one word later - judge counts it twice via an
 *     insert/delete pair). Probe bank: plain counter schedules FIRST
 *     (init before the saves) but local-alloc picks $5, not $2 (p3);
 *     s0/s1 need no pins - unpinned they still allocate $17/$16 and the
 *     save order is unchanged (p1); declaration order does not matter.
 * OPEN for the next window: a lever that yields the retail prologue
 * order with the $2 pin (or a cc-post prologue fixup class), and any
 * c5 anti-merge lever cheaper than the 4 reg-field words. Staging
 * (yaml 0x4B770 flip + src copy) REVERTED per the gates - DIFF != EXACT.
 * ROUND-4 header (the plain distinct-pseudo application): the c5 anti-merge
 * closes as a SOURCE-SHAPE LAW: gcc 2.6.3's cross-jumping matches RTL
 * REGNOS; the c5/c0 chains' loads must live in two DISTINCT pseudos
 * (distinct regnos at jump.c time) for both chains to emit full-length;
 * local-alloc then folds them into the same $v1 as retail (probe ladder
 * b1-b6: head/c1..c4/dispatch eliminated, same-pseudo control merges,
 * distinct-pseudo emits 9+9). The r3 memory barrier is gone - it never
 * blocked anything. Previous header:
 * - built on the round-2 sidediff map.
 * ROUND-2 RESULT (banked in the worklog before the third sandbox
 * rollback): SIZE 1388 vs 1424 (-36 B = -9 insns), aligned 295/356,
 * from round-1's 1312 / 183 - the seven levers recovered +76 words.
 * Round-3 levers, read off the round-2 map:
 *  1. The c1 else-path goes OUT-OF-LINE via explicit goto (the built
 *     inverted the branch: beqz vs retail's bnez with the 5-path
 *     falling through B030 inline and the 0x3C-path at B040).
 *  2. The installer arms go OUT-OF-LINE in retail order (B178 a0!=0
 *     arm, B190 ==3 arm with s0 in the j delay, B1A0 ==2 arm falling
 *     into B1AC set6, set6 j over the timer to B284) - round-2's
 *     inline bodies inverted every branch polarity (bne vs beq) and
 *     stranded set6 after the install check.
 *  3. L_timer's s1 = 0xF2000002 moves AFTER the A54 check so the lui
 *     fills the bnez delay (retail B1D0) and the ori floats to the
 *     range-branch delay (retail B1F0).
 *  4. The c5 chain carries an opaque-redefinition asm on the state
 *     load: gcc 2.6.3 tail-merged the structurally-identical c0/c5
 *     three-path chains in round-2 (the built LOST c5's 9 words);
 *     the asm makes the two head blocks RTL-distinct at zero bytes.
 *  5. keep-epilogue + all-scalar externs + computed-goto jtbl + the
 *     case-4 parameter reassignment carry over (all proven by
 *     round-2's aligned regions).
 */
/* cc-post: keep-epilogue */

extern long D_800ABA38;
extern long D_800ABA3C;
extern long D_800ABA40;
extern long D_800ABA44;
extern long D_800ABA48;
extern long D_800ABA4C;
extern long D_800ABA50;
extern long D_800ABA54;
extern long D_80171E08;              /* = SsSeqCalledTbyT_ntracks (curated) */
extern long jtbl_8002220C[];
extern void intr_stop_begin(void);
extern long func_8006B648(long);     /* LANDED slot clear */
extern long func_8006B500(long, long, long);
extern long func_8006B5D8(long);
extern long func_8004AE64(void);     /* curated intr_restart_commit */
extern void VSyncCallback(void (*fn)(void));
extern long InterruptCallback(long, void (*fn)(void));
extern void SpuQuit(void);
extern void SsSeqCalledTbyT(void);
void func_8006B4B8(void);
void func_8006B484(void);

void func_8006AF70(long a0)
{
    long v0;
    long v1;
    register long v5 asm("$5");
    long vt;

    if (a0 & 0x1000) {
        D_800ABA54 = 1;
        D_800ABA50 = a0 & 0xFFF;
    } else {
        D_800ABA54 = 0;
        D_800ABA50 = a0;
    }
    v1 = D_800ABA50;
    /* the label-barrier asm sits BEFORE the >= 6 check: between the two
     * range checks there must be NOTHING (retail fills the first beqz's
     * delay slot with the dispatch's own sltiu; an intervening asm is a
     * scheduling barrier and the built emits a nop instead - the +1 word
     * that shifted every downstream j-target by 4 in the r5 judge) */
    __asm__ ("" : : "i"(&&L_c0), "i"(&&L_c1), "i"(&&L_c2), "i"(&&L_c3),
                    "i"(&&L_c4), "i"(&&L_c5));
    if (v1 >= 6)
        goto L_big;
    if ((unsigned long)v1 < 6)
        goto *((void **)jtbl_8002220C)[v1];
    /* default (B0CC: ori v0,0x3C falls into B0D0's store) */
    vt = 0x3C;
    goto L_store3C;

L_c4:   /* 0x8006AFE4 - the parameter is reassigned to the constant */
    a0 = 0x32;
    v1 = D_800ABA44;
    D_80171E08 = a0;
    if (v1 == 1) {
        v0 = 5;
        goto L_store5;
    }
    D_800ABA50 = a0;
    return;

L_c1:   /* 0x8006B014 - the 5-path falls through B030, 0x3C out-of-line */
    v0 = D_800ABA44;
    v1 = 0x3C;
    D_80171E08 = v1;
    if (v0 != 0)
        goto L_b040;
    v0 = 5;
L_store5:   /* B030: sw v0 -> ABA50, shared by case 1 fall and case 4 beq */
    D_800ABA50 = v0;
    return;
L_b040:     /* B040: sw v1 (0x3C) -> ABA50 */
    D_800ABA50 = v1;
    return;

L_c3:   /* 0x8006B050 */
    D_80171E08 = 0x78;
    return;

L_c2:   /* 0x8006B064 */
    D_80171E08 = 0xF0;
    return;

L_c5:   /* 0x8006B078 - three-path chain; v5 is PINNED to $5 (b20 lever):
         * the load-dest register must differ from c0's $v1 at jump.c time
         * or cross-jumping eats this chain into a [load; j] 4-word stub */
    v5 = D_800ABA44;
    if (v5 == 0)
        goto L_def;
    if (v5 == 1) {
        vt = 0x32;
        goto L_store32;
    }
    vt = 0x3C;
    goto L_store3C;

L_c0:   /* 0x8006B09C - three-path chain, bne polarity, 0x32 falls */
    v1 = D_800ABA44;
    if (v1 == 0)
        goto L_def;
    if (v1 != 1) {
        vt = 0x3C;
        goto L_store3C;
    }
    vt = 0x32;
    /* fall into the shared 0x32 store */
L_store32:  /* B0BC: sw v0 -> D_80171E08 */
    D_80171E08 = vt;
    return;

L_def:      /* B0CC: ori v0, 0x3C, falls into the shared store */
    vt = 0x3C;
L_store3C:  /* B0D0: sw v0 -> D_80171E08 */
    D_80171E08 = vt;
    return;

L_big:      /* B0E0: the >= 6 arm falls into the epilogue */
    D_80171E08 = v1;
    return;
}

void func_8006B0F0(long a0)
{
    long i;
    register long v0 asm("$2");
    register long v1 asm("$3");
    register long s0 asm("$16");
    register long s1 asm("$17");

    v0 = 0x3E7;
    while (v0 >= 0)
        v0 = v0 - 1;
    v1 = D_800ABA50;
    if (v1 == 2)
        goto L_arm2;
    if (v1 < 3) {
        if (v1 == 0)
            return;
        goto L_timer;
    }
    if (v1 == 3)
        goto L_arm3;
    if (v1 != 5)
        goto L_timer;
    if (a0 != 0)
        goto L_armA;
    /* a0 == 0: the VSync-mode counter bump (retail B158, fused pairs) */
    v0 = D_800ABA38;
    v0 = v0 + 1;
    D_800ABA38 = v0;
    goto L_install;

L_armA:     /* B178: the 0xF2000003 arm; s0 rides the j delay */
    s1 = 0xF2000003;
    D_800ABA3C = 0;
    s0 = 1;
    goto L_install;

L_arm3:     /* B190: s0 = 0x89D0 rides the j delay into set6 */
    s1 = 0xF2000002;
    s0 = 0x89D0;
    goto L_set6;

L_arm2:     /* B1A0: falls into set6 (retail layout) */
    s1 = 0xF2000002;
    s0 = 0x44E8;
L_set6:     /* B1AC: shared; j over the timer to the install block */
    D_800ABA3C = 6;
    goto L_install;

L_timer:    /* B1C0 */
    if (D_800ABA54 != 0)
        return;
    s1 = 0xF2000002;                 /* lui fills the bnez delay */
    v1 = D_800ABA50;
    D_800ABA3C = 6;
    if (v1 < 0x46) {
        v0 = 0x204CC0;
        v0 = v0 / v1;                /* EXPAND_DIV guards, probe-proven */
        D_800ABA40 = D_800ABA40 + 1;
        s0 = v0;                     /* rides the j delay (retail B244) */
        goto L_install;
    }
    v0 = 0x409980;
    v0 = v0 / v1;
    s0 = v0;
    /* fall into the install block (retail B278 -> B284) */

L_install:  /* B284 */
    if (D_800ABA38 != 0) {
        VSyncCallback(SsSeqCalledTbyT);
        return;
    }
    intr_stop_begin();
    func_8006B648(s1);
    func_8006B500(s1, s0 & 0xFFFF, 0x1000);
    v0 = 0x7CF;
    while (v0 >= 0)
        v0 = v0 - 1;
    v0 = 0x7CF;
    while (v0 >= 0)
        v0 = v0 - 1;
    func_8006B5D8(s1);
    if (D_800ABA3C == 0) {
        D_800ABA48 = InterruptCallback(0, 0);
        InterruptCallback(D_800ABA3C, func_8006B484);
    } else {
        if (D_800ABA40 == 0)
            InterruptCallback(D_800ABA3C, SsSeqCalledTbyT);
        else
            InterruptCallback(D_800ABA3C, func_8006B4B8);
    }
    func_8004AE64();
}

void func_8006B380(void)
{
    func_8006B0F0(1);
}

void func_8006B3A0(void)
{
    func_8006B0F0(0);
}

void func_8006B3C0(void)
{
    long v0;
    long a0;

    if (D_800ABA54 != 0)
        return;
    D_800ABA40 = 0;
    intr_stop_begin();
    v0 = D_800ABA38;
    if (v0 != 0) {
        VSyncCallback(0);
        D_800ABA38 = 0;
    } else {
        a0 = D_800ABA3C;
        if (a0 != -1) {
            if (a0 == 0)
                InterruptCallback(0, (void (*)(void))D_800ABA48);
            else
                InterruptCallback(a0, 0);
            D_800ABA3C = -1;
        }
    }
    func_8004AE64();
}

void func_8006B464(void)
{
    SpuQuit();
}

void func_8006B484(void)
{
    void (*old)(void);

    old = (void (*)(void))D_800ABA48;
    if (old != 0)
        old();
    SsSeqCalledTbyT();
}

void func_8006B4B8(void)
{
    if (D_800ABA4C == 0) {
        D_800ABA4C = 1;
        return;
    }
    D_800ABA4C = 0;
    SsSeqCalledTbyT();
}

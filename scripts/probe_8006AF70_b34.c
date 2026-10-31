/* BISECT B34 - r5 with c5's load replaced by an explicit 3-word
 * address-materialization asm, output bound to the r5 $5 pin:
 *     __asm__ ("lui %0,%%hi(D_800ABA44)\n\tlw %0,%%lo(D_800ABA44)(%0)\n\tnop"
 *              : "=r" (v5));   with register long v5 asm("$5")
 * QUESTION (round 7, offline screen cron-20261031-1021 window, oracle
 * DOWN - disc links 404 at ~22.7h age): does an opaque byte-emitting
 * load kill the c5/c0 cross-jump merge WITHOUT the $5 reg-field cost?
 * RESULT (cc.sh -S screen, whole-unit diff vs r5 outside the chain is
 * EMPTY apart from label renumbering): the merge is DEAD - both chains
 * emit full-length in retail order, the store blocks stay separate
 * ([sw;j] x2), L_def falls into store3C, c0's 0x32 arm falls into
 * store32 - but the asm output binds to the DECLARED $5, so the built
 * is byte-identical to r5's chain region (maspsx expands the plain
 * `lw $5,D_800ABA44` into the same [lui $5,%hi; lw $5,%lo($5)] pair,
 * marked "# DEBUG: leaving for assembler to expand"). ZERO GAIN over
 * r5: the 4 reg-field words stay $5. The probe banks the MECHANISM:
 * a real byte-emitting asm IS opaque to jump2's tail match (the
 * [lui;lw;nop] prefix no longer matches c0's C-generated load), so
 * opacity works - the register binding is what decides the diff.
 * cc-post: keep-epilogue
 */
/* cc-post: keep-epilogue
 * cc-post: keep-prologue - func_8006B0F0's retail prologue keeps the
 * pinned-counter init ori $v0,0x3E7 ABOVE the ra save (row 8006B0F4),
 * so cc_post's rule-4 restore must not fire here. */


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
    __asm__ ("lui %0,%%hi(D_800ABA44)\n\tlw %0,%%lo(D_800ABA44)(%0)\n\tnop"
             : "=r" (v5));
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

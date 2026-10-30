/* PARKED DRAFT - window 35 (cron-20261030-1113), offline decode of the
 * func_8006AF70 row (g3_eu, 0x590 bytes, 0x8006AF70..0x8006B500, rank 4
 * on the re-ranked real-C reading list, caller func_80028140 - one of the
 * verified game-zone edges). Byte-exact landing WAITS for a witnessed
 * oracle per the INPUT GATES (judge is live-only); the 2026-10-29 15:21
 * CDN links are dead (EU/JP 404 at 11:14Z), witness 0/8.
 *
 * THE TICK-MODE INSTALLER FAMILY - the game's own source-compiled copy of
 * the psyq LIBSND SSCALL tick plumbing around SsSeqCalledTbyT (curated:
 * LIBSND SSCALL member, landed in src/SsSeqCalledTbyT.c; the landed
 * func_8006B648 slot-clear documents this row as its caller). The row is
 * one yaml row with seven function definitions plus the un-glabel'd
 * func_8006B3A0 thunk (the func_8006B648 landing convention: one C file,
 * multiple definitions, address-names for un-glabel'd entries).
 *
 * DATA MAP (curated identities where they exist):
 *   D_800ABA50  the tick-mode word: func_8006AF70 writes (a0 & 0x1000) ?
 *               (a0 & 0xFFF) : a0; switch values 0..5, later rewritten to
 *               5 / 0x3C by cases 1/4 (dual range: mode code OR tempo)
 *   D_800ABA54  the 0x1000 flag bit ("a0 high-bit mode")
 *   D_800ABA44  play state (0/1), read by switch cases 0/1/4/5
 *   D_80171E08  = SsSeqCalledTbyT_ntracks (curated alias!) - the switch
 *               writes 0x32/0x3C/0x78/0xF0/a0/v1 into it
 *   D_800ABA3C  interrupt slot: 6 = timer tick (RCnt2-class), 0 = vblank,
 *               -1 = unregistered
 *   D_800ABA48  the SAVED original vblank callback (chained by 8006B484)
 *   D_800ABA40  timer users count: first install registers the raw
 *               SsSeqCalledTbyT tick, later installs the half-rate divider
 *   D_800ABA4C  the half-rate toggle (tick on every other invocation)
 *   D_800ABA38  VSync-mode flag: when set, install = VSyncCallback only
 */

/* externs for the landing (scalar vs array per site is a landing probe):
 * extern long D_800ABA38[], D_800ABA3C[], D_800ABA40[], D_800ABA44[],
 *             D_800ABA48[], D_800ABA4C[], D_800ABA50[], D_800ABA54[],
 *             D_80171E08[];   // = SsSeqCalledTbyT_ntracks (curated)
 * extern void intr_stop_begin(void);        // curated, INTR cluster entry 1
 * extern long func_8006B648(long);          // LANDED (b22554e2)
 * extern long func_8006B500(long, long, long);
 * extern long func_8006B5D8(long);
 * extern long func_8004AE64(void);          // intr lane, NOT ours to flip
 * extern void VSyncCallback(void (*fn)(void));       // LIBETC INTR member
 * extern long InterruptCallback(long, void (*fn)(void));  // LIBETC member
 * extern void SpuQuit(void);                // LIBSPU S_Q member
 * extern void SsSeqCalledTbyT(void);        // LANDED
 */

/* ---- func_8006AF70: the mode/tempo switch (0x180 bytes incl. tail) ----
 * head: bit 0x1000 splits the arg packing; both arms fall into the switch
 * on D_800ABA50. The slti/sltiu PAIR with two different out-of-range
 * targets = the explicit `v1 >= 6` pre-check (store v1 through) followed
 * by the switch whose default (negatives only) stores 0x3C.
 * jtbl_8002220C (6 words, data_80022208.data.s):
 *   0 -> 0x8006B09C, 1 -> 0x8006B014, 2 -> 0x8006B064, 3 -> 0x8006B050,
 *   4 -> 0x8006AFE4, 5 -> 0x8006B078.
 * Cases 0 and 5 have IDENTICAL C semantics but two structurally different
 * bodies (0: beqz/bne/fall through B0BC; 5: beqz/beq/j B0D0) - the source
 * wrote them separately and retail gcc did not tail-merge.
 */
void func_8006AF70(long a0)
{
    long v1;

    if (a0 & 0x1000) {
        D_800ABA54[0] = 1;
        D_800ABA50[0] = a0 & 0xFFF;
    } else {
        D_800ABA54[0] = 0;
        D_800ABA50[0] = a0;
    }
    v1 = D_800ABA50[0];
    if (v1 >= 6) {                       /* slti; beqz -> B0E0 */
        D_80171E08[0] = v1;
        return;
    }
    switch (v1) {                        /* sltiu; beqz -> B0CC = default */
    case 0:                              /* B09C: beqz->B0CC, bne->B0D0 */
        D_80171E08[0] = (D_800ABA44[0] == 1) ? 0x32 : 0x3C;
        return;
    case 1:                              /* B014: bnez->B040(v1=0x3C), fall B030(v0=5) */
        D_80171E08[0] = 0x3C;
        D_800ABA50[0] = (D_800ABA44[0] != 0) ? 0x3C : 5;
        return;
    case 2:                              /* B064 */
        D_80171E08[0] = 0xF0;
        return;
    case 3:                              /* B050 */
        D_80171E08[0] = 0x78;
        return;
    case 4:                              /* B0AFE4: beq->B030(v0=5), fall =a0 */
        D_80171E08[0] = 0x32;
        D_800ABA50[0] = (D_800ABA44[0] == 1) ? 5 : a0;
        return;
    case 5:                              /* B078: beqz->B0CC, beq->B0BC */
        D_80171E08[0] = (D_800ABA44[0] == 1) ? 0x32 : 0x3C;
        return;
    default:                             /* B0CC -> B0D0 */
        D_80171E08[0] = 0x3C;
        return;
    }
}

/* ---- func_8006B0F0: the installer (frame 0x20: ra/s1/s0) ----
 * TWO dead-result countdown spins (0x3E7-1 = 998; probe PROVEN: the
 * `while (i-- >= 0)` post-decrement form puts the decrement in the bgez
 * BRANCH DELAY SLOT, exactly retail 8006B108/2D8/2E8 - make i dead so gcc
 * keeps the single-register form).
 * Dispatch on D_800ABA50 (reload): 0 -> plain return; 1 -> B1C0 timer;
 * 2 -> s0 = 0x44E8; 3 -> s0 = 0x89D0; 4 -> B1C0; 5 -> a0 picks between
 * D_800ABA38++ (VSync path) and the 0xF2000003/slot-0/s0=1 arm; v1 >= 6
 * also reaches B1C0 (the v1!=5 branch of B13C).
 * B1C0: s1 = 0xF2000002 materializes in the FIRST bnez delay slot and the
 * |= 2 rides the second branch's delay slot (both unconditional); the
 * probe showed the placement depends on s1's use distance - landing probe
 * with the full body. D_800ABA3C = 6 (timer slot); the division pair
 * (0x204CC0 under 0x46, else 0x409980) is a PLAIN long division - probe
 * PROVEN: cc1 EXPAND_DIV emits the exact retail guard structure
 * (div; bnez v1; nop; break 7; addiu at,-1; bne v1,at [delay: lui at,
 * 0x8000]; bne v0,at; nop; break 6; mflo). D_800ABA40++ only on the
 * under-0x46 arm. The v1==5/a0==0 arm reaches install with s1 NEVER
 * written (callee-saved passthrough from the caller) - reproduce with the
 * register-var discipline, note the UB-adjacent retail behavior.
 * install (B284): D_800ABA38 != 0 -> VSyncCallback(SsSeqCalledTbyT) +
 * return; else intr_stop_begin, func_8006B648(s1) [LANDED slot clear],
 * func_8006B500(s1, s0 & 0xFFFF, 0x1000), TWO more 0x7CF spins,
 * func_8006B5D8(s1), then the callback swap: slot == 0 saves the old
 * vblank handler (InterruptCallback(0,0) returns it) and registers the
 * CHAINING wrapper func_8006B484; slot != 0 registers SsSeqCalledTbyT
 * directly on the FIRST timer install (D_800ABA40 == 0) and the HALF-RATE
 * divider func_8006B4B8 afterwards. func_8004AE64 (intr lane) closes.
 */
void func_8006B0F0(long a0)
{
    long i, v1, s0;
    register long s1;

    i = 0x3E7;
    i = i - 1;
    while (i-- >= 0)
        ;
    v1 = D_800ABA50[0];
    if (v1 == 0)
        return;
    if (v1 == 2) {
        s1 = 0xF2000002;
        s0 = 0x44E8;
        D_800ABA3C[0] = 6;
        goto install;
    }
    if (v1 >= 3) {
        if (v1 == 3) {
            s1 = 0xF2000002;
            s0 = 0x89D0;
            D_800ABA3C[0] = 6;
            goto install;
        }
        if (v1 == 5) {
            if (a0 == 0) {
                D_800ABA38[0] = D_800ABA38[0] + 1;
                goto install;
            }
            s1 = 0xF2000003;
            D_800ABA3C[0] = 0;
            s0 = 1;
            goto install;
        }
        /* v1 == 4 or v1 >= 6 -> B1C0 */
    }
    /* B1C0: the timer arm (v1 == 1, 4, >= 6) */
    s1 = 0xF2000002;
    if (D_800ABA54[0] != 0)
        return;                          /* EXIT, s1 dead on this path */
    v1 = D_800ABA50[0];
    D_800ABA3C[0] = 6;
    if (v1 < 0x46) {
        s0 = 0x204CC0 / v1;              /* EXPAND_DIV guards, probe-proven */
        D_800ABA40[0] = D_800ABA40[0] + 1;
    } else {
        s0 = 0x409980 / v1;
    }
install:
    if (D_800ABA38[0] != 0) {
        VSyncCallback(SsSeqCalledTbyT);
        return;
    }
    intr_stop_begin();
    func_8006B648(s1);
    func_8006B500(s1, s0 & 0xFFFF, 0x1000);
    i = 0x7CF;
    i = i - 1;
    while (i-- >= 0)
        ;
    i = 0x7CF;
    i = i - 1;
    while (i-- >= 0)
        ;
    func_8006B5D8(s1);
    if (D_800ABA3C[0] == 0) {
        D_800ABA48[0] = InterruptCallback(0, 0);
        InterruptCallback(D_800ABA3C[0], func_8006B484);
    } else {
        if (D_800ABA40[0] == 0)
            InterruptCallback(D_800ABA3C[0], SsSeqCalledTbyT);
        else
            InterruptCallback(D_800ABA3C[0], func_8006B4B8);
    }
    func_8004AE64();
}

/* ---- func_8006B380 / func_8006B3A0: the two installer thunks ----
 * Same shape as the landed func_8006B680/func_8006B6A0: frame 0x18, the
 * constant 1 / 0 rides the jal DELAY SLOT. func_8006B3A0 carries no
 * glabel of its own (address-named in the C file).
 */
void func_8006B380(void)
{
    func_8006B0F0(1);
}

void func_8006B3A0(void)
{
    func_8006B0F0(0);
}

/* ---- func_8006B3C0: the uninstaller (frame 0x18: ra) ----
 * D_800ABA54 != 0 -> plain return (the bnez leaves with NOTHING undone).
 * Else D_800ABA40 = 0, intr_stop_begin, then: D_800ABA38 != 0 ->
 * VSyncCallback(0) + D_800ABA38 = 0; else slot-based restore: slot == -1
 * skips, slot == 0 restores the SAVED callback InterruptCallback(0, saved),
 * other slots unregister InterruptCallback(slot, 0); D_800ABA3C = -1;
 * func_8004AE64 closes. The SpuQuit thunk func_8006B464 follows in the
 * same piece (own frame 0x18).
 */
void func_8006B3C0(void)
{
    long v0, a0;

    if (D_800ABA54[0] != 0)
        return;
    D_800ABA40[0] = 0;
    intr_stop_begin();
    v0 = D_800ABA38[0];
    if (v0 != 0) {
        VSyncCallback(0);
        D_800ABA38[0] = 0;
    } else {
        a0 = D_800ABA3C[0];
        if (a0 != -1) {
            if (a0 == 0)
                InterruptCallback(0, (void (*)(void))D_800ABA48[0]);
            else
                InterruptCallback(a0, 0);
            D_800ABA3C[0] = -1;
        }
    }
    func_8004AE64();
}

void func_8006B464(void)
{
    SpuQuit();
}

/* ---- func_8006B484: the CHAINING vblank callback ----
 * Runs the saved original first (jalr), then ticks the sequencer.
 */
void func_8006B484(void)
{
    void (*old)(void) = (void (*)(void))D_800ABA48[0];

    if (old != 0)
        old();
    SsSeqCalledTbyT();
}

/* ---- func_8006B4B8: the HALF-RATE timer callback ----
 * Ticks on every other invocation via the D_800ABA4C toggle.
 */
void func_8006B4B8(void)
{
    if (D_800ABA4C[0] == 0) {
        D_800ABA4C[0] = 1;
        return;
    }
    D_800ABA4C[0] = 0;
    SsSeqCalledTbyT();
}

/* ---- THE SIX-STEP MATCHING PLAN (landing window, witnessed oracle) ----
 * 1. SPIN MATRIX: probe `while (i-- >= 0)` with a DEAD loop var for the
 *    single-register form (bgez + delay-slot addiu) vs the probe's live-var
 *    addu copy; the two 0x7CF spins and the 0x3E7 one share the shape.
 *    Probe the addiu-vs-addu decrement choice (probe emitted addu $5,$5,-1;
 *    retail has addiu $v0,$v0,-1 - likely the `i = i - 1` init typing).
 * 2. EXTERN FORMS per site (counter law): D_800ABA40's RMW must be a
 *    SCALAR extern (array CSEs into an la-form reg; retail emits two
 *    separate lui/%lo pairs around the mflo); the single-store sites take
 *    array-declared externs (fused lui/%lo). D_80171E08 carries the
 *    curated alias - the curation pass renames it AFTER the landing.
 * 3. TERNARY SHAPES: cases 0/5 select into a register then ONE store
 *    (branchy, not if-converted bit math - values 0x32/0x3C defeat the
 *    srl/xori fold); probe `?:` vs if/else-into-temp for each body; the
 *    case-4 `? 5 : a0` and case-1 `? 0x3C : 5` pair with them.
 * 4. THE B1C0 DELAY-SLOT PAIR: s1 = 0xF2000002 before the A54 check, with
 *    the lui in the first bnez delay and the |= 2 in the range-branch
 *    delay; the probe (early use) sank the lui instead - re-probe with the
 *    full body where s1's use is at install (B2B0, far later).
 * 5. THE v1==5/a0==0 s1 PASSTHROUGH: s1 unwritten on that path (caller's
 *    callee-saved value flows into func_8006B648); probe what gcc does
 *    with the uninitialized register-var and pin if needed.
 * 6. THUNK + CALLBACK FRAMES: the delay-slot-arg thunks (1/0) are the
 *    proven func_8006B680 shape; func_8006B484's jalr-then-tick order and
 *    the InterruptCallback return-typing (long vs fn-ptr) probe together.
 * After EXACT: flip the yaml row to c, delete the nonmatchings .s, raise
 * the ratchets from the tree in landing order, re-verify 8/8 GREEN.
 */

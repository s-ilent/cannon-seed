/* PARKED DRAFT - window cron-20261031-1525, offline decode of the
 * func_8006AC04 row (g3_eu, listed 0x120 = 0x8006AC04..0x8006AD24, REAL
 * extent 0x14C - see THE TAIL FINDING below). Oracle DOWN (EU/JP 404 at
 * ~51.7h, the 2026-10-30 11:42Z set), witness 0/8, judge live-only per
 * the INPUT GATES - byte-exact landing WAITS for a witnessed oracle.
 * Law Zero held: this decode ran on the committed rows + the re-provisioned
 * psyq 3.3 evidence (sozud/psy-q sparse: LIB + INCLUDE + DOC this time).
 *
 * THE TAIL FINDING (this window's discovery): spimdisasm MISCLASSIFIED the
 * last 0x2C bytes of the function as data - asm/g3_eu/nonmatchings/data/
 * data_8006AD24.data.s is the function's own tail, not data. Word decode:
 *   0x8006AD24  jal 0x8004A048            (GetVideoMode - curated, LIBETC
 *   0x8006AD28  nop                        VMODE member, sig-db agreed)
 *   0x8006AD2C  lui $at,0x800B
 *   0x8006AD30  sw $v0,-0x45BC($at)       = sw to D_800ABA44 (the GCC
 *                                          %hi/%lo split of 0x800ABA44:
 *                                          %lo 0xBA44 has bit15 set, so
 *                                          %hi = 0x800B, eff = 0x800B0000
 *                                          - 0x45BC = 0x800ABA44)
 *   0x8006AD34  lui $at,0x8017
 *   0x8006AD38  sw $zero,-0x52FC($at)     = sw to 0x8016AD04 = the CURATED
 *                                          SsSeqCalledTbyT_guard
 *   0x8006AD3C..4C  lw $ra,0x14(sp); lw $s0,0x10(sp); addiu $sp,sp,0x18;
 *                   jr $ra; nop  - the EPILOGUE, mirroring the row's own
 *                   prologue (addiu -0x18 / sw s0 0x10 / sw ra 0x14)
 * exactly. The row's listed end (no epilogue, execution "falling into a
 * data label") was the tell. The label D_8006AD24 is unreferenced anywhere
 * in the tree (grep: zero hits outside its own file), so re-classifying
 * the tail breaks nothing. Landing step 1 = fix the split (the yaml row
 * 0x120 -> 0x14C / the spimdisasm function-boundary override), re-extract,
 * and the row ends in a jr $ra like every other row.
 *
 * IDENTITY - the row is the psyq 3.3 LIBSND SSINIT member's SsInit /
 * SsInitHot SHARED BODY. This completes the SSINIT function-public map 8/8
 * on the tree:
 *   func_8006AF70 = SsSetTickMode   (banked cron-20261031-1406)
 *   func_8006B380 = SsStart         (banked)
 *   func_8006B3A0 = SsStart2        (banked, UNCALLED sibling)
 *   func_8006B3C0 = SsEnd           (banked)
 *   func_8006B464 = SsQuit          (banked)
 *   func_8006AD50 = SsInit          (wrapper, flag 0 - polarity below)
 *   func_8006AD70 = SsInitHot       (wrapper, flag 1)
 *   func_8006AD90 = SsSetTableSize  (UNCALLED - see THE TABLE-SIZE ROW)
 *
 * WRAPPER POLARITY (SsInit vs SsInitHot): the body's flag selects
 * func_8006B6A0 (0) / func_8006B680 (1) - both feed func_800653AC the
 * constant - which calls func_800642A0(arg) (LANDED, judged EXACT: the
 * arg-gated full init, `if (arg == 0)` carries the 24-voice sweep /
 * addr-0x200 writes / SpuInit-class reset). So flag 0 = FULL = SsInit,
 * flag 1 = light = SsInitHot (the spec: SsInitHot "init without
 * destroying the data already transferred to the sound buffer", hot-reset
 * variant). Caller edges agree: func_80029C18 boot path jal's func_8006AD50
 * (full) BEFORE its own SsSetTickMode(1); func_80029E1C jal's func_8006AD70
 * (hot) immediately before SsSetTickMode(1) -> SsStart -> SsSetMVol
 * (0x7F,0x7F) - the hot re-init + fresh tick install is the documented
 * order (FUNCTION.TXT: "SsSetTableSize は SsInit の直後に呼び..." and the
 * SsSetTickMode install table; the game never calls SsSetTableSize).
 *
 * THE TABLE-SIZE ROW (side finding, same window): func_8006AD90 IS
 * SsSetTableSize, documentary-exact. Signature (char *table, short s_max,
 * short t_max) per FUNCTION.TXT; the body: sh a1 -> SsSeqCalledTbyT_nslots,
 * sh a2 -> SsSeqCalledTbyT_ntracks, then builds SsSeqCalledTbyT_tab[i] =
 * table + i*t_max*172 for i in [0, s_max) - the x172 chain
 * (sll 1/addu/sll 2/subu/sll 2/subu/sll 2) is x172 = SS_SEQ_TABSIZ
 * (libsnd.h: #define SS_SEQ_TABSIZ 172), and the per-track init loop
 * strides 0xAC = 172. FUNCTION.TXT: "s_max ... 上限は 32", table size =
 * SS_SEQ_TABSIZ x s_max x t_max. Retail: s_max cap visible in the row's
 * own consumers (the tab pointer array holds exactly 32 entries = 0x80B,
 * see the zero region). UNCALLED in retail (no jal/j branch to 0x8006AD90
 * in any target's nonmatchings - same class as SsStart2), so its s_max/
 * t_max arguments never run; the game uses the .data defaults.
 * LANE-OWNER FLAG (not renamed here): psyq's SsSetTableSize writes
 * s_max/t_max - the game's slots are SsSeqCalledTbyT_nslots/ntracks, so
 * psyq's _snd_seq_s_max maps on nslots (already flagged cron-20261031-1406)
 * and psyq's _snd_seq_t_max maps on ntracks (0x80172728) - in TENSION with
 * the banked _snd_seq_t_max = 0x80171E08 (the ticks-per-second var the
 * SsSetTickMode switch writes 50/60/120/240 into). The SSCALL cross-ref
 * (TbyT references _snd_seq_t_max) reads BOTH ways (TbyT walks tracks AND
 * does the per-tick math). Kept as evidence for the lane owner; NO rename.
 *
 * THE DECODE (semantically complete; codegen-shape notes inline):
 */

/* externs for the landing (scalar vs array per site is a landing probe,
 * counter law from the func_8006AF70 draft step 2):
 * extern long D_800ABA38[], D_800ABA3C[], D_800ABA40[], D_800ABA44[],
 *             D_800ABA48[];
 * extern short D_80171E08[];     // = _snd_seq_t_max (curated cron-20261031-1406)
 * extern unsigned short D_800ABA08[], D_800ABA18[];  // the two default tables
 * extern long SsSeqCalledTbyT_tab[];   // curated 0x80171EA4 (32 x 4B pointer
 *                                      // array; the state records follow at
 *                                      // +0x80 = 0x80171F24)
 * extern long SsSeqCalledTbyT_slotbits;   // curated 0x8016B10C
 * extern long SsSeqCalledTbyT_guard;      // curated 0x8016AD04
 * extern long GetVideoMode(void);         // curated LIBETC VMODE member
 * extern void ResetCallback(void);        // LIBAPI
 * extern void func_8006B6A0(void), func_8006B680(void);  // LANDED wrappers
 * extern void func_80067690(long);        // SpuInitMalloc(0x20, D_80147D64)
 *                                         // + voice-state clears (alabel in
 *                                         // func_80066BC4.s)
 */

void func_8006AC04(long flag)
{
    unsigned short *dst;
    unsigned short *src;
    long *base;
    long *p;
    long i;
    long r;

    ResetCallback();
    if (flag == 0)
        func_8006B6A0();      /* -> func_800653AC(0) -> func_800642A0(0): FULL */
    else
        func_8006B680();      /* -> func_800653AC(1) -> func_800642A0(1): hot */

    /* SPU voice-register defaults: the SAME 8 halfwords to all 24 voices.
     * Retail keeps the source cursor re-derived from $a3 per outer row
     * (addu $v1,$a3,$zero at .L8006AC4C) and $a3 NEVER advances - one
     * 16-byte row (vol 0/0, pitch 0x1000, addr 0x3000, ADSR1 0x00BF,
     * ADSR2 0, loop 0/0) replicated, NOT a 0x180-byte table. Dest advances
     * 0x10 per row through 0x1F801C00..0x1F801D80 (the 24-voice register
     * block). D_800ABA08 = 0000 0000 1000 3000 00BF 0000 0000 0000. */
    dst = (unsigned short *)0x1F801C00;
    for (i = 0; i < 0x18; i++) {
        src = D_800ABA08;
        for (r = 0; r < 8; r++)
            *dst++ = *src++;
    }

    /* SPU control defaults: 16 halfwords from D_800ABA18 to
     * 0x1F801D80..0x1F801DA0 (mainvol 0x3FFF/0x3FFF first, then reverb
     * vol / key on/off / FM / noise / reverb mode / channel on-off all 0).
     * D_800ABA18 = 3FFF 3FFF 0000 ... 0000 (16 halfwords). */
    dst = (unsigned short *)0x1F801D80;
    src = D_800ABA18;
    for (i = 0; i < 0x10; i++)
        *dst++ = *src++;

    /* The SpuInitMalloc-carried SPU voice-state initializer (zeroes
     * D_8016B108/D_8016AC24 halves, 0xC0 halfwords at D_801476A4, 0x18B at
     * D_80147824, D_8017278C, 0x10B at D_801704A8, clamps the voice count
     * into D_8016B08C). 0x18 = 24, the voice count. */
    func_80067690(0x18);

    /* Zero the 32 x 0x40 state records at SsSeqCalledTbyT_tab + 0x80
     * (0x80171F24..0x80172724, ending exactly at SsSeqCalledTbyT_nslots).
     * tab itself is the 32-entry (s_max cap!) slot-pointer array SsSetTableSize
     * fills; the records follow. Inner loop: 16 words per record, DESCENDING
     * from +0x3C, signed do-while countdown (li 0xF; sw; addiu -1; bgez;
     * delay addiu -4) - the pre-decrement form per the banked AF70 step-1
     * law (`do {...} while (--i >= 0)` = 16 stores; the post-decrement form
     * over-stores 17 and emits the wrong register shape). */
    base = SsSeqCalledTbyT_tab + 0x20;
    for (r = 0; r < 0x20; r++) {
        i = 0xF;
        p = base + 0xF;
        do {
            *p = 0;
            p--;
        } while (--i >= 0);
        base += 0x10;
    }

    /* The static defaults. Retail materializes -1 (addiu $v0,$zero,-1)
     * BEFORE the slotbits store and holds it across two stores - pure
     * scheduling; source order below. */
    D_80171E08[0] = 0x3C;            /* = _snd_seq_t_max: the 60Hz default */
    SsSeqCalledTbyT_slotbits = 0;
    D_800ABA38[0] = 0;               /* VSync-mode flag (0 = timer mode) */
    D_800ABA3C[0] = -1;              /* interrupt slot: unregistered */
    D_800ABA40[0] = 0;               /* timer users count */
    D_800ABA48[0] = 0;               /* saved vblank callback */

    /* THE TAIL (data_8006AD24, misclassified): the video-mode cache write
     * and the TbyT guard clear. D_800ABA44 = GetVideoMode() SEALS the
     * PAL/NTSC-selector reading (the AF70 draft's "no in-tree writer"
     * note is superseded): the selector is written ONCE here, from the
     * LIBETC video mode (MODE_PAL = 1), and read by SsSetTickMode's
     * documented per-video-mode RCntCNT2/CNT3 install table. */
    D_800ABA44[0] = GetVideoMode();
    SsSeqCalledTbyT_guard = 0;
}

/* DATA MAP (g3_eu; curated where named, HELD where D_):
 *   D_800ABA08  voice-register default row (8 halfwords, replicated x24)
 *   D_800ABA18  SPU control default table (16 halfwords; mainvol 3FFF/3FFF)
 *   D_800ABA38  VSync-mode flag (AF70 draft map; 0 = timer mode)
 *   D_800ABA3C  interrupt slot (-1 = unregistered; AF70 draft map)
 *   D_800ABA40  timer users count (AF70 draft map)
 *   D_800ABA44  video-mode cache = GetVideoMode() at init (HELD name; the
 *               PAL/NTSC selector reading now has its writer AND source)
 *   D_800ABA48  saved vblank callback (AF70 draft map)
 *   D_80171E08  _snd_seq_t_max (curated; init default 0x3C)
 *   SsSeqCalledTbyT_tab      0x80171EA4 - 32-entry slot-pointer array
 *   SsSeqCalledTbyT_slotbits 0x8016B10C - zeroed at init
 *   SsSeqCalledTbyT_guard    0x8016AD04 - zeroed at init (TAIL write)
 *   SsSeqCalledTbyT_nslots   0x80172724 - s_max slot (SsSetTableSize target)
 *   SsSeqCalledTbyT_ntracks  0x80172728 - t_max slot (SsSetTableSize target)
 *
 * THE SIX-STEP MATCHING PLAN (landing window, witnessed oracle):
 * 1. THE SPLIT FIX: flip the yaml row 0x4B404 extent 0x120 -> 0x14C (or
 *    the spimdisasm function-boundary override per the house mechanism)
 *    so data_8006AD24 folds into the func_8006AC04 row; re-extract with
 *    the banked post-extract git checkout -- guard, confirm the row now
 *    ends jr $ra and D_8006AD24 disappears; suite + ratchet recompute
 *    from the tree (the 809/150 pair moves only if the .s rows change).
 * 2. HARDWARE-ADDR STORES: the 0x1F801C00/0x1F801D80 walks are plain
 *    addiu/lui-ori pointer arithmetic (no %hi/%lo of a static) - probe
 *    the (unsigned short *)0x1F801C00 cast form first; the AF70 lesson
 *    says array-declared externs for single-store sites, scalars for RMW
 *    (none here - all stores are straight).
 * 3. THE FIXED-SOURCE VOICE LOOP: retail re-derives the source cursor per
 *    outer row (addu $v1,$a3,$zero) - the naive `*dst++ = D_800ABA08[j]`
 *    with j-loop-index form may hoist; probe `src = D_800ABA08;` INSIDE
 *    the outer loop (this draft's shape) vs the pointer-walk
 *    `for (r = 0; r < 8; r++) *dst++ = *src++;` (also this draft's shape)
 *    - whichever keeps the per-row cursor reload.
 * 4. THE DESCENDING ZERO LOOP: pre-decrement do-while (`while (--i >= 0)`,
 *    16 stores) per the banked law; probe i/p register allocation until
 *    the sw/addiu-a0/bgez/addiu-v0 schedule matches (delay-slot p--).
 * 5. THE STATIC BLOCK ORDER: the -1 materialization rides v0 across the
 *    slotbits store (addiu -1 at 8006ACF8, stored at 8006AD10) - source
 *    order `slotbits = 0; ABA38 = 0; ABA3C = -1;` should reproduce it via
 *    scheduling; if not, probe declaring the -1 into a local first.
 * 6. THE TAIL: with the split fixed, D_800ABA44 = GetVideoMode() +
 *    SsSeqCalledTbyT_guard = 0 close the row; GetVideoMode's return
 *    type (long per the curated row) must yield the bare sw $v0 store.
 * After EXACT: flip the yaml row to c, delete the nonmatchings .s, adopt
 * the SSINIT curation names (func_8006AD50 = SsInit, func_8006AD70 =
 * SsInitHot, func_8006AD90 = SsSetTableSize + this row's public name per
 * the lane owner's call) IN THE SAME WINDOW per the libspu-block
 * composition rule, recompute ratchets from the tree, verify 8/8 GREEN.
 */

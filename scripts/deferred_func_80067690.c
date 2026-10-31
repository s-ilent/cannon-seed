/* PARKED DRAFT - window cron-20261101-0151, offline decode of the
 * func_80067690 flow (g3_eu, 0x80067690..0x80067AC8, extent 0x438 - the
 * LAST 0x438 bytes of the walk row func_80066BC4, which spimdisasm
 * fragments into ten symbols: alabel func_80067690, func_800676D8,
 * func_80067700, func_80067734, func_80067778, func_80067780,
 * func_800677A0 (0x1DC), func_8006797C, func_80067988, func_80067A44).
 * Oracle DOWN (EU 404 probed 17:57Z, the 2026-10-30 11:42Z set dead at
 * ~30.2h), witness 0/8, judge live-only per the INPUT GATES - byte-exact
 * landing WAITS for a witnessed oracle. Law Zero held: decode ran on the
 * committed rows + the re-provisioned psyq 3.3 evidence (LIB + INCLUDE +
 * DOC).
 *
 * CALLER (single, g3_eu census): the SSINIT shared body func_8006AC04 at
 * 0x8006ACB0 - jal func_80067690 with delay ori $a0,$zero,0x18 (a1 = 0 is
 * set AFTER return, the call passes a0 = 0x18 only). So the psyq SsInit /
 * SsInitHot body calls this with max_voices = 0x18 = 24 - FUNCTION.TXT:
 * SsInit "clears the sound local memory etc. and initializes the sound
 * system" - this function IS that svm-side init.
 *
 * IDENTITY: the psyq libsnd svm (sound voice manager) init, VMANAGER
 * family. FINGERPRINT (scripts/probe_80067690_member.py, banked): the
 * per-voice SPU-register default store run (ori 0x200 / sh 0x6(a0) / ori
 * 0x1000 / sh 0x4(a0) / ori 0x80FF / sh 0x8(a0) / ori 0x4000 / sh
 * $zero,0x0(a0) / sh $zero,0x2(a0) / sh 0xA($a0) - ten instructions, all
 * non-relocated immediates) appears VERBATIM in psyq 3.3 LIBSND.LIB inside
 * the VMANAGER module - twice (file offsets 0x126d0 + 0x1533c). The game
 * image carries it exactly once (0x80067928). Byte-compare
 * (scripts/compare_80067690_archive.py): the retail copy is NOT a byte-
 * verbatim 3.3 VMANAGER build - the prologue/loop runs match at shifted
 * anchors (verbatim runs: prologue 4 words; loop-A region 11; loop-B 7;
 * loop-C 11; the 0x80067790 gate 7), the layout diverges ~0x2C between
 * archive twin and retail (the 3.3 build has 0x2C more before the
 * zero-loop section). SAME class as the landed func_800642A0 precedent:
 * "psyq 3.3 carries the SAME idiom but is NOT byte-identical - the game
 * copy was compiled from source by the game's own cc1 2.6.3-PSX". The
 * archive twin's prologue (addiu sp,-0x18 / sw s0,0x10 / sw ra,0x14 /
 * addu s0,a0) matches shape-exactly at LIBSND.LIB 0x12464. Which
 * VMANAGER public the function is (SpuVmInit is the obvious candidate;
 * sdk_members.py claims it ambiguous at 0x80066E5C - a different interior
 * start in the same row): LANE-OWNER FLAG, no rename here - the archive
 * symbol-table walk stops early (the banked omf_pubsyms quirk), so a
 * name claim needs the publics-parser fix or an anchored-offset probe.
 *
 * THE DECODE (whole-flow, a0 = max_voices as u8):
 *
 *  1. PROLOGUE + LIBSPU HANDOFF: addiu sp,-0x18; sw s0,0x10(sp); s0 = a0;
 *     sw ra,0x14(sp). Then _spu_setInTransfer(0) (curated LIBSPU S_IT
 *     member 0x800656B4) - clear the in-transfer flag first.
 *
 *  2. SpuInitMalloc(0x20, &D_80147D64) - a1 = &D_80147D64 is loaded
 *     BEFORE the two static-zero stores and consumed in the call's delay
 *     slot chain (GCC arg hoisting); a1 re-zeroes after return as the
 *     loop-A counter. SPU_MALLOC_RECSIZ = 8 (LIBSPU.H), so 8 x (0x20+1) =
 *     264 bytes of malloc-management table at D_80147D64..0x80147E6C.
 *     D_8016B108 = 0 (sh), D_8016AC24 = 0 (sh) - D_8016B108 sits 4 bytes
 *     before the curated SsSeqCalledTbyT_slotbits (0x8016B10C): the svm
 *     bookkeeping pair, both svm-owned, zeroed here (the "statics touch
 *     the TbyT cluster" claim from cron-20261031-1525 verified: the
 *     ADJACENT slotbits is the TbyT member's).
 *
 *  3. THE THREE ZERO SWEEPS (u16 counter discipline - every counter
 *     andi'd 0xFFFF before use):
 *     a. for (u16 i = 0; i < 0xC0; i++) ((u16*)D_801476A4)[i] = 0;
 *        192 halfwords = 24 voices x 8 halfwords of svm voice state.
 *     b. for (u16 i = 0; i < 0x18; i++) D_80147824[i] = 0; - 24 voice
 *        flags (one byte per voice), then D_8017278C = 0 (sh).
 *     c. for (u16 i = 0; i < 0x10; i++) D_801704A8[i] = 0; - 16 key
 *        slots. The data block is CONTIGUOUS: D_801476A4 (0x180) +
 *        D_80147824 (0x18) + D_8014783C (the 24 x 0x34 svm records,
 *        ending exactly at 0x80147D1C where SsSeqCalledTbyT_init's
 *        counter D_80147D1C sits - the layout confirms one svm data
 *        cluster).
 *
 *  4. VOICE COUNT: D_8016B08C = (u8)(max_voices < 0x18 ? max_voices :
 *     0x18) - the cap branch (sltiu a0,0x18 / bnez / ori v0,0x18 in the
 *     fallthrough). Retail call passes 0x18 -> 0x18. THE LOOP BOUND: the
 *     per-voice loop re-reads D_8016B08C (lbu) at the loop bottom, and
 *     SsSeqCalledTbyT_init (0x80067FBC) lbu's it as ITS third
 *     instruction - the statics HAND OFF through it (window-1525's
 *     TbyT-cluster claim, direct evidence).
 *
 *  5. THE PER-VOICE LOOP (0x800677A0..0x80067A44, gate beqz on
 *     D_8016B08C; t1 = 0xFF, t0 = 1; u16 voice index v):
 *     a. svm record writes, rec = D_8014783C + v*0x34 (the x52 chain
 *        sll 1/addu/sll 2/addu/sll 2): rec+0x02 = 0x18 (sh), rec+0x0E =
 *        -1 (sh), rec+0x00 = 0xFF (sh, t1), rec+0x1B = 0 (sb), rec+0x04
 *        = 0, rec+0x06 = 0, rec+0x10 = 0, rec+0x12 = 0, rec+0x14 = 0xFF
 *        (sh, t1), rec+0x08 = 0, rec+0x0A = 0x40 (sb), rec+0x1C..0x30
 *        even halfwords = 0 (sh: 0x1C/1E/20/22/24(via D_80147860)/28/2A/
 *        2C/2E/30). Untouched: +0x0C, +0x16, +0x18, +0x1A, +0x26, +0x32.
 *     b. SPU HARDWARE VOICE REGS via *D_800AB874 (= 0x1F801C00, the SPU
 *        voice register base, read fresh per voice: a0 = v*8, sll 1 ->
 *        v*16, addu the loaded base): +0x00 = 0 (vol L), +0x02 = 0 (vol
 *        R), +0x04 = 0x1000 (pitch, center), +0x06 = 0x200 (start addr,
 *        the mute address - same 0x200 the landed func_800642A0 full-init
 *        sweep writes), +0x08 = 0x80FF (ADSR1), +0x0A = 0x4000 (ADSR2).
 *     c. D_801704A2 = v (sh) then lhu RELOAD - the store-reload round
 *        trip of the svm "current voice" static (readers: func_80067C24,
 *        func_80068380, func_80069B3C).
 *     d. the 24-voice mask split: (v < 0x10) ? (a3 = 1 << v, a2 = 0)
 *        : (a3 = 0, a2 = 1 << (v - 0x10)) - sllv/sllv off the reloaded
 *        index.
 *     e. LOOP TAIL re-zeroes rec+0x1B = 0 (sb), rec+0x04 = 0 (sh),
 *        rec+0x00 = 0 (sh) - SAME addresses the head wrote (0xFF->0,
 *        0->0, 0->0). GCC KEEPS both because the SPU-register store run
 *        between them dereferences the global pointer *D_800AB874: the
 *        potential alias makes the head stores observable (same law as
 *        the landed func_800642A0's pointer re-read pattern - write the
 *        C naturally through the pointer and cc1 2.6.3 keeps the pair).
 *     f. mask bookkeeping: D_8017281C |= a3; D_80172820 |= a2 (the svm
 *        voice-on masks, lhu/or/sh per half); D_80147DF0 &= ~a3;
 *        D_80147DF4 &= ~a2 (lhu/nor-and/sh) - then loop while (u16)v <
 *        lbu D_8016B08C (the loop bottom re-loads the count).
 *
 *  6. THE TAIL (0x80067A44, reached by loop completion OR the beqz
 *     voice-count gate): D_801652F8 = 0x3FFF, D_801652FA = 0x3FFF (the
 *     svm main-volume pair, matching the SSINIT control defaults
 *     mainvol 0x3FFF/0x3FFF banked cron-20261031-1525); v0 = 0x80; then
 *     the mask statics ZEROED (overwriting the loop's bookkeeping):
 *     D_80147DF0 = 0, D_80147DF4 = 0, D_8017281C = 0, D_80147DF8 = 0,
 *     D_80147DFC = 0 (sh each); D_801652F0 = 0, D_801652F4 = 0 (sw);
 *     D_8017057C = 0 (sb; SsSeqCalledTbyT_init's row is the other
 *     referent - the handoff); _svm_stereo_mono = 0 (sh, CURATED name -
 *     the VS_MONO backing flag per cron-20261031-1406); D_8016AD08 =
 *     0x80 (sh; the SsSeqCalledTbyT_guard 0x8016AD04 + 4). Then
 *     jal SsSeqCalledTbyT_init (0x80067FBC, the curated game-side init
 *     callee) and the epilogue (lw ra,0x14 / lw s0,0x10 / addiu sp,0x18 /
 *     jr ra) - the frame mirrors the SSINIT shared body's.
 *
 * NOTE the loop's mask writes (e/f) are OBSERVABLY DEAD in the init path
 * - the tail zeroes D_8017281C/DF0/DF4 anyway - but they are the real
 * bytes (the source presumably carried the per-voice off-bookkeeping);
 * the C draft reproduces them and the matching window keeps them.
 *
 * LANDING PLAN (six steps, witnessed window only):
 *  1. yaml split: carve [0x473C4, asm, func_80066BC4] (0xf04) at 0x47E90
 *     - head extent 0xACC stays asm, new row [0x47E90, c,
 *     func_80067690] 0x438; the scan's name-uniqueness registry +
 *     glabel_collision_pass.py handle the ~40 interior spimdisasm
 *     labels of the head (no hand renames; never casual splat split).
 *  2. src/func_80067690.c from this draft: externs _spu_setInTransfer,
 *     SpuInitMalloc, SsSeqCalledTbyT_init (all curated already); the
 *     svm statics keep their D_ names until the lane owner banks the
 *     svm cluster names; u16 counter discipline; the SPU regs through
 *     a volatile-qualified pointer load per voice (the func_800642A0
 *     law: the base pointer variable re-read at every reload site).
 *  3. make extract; git checkout -- the three known dirty .s files
 *     (asm/mainmenu_eu/nonmatchings/func_80034EBC.s,
 *     asm/g3_jp/nonmatchings/func_80050108.s,
 *     asm/g3org_jp/nonmatchings/func_800250FC.s); byte-scan before any
 *     'repair' (the terminal eats literal "[m").
 *  4. make verify TARGET=g3_eu until 8/8 GREEN (cmp -l per
 *     tools/verify.sh for any diff; expect iteration on the mask
 *     bookkeeping order and the a1-hoist shape of step 2).
 *  5. judge EXACT via the live oracle (decomp.wtf loop, native) - the
 *     witness gate makes this live-only; ratchets recomputed from the
 *     tree (809/150 at the time of this draft).
 *  6. commit+push (type: landing summary), worklog section, then the
 *     psyq-symbol curation pass may adopt the svm cluster names IF the
 *     archive side (VMANAGER publics offsets) is pinned first - see the
 *     omf_pubsyms quirk item.
 *
 * CROSS-TARGET NOTE: the same flow exists in every target's LIBSND
 * cluster (g3_jp's row func_80067640 0xf0 is a DIFFERENT function - the
 * loop-over-voices caller at 0x80067640, whose 0x80067690 interior
 * address coincidentally collides with this g3_eu name; the cross-target
 * census for THIS function's twins is a follow-up decode).
 */

/* externs (all curated or landed): */
extern void _spu_setInTransfer();
extern long SpuInitMalloc(long num, char *top);
extern void SsSeqCalledTbyT_init();

/* svm data cluster (D_ names until the lane owner banks the svm names): */
extern unsigned char D_8016B08C;          /* active voice count, cap 0x18 */
extern unsigned short D_8016B108;         /* svm bookkeeping, slotbits-4 */
extern unsigned short D_8016AC24;         /* svm bookkeeping */
extern unsigned short D_801476A4[0xC0];   /* 24 x 8 svm voice halfwords */
extern unsigned char D_80147824[0x18];    /* 24 voice flags */
extern unsigned short D_8017278C;
extern unsigned char D_801704A8[0x10];    /* 16 key slots */
extern unsigned short D_8016AD08;         /* guard+4, set 0x80 */
extern unsigned short D_80147DF0;         /* key-on mask low */
extern unsigned short D_80147DF4;         /* key-on mask high */
extern unsigned short D_80147DF8;
extern unsigned short D_80147DFC;
extern unsigned short D_8017281C;         /* voice-on mask low */
extern unsigned short D_80172820;         /* voice-on mask high */
extern unsigned short D_801652F0;
extern unsigned int D_801652F4;
extern unsigned short D_801652F8;         /* main vol L */
extern unsigned short D_801652FA;         /* main vol R */
extern unsigned char D_8017057C;
extern unsigned short _svm_stereo_mono;   /* CURATED */
extern unsigned short D_801704A2;         /* svm current voice */
extern unsigned short D_8014783C[0x270];  /* 24 x 0x34 svm records (view) */
extern char D_80147D64[];                 /* SpuInitMalloc table, 264 B */
extern unsigned short *volatile D_800AB874; /* SPU voice reg base = 0x1F801C00 */

/* MATCHING draft - NOT verbatim-exact; the six-step plan governs. */
void func_80067690(unsigned char max_voices)
{
    unsigned char *rec;
    unsigned short *spu;
    unsigned short mask_lo, mask_hi;
    unsigned int v;
    unsigned int i;

    _spu_setInTransfer(0);
    SpuInitMalloc(0x20, D_80147D64);
    D_8016B108 = 0;
    D_8016AC24 = 0;
    for (i = 0; i < 0xC0; i++) {
        D_801476A4[i] = 0;
    }
    for (i = 0; i < 0x18; i++) {
        D_80147824[i] = 0;
    }
    D_8017278C = 0;
    for (i = 0; i < 0x10; i++) {
        D_801704A8[i] = 0;
    }
    D_8016B08C = (max_voices < 0x18) ? max_voices : 0x18;
    if (D_8016B08C != 0) {
        for (v = 0; (unsigned short)v < (unsigned short)D_8016B08C; v++) {
            rec = (unsigned char *)(D_8014783C + v * 0x1A); /* v*0x34 bytes */
            *(unsigned short *)(rec + 0x02) = 0x18;
            *(unsigned short *)(rec + 0x0E) = -1;
            *(unsigned short *)(rec + 0x00) = 0xFF;
            rec[0x1B] = 0;
            *(unsigned short *)(rec + 0x04) = 0;
            *(unsigned short *)(rec + 0x06) = 0;
            *(unsigned short *)(rec + 0x10) = 0;
            *(unsigned short *)(rec + 0x12) = 0;
            *(unsigned short *)(rec + 0x14) = 0xFF;
            *(unsigned short *)(rec + 0x08) = 0;
            rec[0x0A] = 0x40;
            *(unsigned short *)(rec + 0x1C) = 0;
            *(unsigned short *)(rec + 0x1E) = 0;
            *(unsigned short *)(rec + 0x20) = 0;
            *(unsigned short *)(rec + 0x22) = 0;
            *(unsigned short *)(rec + 0x28) = 0;
            *(unsigned short *)(rec + 0x2A) = 0;
            *(unsigned short *)(rec + 0x2C) = 0;
            *(unsigned short *)(rec + 0x2E) = 0;
            *(unsigned short *)(rec + 0x30) = 0;
            *(unsigned short *)(rec + 0x24) = 0; /* retail writes +0x24 LAST */
            spu = *D_800AB874 + v * 8; /* v*16 bytes through the base */
            spu[3] = 0x200;
            spu[2] = 0x1000;
            spu[4] = 0x80FF;
            spu[0] = 0;
            spu[1] = 0;
            spu[5] = 0x4000;
            D_801704A2 = (unsigned short)v;
            if ((unsigned short)D_801704A2 < 0x10) {
                mask_lo = 1 << v;
                mask_hi = 0;
            } else {
                mask_lo = 0;
                mask_hi = 1 << (v - 0x10);
            }
            rec[0x1B] = 0;
            *(unsigned short *)(rec + 0x04) = 0;
            *(unsigned short *)(rec + 0x00) = 0;
            D_8017281C |= mask_lo;
            D_80172820 |= mask_hi;
            D_80147DF0 &= ~mask_lo;
            D_80147DF4 &= ~mask_hi;
        }
    }
    D_801652F8 = 0x3FFF;
    D_801652FA = 0x3FFF;
    D_80147DF0 = 0;
    D_80147DF4 = 0;
    D_8017281C = 0;
    D_80147DF8 = 0;
    D_80147DFC = 0;
    D_801652F0 = 0;
    D_801652F4 = 0;
    D_8017057C = 0;
    _svm_stereo_mono = 0;
    D_8016AD08 = 0x80;
    SsSeqCalledTbyT_init();
}

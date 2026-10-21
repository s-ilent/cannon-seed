/* GsTMDdivG4LFG offline probe (window cron-202610211858).
 *
 * The sibling of the queued GsTMDdivTG4LFG 0x304 row: the non-textured
 * divide-G4 member, 0x2C0, FOUR standalone asm sdk rows (mainmenu_jp
 * file 0x4B838 true 0x8006B038, mainmenu_eu 0x4B244, g3_jp 0x37324,
 * g3org_eu 0x341BC) plus TWO data-row-hosted copies (g3_eu inside
 * data_8005E494 at +0x244 of the 0x504 row at file 0x36B24, g3org_jp
 * inside data_8005B8FC at +0x244 of the 0x284 row at file 0x3457C) -
 * the wave is 6 targets, 169 of 176 words byte-identical (the 7
 * differing slots are exactly the relocations: 5 jal + 1 hi/lo pair).
 *
 * KEY QUESTION this probe answers: does OUR cc1 slide the a2 param
 * home out of the entry block the way it does for the T sibling
 * (the 200-of-193 entry-cascade wall)? Retail batches BOTH homes at
 * entry here too (addu s7,a1 / addu fp,a2 in the first four slots).
 * The G DAG differs: pk is a stack parm loaded into s6 via lw at
 * entry, nt homes to fp (not s6), the loop counter is a spilled
 * local (0x60(sp)) not a register, and the beqz delay slot carries
 * the useful p78 spill - a different fill candidate pool.
 *
 * Body map (mainmenu_jp render, true VA 0x8006B038):
 *   s6 = pk (lw 0xC4(sp), the 8th arg), s7 = vt, fp = nt
 *   s5..s2 = v1o..v4o = pk+0x18/0x30/0x48/0x60, s0 = tmd+3,
 *   s1 = tmd+4 (the color pointer, recomputed per iteration),
 *   spills: 0x50 tmd, 0x58 ret, 0x60 counter, 0x68 p78, 0x70 &u44;
 *   locals: 0x40 buf40 (dv's otz out, read as ushort), 0x44 u44
 *   (RotTransPers arg-4 scratch, never read), 0x48 p4C (RTP arg-3
 *   out, the dpq color index).
 *   dv = RotAverageNclipColorDpq3_1 (landed; called by name), args
 *   8-10 are v*o+0x10 here (the T sibling passes v*o+4), arg 14 is
 *   &buf40 (T: &buf40[1]) - different actuals, same 15-arg shape.
 *   sz = func_800667B8 (the 0x18 SZ-fifo reader, ReadSZfifo4 slot),
 *   pk member = func_8006F250, ft table = the D_ hi/lo pair.
 *   The T sibling's UV stores (pk+0xC/0xE) and the four v*o+8 record
 *   stores are ABSENT here - the non-textured primitive carries no
 *   texture words; the color comes from the record itself (tmd+4).
 *   The loop advances the record base by 0x18 (the 0x18-stride
 *   primitive) and s0 rides tmd+3; the counter is the spilled local.
 *
 * SPELLING LAW (this window): our cc1's loop pass runs combine_givs
 * (stock gcc 2.6.3 loop.c), which folds EVERY const-offset DEST_ADDR
 * giv of a biv into the LAST-RECORDED one (the list is prepend-ordered,
 * so the host = the LAST field read in insn order) and the reduction
 * then creates the re-based loop register = biv + host_add. Retail's
 * compiler never re-bases (both dividers' renders read the raw biv
 * form). The dodge is to spell the field reads DIRECTLY off the record
 * base (tmd+0xA..tmd+0x16, no s0 = tmd+3 intermediate) so the FLAG BYTE
 * read (tmd+3, the last statement) becomes the host giv: the reduced
 * register = tmd+3 - exactly retail's s0 - every read lands at retail's
 * exact positive offset (5..0x13), and the biv (tmd itself, now used
 * only for the per-iteration color tmd+4) loses its register and spills
 * to 0x50(sp) as the raw a0 - retail's exact entry spill. The T
 * sibling's committed probe carries the SAME re-base delta (its reads
 * ride tmd+0xC vs retail's tmd+0x10); its K=3 spelling must be fixed
 * the same way before landing.
 */

/*
 * STATUS (window cron-202610211858, five probe iterations): the
 * combine_givs dodge WORKS - the probe's field reads now ride retail's
 * exact base (lhu v0,7(s0) with the s0 = tmd+3 register; slot 32 word
 * 96020007 = retail's word exactly) and the param homes are retail's
 * (addu s7,a1 / addu fp,a2 at slots 4/6). Word count is EQUAL (176 =
 * 176) for the first time. Remaining deltas, all in the allocation
 * order, ~57 words:
 *   1. the color temp (131, 6 refs / LL 33) interleaves into the v*o
 *      block: probe [giv=s0, v4o=s1, v3o=s2, color=s3, v2o=s4, v1o=s5,
 *      pk=s6, vt=s7, nt=fp] vs retail [giv=s0, color=s1, v4o=s2, v3o=s3,
 *      v2o=s4, v1o=s5, pk=s6, vt=s7, nt=fp] - the color must allocate
 *      BEFORE v4o (its pri 15.5/33 = 0.469 vs v4o's 43/96 = 0.448 says
 *      it should - the observed qsort order disagrees; lever = shorten
 *      the color's life or find the exact LL/n_refs the sort saw).
 *   2. the frame: probe 0xA0 vs retail 0xA8 - retail's local area has a
 *      4-byte hole at 0x4C (between p4C and the tmd spill) and its save
 *      area starts at 0x80 (ours 0x78); the pk lw offset (0xBC vs 0xC4)
 *      follows the frame. Candidate: retail's dv or otz is a spilled
 *      local where ours rides regs.
 *   3. the counter/p78 spill-slot order fixed by declaring the counter
 *      before p78 (slot 16 now matches: sw zero,0x60).
 * The v2o/v1o/pk/vt/nt assignments and every loop-body read word MATCH.
 * Next window: steer the color's allocation position (decl-order and
 * life-length levers), fix the frame hole, then the wave is 6 targets
 * (4 standalone flips + 2 data-row splits on the data_80066CF4 pattern)
 * with aliases _dv/_sz/_pk/_ft curated per target.
 * ALSO: the committed GsTMDdivTG4LFG probe carries the SAME re-base
 * delta (its reads ride the host = the last-recorded read, tmd+0xC vs
 * retail's tmd+0x10) - the "loop body matches modulo the entry cascade"
 * claim in its header is STALE; its fix is the same K=0 dodge (read the
 * fields via tmd directly; the T's last-recorded read is *(long *)s0 =
 * tmd+0x10 = exactly retail's base, so the T's re-base becomes
 * INVISIBLE with that spelling) - re-derive its wave after the G wave
 * lands.
 */

/*
 * STATUS (window cron-202610212014): the committed header had LOST its
 * COMMENT OPENER on this block (the final edit landed after the last
 * verified compile) so cpp exited 33 on the prose apostrophes and the
 * probe could not compile at all - repaired first (acd1a4ea).  Then the
 * allocation war was re-opened with the exact gcc source in hand:
 *
 * 1. THE PRI LAW CORRECTED: global.c allocno_compare sorts by
 *    ((floor_log2(n_refs) * n_refs) / live_length) * 10000 * size
 *    descending, tie -> ascending allocno number - floor_log2, NOT
 *    log2.  The STATUS above ("pri 0.469 vs 0.448 says it should") used
 *    exact log2 and INVERTED the verdict: with floors the color is
 *    2*6/LL vs v4o's 3*12/LL_class - the color LOSES unless its numbers
 *    change.  The sort was right; the measurement was wrong.
 * 2. THE INSTRUMENT: cc1 -da's .flow dump prints the authoritative
 *    inputs verbatim ("Register 131 used 6 times across 39 insns") -
 *    scripts/allocno_pri.py turns it into the pri table; the .greg
 *    dump's "regs to allocate" line is the POST-local-alloc ground
 *    truth (local-alloc.c copy propagation MUTATES reg_n_refs at its
 *    lines 780/912/1109, so flow-order != greg-order; observed delta:
 *    pk 78 falls 2nd -> 7th, the v*o quartet flips 83,82,81,80 -> 80,
 *    81 then 82,83).  Current greg order: 167 80 81 131 82 83 78 72 73
 *    84 79 71 138 77 75 85 76 = the v5 register map exactly.
 * 3. THE PSEUDO MAP (flow dump, this compile): 167 = the reduced giv
 *    (s0), 80/81/82/83 = v4o/v3o/v2o/v1o, 131 = the color, 78 = pk,
 *    72 = vt, 73 = nt, 71 = tmd (spilled 0x50), 85 = ret (0x58), 84 =
 *    the counter (0x60), 138 = &u44 (0x70), &p78 = the fifth spill
 *    (0x68); cnt/shift/otp are equiv-REPLACED (no slot - re-read from
 *    the incoming area every iteration: lw 0xB8/0xBC/0xC0).
 * 4. THE FRAME DECOMPOSED: the "4-byte hole at 0x4C" is AUTOMATIC -
 *    the declared locals end at 0x48+4 and the reload spill zone is
 *    8-aligned, so 0x4C is skipped by construction.  The REAL delta is
 *    ONE MORE 8-spaced spill slot at 0x78 (retail vars= 0x40 vs our
 *    0x38): a sixth spilled pseudo whose every reference then died
 *    (slot carved, never touched - the render reads/writes nothing at
 *    0x78).  Three carve-then-die spellings REFUTED on our cc1: an
 *    if (0) address-take, a self-compare-guarded address-take, and an
 *    unreachable address-take after return - all three fold at tree
 *    level and never carve.  The sixth spill's identity is open.
 * NEXT LEVERS, in order: (a) the color's n_refs 6 -> 7 or 8 with a
 *    zero-insn spelling (7 gives 14/39 = 0.359, 8 gives 24/39 = 0.615 -
 *    both over v4o's 0.340; every loop-depth occurrence counts, so any
 *    extra appearance in a pattern or call arg list works); (b) the
 *    sixth retail spill: hunt a pseudo that ours equiv-replaced but
 *    retail spilled-then-died, or a decl-order lever that re-times the
 *    spill-zone carving; (c) model local-alloc's ref mutations so the
 *    POST-mutation pri is predictable and the greg order stops being
 *    trial-and-error.  Only after the color lands does the wave open
 *    (6 targets: 4 flips + 2 splits, aliases _dv/_sz/_pk/_ft curated
 *    per target), then the T sibling's K=0 re-derivation.
 */

/*
 * STATUS (window cron-20261021-1443): lever (a) is TESTED AND REFUTED,
 * and the retail shape question it depended on is CLOSED.
 *
 * 1. RETAIL s1 SHAPE CONFIRMED from the render word-for-word: s1 is a
 *    PER-ITERATION CSE TEMP, not a self-incrementing giv.  addiu s1,t1,4
 *    at file 0x4B99C (t1 = the reloaded raw tmd biv), the dv arg-7 stack
 *    store sw s1,0x18(sp) at 0x4B9DC, the NormalColorDpq arg-2 copy
 *    addu a1,s1,zero at 0x4BA24, and the loop bottom increments ONLY s0
 *    (addiu s0,s0,0x18 at 0x4BA98) - s1 carries NO loop-bottom increment,
 *    it is recomputed from the reloaded biv every iteration.  That is
 *    structurally IDENTICAL to our pseudo 131: one def (131 = biv+4),
 *    the dv arg-7 store, the a1 copy, no self-increment, 6 refs / LL 33
 *    post-loop (6/39 pre-loop).  The allocation war is purely about what
 *    the mutated pri sort does with these identical inputs.
 *
 * 2. THE REF-RAISING LEVER REFUTED with the empty-asm experiment: an
 *    extra loop-depth value use of the color pointer (asm volatile with
 *    an r operand spelled tmd+4, placed before the NormalColorDpq call)
 *    does NOT add one occurrence to pseudo 131 - it CONVERTS the temp:
 *    loop.c turns the value use into a proper value GIV, the CSE temp
 *    merges into it, and the pseudo renumbers with 11 refs / LL 91 /
 *    crosses 5 calls (a whole-function giv - a shape retail does NOT
 *    have) and the render breaks (172 words vs 176; the barrier also
 *    disturbs the loop scheduling).  Every conceivable clean spelling
 *    collapses at tree level (constant folding) or takes the giv shape,
 *    so there is NO zero-insn +1-ref spelling on our cc1: lever (a) is
 *    dead in both its zero-insn and added-value-use forms.  Even in giv
 *    form (11 refs) the pseudo still allocated after 80/81 in the greg
 *    line - the post-mutation quartet rise beats it.
 *
 * 3. CONSEQUENCE: the color flip must come from the MUTATION side (the
 *    2014 window's lever (c)) - our post-local-alloc order 80 81 131 82
 *    83 means copy propagation RAISES 80/81 above the color; what it
 *    chews is determined by the copy insns present, which differ between
 *    our compile and retail's exactly where the entry-cascade wall sits
 *    (the deferred a2 home, the deferred pk load timing, the counter
 *    spill init).  The color allocation, the sixth spill and the entry
 *    cascade are ONE coupled question: any entry-block spelling change
 *    re-times local-alloc's propagation walk and can move all three.
 *    Next window: read local-alloc.c 780/912/1109 against the .lreg
 *    dump's copy list for THIS function, enumerate which copies fire,
 *    and derive the entry spelling that leaves the color's mutated pri
 *    on top - the same stroke should explain the sixth spill.
 */

/*
 * STATUS (window cron-20261021-1713): lever (c) CLOSED AS AN INSTRUMENT
 * - the greg order is now fully PREDICTABLE, and the prediction retires
 * the copy-prop theory.  Oracle-blocked window (witness 0/8, discs
 * eaten, CHD links expired); everything below is offline on the tree.
 *
 * 1. THE MECHANISM CHAIN, source-verified (gcc-2.6.3 re-mirrored to
 *    /tmp/gcc-2.6.3 from gcc.gnu.org/pub/gcc/old-releases/gcc-2/):
 *    the flow->greg order shift is NOT local-alloc copy propagation.
 *    The chain is: (i) .flow = pre-combine life_analysis numbers;
 *    (ii) schedule_insns runs BETWEEN combine and local_alloc
 *    (toplev.c 3053/3082/3098-3101) and REWRITES reg_live_length from
 *    the scheduled stream (sched.c 4899-4905; every rewrite prints as
 *    ";; register N life shortened/extended from X to Y" in the .sched
 *    dump - 131: 39->33, 80: 106->96, 78: 108->104); (iii) regclass()
 *    never recounts reg_n_refs (no reg_scan call in it), so n_refs at
 *    the sort is the STALE pre-combine reg_scan count; (iv) inside
 *    local_alloc, update_equiv_regs gives every MEM-loaded parm a
 *    REG_EQUIV note and DOUBLES its reg_live_length (local-alloc.c
 *    1063) - 75/76/77/78 on this function (lreg = 2x the sched-final
 *    value verbatim), the SAME four on the T sibling; (v) the
 *    copy-prop optimizers (780/782, 912/913) netted ZERO n_refs delta
 *    on all rows of BOTH dividers - the 2014/1443 "copy propagation
 *    RAISES 80/81" reading is retired; (vi) the equiv-kill (line
 *    1109) zeroes 74/122/139/150 (cnt/shift/otp + one more), the four
 *    rows missing from the .lreg table.
 * 2. THE INSTRUMENT: tools/allocno_model.py sorts the .lreg table
 *    with global.c allocno_compare verbatim (pri = floor_log2(n) *
 *    n / LL * 10000 * size, descending, tie -> ascending allocno) and
 *    reproduces the observed greg line EXACTLY: G 17/17, T sibling
 *    16/16, first shot, both first tries.  The trial-and-error era of
 *    the allocation war is over: compile with CC1FLAGS_EXTRA='-da',
 *    run the model, READ the order before touching a register map.
 * 3. THE NUMERIC GATE (why the color cannot take s1 here): post-sched
 *    pri - color 2*6/33 = 0.3636, v4o 3*12/96 = 0.375, v3o 36/98 =
 *    0.3673, v2o 36/100 = 0.36.  The color sits between v3o and v2o;
 *    retail's color-over-v4o needs color LL <= 31 (12/31 = 0.387;
 *    12/32 = 0.375 TIES and the tie sends 80 first - allocno 80 < 131),
 *    or BOTH v4o/v3o LL >= 100, or n_refs >= 8 (lever (a), refuted).
 *    All three spans are sched-slaved: the color's 33 = def (the
 *    per-iteration biv+4 recompute, which must precede dv's arg-7
 *    stack store) to death (the NCDpq arg-2 copy) - the loop body
 *    between them is byte-exact already, so no local spelling can
 *    shave it; the v*o spans likewise.  THE COUPLING IS NOW PROVEN
 *    WITH THE TRANSFER MECHANISM: entry shape -> combine -> sched
 *    placement -> LL writeback -> equiv x2 -> sort.  The color flip,
 *    the sixth spill and the entry cascade are one question, and the
 *    instrument to CHECK any future entry-cascade candidate is banked.
 */

typedef struct { char b[8]; } GsTMDdivG4LFG_v8;

extern long RotTransPers(long *a0, long *a1, long *a2, long *a3);
extern void NormalColorDpq(long *a0, long *a1, long c, long *a3);
extern long GsTMDdivG4LFG_dv(long *, long *, long *, char *, char *,
                             char *, long *, long *, long *, long *,
                             long *, long *, long *, long *, long *);
extern void GsTMDdivG4LFG_sz(long *, long *, long *, long *);
extern long GsTMDdivG4LFG_pk(long, char *, long, long *);
extern unsigned char GsTMDdivG4LFG_ft[];

long GsTMDdivG4LFG(tmd, vt, nt, pkin, cnt, shift, otp, pk)
    unsigned char *tmd;
    char *vt;
    char *nt;
    long *pkin;
    unsigned long cnt;
    unsigned long shift;
    long *otp;
    char *pk;
{
    long ret = (long)pkin;
    long *v4o = (long *)(pk + 0x60);
    long *v3o = (long *)(pk + 0x48);
    long *v2o = (long *)(pk + 0x30);
    long *v1o = (long *)(pk + 0x18);
    unsigned long fp = 0;
    long *p78 = (long *)(pk + 0x78);
    long buf40;
    long u44;
    long p4C;
    unsigned long otz;
    unsigned long dv;

    *(long **)(pk + 0xF0) = v1o;
    *(long **)(pk + 0xF4) = v2o;
    *(long **)(pk + 0xF8) = v3o;
    *(long **)(pk + 0xFC) = v4o;

    if (cnt != 0) {
        do {
            *(GsTMDdivG4LFG_v8 *)v1o =
                *(GsTMDdivG4LFG_v8 *)(vt + *(unsigned short *)(tmd + 0xA) * 8);
            *(GsTMDdivG4LFG_v8 *)v2o =
                *(GsTMDdivG4LFG_v8 *)(vt + *(unsigned short *)(tmd + 0xE) * 8);
            *(GsTMDdivG4LFG_v8 *)v3o =
                *(GsTMDdivG4LFG_v8 *)(vt + *(unsigned short *)(tmd + 0x12) * 8);
            *(GsTMDdivG4LFG_v8 *)v4o =
                *(GsTMDdivG4LFG_v8 *)(vt + *(unsigned short *)(tmd + 0x16) * 8);

            if (GsTMDdivG4LFG_dv(v1o, v2o, v3o,
                                 nt + *(unsigned short *)(tmd + 8) * 8,
                                 nt + *(unsigned short *)(tmd + 0xC) * 8,
                                 nt + *(unsigned short *)(tmd + 0x10) * 8,
                                 (long *)((char *)tmd + 4),
                                 (long *)((char *)v1o + 0x10),
                                 (long *)((char *)v2o + 0x10),
                                 (long *)((char *)v3o + 0x10),
                                 (long *)((char *)v1o + 0xC),
                                 (long *)((char *)v2o + 0xC),
                                 (long *)((char *)v3o + 0xC),
                                 &buf40, &u44) > 0) {
                RotTransPers(v4o, (long *)((char *)v4o + 0x10), &p4C, &u44);
                GsTMDdivG4LFG_sz((long *)((char *)v1o + 0x14),
                                 (long *)((char *)v2o + 0x14),
                                 (long *)((char *)v3o + 0x14),
                                 (long *)((char *)v4o + 0x14));
                NormalColorDpq((long *)(nt + *(unsigned short *)(tmd + 0x14) * 8),
                               (long *)((char *)tmd + 4), p4C,
                               (long *)((char *)v4o + 0xC));
                otz = *(unsigned short *)&buf40;
                dv = (otz - otp[2]) >> shift;
                *(long *)(pk + 0x14) = (long)((dv << 2) + otp[1]);
                *(unsigned char *)(pk + 0x13) =
                    (unsigned char)((GsTMDdivG4LFG_ft[0] << 1) | tmd[3]);
                ret = GsTMDdivG4LFG_pk(ret, pk, 0, p78);
            }
            fp++;
            tmd += 0x18;
        } while (fp < cnt);
    }
    return ret;
}

/* GsTMDdivG4LFG World A spelling variant (window cron-20261022-0158).
 *
 * REFUTED AS SPELLED - do not land.  This variant folds the self-kill
 * pair into the live dv computation ("tcol = (char *)tmd + 4;" plus
 * "dv = ((otz - otp[2]) + (tcol - tcol)) >> shift;") so the subtract
 * carries a live consumer (the store-consumer lesson from the 0043
 * smoke).  Through the guarded cc1 the pair DOES survive cse2 (+2
 * insns across every .flow line), but the surviving insn is
 *   (insn 257 (set (reg:SI 154) (minus:SI (reg/v:SI 90) (reg:SI 155))))
 * - cse's reg substitution retargeted the two tcol reads to two
 * DIFFERENT pseudos (the canonical color giv 90 and tcol's own 155),
 * so no pseudo's used-count moved (every tally line identical to the
 * control) and combine cannot fold a non-self-kill (the render would
 * change).  The plain in-loop pair shape from the 2328 design is dead
 * at the G-probe level; the 0043 smoke only worked because its operand
 * is a single static extern with a unique cse equivalence.
 * NEXT (GUARD 4): suppress cse's substitution INTO the same-operand
 * MINUS insn (the 2328 design's own path-(b) guard, narrowed to the
 * pair, not the function) - then the pair survives as copy+minus, the
 * color tally gains the copy's read, and combine cancels the pair via
 * LOG_LINKS exactly as designed.  The stock tarball + guarded build
 * recipe are tools/build_cc1_263.sh + tools/patch_cc1_263.sh; the
 * smoke harness is tools/cc1_smoke_run.sh with probes/gcc263/cc1_smoke*.c.
 */

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
 *
 * STATUS (window cron-20261021-1828): the LL framing RETIRED by direct
 * measurement of the retail stream itself.  tools/g_span.py (banked this
 * window) measures first-write -> last-use distances on BOTH post-scheduled
 * streams, and retail's spans EQUAL ours for every resident: color 34=34,
 * v4o 104=104, v3o/v2o/v1o 101=101, vt 67=67, nt 123=123, giv/pk +-1 (the
 * frame slot).  The 1713 numeric gate's arm 1 (retail color LL <= 31) is
 * FALSE IN RETAIL - retail's own loop carries the same 33-insn color span -
 * and arm 2 (retail v4o/v3o LL >= 100) likewise.  Mechanism corrections
 * from the gcc source: reg_scan counts NOTHING (first/last UIDs + sets
 * only); reg_n_refs is life_analysis's LOOP-DEPTH-WEIGHTED tally
 * (+= loop_depth per set AND per use - entry refs at depth 0 count ZERO;
 * color 6 = 3 in-loop refs x 2, v4o 12 = 6 x 2) and combine.c:55 admits
 * it is NOT adjusted when combine folds refs - every odd-delta world
 * (color 7, quartet 11) is unreachable by weighting, the n==2->3 bump
 * needs n==2, copy-prop moves are +-loop_depth = +-2.  THE SURVIVING
 * REFRAME: the retail register MAP never proved the retail pri ORDER.
 * global.c find_reg pass 0 excludes regs_someone_prefers (the union of
 * conflicting lower-priority allocnos' hard_reg_full_preferences, merged
 * along reg-reg copy chains by expand_preferences) - if the color carries
 * a hard-reg preference for s1 that the quartet lacks, OUR OWN pri order
 * (v4o v3o color v2o v1o) settles retail's exact map (v4o pass-0-skips
 * s1 -> s2, v3o -> s3, color -> the untouched s1).  Next: what insn shape
 * creates a hard-reg preference for a data pseudo (global_conflicts'
 * recording site + expand_preferences' copy-chain propagation), and is
 * the color's s1 preference a spelling property of the NCDpq arg-2 copy?
 */

/*
 * STATUS (window cron-20261021-1943): the preference hunt RAN - and the
 * source verdict retires the 1828 reframe while opening the world its
 * odd-delta refutation could not see.  Everything below is source-read
 * (gcc-2.6.3 re-mirrored, tarball is gcc-2.6.3.tar.bz2 at gcc.gnu.org
 * /pub/gcc/old-releases/gcc-2/, NOT .tar.gz) plus one fresh -da compile
 * of this probe (greg line reproduced 17/17: 167 80 81 131 82 83 78 72
 * 73 84 79 71 138 77 75 85 76).
 *
 * 1. THE 1828 PASS-0 MECHANISM IS REFUTED.  find_reg (global.c ~916):
 *    pass 0 runs with used = used1 | ~regs_used_so_far |
 *    regs_someone_prefers - the ~regs_used_so_far term means pass 0 can
 *    ONLY take a hard reg some EARLIER allocno already took ("we never
 *    allocate a register for the first time in pass 0", the comment at
 *    the pass loop).  At v4o's turn in our order the used-so-far set is
 *    {s0} and v4o CONFLICTS with 167, so pass 0 fails and pass 1 lands
 *    the first free reg - s1 - regardless of regs_someone_prefers (pass
 *    1 re-copies used = used1 and DROPS the someone-prefers exclusion).
 *    "v4o pass-0-skips s1 -> s2" is therefore unreachable; someone_prefers
 *    only ever steers the choice among ALREADY-USED regs.
 * 2. THE REAL STEERING PATH IS THE POST-PASS OVERRIDE, and it is EMPTY
 *    here.  After best_reg, find_reg replaces it with a copy-preferred
 *    reg (hard_reg_copy_preferences) and then any preferred reg
 *    (hard_reg_preferences) of the same class when not in used.  The
 *    preference producers, source-verified: set_preference (global.c
 *    ~1534) fires per SET insns scanned by mark_reg (global.c ~1320,
 *    called from global_conflicts) when ONE side is already a hard reg
 *    (reg_renumber >= 0, i.e. local-alloc-assigned or a true hard reg)
 *    and the other a global pseudo - plain copies also set the
 *    copy_preferences bit; a PLUS source (e.g. addiu pseudo,hard,4)
 *    counts as non-copy (copy=0, src unwrapped one level).  The
 *    NCDpq arg-2 copy CANNOT be one of them: addu a1,s1,zero is a
 *    RELOAD-created insn, and reload runs AFTER global alloc - at
 *    global-alloc time the color's consumers are a stack store (src is
 *    a MEM - set_preference returns) and a call-arg use (no copy at
 *    all).  expand_preferences (global.c ~780) only IORs across
 *    pseudo-pseudo single_set copies whose src dies and does not
 *    conflict with the dest - there is no such copy on the color's
 *    chain.  EMPIRICAL CONFIRMATION: dump_conflicts prints a
 *    ";; N preferences:" line for EVERY allocno with non-empty
 *    hard_reg_preferences (it `continue`s otherwise) and our .greg
 *    dump has NONE - all 17 preference sets are EMPTY; .lreg shows
 *    local-alloc assigned NOTHING to $16-$23/$30, so no s-reg hard-reg
 *    copy can even exist; config/mips/mips.h defines NO REG_ALLOC_ORDER
 *    so pass 1 scans regs in NUMERIC order - the observed map is the
 *    pure sequential numeric fill (16,17,...,23,30) with zero
 *    steering, and the same will hold for any spelling of THIS shape.
 * 3. THE WORLD THE ODD-DELTA REFUTATION MISSED.  allocno_compare
 *    (global.c ~630) is (int)((double)(floor_log2(n_refs)*n_refs) /
 *    live_length * 10000 * size), ties -> ascending allocno - a DOUBLE
 *    division truncated to int (pri ladder 3750/3673/3636/3600 for
 *    80/81/131/82).  The stale count is the PRE-COMBINE life_analysis
 *    tally (flow.c set-path ~1977 / use-path ~2406, += loop_depth per
 *    set and per use), never recounted after combine folds refs
 *    (combine.c:55 admits it) - so a ref combine folds ADDS to the
 *    count the sort sees while leaving the scheduled stream, the spans
 *    and the LL writeback UNCHANGED.  The 1828 refutation covered only
 *    the odd deltas (color 7, quartet 11).  The EVEN siblings:
 *    (A) color n_refs 6 -> 8 crosses the floor_log2 boundary (2 -> 3):
 *        pri 3*8/33 = 7272 > v4o's 3750 - the color sorts FIRST among
 *        the s-candidates and pure sequential fill produces retail's
 *        exact map (color=s1, v4o=s2, v3o=s3, v2o=s4, v1o=s5) with NO
 *        preference steering; (D) quartet 12 -> 10 each (one folded
 *        in-loop ref per v*o): 3*10/96 = 3125, 30/98 = 3061, 30/100 =
 *        3000 - all drop below the color's 3636, same retail map.  Both
 *        are reachable by weighting (+-loop_depth = +-2) and both are
 *        INVISIBLE in the retail stream - the stale pre-combine count
 *        is the one pri input the span measurement cannot witness.
 * 4. THE COPY-CHAIN LEMMA (why the naive spelling cannot buy the +2):
 *    rerouting ONE consumer through an intermediate temp moves a use,
 *    it does not add one - def + consumer-use + copy-read = def + 2
 *    uses = the same 3 in-loop refs (count flat at 6), and the dead
 *    second copy folds at tree level before any ref exists.  The +1
 *    in-loop ref must come from a ref combine folds WITHOUT cse
 *    rerouting a use off the temp - i.e. a shape where the temp is
 *    read by an insn combine later eliminates.  Candidate shapes for
 *    the next probe round: an address-temp for one of the v*o addiu
 *    fans (world D, one folded read per v*o) and any folded read of
 *    the color pointer (world A).  THIS FILE's committed shape keeps
 *    count 6 = real 6 (.flow 6/39 = .lreg 6/33, combine folded zero
 *    color refs - verified by grep across the cse2/combine dumps).
 * 5. SESSION STATE: oracle-blocked window (witness 0/8 - the sandbox
 *    re-provision restored the WOVEN baseline set, all 8 failed the
 *    config/sha1 gate and were quarantined outside the repo; discs
 *    eaten, links expired, last window already asked for fresh ones).
 *    verify state unchanged (8/8 on 616d653a); ratchets 374/0.
 *
 * ADDENDUM (same window, the lemma MEASURED): the copy-chain lemma was
 *    put to the test - a variant reroutes the NCDpq arg-2 through a
 *    loop-top intermediate (cp2 = tmd+4 first statement, NCDpq takes
 *    cp2).  RESULT, all four dials: the temp's .flow count stays 6
 *    (89 in the variant vs 131 committed - the cp2 declaration only
 *    shifts pseudo numbering, 138 -> 139), the .lreg sort inputs are
 *    IDENTICAL (used 6 times across 33 insns both sides), the greg
 *    line is positionally identical (167 80 81 <color> 82 83 78 72 73
 *    84 79 71 <&u44> 77 75 85 76) and the .mas.s render differs ONLY
 *    in the .file line.  The rerouting copy never reaches the tally:
 *    it is eliminated BEFORE life_analysis counts (an earlier read of
 *    the same run mistook the renumbered temp 89 for a surviving copy
 *    - the byte-identical render proves no extra insn exists).  CONSEQUENCE: consumer rerouting is
 *    FULLY TRANSPARENT to global alloc - the stale count is immovable
 *    from the consumer side, and with it every pure-C path to the
 *    even-delta worlds (A)/(D).  The +2, if retail's compile carried
 *    one, must originate in the pre-loop entry-cascade structure (the
 *    coupled question the 1443 window named) - that hunt is the
 *    surviving path to the color flip.  Variant retained at
 *    probe-work/gdiv/lemma/ (repo-external).
 */

/*
 * STATUS (window cron-20261021-2058): the entry cascade is MEASURED
 * STRUCTURALLY IDENTICAL and the hunt's map is redrawn - three closes
 * and one correction, all offline (witness 0/8 woven set, discs
 * missing, links expired; verify state unchanged 8/8 on 616d653a;
 * ratchets 374/0).
 *
 * 1. THE STRUCTURAL DIFF (tools/g_struct_diff.py, banked): position-
 *    by-position alignment of the retail row (func_80076388.s
 *    glabel GsTMDdivG4LFG block, 176 insns) against the committed
 *    probe's .mas.s render (175 + the lui/lbu macro pair), with
 *    role normalization (the two allocation maps), frame
 *    normalization (sp-offsets >= 0x78 shift by the 0xA8-0xA0
 *    delta), and gas-macro forms (beqz == beq r,$0, j $31 == jr
 *    $ra, srl d,t,reg == srlv, addu/subu imm == addiu signed).
 *    RESULT: 164/176 SAME; EVERY delta is a known class - 2 FRAME
 *    (prologue sp decrement and its epilogue mirror, 0xA8 vs 0xA0),
 *    1 PAIR (retail lui %hi + lbu %lo(D_80194CD4) vs the probe's
 *    single lbu-symbol macro form), and the 7-insn loop-bottom block
 *    where the two reload temporaries are NAME-SWAPPED (retail
 *    tmd=t1/counter=t0 vs probe tmd=t0/counter=t1 - a pure
 *    isomorphic permutation downstream of the s-reg shift, zero
 *    structural content).  THE ENTRY CASCADES ARE IDENTICAL: every
 *    insn, same order, same offsets modulo frame, same shapes.  The
 *    probe's entry spelling ALREADY produces retail's entry
 *    structure - the lemma addendum's surviving path ("the +2 must
 *    originate in the pre-loop entry-cascade structure") is REFUTED
 *    AT THE RENDER LEVEL: there is no structural delta left to hunt.
 *
 * 2. THE PRI-INPUT PIN-DOWN: with identical post-sched streams and
 *    an identical pipeline, every sort input is pinned except the
 *    stale pre-combine n_refs (combine folds refs without
 *    recounting, combine.c:55).  The update_equiv_regs x2 set is
 *    determined by the post-sched stream itself (update_equiv runs
 *    inside local_alloc on that stream) - identical input means
 *    identical decisions, so it cannot differ; the sweep below
 *    confirms no single-row divergence could explain retail's map
 *    even if it could happen.
 *
 * 3. THE X2 SWEEP (repo-external one-off, scripts/x2_variants.py):
 *    for every row, add the x2 (13 eligible) and drop it (the
 *    committed four): NO single-row equiv-set change reproduces
 *    retail's order (+x2 on 85/138/167 and every -x2 reproduce the
 *    observed order unchanged; every other variant scrambles it
 *    differently).  The equiv-divergence path is CLOSED at the
 *    single-dial level.
 *
 * 4. WORLD D REFUTED (corrects the 1943 record): quartet 12->10 on
 *    all four drops 81/82/83 BELOW pk 78's x2'd 4*16/208 = 3077 (81:
 *    30/98 = 3061 < 3077), so the model order becomes 167 131 80 78
 *    81 82 83 ... - pk INTERPOSES and retail's exact map does NOT
 *    follow.  The 1943 "same map" claim overlooked pk.  World D is
 *    dead in both its single-row and all-four forms (single-row
 *    variants leave the untouched quartet members above the color).
 *
 * 5. WORLD A STANDS ALONE (model-confirmed on the real dumps): color
 *    stale n_refs 6->8 sorts the color FIRST and reproduces retail's
 *    exact 17-row order verbatim (167 131 80 81 82 83 78 72 73 84 79
 *    71 138 77 75 85 76).  The color war reduces to ONE open
 *    question: does a C spelling exist whose pre-combine stream
 *    reads the color ONE extra time in-loop, where COMBINE (not cse)
 *    folds that insn away - cse killing the rerouting-copy class
 *    pre-flow is the measured lemma (c513c18f); preference steering
 *    is refuted (f54082f3); the entry cascade is measured empty of
 *    structure deltas (this window, point 1); the x2 set is closed
 *    (this window, point 3).  The remaining test enumerates
 *    combine's fold repertoire against the color's two consumers
 *    (the arg-7 stack store, the call-arg use) for any two-insn
 *    shape that survives cse2 into the .flow tally and dies in
 *    combine with the .mas.s render byte-identical.  Acceptance gate
 *    unchanged: world A's order above + render byte-identical.
 */

/*
 * STATUS (window cron-20261021-2213): THE COMBINE-FOLD ENUMERATION IS
 * EMPTY - the color war PARKS AS A COMPILER-VERSION DELTA per the
 * 2058 acceptance gate's own fallback.  Oracle-blocked window (the
 * thirty-third rollback's class: worklog reverted with all 62 windows
 * missing - RESTORE NOTE appended; baselines on disk are the WOVEN
 * set, witness 0/8; discs eaten, the 2026-10-20 links expired).  The
 * enumeration ran on the baseline-independent probe line, BOTH
 * source-read and measured.  The gcc-2.6.3 source is re-mirrored at
 * probe-work/gcc-2.6.3 (tarball gcc-2.6.3.tar.bz2, sha256
 * 71f673849f4dc7f20aba6ba1ecb6221c6704ef3152779aef15602e974ae3c140,
 * from gcc.gnu.org/pub/gcc/old-releases/gcc-2/ - the .tar.gz URL 404s;
 * the tree extracts FLAT, gcc/ combine.c is combine.c at the top).
 *
 * 1. SOURCE VERDICT (combine.c/cse.c/flow.c read end to end for the
 *    deletion paths): combine pairs insns EXCLUSIVELY through
 *    LOG_LINKS (combine_instructions walks links and links-of-links;
 *    flow.c 1995-2003 builds a link only from an insn that USES a reg
 *    back to its setter), so a redefinition that does not read the
 *    previous value (the "t := cp; t := Y" dead-def pair, whose sweep
 *    count stays nonzero via the later use of t's SECOND value -
 *    delete_dead_from_cse counts remaining uses function-wide, cse.c
 *    8535's backward scan) is NEVER PAIRED and renders.  Every
 *    paired merge SUBSTITUTES i2src into i3 (subst) and retires i2
 *    (PUT_CODE NOTE, combine.c 2138-2146) with the reads TRANSFERRED
 *    into the merged pattern - count-neutral (the c513c18f
 *    transparency lemma, now source-explained).  A read can vanish
 *    only two ways: (a) the substituted form hits an arithmetic
 *    self-kill (minus/xor of the same rtx, mult by 0, and x with 0,
 *    compare-with-itself) - every C shape for those folds at tree
 *    level (fold-const) or at cse (fold_rtx folds x-x once both
 *    operands land in one quantity class), pre-flow; or (b) the
 *    value-propagation substitution expands a known reg_last_set
 *    value (cp -> (plus tmd_reload 4)), which RETARGETS the read to
 *    another pseudo and leaves a render-visible residue.  There is
 *    no third path: no store folding (SET_DEST mem is always live in
 *    the sweep), no memory forwarding in combine, no cross-block
 *    merges, MIPS has no CC0, and the i3_subst_into_i2 special case
 *    requires a PARALLEL i2 the stream does not have.
 * 2. MEASURED (three variants, each compiled EXIT 0 through cc.sh
 *    with -da; sources retained repo-external at
 *    probe-work/combine-enum/{vA,vB,vF}.c; base state re-reproduced
 *    first: greg 17/17 via allocno_model, g_struct_diff 164/176 SAME
 *    with the known-class tail): (vA) the dead-copy pair "tA = tmd+4;
 *    tA = (u8*)v4o" with no later use - color row 6 refs / 39 insns
 *    UNCHANGED (renumbered 131->132 by the extra decl, order shape
 *    identical: 168 80 81 132 82 83 78 72 73 84 79 71 139 77 75 85
 *    76) and the render byte-identical modulo the .file line - the
 *    sweep kills the dead defs pre-flow exactly as read; (vB) naming
 *    ONE consumer's eval (cpB at the NCDpq arg-2, dv keeps the
 *    inline expr) - the family RESTRUCTURES (color 91: 6 refs / 50
 *    insns, LL 39->50, pri 2*6/50 = 0.24 WORSE), no gain, the
 *    eval-family law again; (vF) the split-constant def "cpF = tmd+2;
 *    cpF += 2" with both consumers on cpF - cse's fold_rtx folds the
 *    constant association pre-flow (color 91: 6 / 50 again), the def
 *    line itself changes in the render (addu $19,$9,4 gone), no
 *    gain.  NO shape produced the +1 in-loop ref; the 1443 result
 *    already covered the value-use class (any loop-depth value use
 *    becomes a giv, 11 refs / LL 91, render breaks).
 * 3. CONSEQUENCE (the honest 2058 fallback): stock gcc 2.6.3 cannot
 *    express retail's pre-combine stream from ANY C spelling - the
 *    8-ref stream retail's sort saw is unreachable from C on our
 *    cc1, so the color war parks as a COMPILER-VERSION DELTA
 *    (retail's cc1 is not behaviorally identical to stock 2.6.3 in
 *    its combine/cse surface, or retail's source differs from our
 *    reconstruction in a way that survives the family law - both
 *    unprovable from the binaries alone).  The G wave and the T
 *    sibling's K=0 re-derivation stay gated on the color taking s1;
 *    the sixth spill stays parked with it.  The two live reopeners:
 *    (a) fresh disc links - the oracle lane (witness 8/8 STRICT,
 *    pair_report/density, the parked renames); (b) a MODIFIED-cc1
 *    experiment (a combine/cse-patched build proving the map is
 *    REACHABLE) - a different evidence class that can never show
 *    retail's compiler did it that way, so it stays a tool, not a
 *    landing path.
 */

/*
 * STATUS (window cron-20261021-2328): the MODIFIED-cc1 experiment's
 * first milestone banked.  Oracle-blocked window (the thirty-fourth
 * rollback's class: worklog reverted with all 62 windows missing -
 * RESTORE NOTE appended; baselines on disk the WOVEN set, witness
 * 0/8; discs eaten, the 2026-10-20 links expired).  Three things
 * landed, all on the baseline-independent probe line.
 *
 * 1. BASE STATE RE-REPRODUCED on the rolled-back sandbox: the
 *    committed probe compiles EXIT 0 through cc.sh with -da
 *    (build/probe/gdiv.*); allocno_model 17/17 MATCH first shot
 *    (equiv-DOUBLED rows [75,76,77,78] re-derived identically);
 *    g_struct_diff 164/176 SAME + 1 PAIR with the known-class tail
 *    (the 2 FRAME sp pair, the 7-insn name-swapped loop bottom).
 *    The color's before-values pinned from the fresh dumps: .flow
 *    Register 131 used 6 times across 39 insns; .lreg used 6 across
 *    33 - World A's target is 6 -> 8 (one extra in-loop read at
 *    depth 2).
 * 2. THE SOURCE TARBALL IS BANKED: gcc-2.6.3.tar.bz2 at
 *    /home/z/my-project/tools-local/ (survives re-provisions per
 *    get_gcc.sh), sha256
 *    71f673849f4dc7f20aba6ba1ecb6221c6704ef3152779aef15602e974ae3c140
 *    - the exact hash the 2213 record pinned, re-downloaded from
 *    gcc.gnu.org/pub/gcc/old-releases/gcc-2/gcc-2.6.3.tar.bz2 (the
 *    extra gcc-2.6.3/ path component 404s).  The stock tree extracts
 *    FLAT.  The tools-local/gcc-2.6.3-psx dir is BINARIES ONLY (no
 *    source, no Makefile) - get_gcc.sh fetches prebuilt cc1 from
 *    decompals/old-gcc, so the modified-cc1 build needs: the stock
 *    source (now banked) + the PSX patch set (decompals' source
 *    repo - locate next window) + a host-build recipe (gcc 2.6.3
 *    under a modern host compiler needs -std=gnu89 -fcommon class
 *    compat flags; the PSX patches are REQUIRED for the asm dialect
 *    maspsx consumes, stock mips.c output is not drop-in).
 * 3. THE PATCH-SEAM DESIGN (read off the 2213 source verdict, now
 *    concretized): the fold that must move from pre-flow to combine
 *    happens at THREE levels for the same-var self-kill shape - (i)
 *    fold-const folds X-X at TREE level for any same-operand
 *    integral expression, so no syntactic C spelling reaches RTL
 *    with the self-kill intact on stock OR cse-patched cc1; (ii)
 *    cse's fold_rtx folds it again post-substitution; (iii) combine
 *    simplify folds it in the merged i3 - the one level we WANT.
 *    So the patch must suppress the fold at (i) AND (ii) - and (ii)
 *    is two guards, not one: fold_rtx's minus-self recognition AND
 *    cse's value-propagation substitution into that insn (path (b)
 *    of the 2213 verdict: substitution retargets the reads to the
 *    color and leaves the insn rendering (minus cp cp) - a render
 *    change even with the fold suppressed).  The working shape is
 *    then the plain in-loop pair "t = cp; x = t - t" with t/x dead
 *    after: tree fold suppressed -> the pair reaches RTL; cse fold
 *    + substitution suppressed -> it survives cse2, .flow counts
 *    the copy's cp read (6 -> 8, the tally feeds regclass stale);
 *    combine pairs via LOG_LINKS (the subtract reads t, links to
 *    the copy), merges to (minus cp cp), folds to 0, t/x dead, the
 *    pair vanishes - render byte-identical to the committed render,
 *    exactly the stock pipeline's output.  REJECTED shapes: the
 *    conditional-set "u = c ? cp : cp2; x = u - u" (tree cannot
 *    fold it, but the render carries the branch - mips1 has no
 *    conditional move, combine folds the subtract and NOT the
 *    conditional), and the memory-aliased self-subtract (the reads
 *    are of the color's MEMORY, the wrong count class).  Open
 *    risks for the build window: suppressing fold-const X-X
 *    function-wide touches every other fold in the unit (the
 *    render-diff gate catches collateral); cse's substitution
 *    guard must be narrowed to the copy-set/read pair, not the
 *    whole function, or unrelated forwarding breaks the render.
 *    Success gate: patched cc1 + variant source compiles to .flow
 *    color 8, allocno model sorts World A's retail order
 *    (167 131 80 81 82 83 78 72 73 84 79 71 138 77 75 85 76), and
 *    g_struct_diff vs the committed render stays 164/176+PAIR with
 *    the known-class tail.
 */

/*
 * STATUS (window cron-20261022-0043): MILESTONE 2 - THE MODIFIED CC1
 * EXISTS AND IS RENDER-EQUIVALENT.  Oracle-blocked again (the
 * thirty-fifth rollback's class: clone 210 commits behind, worklog
 * reverted with all 63 windows missing - RESTORE NOTE appended;
 * witness 0/8 woven set; discs still missing, no fresh links yet -
 * the request stands from 2328, not repeated).
 *
 * 1. THE BUILD RECIPE IS LOCATED AND PROVEN: decompals/old-gcc
 *    (cloned repo-external to tools-local/old-gcc-src) carries
 *    gcc-2.6.3-psx.Dockerfile + patches/ - the EXACT patch set:
 *    varargs.h->stdarg.h sed, obstack-2.7.2.h.patch, sdbout-2.6.3.c.patch,
 *    g++-2.6.3.c.patch, then psx-2.5.7.patch (the ASPSX backend,
 *    creates config/mips/psx.h + xm-psx.h); configure --target=
 *    mips-sony-psx --with-endian-little --with-gnu-as; make CFLAGS=
 *    "-std=gnu89 -m32 -static -Dbsd4_4 -Dmips -march=i686
 *    -DHAVE_STRERROR".  Adaptations for this sandbox: no multilib
 *    (no Scrt1.o/crti.o) -> the -m32 pair dropped, -fcommon added
 *    (64-bit host); gcc.c hardcodes sys_errlist/sys_nerr (removed
 *    from modern glibc, no strerror path in 1994 code) -> patched
 *    to strerror(errno) with #include <string.h> + sys_nerr defined
 *    away (the ONLY source change beyond the Dockerfile recipe).
 *    BUILD: exit 0, ~5 min, cc1+cpp+xgcc static.
 * 2. THE EQUIVALENCE GATE PASSES FIRST SHOT: the self-built
 *    64-bit-host cc1 renders the committed G probe BYTE-IDENTICAL
 *    to the decompals 32-bit binary (diff of the .gcc.s, modulo the
 *    flags-echo comment line: ZERO lines).  Host word size does not
 *    change the mips target output on this unit.  qemu bypass for
 *    the 64-bit binary: QEMU=/usr/bin/env in cc.sh's env overrides.
 * 3. THE GUARDS ARE IN AND PROVEN INERT: two one-line suppressions -
 *    fold-const.c ~3750 (the "&x - &x" tree fold, X-X ->
 *    integer_zero_node) and cse.c ~3630 (fold_rtx's rtx_equal_p
 *    MINUS self-kill -> CONST0_RTX), each `if (0 && ...)` with a
 *    MODIFIED-CC1 comment.  Rebuild clean.  REGRESSION: the
 *    UNMODIFIED G probe through the patched cc1 renders
 *    byte-identical to the decompals render (the probe has no X-X
 *    shape; the guards are inert on it) - the collateral-risk
 *    question from 2328 is answered for this unit.
 * 4. THE MECHANISM SMOKE (probe-work/cc1-smoke/, two shapes, stock
 *    vs patched on identical .i): smoke1 "t=a; x=t-t; y=y+t; return
 *    y" and smoke2 "t=a; *gp=t-t; y=y+t" - FINAL RENDERS IDENTICAL
 *    both shapes (good), but the .flow counts are IDENTICAL TOO
 *    (the +1 read never materialized).  Dump inspection: the patched
 *    cse2 stream has NO copy and NO subtract - two unguarded
 *    mechanisms ate the chain: (a) cse's plain VALUE FORWARDING
 *    rewrote y=y+t into y=y+a (count-neutral move, kills the copy),
 *    and (b) the dead subtract then died in delete_dead_from_cse's
 *    cascade (the 2213 vA law), taking the copy's read with it; the
 *    store-consumer variant (stores are never sweep-dead) still lost
 *    the subtract to (c) THE ASSOCIATE PATH: fold_rtx's PLUS/MINUS
 *    op-list decomposition (the negs[] machinery, cse.c ~4130+)
 *    cancels a-a independently of the ~3630 direct site - the guard
 *    closed ONE of TWO doors.  MILESTONE 3 (next window): guard the
 *    associate-path cancellation (or short-circuit fold_rtx for
 *    same-operand MINUS at entry), then re-run the smoke - the
 *    success signature is .flow a-count +1 on the patched side with
 *    IDENTICAL final renders; then integrate the spelling into the
 *    G probe's loop and measure the World A gate.
 * 5. Banked repo-externally: tools-local/gcc-2.6.3-src/gcc-2.6.3
 *    (patched tree + build), tools-local/old-gcc-src (the recipe),
 *    probe-work/cc1-smoke (the smoke units + dumps).  The stock
 *    tarball re-downloaded to tools-local at the 2213-pinned sha256
 *    (the 2328 copy was eaten by the rollback).
 */

/*
 * STATUS (window cron-20261022-0428): MILESTONE 4 - GUARD 4 IS IN AND ALL
 * GATES PASS.  The 38th rollback opened the window (clone at 7623cd2, worklog
 * reverted, the 03:33 links' CHDs eaten and re-downloaded + sha256-gated, the
 * tools-local cc1 tree eaten and rebuilt via the banked one-command setup,
 * guards 1-3 re-applied idempotently).  THE 0158 READING IS REFUTED BY THE
 * FRESH PASS DUMPS: the pre-cse RTL ALREADY splits the shape across two
 * insns - insn 257 (minus (reg/v 90) (reg 155)) is (otz - otp[2]), and the
 * ACTUAL self-kill is insn 259 (minus (reg/v 89) (reg/v 89)) = (tcol - tcol),
 * which SURVIVES the first cse pass (as (minus 132 132), guards 1-3 holding
 * every fold door).  The real eater is LOOP.C: "giv at 259 reduced to
 * (reg:SI 171)" - loop.c strength-reduces the minus's own dest into a new
 * giv register, reg_map rewrites the CONSUMER (insn 261: 156 -> 171), the
 * original minus is orphaned, and the second cse's dead-deletion cascade
 * eats it.  GUARD 4 (loop.c, pair-narrowed): a replaceable giv whose insn
 * is a same-operand integral MINUS keeps its dest->new_reg map UNSET - the
 * consumer stays on the original giv reg, the minus stays live into cse2,
 * the reduced reg goes unread so its init/increment insns die downstream,
 * and biv elimination (all_reduced) is untouched.  THE MEASUREMENT (the
 * wa variant through the GUARD-4 cc1 vs the decompals stock, both -da):
 * (1) SURVIVAL - .cse2 insn 259 = (minus:SI (reg:SI 132) (reg:SI 132)) as a
 *     live {subsi3_internal}; (2) TALLY - the color giv reg 132 used 6 -> 10
 *     across 39 -> 46 insns and now crosses 4 calls (+3 - the subtract's
 *     reads extend the life; the exact +4-ref accounting vs the designed
 *     +1-copy-read class is the one open footnote); (3) COMBINE CANCELS -
 *     the final renders carry the SAME 162 instruction words (the diff is
 *     register RENUMBERING ONLY: 18/17 -> 19/18 in the v*o block, the
 *     reduced giv 168 -> 170, block-3 shifts - NO surviving copy/sub pair),
 *     the World A allocation-shift mechanism armed.  REGRESSIONS: the
 *     UNMODIFIED G probe through the GUARD-4 cc1 renders byte-identical to
 *     the decompals binary (0 diff lines); the two smoke units via
 *     tools/cc1_smoke_run.sh - smoke1 (register-consumer) render PASS with
 *     no .flow delta exactly as the 0043 record predicted, smoke2
 *     (store-consumer) render PASS with the m3 tally class preserved.  The
 *     smoke harness's tally gate had a filename bug ($stem.c.flow vs cc.sh's
 *     $stem.i.flow) - fixed in the same commit.  NEXT (the World A gate):
 *     the 1713 allocno-order instrument on this guarded render - the
 *     .greg/.lreg order vs World A's retail order (167 131 80 81 82 83 78
 *     72 73 84 79 71 138 77 75 85 76), then g_struct_diff vs the committed
 *     render (the 164/176+PAIR known-class tail).
 */
 *
 * STATUS (window cron-20261022-0543): MILESTONE 5 - THE WORLD A GATE CLOSES,
 * ALL ARMS PASS.  Session start: the 39th rollback (worklog fully reverted to
 * its 2026-10-14 state, RESTORE NOTE cron-20261022-0543-restore re-indexed all
 * 82 windows, digest exit 0; the 03:33 CHDs eaten with the prompt links 404 -
 * witness 0/8, the oracle DOWN, fresh links requested; the tools-local cc1
 * tree eaten and rebuilt via the banked one-command setup, guards 1-4
 * re-applied idempotently).  Regression first: the unmodified G probe through
 * the freshly rebuilt guarded cc1 renders byte-identical to the decompals
 * stock render (the 0428 gate re-proved on the new tree).  All milestone-4
 * gates reproduce exactly on the fresh tree: .flow color 132 = 6 -> 10 uses /
 * 39 -> 46 insns / crosses 3 -> 4 calls, the minus live in .cse2, renders
 * 179 = 179.  THE MODEL: allocno_model predicted == observed 17/17 on ALL
 * THREE compiles (G-probe stock, wa stock, wa guarded) - the 1713 instrument
 * holds on every table.  THE ORDER: the guarded wa greg line = 170 132 80 81
 * 82 83 78 72 73 84 79 71 139 77 75 85 76 == the World A target 167 131 80 81
 * 82 83 78 72 73 84 79 71 138 77 75 85 76 VERBATIM under the wa spelling's
 * pseudo renumbering (dv-temp 167->170, color 131->132, the 92-insn reg
 * 138->139); the tail 15/15 raw-identical.  THE MAP: the guarded render's
 * s-map = RETAIL'S EXACT NINE-REGISTER MAP (16 GIV / 17 COLOR / 18 V4O /
 * 19 V3O / 20 V2O / 21 V1O / 22 PK / 23 VT / 30 NT); stock vs guarded is
 * 179 = 179 insns with EXACTLY 23 differing lines, every one an instance of
 * the single body 3-cycle (v4o $17->$18, v3o $18->$19, color $19->$17), the
 * prologue/epilogue byte-identical - the color TAKES s1 exactly as retail
 * does ($17 = tmd+4, feeding the dv arg store and NormalColorDpq's a1).
 * THE ROLE CORRECTION (fixes this file's own 2058-era reading): in the
 * G-probe numbering 167 is the DV-TEMP (the reduced-giv role: 23 refs across
 * 91, no pointer tag), NOT the color; 131 is the color (6 refs across 33,
 * pointer - the row the wa spelling carries at 132).  World A therefore reads
 * dv-temp first, color second, and the guarded compile delivers exactly that
 * pair order (the dv-temp's stale 23 refs outrank the color's 10 at
 * global-alloc time; the reduced giv's insns then die in combine, freeing s1
 * for the color - the map-level mechanism the 0428 record armed).  THE 0428
 * FOOTNOTE RESOLVES: the model on the fresh G-probe table returns the World A
 * order for BOTH the designed tally (color stale n_refs 6 -> 8) and the
 * measured tally (6 -> 10) - the numeric gate is n_refs >= 7 (pri 2*7/33 =
 * 0.4242 beats the quartet head's 12/96 = 0.3750; n=6 gives 0.3636 and
 * loses), so the exact +2/+4 ref accounting no longer matters at the order
 * level.  NEXT: the map and order arms are proven end to end; landing the G
 * wave + T sibling stays gated on the lane-owner decision (the guarded cc1 is
 * an experiment instrument, not the build compiler); the oracle lane stays
 * blocked on fresh disc links (witness 0/8).
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
    long tcol;
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
                tcol = (long)((char *)tmd + 4);
                otz = *(unsigned short *)&buf40;
                dv = ((otz - otp[2]) + (tcol - tcol)) >> shift;
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

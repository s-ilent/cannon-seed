/* mainmenu_jp data_8008433C row TRUE HEAD #1 (listing 0x8007736C..
 * 0x80077650, 0x50 frame, ra+s0..s5) - CdSearchFile: the path resolver
 * that ties the whole func_80084924 cluster together. Offline decode,
 * cron-20261101-0621 window (second item), oracle DOWN (links 404;
 * the disc-free witness restore covers the gates).
 *
 * IDENTITY (format strings): D_800235A0 "CdSearchFile: searching %s...\n"
 * (cache phase entry, >= 2), D_800235C0 "%s:  found\n" (two spaces,
 * retail), D_800235CC "%s: not found\n" (> 0), D_80023584 "CdSearchFile:
 * disc error\n" (fn3 failure), D_80023550 "%s: path level (%d) error\n",
 * D_8002356C "%s: dir was not found\n". printf = 0x8005C62C pinned.
 *
 * SIGNATURE: a0 = out record pointer (s5; the matched 0x18-byte cache
 * record is copied here in full), a1 = path string (s3; the %s in every
 * message). Returns the matched record's pointer, or 0.
 *
 * FLOW: mount guard (D_800C8028 vs D_800C7CFC, CD_newmedia on mismatch),
 * absolute-path check, then the component loop (separator hops run fn2
 * with the empty string; components copy into the 0x20 buf at sp+0x10
 * and chain the dir id), final_check (level/buf gates, CD_cachefile,
 * the "searching" print), the 0x40-record cache search (empty-name
 * sentinel ends the used slots; strncmp-12 leaf; the 0x18 record copy).
 *
 * THE DEAD BRANCH (retail quirk, banked): the fn3 gate is a plain
 * bnez - the C tested `if (!CD_cachefile(id))`, but CD_cachefile returns
 * -1 (never 0) on failure, so -1 takes the SUCCESS path and the
 * "CdSearchFile: disc error" branch is UNREACHABLE; a failed cache falls
 * into the search over the stale/zeroed cache and ends as "%s: not
 * found" (or a stale false positive). Retail ships it; the C draft must
 * preserve the `== 0` test exactly.
 *
 * LADDER STATE (cron-202611031758, oracle UP disc-free sixteenth
 * rehearsal; probe = judge_unit live; DIFF 170/179 -> 117/186, SIZE 716
 * -> 756 vs 744):
 *  - RULE-20 STATE (cron-202611070146, judge live with rules 19+21+20
 *    staged: site-fresh-const -1 $22 + import-order $21,$19 + vol-extend
 *    1): SIZE 744 = RETAIL for the first time (186 words both sides),
 *    DIFF 144/186 - the volatile-re-load merge andi is gone. Wordmap
 *    classes: funct=7, opcode=115 (the walk cluster + the tail phase),
 *    same-op-imm=4 (68 152 520 600), same-op-mixed=10, same-op-reg=6,
 *    same-op-target=2 (112 120). Tail map (668+): built[k] == retail[k-1]
 *    - a one-word phase, OPPOSITE direction to the walk cluster's -2;
 *    the rule-22 site list comes from a FRESH wordmap at implementation
 *    time, never a stale one. Raw-maspsx trap banked: the load-use fill
 *    before the merge andi is DEBUG-annotated
 *    (`nop # DEBUG: Reuse of '$2'. ...`), and the prepasses run before
 *    main's NOP normalization - rule 20's walk matches by the module NOP
 *    pattern, the regression test pins it.
 *    - RULE-22 STATE (cron-202611071331, judge live with rules
 *      19+21+20+22 staged: reg-field $20->$18 at $L27:2/$L33:2/$L33:3):
 *      DIFF 144/186 UNCHANGED, SIZE 744 = retail - the reg-field words
 *      are PHASE-MASKED: the three rewritten words now text-match
 *      retail's walk-tail insns exactly (`move $s2,$zero` /
 *      `addiu $s2,$s2,1` / `slti $v0,$s2,0x40`) but sit one word late
 *      (built[652]/[656] vs retail[648]/[652]) - the +1 phase the (a)
 *      extra retail [lbu,nop] pair creates; the tail runs the OPPOSITE
 *      direction (the stray built nop before the return-zero move + the
 *      epilogue [j|addiu-delay] vs retail [addiu|j|nop]). The (d)
 *      w163-165 loop-head pair is the SAME i-home class (the $4/$2
 *      fields there are the phase-shifted name/empty-check operands).
 *      (e) EVALUATED: not a standalone rule - it is net-zero words only
 *      TOGETHER with the stray-nop delete, folds into the phase chain.
 *      FULL SITE LIST + closure order ((a) c8 source probe first, then
 *      the d2 position mover) banked in docs/CC_POST_RULE_CLASSES.md
 *      section 6 STATUS. Suite 207 -> 224 (17 rule-22 tests).
 *  - RULE-22 SITE-LIST STARTING POINT (same window, difflib block map of
 *    the 186-word streams; WORD indices, the wordmap's idx field is
 *    BYTES = 4x these): (a) w41-43 the copy-exit merge - retail carries
 *    ONE MORE [lbu,nop] pair than the built (the built's merged test
 *    reads the carried value, retail re-loads; the built stream is one
 *    word short here and one word long at the tail - the net-zero
 *    reshuffle the equal SIZE hides); (b) w118-124 the walk block's
 *    anchor temp - built lui $16,0x8014 + addiu $16,0x7884-form vs
 *    retail lui $2,0x8014 / addiu $2,0x788c / addiu $16,$2,-8 /
 *    move $18,$2 + a fresh addiu $1,$2,0x788c - the reg-field +
 *    position mover's core site (d2's genuinely-new transform); (c)
 *    w143-160 the cache-copy scheduler positions (retail's lw/sw
 *    triple blocks vs the built's extra nops + a duplicated sw/j pair);
 *    (d) w163-165 the loop-head reg fields (built $20/$4 vs retail
 *    $18/$2); (e) w183-185 the EPILOGUE position class - retail
 *    [addiu $sp,0x50; j $31; nop] vs built [j $31; addiu $sp in the
 *    delay] - the frame-addiu sits OUTSIDE the delay slot in retail,
 *    one word earlier, a nop fills the delay; (f) the branch/call
 *    offset +-k cascade (w17/28/30/38/48/60/64/72/78/87/91/100/106/
 *    126/130) rides the two phase ends, not a separate class. This list
 *    is the STARTING point only - rule 22 re-derives from a FRESH
 *    wordmap at implementation time (the tree moves again first).
 *  - CLOSED (cron-202611021158): the mount guard reads D_800C8028; buf is
 *    0x20 bytes; the mount-guard store's load-use nop now derives
 *    upstream from the maspsx far-store look-past (pad-lw RETIRED).
 *  - CLOSED (cron-202611021204): the component loop's rotation (do-while
 *    with the entry pre-test, the shared tail, the a0-chain).
 *  - CLOSED this window: REMAINING (1) the cache loop's FOUR-STATE
 *    walker form - rec = (unsigned char*)&D_8014788C[-8] (s0, the addiu
 *    s0,v0,-8 setup), name = &D_8014788C[0] (s3), off = the s1 anchor-
 *    relative offset advanced in the back-edge delay, i = the 0x40
 *    counter (s2, zeroed in the searching-print skip branch's delay);
 *    the empty check reads the EXTERN D_8014788C[off] directly (the
 *    4-insn at-split), NOT a local pointer. (2) the record copy is six
 *    explicit word pairs (lw 0/4/8/C, sw 0/4/8/C, lw 10/14, sw 10/14)
 *    through the s0 walker, returning rec. (3) the copy-exit re-load -
 *    the exit NUL check and the bottom test read *(volatile char*)src
 *    so gcc cannot CSE them into the back-edge load (retail re-loads
 *    *src before the dead check). (4) the sep CSE residue - an empty
 *    asm barrier (gcc 2.6.3 form: asm("" : "=r" (sep) : "0" (sep)); the
 *    '+r' modifier does not exist yet) after sep = '\\' makes the
 *    pinned s4 value opaque so the bottom test materializes a FRESH
 *    ori v1,0x5C (retail re-reads the constant per outer iteration).
 *  - THE INTERLEAVE LAW (this window, the biggest finding): with the
 *    param imports expressed as PINNED-LOCAL INITS (register ... asm()
 *    = param), gcc 2.6.3 DOES emit the interleaved save+import prologue
 *    (sw s5,0x44/addu s5,a0, sw s3,0x3C/addu s3,a1, then ra, then the
 *    batch, s0 in the branch delay) - the shape WithMode proved
 *    unreachable for raw params. The pinned-local-init class is the
 *    rule-15 bypass for the whole interleave family.
 *  - REMAINING (probe 117/186, all localized):
 *    (5) THE IMPORT ORDER: built emits the pinned-local inits in gcc's
 *        allocation/use order (pathv/s3 first - pathv[0] is the first
 *        param use after the guard); retail emits out/s5 FIRST (param
 *        order a0-then-a1). Steering not found this window: declaration
 *        order does not drive it. Next: try an early dead use of outp
 *        before the pathv[0] read, or gcc 2.6.3 K&R register-param
 *        declarations (register ... asm() in the param list).
 *    (5b) K&R REGISTER-PARAM PROBE kr1 MEASURED NEGATIVE (cron-202611060731,
 *         live judge): gcc 2.6.3 DROPS the asm() register bindings on K&R
 *         param declarations - the params reallocate (a0 landed s2 = level's
 *         reg, import order a0-first = retail-INVERTED) and the whole
 *         prologue re-lays (sw ra,0x4c vs retail 0x48). K&R is not the
 *         import-order lever. Remaining candidates: a cc_post rule-15-family
 *         extension matching THIS prologue family (no jal - the guard branch
 *         leads), or an early real use of out before the path[0] read that
 *         gcc cannot fold. The import-order block parks unless one of those
 *         opens.
 *    (5c) THE FRESH WORD-DIFF MAP (same window, live judge 117/186
 *         REPRODUCED, offline 99/186): the residue decomposes as (i) the
 *         prologue import order 0x00..0x70 (the parked (5)); (ii) the
 *         component-loop/final_check insert-delete blocks 0x14..0xb8
 *         (the built runs 189 vs 186 - the +3 SIZE lives here); (iii)
 *         @0xc8 the -1-constant REGISTER CLASS (built bne $2,$22 vs retail
 *         bne $2,$3 - the id==-1 test's constant home: s6 vs v1); (iv) the
 *         branch DISPLACEMENT cascades (@0xf8 beq -8 vs -9 etc.) riding the
 *         +3 size skew - NOT independent words; (v) @0xe8 the jal-0 vs
 *         jal-leaf word is an OFFLINE ARTIFACT (extern reloc vs the
 *         committed listing's resolved encoding - the live judge resolves
 *         it). Next lever order: (iii) the -1 home (a source shape that
 *         pins the -1 materialization to v1), then (ii) the component-loop
 *         size, then (5) last (cosmetic count only if (ii)/(iii) land).
 *    (5d) PROBE c3 (cron-202611062001, probes/gcc263/func_8007736C_probe_c3.c,
 *         live judge DIFF 122/186, SIZE 756 vs 744): THE @0xc8 CLASS IS
 *         CLOSED. Two structural moves: (a) the carried-c component loop -
 *         one local `c` in v0 carries the char (load A per outer iteration
 *         feeds the head test; the top NUL check reads the BACK-EDGE value
 *         with no reload; load B copies; load C is the bottom-test operand;
 *         load D = the volatile exit re-load; the hop re-enters at the
 *         MERGED check reusing load A) - kills the old shape's extra
 *         loop-top load and the hop-target skew; (b) the sep2 lever - the
 *         bottom test compares against a NON-PINNED local assigned '\\'
 *         with the "=r"/"0" barrier INSIDE the outer loop body (after the
 *         head-test branch): the per-iteration opaque def blocks the
 *         invariant hoist (nested-loop use) -> `ori $v1,$zero,0x5C` at the
 *         inner preheader per outer iteration + `bne $v0,$v1` = retail
 *         exact. The old once-before-the-loop barrier does NOT block it.
 *         NEW findings parked in the c3 header: the -1 home solves in
 *         isolation via a tail-scoped pinned asm("$2") local (retail's
 *         addiu $v0,-1 / beq $a0,$v0 exact; a disjoint second $2 pin for
 *         the walk's anchor compiles and lands both words) BUT the $2 pin
 *         is function-global and displaces the other v0 scratch pseudos
 *         (the walk's i slid to s4, DIFF 122 -> 149/152) - a non-pin -1
 *         shape is still owed. The volatile load D emits a redundant
 *         `andi $2,$2,0x00ff` at the merge (+1; gcc 2.6.3 volatile reads
 *         bypass the zero-extend tracking); a plain read gets CSE-eliminated
 *         (retail's re-load is real); asm volatile("" ::: "memory") kills
 *         the andi but EATS maspsx delay-slot labels (the '# DEBUG:
 *         skipped' line) - memory clobbers are a maspsx hazard, banked.
 *         Remaining: the andi, the -1 home, (ii) the component-loop +2,
 *         (5) the prologue order, the walk's i-home/off-init positions.
 *    (6) the s2 counter: the cache loop's i must reuse level's s2 (it
 *        does naturally) but built still holds +3 words (189 vs 186)
 *        - re-measure after (5): the residue sits in the loop head
 *        region 0x800773f0..0x80077420 (the cur=buf delay and the
 *        fresh-v1 placement) and single delay-slot words down the
 *        function (word 50/62/66/74/80/89/93/96/102/108/115, likely
 *        one register-cascade class), then the cache walk 120..188.
 *        c3 note: the walk's i-home divergence (built s4 vs retail s2,
 *        with the off-init slid before the searching printf) exists in
 *        BOTH the unpinned 122 state and the pinned variants - it is a
 *        separate open class in the walk region, not a $2-pin artifact.
 *         EXPLICIT-I NOTE: the walk's i was compiling as an IMPLICIT int
 *         (gnu89) in the staged copy; an explicit function-scope `int i;`
 *         was added and re-judged - SAME 122/186, i still homes to s4.
 *         The i-home is allocation-order driven (s2/s4 both free where
 *         the walk allocates; gcc picked s4), not declaration-driven.
 *    (7) THE -1 NON-PIN SHAPE: REFUTED (cron-202611062116, probe c4,
 *         judge 122/186 SIZE 756 = identical). The sep2 lever applied to
 *         the -1 (m1 = -1 + the "=r"/"0" opaque barrier inside the outer
 *         loop, immediately before the test) does NOT block the hoist:
 *         the tail def dominates the loop latch (every back edge passes
 *         it), so loop.c hoists the def+barrier pair regardless; the "0"
 *         tie then drags the compare onto the hoisted register (s6).
 *         The sep2 lever's boundary law: the opaque def must sit on a
 *         CONDITIONAL path that does not dominate the latch (sep2's sits
 *         on the head-test fall-through arm). With this plus the banked
 *         findings (the barrier inherits the hoisted input's register;
 *         def-before-call+use-after = callee-saved; the -1 has no
 *         nested-loop use), the non-pin shape is refuted from three
 *         directions - the route to retail's fresh
 *         `addiu $v0,-1; beq $a0,$v0` is a cc_post rule-class, not a
 *         source shape.
 *    (8) THE WALK I-HOME: PARKED AS ITS OWN CLASS (cron-202611062116,
 *         probes c5a/c5b, judge 122/186 both). Block-scoped `int i;`
 *         inside the walk block (after AND before the rec/name/off
 *         pins) leaves i in s4 (sep's dead reg) - the i-home is
 *         insensitive to declaration scope AND order (four shapes now:
 *         implicit function-scope, explicit function-scope, block-scope
 *         after the pins, block-scope before the pins). Retail's s2
 *         (level's dead reg) is unreachable by source steering; the
 *         class joins the cc_post reg-field-candidate family.
 *    (9) THE PROLOGUE IMPORT ORDER: FULLY PARKED (cron-202611062231,
 *         probe c6, judge 127/186 = +5 WORSE). The third and last
 *         candidate - an input-only empty asm consuming outp before the
 *         pathv[0] read - did NOT reorder the init copies (the order is
 *         not first-use-driven either) and the barrier displaced the
 *         guard loads into the import block and reshuffled the spill
 *         batch. With declaration order and K&R register params already
 *         refuted, the class is a cc_post rule-15-family extension or
 *         nothing.
 *   (10) THE WALK-HEAD ANCHOR CLASS (retail [120]-[124]: anchor into v0,
 *         rec = addiu $s0,$v0,-8, name = move $s3,$v0 - a REAL copy from
 *         the scratch): REFUTED from three source shapes
 *         (cron-202611062231). (a) c3 form: the -8 folds into rec's own
 *         materialization (lui/addiu 0x7884 into s0, name = s0+8). (b)
 *         c7 transparent shared anchor: gcc homes the anchor in name's
 *         own s3 (lui $s3 direct), rec = s3-8. (c) c7b opaque anchor
 *         (the "=r"/"0" barrier, C89-clean statement order): the anchor
 *         STILL homes in s3 - the barrier blocks value propagation but
 *         not REGISTER coalescing, and the anchor->name copy becomes a
 *         no-op instead of retail's real move. The v0-scratch route is
 *         unreachable from the source; the class joins the cc_post
 *         reg-field-candidate family. Side finding: the c7b restructure
 *         moved i's init into the walk block head (move $s4,$zero at
 *         [123]) without changing the count - the i-init position is
 *         likewise not worth a source lever.
 */

extern int D_800C8028;               /* mount guard: cached state */
extern int D_800C7CFC;               /* mount guard: expected state */
extern int D_800C7CF0;               /* trace level */
extern unsigned char D_80147884[];   /* the 0x40-entry cache table */
extern unsigned char D_8014788C[];   /* cache + 8: the name-field anchor */
extern char D_80023550[];
extern char D_8002356C[];
extern char D_80023584[];
extern char D_800235A0[];
extern char D_800235C0[];
extern char D_800235CC[];
extern int func_80077678();
extern int func_8007796C();
extern int func_80077A18();
extern int func_80077654();
extern int printf();

unsigned char *func_8007736C(unsigned char *out, const char *path) {
    unsigned char buf[0x20];     /* sp+0x10 */
    const char *src;
    int id;
    int level;
    int i;
    register unsigned char *cur asm("$17");   /* s1: the buf cursor */
    register int sep asm("$20");              /* s4: the head-test constant */
    register unsigned char *outp asm("$21") = out;   /* s5: the copy destination */
    register const char *pathv asm("$19") = path;    /* s3: the %s in every message */

    if (D_800C8028 != D_800C7CFC) {
        if (func_80077678() == 0) {
            return 0;
        }
        D_800C8028 = D_800C7CFC;
    }
    if (pathv[0] != '\\') {
        return 0;
    }
    id = 1;
    buf[0] = 0;
    src = pathv;
    level = 0;
    sep = '\\';
    asm("" : "=r" (sep) : "0" (sep));   /* opaque: bottom test re-materializes */
    {
        /* The carried char (v0): load A feeds the head test, the top NUL
         * check reuses the back-edge load C (NO reload), the bottom test
         * compares the carried value, the copy-exit re-loads volatile
         * (load D), and the separator hop re-enters at the merged NUL
         * check reusing the head-test load. */
        unsigned int c;
        int sep2;
        while (1) {
            cur = buf;
            c = *src;                            /* load A: per outer iteration */
            if (c == sep) {
                goto nul_check;                  /* the hop: reuse load A */
            }
            sep2 = '\\';                         /* fresh def per outer iteration */
            asm("" : "=r" (sep2) : "0" (sep2));  /* opaque: blocks the invariant hoist */
            do {
                if (c == 0) {
                    goto final_check;
                }
                c = *src;                        /* load B */
                src++;
                *cur = c;
                cur++;
                c = *src;                        /* load C */
            } while (c != sep2);
            c = *(volatile const char *)src;     /* load D: the copy-exit re-load */
        nul_check:
            if (c == 0) {
                goto final_check;
            }
tail:
            src++;
            *cur = 0;
            id = func_8007796C(id, buf);            /* the a0 chain */
            if (id == -1) {
                buf[0] = 0;
                goto final_check;
            }
            level++;
            if (level >= 8) {
                break;
            }
        }
    }
final_check:
    if (level >= 8) {
        if (D_800C7CF0 > 0) {
            printf(&D_80023550, pathv, level);
        }
        return 0;
    }
    if (buf[0] == 0) {
        if (D_800C7CF0 > 0) {
            printf(&D_8002356C, pathv);
        }
        return 0;
    }
    if (func_80077A18(id) == 0) {
        if (D_800C7CF0 > 0) {
            printf(&D_80023584);
        }
        return 0;
    }
    if (D_800C7CF0 >= 2) {
        printf(&D_800235A0, buf);
    }
    {
        /* the four-state cache walk: s0 = the record walker (anchor-8),
         * s3 = the name walker (anchor, reusing the dead pathv reg),
         * s1 = the anchor-relative byte offset (reusing the dead cur
         * reg), s2 = the 0x40 counter (reusing level's reg); the empty
         * check reads the extern through the at-split with the running
         * offset */
        register unsigned char *rec asm("$16") =
            (unsigned char *)&D_8014788C[-8];
        register const unsigned char *name asm("$19") = &D_8014788C[0];
        register int off asm("$17") = 0;
        for (i = 0; i < 0x40; i++, off += 0x18) {
            if (D_8014788C[off] == 0) {
                break;
            }
            if (func_80077654(name, buf) != 0) {
                if (D_800C7CF0 >= 2) {
                    printf(&D_800235C0, buf);
                }
                *(int *)(outp + 0x00) = *(int *)(rec + 0x00);
                *(int *)(outp + 0x04) = *(int *)(rec + 0x04);
                *(int *)(outp + 0x08) = *(int *)(rec + 0x08);
                *(int *)(outp + 0x0C) = *(int *)(rec + 0x0C);
                *(int *)(outp + 0x10) = *(int *)(rec + 0x10);
                *(int *)(outp + 0x14) = *(int *)(rec + 0x14);
                return rec;
            }
            rec += 0x18;
            name += 0x18;
        }
    }
    if (D_800C7CF0 > 0) {
        printf(&D_800235CC, buf);
    }
    return 0;
}

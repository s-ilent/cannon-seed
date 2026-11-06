/* PROBE c5 (cron-202611062116): the walk i-home steering - block-scoped i
 * (queue item (2), its own probe). Judge: DIFF 122/186, SIZE 756 vs 744 -
 * MEASURED NEGATIVE in BOTH declaration positions (after the pins = c5a,
 * before the pins = c5b), identical to c3.
 * Rest of the ladder state in scripts/deferred_func_8007736C.c.
 *
 * C5 CHANGE: `int i;` moves from function scope into the walk block (two
 * positions judged: AFTER the rec/name/off pins = c5a, FIRST in the list =
 * c5b; both identical 122/186) - the walk's counter becomes its own block
 * allocno. LAW (third confirmation, with the 2001 window's implicit and
 * explicit function-scope variants): the walk i-home is INSENSITIVE to
 * declaration scope and order - gcc 2.6.3 hands it s4 (sep's dead reg) in
 * every shape; retail's s2 (level's dead reg) is unreachable by steering
 * at the source level. The i-home parks as its own class (a cc_post
 * reg-field-class candidate, like the AF70 option B family). Retail homes the walk's i in s2 (level's
 * dead reg); the built has taken s4 (sep's dead reg) in every variant so
 * far (function-scope implicit AND explicit judged identical 122).
 *
 * ===== c4 state (cron-202611062116, MEASURED NEGATIVE) =====
 * THE M1 LEVER (the sep2 lever applied to the -1) DOES NOT FIRE: m1 = -1
 * + the "=r"/"0" opaque barrier immediately before the test judged
 * IDENTICAL to c3 (122/186, SIZE 756) - the raw gcc output shows the same
 * single hoisted `addiu $22,$zero,-1` and no per-iteration def. LAW: the
 * sep2 lever requires the def to sit on a CONDITIONAL path that does not
 * dominate the loop latch (the sep2 def is on the head-test fall-through
 * arm); a def+barrier in the tail dominates the latch (every back edge
 * passes it) so loop.c hoists it regardless of the barrier - the "0" tie
 * then drags the compare onto the hoisted register (s6). Combined with
 * the banked findings (the barrier inherits the hoisted input's register;
 * def-before-call+use-after = callee-saved; the -1 has no nested-loop
 * use), the -1 non-pin shape is now REFUTED from three directions - the
 * remaining route to retail's fresh `addiu $v0,-1; beq $a0,$v0` is a
 * cc_post rule-class, not a source shape.
 *
 * ===== c4 header (what it tried) - THE -1 HOME (lever (iii):
 * the 122 map's biggest single class): the c3 carried-c regalloc hoisted
 * the -1 constant to s6 (`addiu $22,$zero,-1` before the outer loop +
 * `beq $4,$22` at the test + the s6 sw/lw pair in the prologue/epilogue;
 * retail has `addiu $v0,$zero,-1; beq $a0,$v0` FRESH at the site and does
 * not save s6). The sep2 lever generalizes: the -1 is materialized into a
 * variable `m1` with the "=r"/"0" opaque barrier INSIDE the outer loop
 * body, immediately before the test - the per-iteration asm def is not
 * loop-invariant so loop.c cannot hoist it, and the constant must
 * materialize fresh at the site. If gcc homes m1 in v0 (free after the
 * `addu $4,$2,$zero` id copy - v0 is dead there), the two words are
 * retail's EXACT pair and the s6 save/restore pair dies with it (SIZE
 * -2); if it homes v1 (the sep2 precedent - sep2 took v1 when v0 held c),
 * the position still closes but the reg fields stay DIFF. The walk's
 * i-home (s4 vs retail s2) is deliberately untouched in this probe.
 *
 * ===== c3 state (cron-202611062001) =====
 * THE @0xc8 LEVER (iii) CLOSED (probe c3, carried over unchanged):
 *   - The carried-c shape: ONE local `c` carries the char across the
 *     component loop - load A (per outer iteration, after cur=buf) feeds
 *     the head test; the top NUL check reads the BACK-EDGE value with NO
 *     reload (retail: beqz $v0 with $v0 from the previous load C); load B
 *     = the copy char; load C = the next char (the bottom test operand);
 *     load D = the volatile copy-exit re-load; the separator hop re-enters
 *     at the MERGED NUL check reusing load A's value. gcc 2.6.3 keeps `c`
 *     in $2 (v0) = retail's exact home.
 *   - The sep2 lever: the bottom test compares against a NON-PINNED local
 *     `sep2` assigned '\' + the asm("" : "=r" : "0") barrier INSIDE the
 *     outer loop body (fall-through path only). The per-iteration opaque
 *     def BLOCKS the invariant hoist (the use sits inside the nested
 *     loop, so loop.c refuses to move the def) -> gcc materializes
 *     `ori $v1,$zero,0x5C` at the inner preheader PER OUTER ITERATION and
 *     the bottom test emits `bne $v0,$v1` = RETAIL'S EXACT WORDS @0xc8
 *     (was bne $v0,$s6 with the s6 ori hoisted before the outer loop).
 *     The old draft-level sep barrier (once, before the loop) does NOT
 *     block the hoist - the def must sit after the head-test branch.
 *
 * THE -1 HOME FINDINGS (the test stays `id == -1` in this probe; the
 * carried-c regalloc hoists the -1 constant to s6: `addiu $22,$zero,-1`
 * before the outer loop + `beq $4,$22` at the test; retail has
 * `addiu $v0,$zero,-1; beq $a0,$v0` fresh at the site):
 *   - A pinned local `register int minus1 asm("$2") = -1;` scoped to the
 *     tail block reproduces retail's two words EXACTLY - and the SECOND
 *     pin (`register unsigned char *anchor asm("$2") = &D_8014788C[0];`
 *     in the walk block, disjoint live range) COMPILES and lands the
 *     walk's anchor temp back in v0 (retail lui/addiu $v0). Both words
 *     correct simultaneously.
 *   - BUT the $2 pin is FUNCTION-GLOBAL: reserving v0 displaces every
 *     other v0 scratch pseudo - the walk's `i` counter slid to s4
 *     (retail: level's s2), the off-init slid before the searching
 *     printf, DIFF worsened 122 -> 149/152. A non-pin solution for the
 *     -1 is still owed (candidates: none found this window - the barrier
 *     inherits the hoisted input's register via the "0" tie; def+use in
 *     the same straight region always hoists because the dest reg is
 *     dead at loop exit; def-before-call+use-after = callee-saved; the
 *     sep2 trick needs a nested-loop use between def and use).
 *
 * THE ANDI CLASS (+1 word, still open): the volatile load D's result gets
 * `andi $2,$2,0x00ff` at the merge (gcc 2.6.3 volatile reads bypass the
 * zero-extend tracking; non-volatile reads do not). Retail has no andi -
 * its exit re-load result feeds the merged beqz directly. A plain
 * non-volatile read gets CSE-ELIMINATED entirely (load D vanishes,
 * retail's re-load is real). asm volatile("" ::: "memory") kills the
 * andi but BREAKS maspsx's delay-slot handling (the $L9 label got eaten
 * into a '# DEBUG: skipped' comment line - NEW TOOL LESSON: memory
 * clobbers are a maspsx hazard, do not ship them through this pipeline).
 *
 * REMAINING CLASSES in the 122 map: the andi (+1); the -1 home (s6 hoist
 * vs retail v0-fresh); the prologue import order (lever (5), parked);
 * the component-loop +2 residue (lever (ii): the insert-delete blocks
 * 0x14..0xb8 minus the s6-ori word this probe removed); the walk's
 * i-home/off-init positions (untouched); displacement cascades riding
 * the +3.
 */

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
 *    (6) the s2 counter: the cache loop's i must reuse level's s2 (it
 *        does naturally) but built still holds +3 words (189 vs 186)
 *        - re-measure after (5): the residue sits in the loop head
 *        region 0x800773f0..0x80077420 (the cur=buf delay and the
 *        fresh-v1 placement) and single delay-slot words down the
 *        function (word 50/62/66/74/80/89/93/96/102/108/115, likely
 *        one register-cascade class), then the cache walk 120..188.
 *         EXPLICIT-I NOTE: the walk's i was compiling as an IMPLICIT int
 *         (gnu89) in the staged copy; an explicit function-scope `int i;`
 *         was added and re-judged - SAME 122/186, i still homes to s4.
 *         The i-home is allocation-order driven (s2/s4 both free where
 *         the walk allocates; gcc picked s4), not declaration-driven.
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
        int m1;
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
            m1 = -1;                             /* fresh def per outer iteration */
            asm("" : "=r" (m1) : "0" (m1));     /* opaque: blocks the -1 hoist */
            if (id == m1) {
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
        int i;
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

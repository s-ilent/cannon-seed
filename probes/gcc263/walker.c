/* Walker-family C-match probe (func_800263E8, mainmenu_jp) - cron-20261013-0011.
 *
 * STATUS: 46/51 instructions byte-exact (this file compiles to the 910-score
 * permuter candidate). NOT a match yet - see REMAINING DIFFS at the bottom.
 *
 * MEASURED CONTRACTS (docs/FABRIC.md "reset walker's entry contract"), now
 * with the compiler mechanics that produce them:
 *
 * 1. THE LOOP VARIABLE THREADS THROUGH THE WALK CALL'S 2ND ARGUMENT.
 *    `mode = func_800257A4(base, mode)` - the query result (first iteration)
 *    and the previous walk result (retries) are the real a1 inputs; the C
 *    driver's `mode` argument is copied to s3 and never consumed as a1
 *    (the "ABI facade the callee partially ignores" is this reassignment).
 *    GCC keeps the variable in $5 (its argument home) and emits the result
 *    copy `addu $a1,$v0` after each call - the 26414 entry copy included.
 *
 * 2. THE REARM PARAMETER IS REASSIGNED TO -1 AND BECOMES THE PHASE-1
 *    COMPARE CONSTANT. `rearm = -1; ... if (r_a1 != rearm)` - GCC keeps the
 *    reassigned param in $18 and materializes `addiu $s2,$zero,-1` (26418).
 *    Phase 2 compares against the LITERAL -1 via r_v0 instead (2646C:
 *    `addiu $v0,$zero,-1`), which is why the two loops shape differently.
 *
 * 3. THE FATAL-PATH TAIL JUMP (j .L80025788 + move $v0,$zero in the delay)
 *    reproduces byte-exactly with a .set noreorder-wrapped asm + break:
 *      __asm__ volatile(".set\tnoreorder\n\tj .L80025788\n\t
 *                        addu $v0,$zero,$zero\n\t.set\treorder");
 *      break;
 *    - maspsx appends `nop` after any j/jal it sees while .set reorder is
 *      active (maspsx/__init__.py "branch/jump" rule); the noreorder window
 *      suppresses it. The TABS in ".set\tnoreorder" are REQUIRED (maspsx
 *      matches ".set\t" - a space slips through and the nop returns).
 *    - The `break;` after the asm is what removes GCC's loop back-edge:
 *      without it GCC emits `j $L2` between the asm and phase 2's head.
 *    - The delay-slot `move $v0,$zero` is semantically dead at the target
 *      (0x80025788's first insn is `lw $v0,0x14($gp)`) - pure fill artifact.
 *
 * 4. THE COUNTER'S LUI/ORI STRADDLE THE QUERY CALL (26408 lui / 2640C jal /
 *    26410 ori-in-delay). A plain `s0 = 0xFFFFFFF` materializes contiguously
 *    (GCC folds any two-step constant init of a normal local). The split
 *    needs an OPAQUE first half: `asm("lui %0,0xFFF" : "=r"(s0))` (output-
 *    only asm def - s0's value unknown) then `s0 |= 0xFFFF` AFTER the call
 *    emits the real ori, which lands in the jal's delay or just after.
 *    GCC 2.6.3 has no `+` asm constraints - read-write opaqueness needs
 *    the matching-constraint form ("=r"(x) : "0"(x)).
 *
 * 5. GLOBAL REGISTER VARIABLES (r_v0=$2, r_a1=$5, c478 rule-6 precedent)
 *    bind the result copies to their retail positions:
 *    - `r_a1 = r_v0` after the query emits the 26414 entry copy.
 *    - `r_v0 = -1; if (r_a1 != r_v0) return r_a1;` in phase 2 forces
 *      `addiu $v0,$zero,-1` + `bne $a1,$v0` (retail 2646C/26470).
 *    - Global reg vars are NOT prologue-saved (probe_g) - never bind the
 *      counter (retail saves $16); keep it a normal local.
 *    - GCC 2.6.3 never tail-calls (probe B: `return f(0)` -> jal + epilogue).
 *
 * REMAINING DIFFS (asm vs this file, both pure scheduling):
 *   a. Prologue interleave: compiler emits [sw s1, move s1][sw s0, lui]
 *      [sw s3, move s3][sw ra][jal][sw s2-in-delay] where retail has the
 *      canonical contiguous block [sw ra, s3, s2, s1, s0][move s1][move s3]
 *      [lui][jal][ori-in-delay]. The param-home save/copy pairs are
 *      intrinsic to this cc1; rearm's save is LAZY (at its def) where
 *      retail has it in the template block. An early opaque clobber of
 *      rearm ("=r"/"0" empty asm) did NOT pull the save forward.
 *   b. Phase-2 bne delay: compiler fills with the adjacent counter decrement
 *      (dead-on-taken, legal); retail has the return copy `move $v0,$a1`
 *      (live-on-taken, pulled from the return block at the function end).
 *      The eager `r_v0 = r_a1; return;` restructure INVERTS the branch
 *      (beq) - rejected. dbr prefers the adjacent dead fill over the
 *      distant live one; need the return copy adjacent in-stream instead.
 *
 * Permuter state: decomp-permuter cloned to /home/z/my-project/decomp-permuter,
 * toml installed into the venv (uv). Project dir /tmp/perm_walker (base.c =
 * this shape, target.o from asm/mainmenu_jp/nonmatchings/func_800263E8.s).
 * Base score 1045 -> best 910 with the s2-local -> rearm-param change above.
 * Run: cd cannon-seed && PYTHON=/home/z/my-project/.venv/bin/python3
 *      PY=same sh tools/permuter/run.sh /tmp/perm_walker -j 2 --stop-on-zero
 *      (PYTHON env is REQUIRED - the permuter imports toml, venv-only).
 */

extern int func_80059F90(void);
extern int func_80059F9C(void);
extern int func_800257A4(int, int);
extern void func_8005C62C(int);
extern int D_800200AC;
extern int D_800200C8;

register int r_v0 asm("$2");
register int r_a1 asm("$5");

int func_800263E8(int base, int mode, int rearm)
{
    int s0;
    int m3;

    m3 = mode;
    __asm__("lui %0,0xFFF" : "=r"(s0));
    func_80059F90();
    s0 |= 0xFFFF;
    r_a1 = r_v0;
    rearm = -1;
    for (;;) {
        r_a1 = func_800257A4(base, r_a1);
        if (r_a1 != rearm) break;
        if (--s0 == 0) {
            func_8005C62C((int)&D_800200AC);
            __asm__ volatile(".set\tnoreorder\n\t"
                             "j .L80025788\n\t"
                             "addu $v0,$zero,$zero\n\t"
                             ".set\treorder");
            break;
        }
    }
    r_a1 = func_80059F9C();
    for (;;) {
        r_a1 = func_800257A4(m3, r_a1);
        r_v0 = -1;
        if (r_a1 != r_v0) return r_a1;
        if (--s0 == 0) break;
    }
    func_8005C62C((int)&D_800200C8);
    return 0;
}

/* Walker-family C-match probe (func_800263E8, mainmenu_jp) - cron-20261013-0126.
 *
 * STATUS: 45/52 instruction positions byte-exact (this body = the s9 shape,
 * permuter base score 755, was 910 at cron-20261013-0011). NOT a match yet -
 * two problems remain, both now with MECHANISM-LEVEL explanations from the
 * gcc-2.6.3 source (fetched to /tmp/gcc263.tar.bz2 this session; extract
 * reorg.c + config/mips/mips.c to re-derive).
 *
 * MEASURED CONTRACTS (docs/FABRIC.md "reset walker's entry contract"), with
 * the compiler mechanics that produce them:
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
 *    Moving the reassignment EARLIER (s2) makes GCC route -1 via a THIRD
 *    register (li s3,-1 + move s2) - strictly worse; the reassignment must
 *    stay after the query call in source order.
 *
 * 3. THE FATAL-PATH TAIL JUMP (j .L80025788 + move $v0,$zero in the delay)
 *    reproduces byte-exactly with a .set noreorder-wrapped asm + break:
 *      __asm__ volatile(".set\tnoreorder\n\tj .L80025788\n\t
 *                        addu $v0,$zero,$zero\n\t.set\treorder");
 *      break;
 *    - maspsx appends `nop` after any j/jal it sees while .set reorder is
 *      active (maspsx/__init__.py "branch/jump" rule); the noreorder window
 *      suppresses it. The TABS in ".set\tnoreorder" are REQUIRED.
 *    - The `break;` after the asm is what removes GCC's loop back-edge.
 *
 * 4. THE COUNTER'S LUI/ORI STRADDLE THE QUERY CALL (26408 lui / 2640C jal /
 *    26410 ori-in-delay). A plain `s0 = 0xFFFFFFF` folds contiguously; the
 *    split needs an OPAQUE first half. GCC 2.6.3 has no `+` asm constraints.
 *
 * 5. GLOBAL REGISTER VARIABLES (r_v0=$2, r_a1=$5, c478 rule-6 precedent)
 *    bind the result copies to their retail positions. Global reg vars are
 *    NOT prologue-saved - never bind the counter; keep it a normal local.
 *
 * 6. NEW (0126): THE VOLATILE LUI IS A SCHEDULER BARRIER THAT BUILDS THE
 *    PROLOGUE GROUP. mips.c mips_expand_prologue calls save_restore_insns
 *    right after the sp decrement: the five saves ARE emitted canonically
 *    as ordinary RTX stores. At -O2 the first scheduler then SCATTERS them
 *    (this session's pre-s9 shapes: [sw s1, move s1][sw s0, lui][sw s3,
 *    move s3][sw ra][jal][sw s2-in-delay]). Making the lui asm `volatile`
 *    blocks the scheduler from floating the param defs up among the saves:
 *    the stores become a contiguous group and the ori lands in the jal
 *    delay slot (retail 28) for free. This one word took the probe from
 *    46/51-with-interleave to the s9 shape (score 910 -> 755).
 *
 * REMAINING DIFF 1 - PROLOGUE STORE ORDER (7 positions):
 *    retail:  [sw ra][sw s3][sw s2][sw s1][sw s0][move s1][move s3]
 *    s9:      [sw s1][move s1][sw s3][move s3][sw ra][sw s2][sw s0]
 *    MECHANISM (mips.c save_restore_insns): emission order IS high-to-low
 *    offset (ra,s3,s2,s1,s0 - "debuggers prefer ra at func+4") = retail's
 *    exact order. The scheduler re-orders because (a) the five sp+offset
 *    stores are provably non-aliasing to 2.6.3's dependence test, and (b)
 *    each save has an ANTI-dependency with its own reg's def (save sX must
 *    precede def sX) but not with the others, so the scheduler interleaves
 *    [save sX, def sX] pairs - the defs sit on the call-arg critical path
 *    and out-prioritize the stores. Retail kept emission order: the
 *    original compile must have made the saves critical-path (candidate:
 *    param spill-reloads reading the save area) or used a Psy-Q cc1 with
 *    different scheduling. Source-order levers tested and REJECTED:
 *    rearm=-1 early (s2, worse); asm-first statement order (s10 - GCC
 *    routes mode through v1, much worse); rearm=-1 inside the loop (s11,
 *    no change); ret variable + volatile (s12, compile fail - malformed).
 *
 * REMAINING DIFF 2 - PHASE-2 EXIT (delay fill + j elision + exit copy):
 *    retail:  [li v0,-1][bne a1,v0,epilogue][move v0,a1 IN DELAY][addiu s0]
 *             [bnez s0,call][nop][fatal...][move v0,zero FALLS INTO epilogue]
 *    s9:      [li v0,-1][bne ...][addiu s0 IN DELAY][bnez][nop][fatal...]
 *             [j epilogue][move v0,zero delay][move v0,a1][epilogue]
 *    MECHANISM (reorg.c fill_slots): a conditional branch with prediction
 *    <= 0 (mostly_true_jump: forward exit branch out of a loop = rare
 *    destination -> 0) fills from the FALLTHROUGH thread first - the
 *    counter dec wins. Retail's delay holds the RETURN copy, which happens
 *    only if the copy was the in-stream insn after the bne pre-dbr (the
 *    fallthrough fill then moves it into the slot and the exit block
 *    becomes the bare epilogue - which also elides the fatal j-to-next).
 *    Source shapes tested and REJECTED: break + return-after-loop (s4 -
 *    branch inverts to beq); ret-variable + break (s5/s12 - GCC keeps the
 *    copy in the exit block, no in-stream placement); eager r_v0=r_a1
 *    (inverts, prior session); post-loop re-compare (s3 - adds a second
 *    compare). The 860-score permuter candidate from run 1 moved
 *    `m3 = mode` into dead-code position (uninitialized read) - REJECTED
 *    as illegitimate.
 *
 * Permuter state: project /home/z/my-project/perm/perm_walker (base.c = this
 * shape, target.o from asm/mainmenu_jp/nonmatchings/func_800263E8.s,
 * settings.toml regenerated by run.sh). Run:
 *   cd cannon-seed && setsid nohup env PYTHON=/home/z/my-project/.venv/bin/python3 \
 *     PY=/home/z/my-project/.venv/bin/python3 sh tools/permuter/run.sh \
 *     /home/z/my-project/perm/perm_walker -j 2 --stop-on-zero \
 *     > /home/z/my-project/perm/perm.log 2>&1 &
 * (setsid REQUIRED - a bare background job dies with the shell session.
 *  PYTHON env is REQUIRED - the permuter imports toml, venv-only.)
 * Run 2 reached iteration 54 with no improvement over 755 before being
 * stopped at session end.
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
    __asm__ volatile("lui %0,0xFFF" : "=r"(s0));
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

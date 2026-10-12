/* Probe: func_8002C478 (mainmenu_jp, 0x8002C478..0x8002C608).
 * Compiled with tools/cc.sh -S; word-diffed against the retail bytes in
 * asm/mainmenu_jp/nonmatchings/func_8002C220.s (glabel func_8002C478).
 * Not part of any build target; lives here as matching evidence for the
 * first family-C component (docs/FABRIC.md machinery session).
 *
 * STATUS 2026-10-12 (cron-20261012-1026): COMPLETE - every word of the
 * function compiles retail-exact through the pipeline. This file IS the
 * landing source: next session copies it to src/func_8002C478.c, applies
 * the yaml split, and verifies (recipe at the bottom).
 *
 * THE S0-OPACITY GAP IS CLOSED. The recipe that reproduces retail's
 * [lui s0][addiu s0][sw s1,0(s0)][3 at-pair stores] + both
 * [addiu a0,s0,-0x40] argument trains:
 *
 * 1. THE STORE GROUP IS ONE HAND-ASM BLOCK with s0 as an "=r" OUTPUT
 *    operand. C-level `s0 = &D_80089440; *s0 = s1;` folds: cc1's tree
 *    folder pushes the constant through the assignment, the store
 *    becomes a direct-symbol store, the scheduler hoists the next
 *    call's arg setup above the group, and s0 materializes late for the
 *    args only. Tested and REJECTED (all fold or misorder):
 *    tie-constraint asm ("=r"/"0"), output-only asm ("=r"), volatile
 *    input-only asm, volatile store targets, direct-symbol first store.
 *    GCC 2.6.3's cse sees through every empty-asm form; the asm block
 *    is the only mechanism that (a) emits the nine words verbatim,
 *    (b) as a volatile barrier stops the arg-setup hoist, and (c) makes
 *    s0 genuinely opaque so the two args stay register-relative.
 * 2. THE SHARED-RVALUE CSE TRAP: with s0 opaque, the two identical
 *    (int)s0 - 0x40 expressions still share ONE cse entry (same
 *    (plus $16,-64) key, one EBB across the calls) - the first
 *    computation lands in s0's own register (addu $16,$16,-64, a
 *    destructive temp) and the second copies it. Retail recomputes each
 *    argument from s0. A SECOND output-only asm (`__asm__("" : "=r"(s0))`)
 *    re-defines s0 before the last reset-table call, dropping the shared
 *    entry; nothing is emitted, and s0's liveness at the first argument
 *    forces the direct one-insn form (addu $4,$16,-64) for BOTH args.
 * 3. addu-with-immediate assembles to the retail addiu encoding; the
 *    oracle checks the words.
 *
 * Shaping notes (unchanged from the probe session):
 * - r_v0 pins $2: retail reads the flag into $v0 and later materializes
 *   &D_800899D8 in $v0 for the D_800899C0 store. A file-scope register
 *   variable reserves $2 for those exact uses; $2 is call-clobbered per
 *   ABI, so calls still clobber it normally. Rule-6 exception, documented
 *   in the landing file header.
 * - s1/s0 are ordinary long-lived locals; the prologue saves them (the
 *   s0 save lands in the beqz delay slot exactly as retail).
 * - The tail jump out of the equal-path (j .L8002ABD4) is a hand-asm
 *   sibling jump: the target is a mid-function label of another row,
 *   unnameable from C; build.sh's two-pass auto-definition resolves it
 *   and maspsx's reorder-mode branch nop supplies the delay slot.
 * - Incoming jumps: the trampoline band (func_8002DE00.s) targets
 *   .L8002C4C0/.L8002C4DC/.L8002C50C inside this function; the auto-
 *   definition resolves them by address once the bytes are in place.
 *
 * LANDING RECIPE (cron-20261012-0911/1026 sessions; blocked only on
 * scanner semantics - see the worklog):
 * 1. Copy this file to src/func_8002C478.c (verbatim; it IS the source).
 * 2. Split the func_8002C220 row in config/splat.mainmenu_jp.yaml:
 *      [0xCA20, asm, func_8002C220]   # 0x258 pinned
 *      [0xCC78, c, func_8002C478]     # 0x190
 *      [0xCE08, asm, func_8002C608]   # 0x280 pinned
 *      [0xD088, asm, func_8002C888]   # 0x198 pinned
 * 3. make scan TARGET=mainmenu_jp  <- THE LANDMINE: the scanner's v3
 *    rescue seeds a walk at this function's SECOND instruction (the
 *    addiu sp/sw ra prologue pair sits at CC7C, one word past the gp
 *    load that opens the function), and the seeded walk re-decomposes
 *    the zone into data_8002C478 (0x4) + func_8002C47C (0x18c). The
 *    c row must refuse walk SEEDS inside its span while walks from
 *    outside still flow through (the defensive split then carves the
 *    row out at its exact size). cron-20261012-1026 tried three designs
 *    (full no-walk pin / walk-start clip / covered pre-seed): each fixed
 *    mainmenu_jp but perturbed OTHER targets' verified decompositions
 *    (slps func_80025AF0 head -> data; g3_eu func_8004D744 head -> data;
 *    mainmenu_eu data_8003809C falsely walked as code; g3_jp
 *    func_80024FAC merged away). The next session needs a design that
    keeps all seven other targets' scans byte-identical - candidates:
 *    seed-site refusal scoped to c rows only, plus hand-pinning the two
 *    verified islands the interior seeds used to cover (g3_eu
 *    [0x2DF44, asm, func_8004D744] # 0xf0 pinned; mainmenu_eu
 *    [0x1889C, data, data_8003809C] # 0x3d0 pinned).
 * 4. make extract + make verify TARGET=mainmenu_jp, then the full 8/8
 *    regression, then update config/ratchets.json if the censuses moved.
 */

extern int D_80089328;
extern int D_80089368;
extern int D_80089400;
extern int D_80089440;
extern int D_80089444;
extern int D_80089448;
extern int D_8008944C;
extern int D_800896F8;
extern int D_80089738;
extern int D_80089778;
extern int D_800897B8;
extern int D_800897F8;
extern int D_80089838;
extern int D_80089A48;
extern int D_800899C0;
extern int D_800899D8;
extern int D_800C9B3C;
extern int D_800C9B44;
extern void func_800267C8(int, int, int);
extern void func_80026784(int);
extern void func_80026414(int, int, int);
extern int func_80035A78(int);

register int r_v0 asm("$2");

void func_8002C478(void)
{
    int s1;
    int *s0;

    __asm__("lw %0,0x3D8($gp)" : "=r"(r_v0));
    if (r_v0 != 0) {
        func_800267C8((int)&D_80089400, (int)&D_800C9B3C, (int)&D_800C9B44);
        __asm__ volatile("sw $0,0x3D8($gp)");
    }
    __asm__ volatile("lw $5,0x1048($gp)");
    __asm__ volatile("lw $6,0x1050($gp)");
    func_80026784((int)&D_80089400);
    s1 = -1;
    /* MATCHING: retail store group, emitted verbatim; s0 leaves opaque
     * (see header - the tie/output-only/volatile asm alternatives all
     * fold under GCC 2.6.3's cse). */
    __asm__ volatile(
        "lui %0,%%hi(D_80089440)\n\t"
        "addiu %0,%0,%%lo(D_80089440)\n\t"
        "sw %1,0(%0)\n\t"
        "lui $1,%%hi(D_80089444)\n\t"
        "sw %1,%%lo(D_80089444)($1)\n\t"
        "lui $1,%%hi(D_80089448)\n\t"
        "sw %1,%%lo(D_80089448)($1)\n\t"
        "lui $1,%%hi(D_8008944C)\n\t"
        "sw %1,%%lo(D_8008944C)($1)"
        : "=r"(s0) : "r"(s1) : "$1");
    func_80026414((int)&D_80089328, 0, -1);
    func_80026414((int)&D_80089368, 0, -1);
    func_80026414((int)s0 - 0x40, 0, -1);
    func_80026414((int)&D_80089A48, 0, 0);
    func_80026414((int)&D_800896F8, 0, 0);
    func_80026414((int)&D_80089738, 0, 0);
    func_80026414((int)&D_80089778, 0, 0);
    func_80026414((int)&D_800897B8, 0, 0);
    func_80026414((int)&D_800897F8, 0, 0);
    func_80026414((int)&D_80089838, 0, 0);
    /* MATCHING: drop the shared (s0 - 0x40) cse entry so the last
     * reset-table call recomputes its argument from s0 (see header). */
    __asm__("" : "=r"(s0));
    func_80026414((int)s0 - 0x40, 2, -1);
    if (func_80035A78(0xC) == s1) {
        r_v0 = (int)&D_800899D8;
        D_800899C0 = r_v0;
        __asm__ volatile("j .L8002ABD4");
    }
    D_800899C0 = s1;
}

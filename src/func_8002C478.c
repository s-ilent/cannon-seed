/* Matched 2026-10-12 through the round-trip oracle (mainmenu_jp).
 *
 * First family-C component (docs/FABRIC.md): the whole parent function
 * carved out of the func_8002C220 row. The queued 4-piece fabric_band
 * split was proven structurally impossible (cron-20261012-0911) - the
 * C45C/C4C0/C50C windows are frame-sharing label blocks - so the sound
 * unit is this complete function (real prologue saving ra/s1/s0, real
 * epilogue). Evidence + rejected shapes: probes/gcc263/c478.c.
 *
 * Runtime role: clears/re-arms a bank of state words (the D_80089xxx
 * region of the state object map) under the 0x20 frame, then walks the
 * reset table through func_80026414. The four gp-relative accesses are
 * literal offsets off mainmenu's runtime gp base, which is still
 * unmeasured (no lui $gp anywhere in the image - crt0 lives in the
 * compressed entry blob), so they stay hand asm until docs/RUNTIME.md
 * harness work pins the base.
 *
 * The yaml row carries the `noseed` marker: this function OPENS with the
 * gp load, so the scan's prologue-pair anchor sits one word past its
 * head (CC7C) and an interior-seeded walk re-decomposes the zone. The
 * marker refuses walk seeds inside the row only; everything else scans
 * byte-identically.
 *
 * Shaping notes (GCC 2.6.3 -O2 -G8, MIPS1):
 * - MATCHING (rule-6 exception, documented): r_v0 is a file-scope
 *   register variable bound to $2. Retail reads the flag into $v0 and
 *   later materializes &state_block_9 through $v0; there is no C-89 shape
 *   that pins the register without it. $2 is call-clobbered per ABI, so
 *   calls still clobber it normally.
 * - MATCHING: the state_rearm_0 store group is one hand-asm block. cc1
 *   folds a C-level constant pointer (s0 = &state_rearm_0) into at-pair
 *   stores and lets the scheduler hoist the next call's arg setup above
 *   the group; retail materializes s0, stores through it, and keeps the
 *   group in order. The asm block emits the nine retail words verbatim
 *   and its volatile barrier blocks the hoist. s0 leaves the block as
 *   an opaque output operand, so the two (int)s0 - 0x40 arguments stay
 *   register-relative (addiu $a0,$s0,-0x40) exactly as retail.
 * - MATCHING: the second output-only asm re-defines s0 before the last
 *   reset-table call. Without it cse shares the two identical
 *   (s0 - 0x40) expressions into one destructive temp (addu $16,$16,-64
 *   + copies); retail recomputes each argument from s0. The re-definition
 *   drops the shared-expression entry; nothing is emitted.
 * - The jal delay-slot fills reproduce retail when s1 = -1 is placed
 *   after the func_80026784 call in source order (probe shape B).
 * - Other code jumps into the middle of this function (the trampoline
 *   band in func_8002DE00.s: j .L8002C4C0/.L8002C4DC/.L8002C50C), and
 *   the equal-path tail jumps out to .L8002ABD4 in another row. All
 *   resolve by address through build.sh's two-pass auto-definition, as
 *   already exercised by func_8003B568 -> .L80037CB0.
 */

extern int state_block_0;
extern int state_block_1;
extern int state_block_2;
extern int state_rearm_0;
extern int state_rearm_1;
extern int state_rearm_2;
extern int state_rearm_3;
extern int state_block_3;
extern int state_block_4;
extern int state_block_5;
extern int state_block_6;
extern int state_block_7;
extern int state_block_8;
extern int state_block_10;
extern int state_cursor;
extern int state_block_9;
extern int state_record_0;
extern int state_record_1;
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
        func_800267C8((int)&state_block_2, (int)&state_record_0, (int)&state_record_1);
        __asm__ volatile("sw $0,0x3D8($gp)");
    }
    __asm__ volatile("lw $5,0x1048($gp)");
    __asm__ volatile("lw $6,0x1050($gp)");
    func_80026784((int)&state_block_2);
    s1 = -1;
    /* MATCHING: retail store group, emitted verbatim; s0 leaves opaque
     * (see header - the tie/output-only/volatile asm alternatives all
     * fold under GCC 2.6.3's cse). */
    __asm__ volatile(
        "lui %0,%%hi(state_rearm_0)\n\t"
        "addiu %0,%0,%%lo(state_rearm_0)\n\t"
        "sw %1,0(%0)\n\t"
        "lui $1,%%hi(state_rearm_1)\n\t"
        "sw %1,%%lo(state_rearm_1)($1)\n\t"
        "lui $1,%%hi(state_rearm_2)\n\t"
        "sw %1,%%lo(state_rearm_2)($1)\n\t"
        "lui $1,%%hi(state_rearm_3)\n\t"
        "sw %1,%%lo(state_rearm_3)($1)"
        : "=r"(s0) : "r"(s1) : "$1");
    func_80026414((int)&state_block_0, 0, -1);
    func_80026414((int)&state_block_1, 0, -1);
    func_80026414((int)s0 - 0x40, 0, -1);
    func_80026414((int)&state_block_10, 0, 0);
    func_80026414((int)&state_block_3, 0, 0);
    func_80026414((int)&state_block_4, 0, 0);
    func_80026414((int)&state_block_5, 0, 0);
    func_80026414((int)&state_block_6, 0, 0);
    func_80026414((int)&state_block_7, 0, 0);
    func_80026414((int)&state_block_8, 0, 0);
    /* MATCHING: drop the shared (s0 - 0x40) cse entry so the last
     * reset-table call recomputes its argument from s0 (see header). */
    __asm__("" : "=r"(s0));
    func_80026414((int)s0 - 0x40, 2, -1);
    if (func_80035A78(0xC) == s1) {
        r_v0 = (int)&state_block_9;
        state_cursor = r_v0;
        __asm__ volatile("j .L8002ABD4");
    }
    state_cursor = s1;
}

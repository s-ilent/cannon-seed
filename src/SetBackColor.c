/* Matched 2026-10-18 through the round-trip oracle (g3_jp first;
 * region-pair 100.00% twins across slps_00270, sces_00269, g3_jp,
 * g3_eu, g3org_jp - the matching lane's GTE Set-family cluster).
 *
 * LIBGTE member: shift the three colour arguments left by 4 (the
 * 12-bit colour fields occupy bits 4..15 of the GTE BackColour words)
 * and ctc2 them into the RBK/GBK/BKY control registers $13/$14/$15.
 *
 * Retail hoists ALL THREE sll's above the three ctc2's; per-statement
 * "r"(r << 4) inputs let gcc interleave sll/ctc2 pairs (the C shift
 * schedules between the volatile asm boundaries). One asm block with
 * the shifts in the template pins the retail order; the three "r"
 * inputs are satisfied from the dead incoming argument registers, so
 * retail's sll $a0, $a0, 4 form falls out. Frameless leaf.
 */
void SetBackColor(long r, long g, long b)
{
    __asm__ volatile("sll %0, %0, 0x4\n\tsll %1, %1, 0x4\n\tsll %2, %2, 0x4\n\t"
                     "ctc2 %0, $13\n\tctc2 %1, $14\n\tctc2 %2, $15"
                     :: "r"(r), "r"(g), "r"(b));
}

/* Matched 2026-10-18 through the round-trip oracle (g3_jp first;
 * region-pair 100.00% twins across slps_00270, sces_00269, g3_jp,
 * g3_eu, g3org_jp - the matching lane's GTE Set-family cluster).
 *
 * LIBGTE member: shift the three colour arguments left by 4 and ctc2
 * them into the FAR colour control registers $21/$22/$23. Same shape
 * as SetBackColor: one asm block, template shifts, three "r" inputs
 * satisfied from the dead argument registers. Frameless leaf.
 */
void SetFarColor(long r, long g, long b)
{
    __asm__ volatile("sll %0, %0, 0x4\n\tsll %1, %1, 0x4\n\tsll %2, %2, 0x4\n\t"
                     "ctc2 %0, $21\n\tctc2 %1, $22\n\tctc2 %2, $23"
                     :: "r"(r), "r"(g), "r"(b));
}

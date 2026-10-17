/* Matched 2026-10-18 through the round-trip oracle (g3_jp first;
 * region-pair 100.00% twins across slps_00270, sces_00269, g3_jp,
 * g3_eu, g3org_jp - the matching lane's GTE Set-family cluster).
 *
 * LIBGTE member: shift both arguments left by 16 (the GTE screen
 * offsets are packed 16.16 fixed-point) and ctc2 them into the OFX/
 * OFY control registers $24/$25. Retail hoists both sll's above the
 * ctc2's; one asm block with the shifts in the template pins the
 * order, the two "r" inputs are satisfied from the dead argument
 * registers. Frameless leaf.
 */
void SetGeomOffset(long ofx, long ofy)
{
    __asm__ volatile("sll %0, %0, 0x10\n\tsll %1, %1, 0x10\n\t"
                     "ctc2 %0, $24\n\tctc2 %1, $25"
                     :: "r"(ofx), "r"(ofy));
}

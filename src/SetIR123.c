/* Matched 2026-10-18 through the round-trip oracle (g3_jp first;
 * region-pair 100.00% twins across slps_00270, sces_00269, g3_jp,
 * g3_eu, g3org_jp - the matching lane's GTE Set-family cluster).
 *
 * LIBGTE member: mtc2 the three arguments straight into the GTE IR1/
 * IR2/IR3 data registers ($9/$10/$11). Each "r" input is satisfied
 * from the incoming argument register; frameless leaf.
 */
void SetIR123(long ir1, long ir2, long ir3)
{
    __asm__ volatile("mtc2 %0, $9" :: "r"(ir1));
    __asm__ volatile("mtc2 %0, $10" :: "r"(ir2));
    __asm__ volatile("mtc2 %0, $11" :: "r"(ir3));
}

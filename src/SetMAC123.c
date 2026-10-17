/* Matched 2026-10-18 through the round-trip oracle (g3_jp first;
 * region-pair 100.00% twins across slps_00270, sces_00269, g3_jp,
 * g3_eu, g3org_jp - the matching lane's GTE Set-family cluster).
 *
 * LIBGTE member: mtc2 the three arguments straight into the GTE
 * MAC1/MAC2/MAC3 accumulators ($25/$26/$27). Frameless leaf.
 */
void SetMAC123(long mac1, long mac2, long mac3)
{
    __asm__ volatile("mtc2 %0, $25" :: "r"(mac1));
    __asm__ volatile("mtc2 %0, $26" :: "r"(mac2));
    __asm__ volatile("mtc2 %0, $27" :: "r"(mac3));
}

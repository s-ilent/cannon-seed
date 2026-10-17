/* Matched 2026-10-18 through the round-trip oracle (g3_jp first;
 * region-pair 100.00% twins across slps_00270, sces_00269, g3_jp,
 * g3_eu, g3org_jp - the matching lane's GTE Set-family cluster).
 *
 * LIBGTE member: mtc2 the argument straight into the GTE IR0 data
 * register ($8). Frameless leaf.
 */
void SetIR0(long ir0)
{
    __asm__ volatile("mtc2 %0, $8" :: "r"(ir0));
}

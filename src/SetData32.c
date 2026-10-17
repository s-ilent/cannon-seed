/* Matched 2026-10-18 through the round-trip oracle (g3_jp first;
 * region-pair 100.00% twins across slps_00270, sces_00269, g3_jp,
 * g3_eu, g3org_jp - the matching lane's GTE Set-family cluster).
 *
 * LIBGTE member: mtc2 the argument straight into the GTE data
 * register $30. Frameless leaf.
 */
void SetData32(long data)
{
    __asm__ volatile("mtc2 %0, $30" :: "r"(data));
}

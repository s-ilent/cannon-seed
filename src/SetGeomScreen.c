/* Matched 2026-10-18 through the round-trip oracle (g3_jp first;
 * region-pair 100.00% twins across slps_00270, sces_00269, g3_jp,
 * g3_eu, g3org_jp - the matching lane's GTE Set-family cluster).
 *
 * LIBGTE member: ctc2 the argument straight into the GTE H (screen
 * height) control register $26. Frameless leaf.
 */
void SetGeomScreen(long h)
{
    __asm__ volatile("ctc2 %0, $26" :: "r"(h));
}

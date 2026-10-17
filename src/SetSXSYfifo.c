/* Matched 2026-10-18 through the round-trip oracle (g3_jp first;
 * region-pair 100.00% twins across slps_00270, sces_00269, g3_jp,
 * g3_eu, g3org_jp - the matching lane's GTE Set-family cluster).
 *
 * LIBGTE member: mtc2 the three arguments straight into the GTE
 * SX/SY/P fifo registers $12/$13/$14. Frameless leaf.
 */
void SetSXSYfifo(long sx, long sy, long p)
{
    __asm__ volatile("mtc2 %0, $12" :: "r"(sx));
    __asm__ volatile("mtc2 %0, $13" :: "r"(sy));
    __asm__ volatile("mtc2 %0, $14" :: "r"(p));
}

/* Matched 2026-10-18 through the round-trip oracle (g3_jp first;
 * region-pair 100.00% twins across slps_00270, sces_00269, g3_jp,
 * g3_eu, g3org_jp - the matching lane's GTE Set-family cluster).
 *
 * LIBGTE member: mtc2 the three depth arguments straight into the GTE
 * SZ1/SZ2/SZ3 fifo registers ($17/$18/$19). Frameless leaf.
 */
void SetSZfifo3(long sz1, long sz2, long sz3)
{
    __asm__ volatile("mtc2 %0, $17" :: "r"(sz1));
    __asm__ volatile("mtc2 %0, $18" :: "r"(sz2));
    __asm__ volatile("mtc2 %0, $19" :: "r"(sz3));
}

/* Matched 2026-10-17 through the round-trip oracle (g3org_jp first;
 * region-pair 100.00% twins across the sdk lanes, see the pair-report
 * matching lane).
 *
 * LIBGTE fifo reader member: dumps GTE data registers SXY0/SXY1/SXY2
 * ($12/$13/$14) to three 32-bit destinations (swc2 stores the full
 * cop2 word; each SXY lane is the packed SY<<16|SX pair).
 */
void ReadSXSYfifo(short *a0, short *a1, short *a2)
{
    __asm__ volatile("swc2 $12, 0x0(%0)" :: "r"(a0));
    __asm__ volatile("swc2 $13, 0x0(%0)" :: "r"(a1));
    __asm__ volatile("swc2 $14, 0x0(%0)" :: "r"(a2));
}

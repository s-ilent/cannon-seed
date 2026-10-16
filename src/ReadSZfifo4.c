/* Matched 2026-10-17 through the round-trip oracle (g3org_jp first;
 * region-pair 100.00% twins across the sdk lanes, see the pair-report
 * matching lane).
 *
 * LIBGTE fifo reader member: dumps GTE data registers SZ0/SZ1/SZ2/SZ3
 * ($16/$17/$18/$19) to four 32-bit destinations (swc2 stores the full
 * cop2 word). Four-arg variant of ReadSZfifo3.
 */
void ReadSZfifo4(short *a0, short *a1, short *a2, short *a3)
{
    __asm__ volatile("swc2 $16, 0x0(%0)" :: "r"(a0));
    __asm__ volatile("swc2 $17, 0x0(%0)" :: "r"(a1));
    __asm__ volatile("swc2 $18, 0x0(%0)" :: "r"(a2));
    __asm__ volatile("swc2 $19, 0x0(%0)" :: "r"(a3));
}

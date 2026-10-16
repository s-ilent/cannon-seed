/* Matched 2026-10-17 through the round-trip oracle (g3org_jp first;
 * region-pair 100.00% twins across the sdk lanes, see the pair-report
 * matching lane).
 *
 * LIBGTE fifo reader member: dumps GTE data registers RGB0/RGB1/RGB2
 * ($20/$21/$22) to three 32-bit destinations (swc2 stores the full
 * cop2 word; each RGB lane is the packed R/G/B/code byte quadruple).
 */
void ReadRGBfifo(short *a0, short *a1, short *a2)
{
    __asm__ volatile("swc2 $20, 0x0(%0)" :: "r"(a0));
    __asm__ volatile("swc2 $21, 0x0(%0)" :: "r"(a1));
    __asm__ volatile("swc2 $22, 0x0(%0)" :: "r"(a2));
}

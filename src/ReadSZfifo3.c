/* Matched 2026-10-17 through the round-trip oracle (g3org_jp first;
 * region-pair 100.00% twins across the sdk lanes, see the pair-report
 * matching lane).
 *
 * LIBGTE fifo reader member: dumps GTE data registers SZ1/SZ2/SZ3
 * ($17/$18/$19) to three 32-bit destinations (swc2 stores the full
 * cop2 word; the fifo lanes carry the packed 16-bit SZ pairs).
 *
 * Inline-asm shape (the cop2 ops are not reachable from plain C):
 * volatile asm keeps the three stores in program order, and the "r"
 * input binds each destination pointer as the swc2 address operand -
 * gcc satisfies it from the incoming argument register, so retail's
 * swc2 $17, 0($a0) form falls out. Frameless leaf; the jr $ra / nop
 * tail is the stock gcc void-return epilogue.
 */
void ReadSZfifo3(short *a0, short *a1, short *a2)
{
    __asm__ volatile("swc2 $17, 0x0(%0)" :: "r"(a0));
    __asm__ volatile("swc2 $18, 0x0(%0)" :: "r"(a1));
    __asm__ volatile("swc2 $19, 0x0(%0)" :: "r"(a2));
}

/* Matched 2026-10-18 through the round-trip oracle (g3org_jp first;
 * region-pair 100.00% twins across g3org_jp/g3org_eu).
 *
 * LIBGTE AverageSZ3: avsz3 (.word 0x4B58002D), mfc2 the SZ-average
 * out of $7, return. The mfc2 destination is a $2 register-var output
 * (the banked RotTransPers4 return law) so the value lands in $v0 for
 * the stock jr $ra / nop epilogue. Frameless leaf.
 */
long AverageSZ3(void)
{
    register long r asm("$2");
    __asm__ volatile(".word 0x4B58002D");
    __asm__ volatile("mfc2 %0, $7" : "=r"(r));
    return r;
}

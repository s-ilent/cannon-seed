/* Matched 2026-10-18 through the round-trip oracle (g3org_jp first;
 * region-pair 100.00% twins across g3org_jp/g3org_eu).
 *
 * LIBGTE AverageSZ4: avsz4 (.word 0x4B68002E), mfc2 the SZ-average
 * out of $7, return. Same $2 register-var output law as AverageSZ3.
 * Frameless leaf.
 */
long AverageSZ4(void)
{
    register long r asm("$2");
    __asm__ volatile(".word 0x4B68002E");
    __asm__ volatile("mfc2 %0, $7" : "=r"(r));
    return r;
}

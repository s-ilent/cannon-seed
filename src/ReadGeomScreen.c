/* Matched 2026-10-17 through the round-trip oracle (g3org_jp first;
 * region-pair 100.00% twins across the sdk lanes, see the pair-report
 * matching lane).
 *
 * LIBGTE reader member: reads the GTE control register H (C26, the
 * projection-plane distance used by the perspective division) with a
 * single cfc2 into $v0, returned directly. Frameless leaf; the jr $ra
 * / nop tail is the stock gcc return epilogue.
 */
long ReadGeomScreen(void)
{
    long h;
    __asm__ volatile("cfc2 %0, $26" : "=r"(h));
    return h;
}

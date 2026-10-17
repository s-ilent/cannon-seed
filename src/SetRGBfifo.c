/* Matched 2026-10-18 through the round-trip oracle (g3_jp first;
 * region-pair 100.00% twins across slps_00270, sces_00269, g3_jp,
 * g3_eu, g3org_jp - the matching lane's GTE Set-family cluster).
 *
 * LIBGTE fifo member: loads three RGB words from the three a0/a1/a2
 * pointers into the GTE R/G-B fifo registers R20/R21/R22. The lwc2
 * bases are r-bound inputs that gcc satisfies from the incoming
 * argument registers (the banked swc2/lwc2-address law): retail's
 * lwc2 $20, 0($a0) form falls out. Frameless leaf; the jr $ra / nop
 * tail is the stock gcc void-return epilogue.
 */
void SetRGBfifo(long *r0, long *g0, long *b0)
{
    __asm__ volatile("lwc2 $20, 0x0(%0)\n\tlwc2 $21, 0x0(%1)\n\tlwc2 $22, 0x0(%2)"
                     :: "r"(r0), "r"(g0), "r"(b0));
}

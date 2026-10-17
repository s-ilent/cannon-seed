/* Matched 2026-10-18 through the round-trip oracle (g3org_jp first;
 * region-pair 100.00% twins across g3org_jp/g3org_eu).
 *
 * LIBGTE DpqColor: lwc2 the colour (IR? = $6) from a0, mtc2 the depth
 * value into $8, nop, dpcs (.word 0x4A780010), swc2 IR3 ($22) out to
 * a2. One volatile block; r-bound inputs satisfied from the dead
 * argument registers. Frameless leaf.
 */
void DpqColor(long *a0, long c, long *a2)
{
    __asm__ volatile("lwc2 $6, 0x0(%0)\n\tmtc2 %1, $8\n\tnop\n\t"
                     ".word 0x4A780010\n\t"
                     "swc2 $22, 0x0(%2)" :: "r"(a0), "r"(c), "r"(a2));
}

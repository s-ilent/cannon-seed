/* Matched 2026-10-18 through the round-trip oracle (g3org_jp first;
 * region-pair 100.00% twins across g3org_jp/g3org_eu).
 *
 * LIBGTE ColorDpq: lwc2 the RGB colour (IR? triple $9/$10/$11) from
 * a0, lwc2 the colour matrix ($6) from a1, mtc2 the depth into $8,
 * nop, cdp (.word 0x4B280414), swc2 IR3 ($22) out to a3. One volatile
 * block; r-bound inputs. Frameless leaf.
 */
void ColorDpq(long *a0, long *a1, long c, long *a3)
{
    __asm__ volatile("lwc2 $9, 0x0(%0)\n\tlwc2 $10, 0x4(%0)\n\tlwc2 $11, 0x8(%0)\n\t"
                     "lwc2 $6, 0x0(%1)\n\tmtc2 %2, $8\n\tnop\n\t"
                     ".word 0x4B280414\n\t"
                     "swc2 $22, 0x0(%3)" :: "r"(a0), "r"(a1), "r"(c), "r"(a3));
}

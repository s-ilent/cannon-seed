/* Matched 2026-10-18 through the round-trip oracle (g3org_jp first;
 * region-pair 100.00% twins across g3org_jp/g3org_eu).
 *
 * LIBGTE NormalColor: lwc2 the normal (VXY0/VZ0 = $0/$1) from a0, nop,
 * ncs (.word 0x4AC8041E), swc2 IR3 ($22) out to a1. One volatile block;
 * r-bound inputs. Frameless leaf.
 */
void NormalColor(long *a0, long *a1)
{
    __asm__ volatile("lwc2 $0, 0x0(%0)\n\tlwc2 $1, 0x4(%0)\n\tnop\n\t"
                     ".word 0x4AC8041E\n\t"
                     "swc2 $22, 0x0(%1)" :: "r"(a0), "r"(a1));
}

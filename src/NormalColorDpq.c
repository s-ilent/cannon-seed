/* Matched 2026-10-18 through the round-trip oracle (g3org_jp first;
 * region-pair 100.00% twins across g3org_jp/g3org_eu).
 *
 * LIBGTE NormalColorDpq: lwc2 the normal ($0/$1) from a0, lwc2 the
 * colour ($6) from a1, mtc2 the depth into $8, nop, ncds (.word
 * 0x4AE80413), swc2 IR3 ($22) out to a3. One volatile block; r-bound
 * inputs. Frameless leaf.
 */
void NormalColorDpq(long *a0, long *a1, long c, long *a3)
{
    __asm__ volatile("lwc2 $0, 0x0(%0)\n\tlwc2 $1, 0x4(%0)\n\t"
                     "lwc2 $6, 0x0(%1)\n\tmtc2 %2, $8\n\tnop\n\t"
                     ".word 0x4AE80413\n\t"
                     "swc2 $22, 0x0(%3)" :: "r"(a0), "r"(a1), "r"(c), "r"(a3));
}

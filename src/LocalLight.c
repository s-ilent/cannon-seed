/* Matched 2026-10-18 through the round-trip oracle (g3org_jp first;
 * region-pair 100.00% twins across g3org_jp/g3org_eu - the matching
 * lane's LightColor-sibling cluster).
 *
 * LIBGTE LocalLight: lwc2 the light vector (VX0/VZ0 = $0/$1) from a0,
 * nop, mvmva 1,1,0,3,1 (as its exact retail .word 0x4A4A6412 - GNU as
 * knows no mvmva mnemonic), then swc2 IR1/IR2/IR3 ($9/$10/$11) out to
 * a1. One volatile block keeps the retail order; the lwc2/swc2 bases
 * are r-bound inputs satisfied from the incoming argument registers.
 * The nop after the loads is literal in the template. Frameless leaf.
 */
void LocalLight(long *a0, long *a1)
{
    __asm__ volatile("lwc2 $0, 0x0(%0)\n\tlwc2 $1, 0x4(%0)\n\tnop\n\t"
                     ".word 0x4A4A6412\n\t"
                     "swc2 $9, 0x0(%1)\n\tswc2 $10, 0x4(%1)\n\tswc2 $11, 0x8(%1)"
                     :: "r"(a0), "r"(a1));
}

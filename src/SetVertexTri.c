/* Matched 2026-10-17 through the round-trip oracle (g3org_jp first;
 * cross-target byte-identical in g3org_jp, g3_jp, g3_eu, slps_00270,
 * sces_00269 - the matching lane's GTE families queue item).
 *
 * LIBGTE SetVertexTri: pushes a whole triangle into the GTE FIFO -
 * three vertices (a0/a1/a2) in six lwc2 loads into VXY0/VZ0 ($0/$1),
 * VXY1/VZ1 ($2/$3), VXY2/VZ2 ($4/$5), then jr. The three lwc2 bases
 * are r-bound inputs gcc satisfies from the incoming argument
 * registers $4-$6 (the banked swc2-address law, read side).
 */
void SetVertexTri(long *a0, long *a1, long *a2)
{
    __asm__ volatile(
        "lwc2 $0, 0(%0)\n\tlwc2 $1, 4(%0)\n"
        "\tlwc2 $2, 0(%1)\n\tlwc2 $3, 4(%1)\n"
        "\tlwc2 $4, 0(%2)\n\tlwc2 $5, 4(%2)"
        :: "r"(a0), "r"(a1), "r"(a2));
}

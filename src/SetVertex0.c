/* Matched 2026-10-17 through the round-trip oracle (g3org_jp first;
 * cross-target byte-identical in g3org_jp, g3_jp, g3_eu, slps_00270,
 * sces_00269 - the matching lane's GTE families queue item).
 *
 * LIBGTE SetVertex0: pushes one vertex into the GTE FIFO - two lwc2
 * loads from the a0 struct into VXY0 ($0) and VZ0 ($1). The lwc2 base
 * is an r-bound input that gcc satisfies from the incoming argument
 * register (the banked swc2-address law, read side): retail's
 * lwc2 $0, 0($a0) form falls out.
 */
void SetVertex0(long *a0)
{
    __asm__ volatile("lwc2 $0, 0(%0)\n\tlwc2 $1, 4(%0)" :: "r"(a0));
}

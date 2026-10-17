/* Matched 2026-10-17 through the round-trip oracle (g3org_jp first;
 * cross-target byte-identical in g3org_jp, g3_jp, g3_eu, slps_00270,
 * sces_00269 - the matching lane's GTE families queue item).
 *
 * LIBGTE SetVertex1: SetVertex0's second-slot twin - the a0 struct's
 * two words load into VXY1 ($2) and VZ1 ($3).
 */
void SetVertex1(long *a0)
{
    __asm__ volatile("lwc2 $2, 0(%0)\n\tlwc2 $3, 4(%0)" :: "r"(a0));
}

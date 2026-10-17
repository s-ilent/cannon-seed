/* Matched 2026-10-17 through the round-trip oracle (g3org_jp first;
 * cross-target byte-identical in g3org_jp, g3_jp, g3_eu, slps_00270,
 * sces_00269 - the matching lane's GTE families queue item).
 *
 * LIBGTE SetVertex2: SetVertex0's third-slot twin - the a0 struct's
 * two words load into VXY2 ($4) and VZ2 ($5).
 */
void SetVertex2(long *a0)
{
    __asm__ volatile("lwc2 $4, 0(%0)\n\tlwc2 $5, 4(%0)" :: "r"(a0));
}

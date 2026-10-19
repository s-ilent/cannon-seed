/* Matched 2026-10-11 through the round-trip oracle (g3_eu).
 *
 * Empty function: bare `jr $ra; nop` (0x8 bytes). GCC 2.6.3 -O2 emits
 * exactly this for an empty void body - no frame, no prologue, one nop
 * in the jump delay slot. Mirror of the g3_jp match at 0x800629A0; the
 * two targets carry the same compiled source shape under different
 * per-target auto names.
 *
 * Carve-name rename completed 2026-10-20 (the b51807e6 jp law): the
 * row's woven name (the 0x80062280-encoded auto name) stays with the
 * false-positive split detection inside data_8006AAF4 (the slps law -
 * the encoded name is kept by the data row's dlabel at 0x80062280);
 * the C row takes its carve name (name==VMA self-consistency, yaml
 * offset 0x3A0C0). The 7429c736 commit carried the file rename without
 * the function rename - the fresh-sandbox build exposed the missing
 * half as a multiple-definition of the woven name against the data
 * row's dlabel.
 */
void func_800598C0(void)
{
}

/* Matched 2026-10-11 through the round-trip oracle (g3_eu).
 *
 * Empty function: bare `jr $ra; nop` (0x8 bytes). GCC 2.6.3 -O2 emits
 * exactly this for an empty void body - no frame, no prologue, one nop
 * in the jump delay slot. Mirror of the g3_jp match at 0x800629A0; the
 * two targets carry the same compiled source shape under different
 * per-target auto names.
 */
void func_80062280(void)
{
}

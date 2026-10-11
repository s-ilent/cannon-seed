/* Matched 2026-10-11 through the round-trip oracle (g3_jp).
 *
 * Empty function: bare `jr $ra; nop` (0x8 bytes). GCC 2.6.3 -O2 emits
 * exactly this for an empty void body - no frame, no prologue, one nop
 * in the jump delay slot. First C-matched function in g3_jp; the g3_eu
 * counterpart at 0x80062280 is matched the same way (same compiled
 * source shape, different per-target auto name).
 */
void func_800629A0(void)
{
}

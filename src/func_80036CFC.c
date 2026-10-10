/* First C function matched through the round-trip oracle (2026-10-10).
 * Retail body is exactly `jr $ra; nop`: an empty void function. The
 * generated disassembly (asm/nonmatchings/<this name>.s) was deleted at
 * match time; the splat subsegment switched from `asm` to `c`.
 *
 * The original symbol name is not yet identified — the auto-generated
 * address name stands (counted by the unknown_function ratchet).
 */
void func_80036CFC(void)
{
}

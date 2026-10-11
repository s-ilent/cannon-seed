/* Matched 2026-10-11 through the round-trip oracle (mainmenu_jp).
 *
 * Trivial getter: returns its fourth argument unchanged. GCC 2.6.3 -O2
 * shape: `addu $v0, $a3, $zero` (move) + `jr $ra` with a nop delay slot,
 * no frame. First C-matched function in mainmenu_jp.
 */
int func_800791A4(int a, int b, int c, int d)
{
    return d;
}

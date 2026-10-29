/* wave0C - the x8 own-row wave at size 0xC (the eighteenth return's phase F
 * item; the census sha b5f14db96e53). One src unit per row under the row's
 * own walk name; seven byte-identical own-row members, one per game target
 * except mainmenu_jp (whose member is a parent-bound interior, not carvable
 * alone - the census's classification; cross-target identities live in the
 * yaml, the symbols file and the landing commit, not repeated here: the
 * headers name no siblings).
 *
 * Decode (twenty-second window, offline): a halfword-load thunk - reads the
 * u16 at (a0) zero-extended into $v0 and returns it. lhu $v0,0($a0); jr $ra;
 * nop. Zero relocations: no jals, no lui, no gp-relative, no cop2 - one
 * decode lands all seven own-row members.
 *
 * psyq reading: an sdk/getter-class accessor (lhu = the u16 memory read;
 * zero-extend into the full return register). No psyq pin exists anywhere -
 * the units land under their walk names (row-name==unit-name law).
 */
int func_8005E648(unsigned short *a0)
{
    return *a0;
}

/* wave0C - the x8 own-row wave at size 0xC (the eighteenth return's phase F
 * item; the census sha b5f14db96e53). Seven own-row members, one per game
 * target except mainmenu_jp (whose member is the parent-bound interior at
 * func_8007FFAC +0x1BC): slps func_80037BF4, sces func_800377A8,
 * mainmenu_eu func_80074100, g3_jp func_8005E648, g3_eu func_8005ED98,
 * g3org_jp func_8005BAE4, g3org_eu func_8005C1EC.
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
int wave0C(unsigned short *a0)
{
    return *a0;
}

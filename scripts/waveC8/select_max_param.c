/* select_max_param - LIBGS MATRIX3 member, x8 byte-identical own-row wave
 * (0xC8, one member per target; the census's seventeenth-return item 3).
 * Identities: slps func_80036D04, sces func_8003384C, mainmenu_jp func_8006E9BC,
 * mainmenu_eu func_80064010, g3_jp func_800501F8, g3_eu func_8004FB34,
 * g3org_jp func_800542A4, g3org_eu func_8004CF88. Three targets pin the psyq
 * name in symbols (slps/g3org_jp/mainmenu_jp, "pinned member row"); five sit
 * under walk names. Sits between scale_view_param (0xF0) and len_param (0x1C)
 * in every target - the SDK's own MATRIX3 view cluster.
 *
 * Decode (twentieth window, offline cron-202610291140): the max-of-abs
 * selector - reads seven words at (a0)[0..6] and returns the largest
 * absolute value, the bgez/negu abs idiom per member (the twin-island
 * helper's shape at loop scale). Register shape: running max lives in $a1
 * (the dead second arg reg), the loaded word in $v0, the abs'd candidate
 * in $v1 - round p0 stages max = a in the bgez DELAY SLOT, round p1 is
 * single-register (loaded straight into its live reg, nop-filled slot),
 * rounds p2..p6 copy load->candidate in the delay slot (addu $v1,$v0,$zero)
 * and reuse $v0 as the slt destination. Return fills the jr delay slot
 * with the $v0 move (addu $v0,$a1,$zero) - the keep-return-fill class.
 * Zero relocations: no jals, no lui, no gp-relative, no cop2 - a pure ALU
 * leaf, one decode lands all eight.
 *
 * psyq prototype: int select_max_param(int *param); $4 = param,
 * returns $2 = max(|param[0..6]|).
 *
 * cc-post: keep-return-fill (retail fills the return jump's delay slot
 * with the $v0 move - the Square0/Square12 class; gcc's own output is
 * already the filled [j $31][move $2,$5] form and rule 3's default
 * un-fill must not fire).
 */
int select_max_param(int *param)
{
    int max = param[0] < 0 ? -param[0] : param[0];
    int b;
    if (max < (b = (param[1] < 0 ? -param[1] : param[1]))) max = b;
    if (max < (b = (param[2] < 0 ? -param[2] : param[2]))) max = b;
    if (max < (b = (param[3] < 0 ? -param[3] : param[3]))) max = b;
    if (max < (b = (param[4] < 0 ? -param[4] : param[4]))) max = b;
    if (max < (b = (param[5] < 0 ? -param[5] : param[5]))) max = b;
    return max;
}

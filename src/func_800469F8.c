/* Landed 2026-10-25 (window cron-20261025-0321) - the 0x4B pair family,
 * the palette-fade wrapper one-src-many-targets class. This is g3_jp's
 * 0x4B member: its word stream is the landed mainmenu_eu reference
 * src/func_8005AC68.c verbatim (12 words; jal w6, const w7), the only
 * per-target delta being the callee (g3_jp's helper func_80044614 - the
 * same callee the landed g3_jp twin src/func_80046BC4.c spells).
 *
 * Census site (build/invariant_census.txt, fresh oracle 2026-10-24):
 * g3_jp 0x800469F8 = raw 0x271F8, the interior sub-block +0x1EAC of the
 * walk row func_80044B4C (#0x2078). Oracle-proven word-identical to the
 * reference with the const slot 3406004B (probe_0x4B_sites.py).
 *
 * LANDING RECIPE (D-MID-ROW cut, SetColorMatrix class): split the row at
 * +0x1EAC; new c row [0x271F8, c, func_800469F8] # 0x30; the tail
 * re-homes as [0x27228, asm, func_80046A28] # 0x19C on the row's own
 * interior glabel. Zero renames: the row's callers already spell
 * func_800469F8. Then make verify TARGET=g3_jp.
 */
extern void func_80044614(short, short, short);

void func_800469F8(short x, short y)
{
    func_80044614(x, y, 0x4B);
}

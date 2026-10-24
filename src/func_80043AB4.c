/* Landed 2026-10-25 (window cron-20261025-0321) - the 0x4B pair family,
 * the palette-fade wrapper one-src-many-targets class. This is g3org_eu's
 * 0x4B member: its word stream is the landed mainmenu_eu reference
 * src/func_8005AC68.c verbatim (12 words; jal w6, const w7), the only
 * per-target delta being the callee (g3org_eu's helper func_800416D0 -
 * the same callee the landed g3org_eu twin src/func_80043C80.c spells).
 *
 * Census site (build/invariant_census.txt, fresh oracle 2026-10-24):
 * g3org_eu 0x80043AB4 = raw 0x242B4, the interior sub-block +0x1EAC of
 * the walk row func_80041C08 (#0x2078). Oracle-proven word-identical to
 * the reference with the const slot 3406004B (probe_0x4B_sites.py).
 *
 * LANDING RECIPE (D-MID-ROW cut, SetColorMatrix class): split the row at
 * +0x1EAC; new c row [0x242B4, c, func_80043AB4] # 0x30; the tail
 * re-homes as [0x242E4, asm, func_80043AE4] # 0x19C on the row's own
 * interior glabel. Zero renames: the row's callers already spell
 * func_80043AB4. Then make verify TARGET=g3org_eu.
 */
extern void func_800416D0(short, short, short);

void func_80043AB4(short x, short y)
{
    func_800416D0(x, y, 0x4B);
}

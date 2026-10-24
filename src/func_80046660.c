/* Landed 2026-10-25 (window cron-20261025-0321) - the 0x4B pair family,
 * the palette-fade wrapper one-src-many-targets class. This is g3_eu's
 * 0x4B member: its word stream is the landed mainmenu_eu reference
 * src/func_8005AC68.c verbatim (12 words; jal w6, const w7), the only
 * per-target delta being the callee (g3_eu's helper func_8004427C where
 * mainmenu_eu spells func_80058884).
 *
 * Census site (build/invariant_census.txt, fresh oracle 2026-10-24):
 * g3_eu 0x80046660 = raw 0x26E60, the interior sub-block +0x1EAC of the
 * walk row func_800447B4 (#0x2078) - the same +0x1EAC interior layout
 * mainmenu_eu's func_80058DBC carries. Oracle-proven word-identical to
 * the reference with the const slot 3406004B (probe_0x4B_sites.py).
 *
 * LANDING RECIPE (D-MID-ROW cut, SetColorMatrix class): split the row at
 * +0x1EAC; new c row [0x26E60, c, func_80046660] # 0x30; the tail
 * re-homes as [0x26E90, asm, func_80046690] # 0x19C on the row's own
 * interior glabel. Zero renames: the row's callers already spell
 * func_80046660. Then make verify TARGET=g3_eu. g3_eu's 0x17 sibling
 * needs no cut (already landed inside src/func_8004C4CC.c as its
 * func_8004C508 member).
 */
extern void func_8004427C(short, short, short);

void func_80046660(short x, short y)
{
    func_8004427C(x, y, 0x4B);
}

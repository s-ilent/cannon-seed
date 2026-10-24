/* Landed 2026-10-25 (window cron-20261025-0321) - the 0x4B pair family,
 * the palette-fade wrapper one-src-many-targets class. This is g3_jp's
 * 0x17 member: its word stream is the landed mainmenu_eu reference
 * src/func_8005AE70.c verbatim (12 words; jal w6, const w7 = 34060017),
 * the only per-target delta being the callee (g3_jp's helper
 * func_80044614). g3_eu's copy of this shape is already landed inside
 * src/func_8004C4CC.c (its func_8004C508 member) - this file lands the
 * next three carvable copies of the pair's second half.
 *
 * Census site (build/invariant_census.txt, fresh oracle 2026-10-24):
 * g3_jp 0x80046C00 = raw 0x27400 - EXPOSED TAIL-ROW HEAD: the six-twin
 * wave's cut (d5d6c043) re-homed this row from func_80044B4C's tail, so
 * the wrapper sits at the row's own head (+0x0 of #0x131C).
 * Oracle-proven word-identical to the reference (probe_0x4B_sites.py).
 *
 * LANDING RECIPE (head-flip + tail re-home, the quartet's cut class):
 * the c row takes the yaml row's name (zero renames - the row name IS
 * the extract's default label): [0x27400, c, func_80046C00] # 0x30; the
 * tail re-homes as [0x27430, asm, func_80046C30] # 0x12EC on the row's
 * own interior glabel. Then make verify TARGET=g3_jp.
 */
extern void func_80044614(short, short, short);

void func_80046C00(short x, short y)
{
    func_80044614(x, y, 0x17);
}

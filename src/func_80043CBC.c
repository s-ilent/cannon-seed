/* Landed 2026-10-25 (window cron-20261025-0321) - the 0x4B pair family,
 * the palette-fade wrapper one-src-many-targets class. This is g3org_eu's
 * 0x17 member: its word stream is the landed mainmenu_eu reference
 * src/func_8005AE70.c verbatim (12 words; jal w6, const w7 = 34060017),
 * the only per-target delta being the callee (g3org_eu's helper
 * func_800416D0).
 *
 * Census site (build/invariant_census.txt, fresh oracle 2026-10-24):
 * g3org_eu 0x80043CBC = raw 0x244BC - EXPOSED TAIL-ROW HEAD: the six-twin
 * wave's cut (d5d6c043) re-homed this row from func_80041C08's tail, so
 * the wrapper sits at the row's own head (+0x0 of #0x131C).
 * Oracle-proven word-identical to the reference (probe_0x4B_sites.py).
 *
 * LANDING RECIPE (head-flip + tail re-home, the quartet's cut class):
 * the c row takes the yaml row's name (zero renames - the row name IS
 * the extract's default label): [0x244BC, c, func_80043CBC] # 0x30; the
 * tail re-homes as [0x244EC, asm, func_80043CEC] # 0x12EC on the row's
 * own interior glabel. Then make verify TARGET=g3org_eu.
 */
extern void func_800416D0(short, short, short);

void func_80043CBC(short x, short y)
{
    func_800416D0(x, y, 0x17);
}

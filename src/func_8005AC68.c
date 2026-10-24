/* Staged 2026-10-24 (window cron-20261024-1502, offline) - palette-fade
 * wrapper family member for mainmenu_eu, staged from the sibling-finder
 * sweep's third proposal (docs/TASKS.md, d6d87685):
 *
 *   mainmenu_eu 0x8005AC68 <- g3_eu/func_8004C508 +0x30  score 0.97
 *
 * The census candidate is the interior sub-block `func_8005AC68, 0x30` of
 * mainmenu_eu's unlanded walk row func_80058DBC.s. Its word stream is the
 * second wrapper's SHAPE (src/func_8004C4CC.c's func_8004C508 member) with
 * a NEW third-argument constant: 0x4B, not 0x17 - a FIFTH member of the
 * family the landed g3_eu row does not carry (g3_eu has 0x14, 0x17 and the
 * two two-call wrappers). The 0.97 score is the scorer's immediate-overlap
 * term reading the different constant; the instruction stream is the same
 * twelve words. The identical body also sits in g3org_jp at 0x80043E94
 * (staged as src/func_80043E94.c) - one C-source shape, two targets, the
 * NormalColor3 one-src-many-targets class; only the callee extern differs
 * per target (here func_80058884, there func_80041AB0).
 *
 * LANDING RECIPE (mainmenu_eu, D-MID-ROW two-cut split, SetColorMatrix
 * class): the body sits +0x1EAC into func_80058DBC's file range (raw
 * 0x3B468, extent 0x30). Split the row at the body; new c row
 * [raw 0x3B468, c, func_8005AC68] # 0x30. Zero renames: the row's own
 * callers already spell func_8005AC68 (jal sites 0x8005A910 / 0x8005A9B8 /
 * 0x8005AC10). Then make verify TARGET=mainmenu_eu + ratchet audit.
 * Build-inert until the yaml flip.
 */
extern void func_80058884(short, short, short);

void func_8005AC68(short x, short y)
{
    func_80058884(x, y, 0x4B);
}

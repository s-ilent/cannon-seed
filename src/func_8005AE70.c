/* Staged 2026-10-24 (window cron-20261024-1502, offline) - palette-fade
 * wrapper family member for mainmenu_eu, staged from the sibling-finder
 * sweep's second proposal (docs/TASKS.md, d6d87685):
 *
 *   mainmenu_eu 0x8005AE70 <- g3_eu/func_8004C508 +0x30  score 0.97
 *
 * The census candidate is the interior sub-block `func_8005AE70, 0x30` of
 * mainmenu_eu's unlanded walk row func_80058DBC.s. Its word stream is the
 * SECOND wrapper of the landed g3_eu row func_8004C4CC
 * (src/func_8004C4CC.c, the func_8004C508 member) verbatim - plain
 * short extends, the 0x17 third argument - with the one expected
 * per-target delta: the callee is mainmenu_eu's helper func_80058884
 * where g3_eu's copy calls func_8004427C. The 0.97 (vs the first
 * wrapper's 0.99) is the scorer's immediate-overlap term reading the
 * different third-argument constants across proposals, not a shape
 * delta: the instruction stream is the same twelve words.
 *
 * LANDING RECIPE (mainmenu_eu, D-MID-ROW two-cut split, SetColorMatrix
 * class): the body sits +0x20B4 into func_80058DBC's file range (raw
 * 0x3B670, extent 0x30). Split the row at the body; new c row
 * [raw 0x3B670, c, func_8005AE70] # 0x30. Zero renames: the row's own
 * callers already spell func_8005AE70 (jal sites 0x8005A964 / 0x8005A9F4).
 * Then make verify TARGET=mainmenu_eu + ratchet audit. Build-inert until
 * the yaml flip.
 */
extern void func_80058884(short, short, short);

void func_8005AE70(short x, short y)
{
    func_80058884(x, y, 0x17);
}

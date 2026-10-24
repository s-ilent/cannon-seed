/* Staged 2026-10-24 (window cron-20261024-1502, offline) - palette-fade
 * wrapper family member for g3org_jp, staged from the sibling-finder
 * sweep's fourth proposal (docs/TASKS.md, d6d87685):
 *
 *   g3org_jp 0x80043E94 <- g3_eu/func_8004C508 +0x30  score 0.97
 *
 * The census candidate is the interior sub-block `func_80043E94, 0x30` of
 * g3org_jp's unlanded walk row func_80042DEC.s. Its word stream is the
 * second wrapper's SHAPE (src/func_8004C4CC.c's func_8004C508 member) with
 * the NEW third-argument constant 0x4B - the SAME new member as
 * mainmenu_eu's func_8005AC68 (src/func_8005AC68.c): one C-source shape,
 * two targets, the NormalColor3 one-src-many-targets class. Only the
 * callee extern differs per target: here g3org_jp's helper func_80041AB0
 * (unlanded, glabels in func_80046AA0.s / func_80034BA8.s), in mainmenu_eu
 * func_80058884, in g3_eu func_8004427C.
 *
 * LANDING RECIPE (g3org_jp, D-MID-ROW two-cut split, SetColorMatrix
 * class): the body sits +0x10A8 into func_80042DEC's file range (raw
 * 0x24694, extent 0x30). Split the row at the body; new c row
 * [raw 0x24694, c, func_80043E94] # 0x30; the head keeps the yaml name
 * func_80042DEC and the tail re-homes as a fresh asm row named by its
 * TRUE VA. Zero renames. Then make verify TARGET=g3org_jp + ratchet
 * audit. Build-inert until the yaml flip.
 */
extern void func_80041AB0(short, short, short);

void func_80043E94(short x, short y)
{
    func_80041AB0(x, y, 0x4B);
}

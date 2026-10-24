/* Staged 2026-10-24 (window cron-20261024-1502, offline) - palette-fade
 * wrapper family member for mainmenu_eu, staged from the sibling-finder
 * sweep's strongest proposal (docs/TASKS.md, d6d87685):
 *
 *   mainmenu_eu 0x8005AE34 <- g3_eu/func_8004C4CC +0x3C  score 0.99 EXACT
 *
 * The census candidate is the interior sub-block `func_8005AE34, 0x3C` of
 * mainmenu_eu's unlanded walk row func_80058DBC.s, called three times from
 * the same row (jal sites 0x8005A944 / 0x8005A9D4 / 0x8005ABFC). Its word
 * stream is the FIRST wrapper of the landed g3_eu row func_8004C4CC
 * (src/func_8004C4CC.c) verbatim - the *4-fold extend (sll 16 / sra 14),
 * the +0x100, the 0x14 third argument - with the one expected per-target
 * delta: the callee is mainmenu_eu's helper func_80058884 (unlanded, its
 * glabel lives in func_800459D4.s) where g3_eu's copy calls func_8004427C.
 *
 * The row's own header note (src/func_8004C4CC.c) documents the shaping
 * law this copy shares: void wrappers (return discarded), old-ABI short
 * extends at entry, positive 16-bit immediates load with ori in the jal
 * delay slot, epilogue lw $ra + nop + jr $ra with the frame release in
 * the delay slot.
 *
 * LANDING RECIPE (mainmenu_eu, D-MID-ROW two-cut split, SetColorMatrix
 * class): the body sits +0x2078 into func_80058DBC's file range (raw
 * 0x3B634, extent 0x3C). Split the row at the body: head row keeps the
 * yaml name func_80058DBC, new c row [raw 0x3B634, c, func_8005AE34]
 * # 0x3c, tail row re-homed as a fresh asm row named by its TRUE VA
 * (0x8005AE70's block boundary - the next sub-block start). Zero renames:
 * every caller already spells func_8005AE34. Then make verify
 * TARGET=mainmenu_eu + ratchet audit. Build-inert until the yaml flip
 * (build.sh compiles src/<row>.c only for targets whose yaml lists it).
 */
extern void func_80058884(short, short, short);

void func_8005AE34(short x, short y)
{
    func_80058884((short)(x * 4 + 0x100), y, 0x14);
}

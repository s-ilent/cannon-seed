/* Landed 2026-10-24 (window cron-20261024-1812) - palette-fade wrapper
 * family member for g3org_jp, landed from the census re-derivation's
 * six-twin wave (build/invariant_census.txt on the fresh disc-return
 * oracle): func_8005AE34's shape carries six instances, one per game
 * module; this is the g3org_jp copy (word-eq 14/15, votes 6).
 *
 * The census candidate is the interior sub-block `func_80044060, 0x3C`
 * of the re-homed tail row func_80043EC4 (yaml 0x246C4 # 0x14f4, cut
 * out of func_80042DEC by the quartet landing): the tail's first 0x19C
 * bytes are the same block mainmenu_eu spells func_8005AC98, this body
 * sits at +0x19C, the func_8005AE70-shape wrapper follows at +0x1D8.
 * Its word stream is the landed mainmenu_eu wrapper
 * (src/func_8005AE34.c) verbatim - the *4-fold extend (sll 16 /
 * sra 14), the +0x100, the 0x14 third argument - with the one expected
 * per-target delta: the jal slot, which names this target's own helper
 * func_80041AB0 (the same callee the landed src/func_80043E94.c
 * externs) where mainmenu_eu's copy calls func_80058884.
 *
 * LANDING RECIPE (g3org_jp, one-cut split at the body, the quartet
 * class): split the row at +0x19C; head row keeps the yaml name
 * func_80043EC4 (0x19c), new c row [0x24860, c, func_80044060] # 0x3c,
 * tail row re-homed as a fresh asm row named by its TRUE VA (the next
 * sub-block start, 0x8004409C - the func_8005AE70-shape twin the census
 * also carries). Zero renames: the trees already spell every name. Then
 * make verify TARGET=g3org_jp + ratchet audit.
 */
extern void func_80041AB0(short, short, short);

void func_80044060(short x, short y)
{
    func_80041AB0((short)(x * 4 + 0x100), y, 0x14);
}

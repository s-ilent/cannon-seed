/* Landed 2026-10-24 (window cron-20261024-1812) - palette-fade wrapper
 * family member for g3org_eu, landed from the census re-derivation's
 * six-twin wave (build/invariant_census.txt on the fresh disc-return
 * oracle): func_8005AE34's shape carries six instances, one per game
 * module; this is the g3org_eu copy (word-eq 14/15, votes 6).
 *
 * The census candidate is the interior sub-block `func_80043C80, 0x3C`
 * of g3org_eu's walk row func_80041C08 (yaml 0x22408 # 0x33d0), the
 * near-twin of g3_jp's func_80044B4C and mainmenu_eu's func_80058DBC:
 * the 0x30 wrapper at +0x1EAC, the 0x19C block at +0x1EDC, this body at
 * +0x2078, the 0x30 wrapper at +0x20B4. Its word stream is the landed
 * mainmenu_eu wrapper (src/func_8005AE34.c) verbatim - the *4-fold
 * extend (sll 16 / sra 14), the +0x100, the 0x14 third argument - with
 * the one expected per-target delta: the jal slot, which names this
 * target's own helper func_800416D0 (glabel in func_800347C8.s) where
 * mainmenu_eu's copy calls func_80058884.
 *
 * LANDING RECIPE (g3org_eu, one-cut split at the body, the quartet
 * class): split the row at +0x2078; head row keeps the yaml name
 * func_80041C08 (0x2078), new c row [0x24480, c, func_80043C80] # 0x3c,
 * tail row re-homed as a fresh asm row named by its TRUE VA (the next
 * sub-block start, 0x80043CBC - the func_8005AE70-shape twin the census
 * also carries). Zero renames: the trees already spell every name. Then
 * make verify TARGET=g3org_eu + ratchet audit.
 */
extern void func_800416D0(short, short, short);

void func_80043C80(short x, short y)
{
    func_800416D0((short)(x * 4 + 0x100), y, 0x14);
}

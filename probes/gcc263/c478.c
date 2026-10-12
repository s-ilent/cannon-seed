/* Probe: func_8002C478 (mainmenu_jp, 0x8002C478..0x8002C608).
 * Compiled with tools/cc.sh -S; word-diffed against the retail bytes in
 * asm/mainmenu_jp/nonmatchings/func_8002C220.s (glabel func_8002C478).
 * Not part of any build target; lives here as matching evidence for the
 * first family-C component (docs/FABRIC.md machinery session).
 *
 * STATUS 2026-10-12 (probed, not landed as a C row):
 * - Prologue and epilogue are RETAIL-EXACT through the pipeline:
 *   [lw v0,0x3D8(gp)][addiu sp,-0x20][sw ra][sw s1][beqz (sw s0 delay)]
 *   and [lw ra][lw s1][lw s0][jr ra (addiu sp delay)]. The epilogue
 *   needed cc_post rule 1's three-load variant; the prologue needed
 *   rule 7 (leading-load hoist) plus a schedulable (non-volatile) asm
 *   load so cc1's own reorg fills the beqz delay with the s0 spill.
 * - The literal-offset gp asm words are byte-exact (8f8203d8, 8f851048,
 *   8f861050, af8003d8): the runtime gp base is still unmeasured, so
 *   the four accesses are emitted as offsets, not symbols.
 * - OPEN GAP (the only divergence class left): GCC folds the constant
 *   pointer s0 = &D_80089440 - the *s0 store becomes an at-pair and
 *   (int)s0 - 0x40 folds to absolute lui/addiu pairs, while retail
 *   materializes s0 (lui/addiu) and stores/adds through the register.
 *   The retail source must have held s0 opaquely; a C-89 source shape
 *   that reproduces that without extra insns is the remaining matching
 *   question before this function can land as src/func_8002C478.c.
 *
 * Shaping notes:
 * - r_v0 pins $2: retail reads the flag into $v0 and later materializes
 *   &D_800899D8 in $v0 for the D_800899C0 store. A file-scope register
 *   variable reserves $2 for those exact uses; $2 is call-clobbered per
 *   ABI, so calls still clobber it normally.
 * - s1/s0 are ordinary long-lived locals; the prologue saves them (the
 *   s0 save lands in the beqz delay slot exactly as retail).
 * - The tail jump out of the equal-path (j .L8002ABD4) is a hand-asm
 *   sibling jump: the target is a mid-function label of another row,
 *   unnameable from C; build.sh's two-pass auto-definition resolves it
 *   and maspsx's reorder-mode branch nop supplies the delay slot.
 */

extern int D_80089328;
extern int D_80089368;
extern int D_80089400;
extern int D_80089440;
extern int D_80089444;
extern int D_80089448;
extern int D_8008944C;
extern int D_800896F8;
extern int D_80089738;
extern int D_80089778;
extern int D_800897B8;
extern int D_800897F8;
extern int D_80089838;
extern int D_80089A48;
extern int D_800899C0;
extern int D_800899D8;
extern int D_800C9B3C;
extern int D_800C9B44;
extern void func_800267C8(int, int, int);
extern void func_80026784(int);
extern void func_80026414(int, int, int);
extern int func_80035A78(int);

register int r_v0 asm("$2");

void func_8002C478(void)
{
    int s1;
    int *s0;

    __asm__("lw %0,0x3D8($gp)" : "=r"(r_v0));
    if (r_v0 != 0) {
        func_800267C8((int)&D_80089400, (int)&D_800C9B3C, (int)&D_800C9B44);
        __asm__ volatile("sw $0,0x3D8($gp)");
    }
    __asm__ volatile("lw $5,0x1048($gp)");
    __asm__ volatile("lw $6,0x1050($gp)");
    func_80026784((int)&D_80089400);
    s1 = -1;
    s0 = &D_80089440;
    *s0 = s1;
    D_80089444 = s1;
    D_80089448 = s1;
    D_8008944C = s1;
    func_80026414((int)&D_80089328, 0, -1);
    func_80026414((int)&D_80089368, 0, -1);
    func_80026414((int)s0 - 0x40, 0, -1);
    func_80026414((int)&D_80089A48, 0, 0);
    func_80026414((int)&D_800896F8, 0, 0);
    func_80026414((int)&D_80089738, 0, 0);
    func_80026414((int)&D_80089778, 0, 0);
    func_80026414((int)&D_800897B8, 0, 0);
    func_80026414((int)&D_800897F8, 0, 0);
    func_80026414((int)&D_80089838, 0, 0);
    func_80026414((int)s0 - 0x40, 2, -1);
    if (func_80035A78(0xC) == s1) {
        r_v0 = (int)&D_800899D8;
        D_800899C0 = r_v0;
        __asm__ volatile("j .L8002ABD4");
    }
    D_800899C0 = s1;
}

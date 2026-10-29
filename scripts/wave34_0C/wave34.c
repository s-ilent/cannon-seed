/* wave34 - the x8 own-row wave at size 0x34 (the eighteenth return's phase F
 * item; the census sha 0e4f6b4412ab). Seven own-row members, one per game
 * target except mainmenu_jp (whose member is the parent-bound interior at
 * func_80085B5C +0x168): slps func_8003C8F8, sces func_8003C6EC,
 * mainmenu_eu func_800792C0, g3_jp func_8006334C, g3_eu func_80063CDC,
 * g3org_jp func_800607E8, g3org_eu func_80061130.
 *
 * Decode (twenty-second window, offline): a word-copy loop over u32 units -
 * copy n words from (a1) to (a0), pointer walks + an up-counter against the
 * unsigned third arg (sltu, the loop-inverted form: beqz a2 guard at top,
 * bnez at bottom). Loop schedule: lw first, src++ next, counter++ next, sw,
 * sltu, bnez, dst++ in the branch delay slot. Zero relocations: no jals,
 * no lui, no gp-relative, no cop2 - one decode lands all seven own-row
 * members.
 *
 * OPEN SHAPE QUESTION (honest, first iteration): the dead 8-byte frame
 * (addiu sp,-8 / addiu sp,8, nothing stored, no ra save) - gcc 2.6.3 does
 * not normally allocate unused frames; the memmove five-clause evidence
 * chain flagged exactly this shape. If no C spelling reproduces the frame,
 * the landing falls back to the banked hand-asm shape (the func_80031ABC
 * precedent, the wave88 surgery): bare file-scope __asm__, .globl + label
 * under each row's walk name.
 *
 * psyq reading: a libc/kernel-class word copier (the memmove family's
 * forward sibling). No psyq pin exists anywhere - the units land under
 * their walk names (row-name==unit-name law).
 */
void wave34(unsigned int *dst, unsigned int *src, unsigned int n)
{
    unsigned int i;
    for (i = 0; i < n; i++) {
        *dst++ = *src++;
    }
}

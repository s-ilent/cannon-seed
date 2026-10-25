/* Matched 2026-10-26 through the judge oracle (the pair-pool's second
 * harvest wave; 100.00% byte twins across the g3_jp/g3_eu region pair
 * while both sides were still asm: file offsets 0x32284 g3_jp, 0x31BC0
 * g3_eu - the 0x28 sdk rows at the pinned LIBGTE member addresses).
 *
 * LIBGTE Square12: the Square0 twin with the SQR command's sf bit set
 * (0x4AA80428 vs 0x4AA00428 - the single differing word of the pair).
 * Loads the three-longword vector (a0) into the IR registers
 * ($9/$10/$11), one scheduler nop, runs SQR sf=1, stores
 * MAC1/MAC2/MAC3 ($25/$26/$27) through the output pointer (a1), and
 * returns the output pointer through the stock jr $ra with the
 * addu $v0,$a1,$zero move riding the delay slot.
 *
 * psyq prototype: long *Square12(long *v, long *out); args stay long*
 * so gcc emits no caller-side extensions. The returned out pointer
 * rides the jr delay slot through the banked $2 register-var pattern
 * (the RotTransPers law): the assignment after the volatile block is
 * plain C on the $2 register var, and gcc's filler parks it in the
 * return's delay slot exactly as retail. One volatile asm block with
 * the retail register assignments hardcoded (the cop2 ops are not
 * reachable from plain C - the OuterProduct12 precedent).
 *
 * RETURN-FILL TAIL (`cc-post: keep-return-fill` marker): retail fills
 * the return jump's delay slot with the out-pointer move - the
 * opposite of the landed `return d;` getter class that keeps the move
 * before the jump; the marker skips cc_post's rule-3 un-fill so the
 * gcc-filled tail survives to the .o byte for byte.
 */
long *Square12(long *a0, long *a1)
{
    register long *vv asm("$2");
    __asm__ volatile(
        "lwc2 $9, 0x0($4)\n"
        "\tlwc2 $10, 0x4($4)\n"
        "\tlwc2 $11, 0x8($4)\n"
        "\tnop\n"
        "\t.word 0x4AA80428\n" /* sqr 1 */
        "\tswc2 $25, 0x0($5)\n"
        "\tswc2 $26, 0x4($5)\n"
        "\tswc2 $27, 0x8($5)"
    );
    vv = a1;
    return vv;
}

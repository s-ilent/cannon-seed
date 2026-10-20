/* Matched 2026-10-20 through the round-trip oracle (g3_jp first;
 * region-pair 100.00% byte twins across g3_jp/g3_eu, the matching
 * lane's RotAverage cluster queue item).
 *
 * LIBGTE RotAverageNclip3: the three vertices (a0/a1/a2) load into
 * the V registers ($0-$5), rtpt (0x4A280030 - GNU as has no GTE
 * mnemonics, banked as its exact retail .word) rotates/perspects all
 * three into the SXY fifo; the flag pointer (stack arg at 0x20)
 * stores FLAG ($31) as read right after the command, then nclip
 * (0x4B400006) puts the normal-clip value into MAC0 ($24), which
 * mfc2 reads into $2 as the return value. The positive branch stores
 * SXY0/SXY1/SXY2 ($12/$13/$14) through the sxy pointers and IR0
 * ($8, the averaged depth) through the p pointer, then avsz3
 * (0x4B58002D) writes OTZ ($7) through the otz pointer. The function
 * is frameless: the stacked args are read at the caller's 0x10($sp)
 * window exactly as retail.
 *
 * psyq prototype: long RotAverageNclip3(SVECTOR *v0, SVECTOR *v1,
 * SVECTOR *v2, long *sxy0, long *sxy1, long *sxy2, long *p,
 * long *otz, long *flag); args stay long* so gcc emits no
 * caller-side extensions. One volatile asm block with the retail
 * register assignments hardcoded; the two branches are banked as
 * their exact retail .words (maspsx appends a hazard nop after every
 * branch mnemonic under .set reorder, which retail does not carry),
 * the mfc2 targets the return register, so the $2 register-var
 * output needs no post-block move and the epilogue is the stock
 * frameless jr $ra with a nop delay slot. Row 0x90 vs function 0x88
 * - the trailing pad words are ld zero fill in the real build (the
 * banked pad law).
 */
long RotAverageNclip3(long *a0, long *a1, long *a2, long *a3, long *a4,
                      long *a5, long *a6, long *a7, long *a8)
{
    register long vv asm("$2");
    __asm__ volatile(
        "lwc2 $0, 0x0($4)\n"
        "\tlwc2 $1, 0x4($4)\n"
        "\tlwc2 $2, 0x0($5)\n"
        "\tlwc2 $3, 0x4($5)\n"
        "\tlwc2 $4, 0x0($6)\n"
        "\tlwc2 $5, 0x4($6)\n"
        "\tnop\n"
        "\t.word 0x4A280030\n" /* rtpt */
        "\tlw $8, 0x20($sp)\n"
        "\tcfc2 $9, $31\n"
        "\tnop\n"
        "\tsw $9, 0x0($8)\n"
        "\t.word 0x4B400006\n" /* nclip */
        "\tlw $8, 0x10($sp)\n"
        "\tlw $9, 0x14($sp)\n"
        "\tlw $10, 0x18($sp)\n"
        "\tmfc2 $2, $24\n"
        "\tnop\n"
        "\t.word 0x1C400003\n" /* bgtz $2, 1f */
        "\tnop\n"
        "\t.word 0x1000000B\n" /* b 2f */
        "\tnop\n"
        "1:\n"
        "\tswc2 $12, 0x0($7)\n"
        "\tswc2 $13, 0x0($8)\n"
        "\tswc2 $14, 0x0($9)\n"
        "\tswc2 $8, 0x0($10)\n"
        "\tnop\n"
        "\t.word 0x4B58002D\n" /* avsz3 */
        "\tlw $9, 0x1c($sp)\n"
        "\tmfc2 $8, $7\n"
        "\tnop\n"
        "\tsw $8, 0x0($9)\n"
        "2:\n"
        : "=r"(vv)
        : : "8", "9", "10");
    return vv;
}

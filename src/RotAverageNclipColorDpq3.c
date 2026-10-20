/* Matched 2026-10-20 through the round-trip oracle (g3_jp first;
 * region-pair 100.00% byte twins across g3_jp/g3_eu, the matching
 * lane's pair-report pick list: the RotAverageNclipColorCol3/
 * RotAverageNclipColorDpq3 pair at true 0x8005B284/0x8005B354).
 *
 * LIBGTE RotAverageNclipColorDpq3: byte-shape identical to
 * RotAverageNclipColorCol3 except the lighting command - the three
 * vertices (a0/a1/a2) load into the V registers ($0-$5), rtpt
 * (0x4A280030) rotates/perspects all three into the SXY fifo; the
 * flag pointer (stack arg at 0x38) stores FLAG ($31), then nclip
 * (0x4B400006) puts the normal-clip value into MAC0 ($24), which
 * mfc2 reads into $2 as the return value. The positive branch loads
 * the three normals (a3 and the stack args at 0x10/0x14) plus the
 * single color word (0x18) into the V registers and RGB ($6), ncdt
 * (0x4AF80416, normal-color-depth triple - the depth-carrying
 * variant of ncct) lights the triple into RGB0/1/2 ($20/$21/$22),
 * then the projected SXY0/1/2 ($12/$13/$14, still holding rtpt's
 * fifo) store through the stack args at 0x1C/0x20/0x24 and the
 * colored RGB0/1/2 through 0x28/0x2C/0x30; avsz3 (0x4B58002D) writes
 * OTZ ($7) through the otz pointer (0x34). The function is
 * frameless: the stacked args are read at the caller's 0x10($sp)
 * window exactly as retail.
 *
 * psyq prototype: long RotAverageNclipColorDpq3(SVECTOR *v0,
 * SVECTOR *v1, SVECTOR *v2, SVECTOR *n0, SVECTOR *n1, SVECTOR *n2,
 * CVECTOR *col, long *sxy0, long *sxy1, long *sxy2, CVECTOR *c0,
 * CVECTOR *c1, CVECTOR *c2, long *otz, long *flag); args stay long*
 * so gcc emits no caller-side extensions. One volatile asm block
 * with the retail register assignments hardcoded; the two branches
 * are banked as their exact retail .words (maspsx appends a hazard
 * nop after every branch mnemonic under .set reorder, which retail
 * does not carry) - the bgtz offset is 2 (target 1: = bgtz+12 - the nop + b pair only, one less than RotAverageNclip3 whose b carries its own nop slot), and the skip-b
 * offset is 0x1B with the shared-slot shape (retail's b delay slot
 * is the tail's first lwc2, one load serving both paths - the
 * Col3 sister's NEW slot shape law). The mfc2 targets the return
 * register, so the $2 register-var output needs no post-block move
 * and the epilogue is the stock frameless jr $ra with a nop delay
 * slot. Row 0xd0 vs function 0xc8 - the trailing pad words are ld
 * zero fill in the real build (the banked pad law).
 */
long RotAverageNclipColorDpq3(long *a0, long *a1, long *a2, long *a3,
                              long *a4, long *a5, long *a6, long *a7,
                              long *a8, long *a9, long *a10, long *a11,
                              long *a12, long *a13, long *a14)
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
        "\tlw $8, 0x38($sp)\n"
        "\tcfc2 $9, $31\n"
        "\tnop\n"
        "\tsw $9, 0x0($8)\n"
        "\t.word 0x4B400006\n" /* nclip */
        "\tlw $8, 0x10($sp)\n"
        "\tlw $9, 0x14($sp)\n"
        "\tlw $10, 0x18($sp)\n"
        "\tmfc2 $2, $24\n"
        "\tnop\n"
        "\t.word 0x1C400002\n" /* bgtz $2, 1f - target is bgtz+12 (nop + b only) */
        "\tnop\n"
        "\t.word 0x1000001B\n" /* b 2f - delay slot is 1:'s first lwc2 */
        "1:\n"
        "\tlwc2 $0, 0x0($7)\n"
        "\tlwc2 $1, 0x4($7)\n"
        "\tlwc2 $2, 0x0($8)\n"
        "\tlwc2 $3, 0x4($8)\n"
        "\tlwc2 $4, 0x0($9)\n"
        "\tlwc2 $5, 0x4($9)\n"
        "\tlwc2 $6, 0x0($10)\n"
        "\tnop\n"
        "\t.word 0x4AF80416\n" /* ncdt */
        "\tlw $8, 0x1c($sp)\n"
        "\tlw $9, 0x20($sp)\n"
        "\tlw $10, 0x24($sp)\n"
        "\tlw $11, 0x28($sp)\n"
        "\tlw $12, 0x2c($sp)\n"
        "\tlw $13, 0x30($sp)\n"
        "\tswc2 $12, 0x0($8)\n"
        "\tswc2 $13, 0x0($9)\n"
        "\tswc2 $14, 0x0($10)\n"
        "\tswc2 $20, 0x0($11)\n"
        "\tswc2 $21, 0x0($12)\n"
        "\tswc2 $22, 0x0($13)\n"
        "\tnop\n"
        "\t.word 0x4B58002D\n" /* avsz3 */
        "\tlw $9, 0x34($sp)\n"
        "\tmfc2 $8, $7\n"
        "\tnop\n"
        "\tsw $8, 0x0($9)\n"
        "2:\n"
        : "=r"(vv)
        : : "8", "9", "10", "11", "12", "13");
    return vv;
}

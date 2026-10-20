/* Matched 2026-10-20 through the round-trip oracle (g3_jp first;
 * region-pair 100.00% byte twins across g3_jp/g3_eu, the matching
 * lane's RotAverage cluster queue item).
 *
 * LIBGTE RotAverageNclip4: the four vertices (a0-a3) - three through
 * rtpt (0x4A280030), the fourth through rtps (0x4A180001) reusing the
 * fifo - the flag pointer (stack arg at 0x28) stores the rtpt FLAG
 * ($31) first, nclip (0x4B400006) puts the normal-clip value into
 * MAC0 ($24), which mfc2 reads into $2 as the return value; the
 * positive branch stores SXY0/SXY1/SXY2 ($12/$13/$14) through their
 * pointers, runs the fourth vertex, stores the rtps SXY2 ($14) as
 * the fourth sxy and IR0 ($8) as p, ORs the rtps FLAG into the rtpt
 * flag (retail's cumulative flag law), and avsz4 (0x4B68002E) writes
 * OTZ ($7) through the otz pointer. Frameless: the stacked args are
 * read at the caller's 0x10($sp) window exactly as retail.
 *
 * psyq prototype: long RotAverageNclip4(SVECTOR *v0, SVECTOR *v1,
 * SVECTOR *v2, SVECTOR *v3, long *sxy0, long *sxy1, long *sxy2,
 * long *sxy3, long *p, long *otz, long *flag); args stay long* so
 * gcc emits no caller-side extensions. One volatile asm block with
 * the retail register assignments hardcoded; the two branches are
 * banked as their exact retail .words (maspsx appends a hazard nop
 * after every branch mnemonic under .set reorder, which retail does
 * not carry), the mfc2 targets the return register, so the $2
 * register-var output needs no post-block move and the epilogue is
 * the stock frameless jr $ra with a nop delay slot. The row is 0xb0
 * and the function is 0xb0 - no pad words on this one.
 */
long RotAverageNclip4(long *a0, long *a1, long *a2, long *a3, long *a4,
                      long *a5, long *a6, long *a7, long *a8, long *a9,
                      long *a10)
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
        "\tlw $8, 0x28($sp)\n"
        "\tcfc2 $3, $31\n"
        "\tnop\n"
        "\tsw $3, 0x0($8)\n"
        "\t.word 0x4B400006\n" /* nclip */
        "\tlw $8, 0x10($sp)\n"
        "\tlw $9, 0x14($sp)\n"
        "\tlw $10, 0x18($sp)\n"
        "\tmfc2 $2, $24\n"
        "\tnop\n"
        "\t.word 0x1C400003\n" /* bgtz $2, 1f */
        "\tnop\n"
        "\t.word 0x10000015\n" /* b 2f */
        "\tnop\n"
        "1:\n"
        "\tswc2 $12, 0x0($8)\n"
        "\tswc2 $13, 0x0($9)\n"
        "\tswc2 $14, 0x0($10)\n"
        "\tlwc2 $0, 0x0($7)\n"
        "\tlwc2 $1, 0x4($7)\n"
        "\tnop\n"
        "\t.word 0x4A180001\n" /* rtps */
        "\tlw $8, 0x1c($sp)\n"
        "\tlw $9, 0x20($sp)\n"
        "\tlw $10, 0x28($sp)\n"
        "\tswc2 $14, 0x0($8)\n"
        "\tcfc2 $11, $31\n"
        "\tswc2 $8, 0x0($9)\n"
        "\tor $11, $11, $3\n"
        "\tsw $11, 0x0($10)\n"
        "\t.word 0x4B68002E\n" /* avsz4 */
        "\tlw $9, 0x24($sp)\n"
        "\tmfc2 $8, $7\n"
        "\tnop\n"
        "\tsw $8, 0x0($9)\n"
        "2:\n"
        : "=r"(vv)
        : : "8", "9", "10", "11", "3");
    return vv;
}

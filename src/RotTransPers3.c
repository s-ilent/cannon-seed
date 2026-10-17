/* Matched 2026-10-17 through the round-trip oracle (g3org_jp first;
 * cross-target byte-identical in mainmenu_jp, g3_eu, g3org_jp, g3org_eu -
 * the matching lane's GTE families queue item).
 *
 * LIBGTE RotTransPers3: full rtpt over the first three vertices (VXY0/VZ0
 * .. VXY2/VZ2 loaded from a0/a1/a2), then the three SXY fifo results
 * ($12/$13/$14) stored through a3 and the caller's stacked output
 * pointers (o32 args 5-7 at 0x10/0x14/0x18($sp)), the MAC0 division
 * result ($8) through the stacked arg 8 at 0x1C($sp), and FLAG (C31)
 * through the stacked arg at 0x1C($sp) - see the asm order: $11 carries
 * the 0x1C pointer, the MAC0 store drains it into ($10) first. Returns
 * SZ3 (DR19) >> 2 with the sra in the return delay slot exactly as
 * retail.
 *
 * One volatile asm block with the retail register assignments hardcoded
 * ($4-$7 = the o32 register args, $8-$11 = the stacked pointers; the
 * banked RotTransPers4 class). rtpt is a GTE command alias GNU as does
 * not know, emitted as its exact retail word.
 *
 * psyq prototype: long RotTransPers3(VECTOR *v0, VECTOR *v1, VECTOR *v2,
 * long *sxy0, long *sxy1, long *sxy2, long *p, long *flag) - the stacked
 * args 5-8 are read block-internally at 0x10..0x1C($sp) like
 * RotTransPers4's args 5-10; args stay long* so gcc emits no caller-side
 * extensions.
 */
long RotTransPers3(long *a0, long *a1, long *a2, long *a3)
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
        "\tlw $8, 0x10($sp)\n"
        "\tlw $9, 0x14($sp)\n"
        "\tlw $10, 0x18($sp)\n"
        "\tlw $11, 0x1C($sp)\n"
        "\tswc2 $12, 0x0($7)\n"
        "\tswc2 $13, 0x0($8)\n"
        "\tswc2 $14, 0x0($9)\n"
        "\tswc2 $8, 0x0($10)\n"
        "\tcfc2 $3, $31\n"
        "\tmfc2 $2, $19\n"
        "\tsw $3, 0x0($11)"
        : "=r"(vv)
        :
        : "3", "8", "9", "10", "11");
    return vv >> 2;
}

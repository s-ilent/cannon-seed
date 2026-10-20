/* Matched 2026-10-20 through the round-trip oracle (g3_jp first;
 * region-pair 100.00% byte twins across g3_jp/g3_eu, the matching
 * lane's libgte math cluster queue item).
 *
 * LIBGTE OuterProduct12: saves the rotation matrix rows the command
 * will clobber (cfc2 $13/$14/$15 off control 0/2/4), installs the
 * caller's matrix (a0, three packed-halfword words through cpu
 * $8/$9/$10 into ctc2 control 0/2/4), loads the vector (a1) into the
 * V registers - retail's lwc2 order is reversed (offset 8 first),
 * which the scheduler chose and the block pins - runs the op command
 * (0x4B78000C, sf set - GNU as has no GTE mnemonics, banked as its
 * exact retail .word), stores MAC1/MAC2/MAC3 ($25/$26/$27) through
 * a2, and restores the saved matrix rows before the stock jr $ra with
 * a nop delay slot.
 *
 * psyq prototype: void OuterProduct12(MATRIX *m, VECTOR *v,
 * VECTOR *out); args stay long* so gcc emits no caller-side
 * extensions. One volatile asm block with the retail register
 * assignments hardcoded (the cop2 ops are not reachable from plain C).
 */
void OuterProduct12(long *a0, long *a1, long *a2)
{
    __asm__ volatile(
        "cfc2 $13, $0\n"
        "\tcfc2 $14, $2\n"
        "\tcfc2 $15, $4\n"
        "\tlw $8, 0x0($4)\n"
        "\tlw $9, 0x4($4)\n"
        "\tlw $10, 0x8($4)\n"
        "\tctc2 $8, $0\n"
        "\tctc2 $9, $2\n"
        "\tctc2 $10, $4\n"
        "\tlwc2 $11, 0x8($5)\n"
        "\tlwc2 $9, 0x0($5)\n"
        "\tlwc2 $10, 0x4($5)\n"
        "\tnop\n"
        "\t.word 0x4B78000C\n" /* op12 */
        "\tswc2 $25, 0x0($6)\n"
        "\tswc2 $26, 0x4($6)\n"
        "\tswc2 $27, 0x8($6)\n"
        "\tctc2 $13, $0\n"
        "\tctc2 $14, $2\n"
        "\tctc2 $15, $4\n"
        : : : "8", "9", "10", "13", "14", "15");
}

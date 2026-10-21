/* Matched 2026-10-21 through the judge oracle (byte-identical pair first:
 * file offsets 0x2A348 g3_eu, 0x15460 slps_00270 - both the 0x5c sdk rows
 * at the pinned LIBGTE member addresses; the byte search across all eight
 * baselines then found the same 92 bytes in every executable, so the wave
 * is 8 of 8 with six merged-parent splits - four data-row hosts (the
 * data_80066CF4 pattern again in mainmenu_jp/mainmenu_eu, plus g3_jp and
 * sces_00269) and two asm-row carves (the g3org pair, where the member
 * already renders as its own labeled function inside the merged row)).
 *
 * LIBGTE ApplyMatrixSV: the 0x14-byte matrix record ($4) loads five words
 * into $8-$12 and ctc2 moves them into GTE regs 0..4 (the rotation matrix
 * columns), the vector ($5) loads two words into VXY0/VZ0 via lwc2, mvmva
 * 1,0,0,3,0 (0x4A486012 - GNU as has no GTE mnemonics, banked as its exact
 * retail .word) multiplies, and the IR1/IR2/IR3 results mfc2 back into
 * $8-$10 and store as three shorts through the out pointer ($6). The out
 * pointer returns via addu $2,$6,$0 in the asm block (the $2 register-var
 * output needs no post-block move) and the epilogue is the stock frameless
 * jr $ra with a nop delay slot.
 *
 * Unlike the SetColorMatrix moves, this member's ctc2/mfc2/lwc2/sh retail
 * words match gas's own encodings exactly (0x48C80000-family rs=6 true
 * ctc2 form, 0x48084800 mfc2 form) - only the mvmva needs the .word.
 *
 * psyq prototype: VECTOR *ApplyMatrixSV(MATRIX *m, VECTOR *v, VECTOR *out);
 * args stay long* so gcc emits no caller-side extensions.
 */
long *ApplyMatrixSV(long *m, long *v, long *out)
{
    register long *ret asm("$2");
    __asm__ volatile(
        "lw $8, 0x0($4)\n"
        "\tlw $9, 0x4($4)\n"
        "\tlw $10, 0x8($4)\n"
        "\tlw $11, 0xc($4)\n"
        "\tlw $12, 0x10($4)\n"
        "\tctc2 $8, $0\n"
        "\tctc2 $9, $1\n"
        "\tctc2 $10, $2\n"
        "\tctc2 $11, $3\n"
        "\tctc2 $12, $4\n"
        "\tlwc2 $0, 0x0($5)\n"
        "\tlwc2 $1, 0x4($5)\n"
        "\tnop\n"
        "\t.word 0x4A486012\n" /* mvmva 1,0,0,3,0 */
        "\tmfc2 $8, $9\n"
        "\tmfc2 $9, $10\n"
        "\tmfc2 $10, $11\n"
        "\tsh $8, 0x0($6)\n"
        "\tsh $9, 0x2($6)\n"
        "\tsh $10, 0x4($6)\n"
        "\taddu $2, $6, $0"
        : "=r"(ret));
    return ret;
}

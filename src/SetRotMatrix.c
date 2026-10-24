/* Matched 2026-10-25 through the D-MID-ROW SDK resolution (queue item b):
 * the census's parked mainmenu_jp candidates voting 7/12 against the landed
 * SetColorMatrix row are NOT SetColorMatrix copies - the five differing
 * words (differing set exactly [5..9]) carry ctc2 encodings into the GTE
 * CONTROL registers 0..4, the ROTATION matrix block, where SetColorMatrix
 * writes 16..20 (the color matrix). Same 5-lw + 5-move + jr/nop template,
 * different destination register file: this is LIBGTE SetRotMatrix.
 *
 * The site: mainmenu_jp file 0x3EFE8 (VA 0x8005E7E8), the third
 * nonmatching block of the data_8005E6A0 data row, followed immediately
 * by the SetLightMatrix copy (the census's second 7/12 candidate) and the
 * landed SetColorMatrix row at 0x3F048. The walk had already claimed the
 * pair as one 0x60 nonmatching block; the split renders
 * each copy as its own c row.
 *
 * The five moves assemble NATIVELY (ctc2 mnemonic, the ApplyMatrixSV
 * precedent - that member's landed body writes the very same control
 * registers 0..4): no .word spellings needed, unlike SetColorMatrix whose
 * retail copies carry the same rs=6 form but which was landed before the
 * ctc2-native pattern was proven. The loads and moves stay in ONE asm
 * block so the retail order (all five loads first, then all five moves)
 * is guaranteed.
 *
 * psyq prototype: void SetRotMatrix(MATRIX *m); the record pointer
 * passes through $4 untouched.
 */
void SetRotMatrix(long *m)
{
    __asm__ volatile(
        "lw $8, 0($4)\n"
        "\tlw $9, 4($4)\n"
        "\tlw $10, 8($4)\n"
        "\tlw $11, 12($4)\n"
        "\tlw $12, 16($4)\n"
        "\tctc2 $8, $0\n"
        "\tctc2 $9, $1\n"
        "\tctc2 $10, $2\n"
        "\tctc2 $11, $3\n"
        "\tctc2 $12, $4\n"
    );
}

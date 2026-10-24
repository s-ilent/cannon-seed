/* Matched 2026-10-25 through the D-MID-ROW SDK resolution (queue item b):
 * the census's second parked mainmenu_jp candidate (votes 2, eq 7/12
 * against the landed SetColorMatrix row) is the LIGHT matrix member of
 * the same 5-lw + 5-move template - its five differing words (differing
 * set exactly [5..9], like its back-to-back sibling SetRotMatrix) carry
 * ctc2 encodings into the GTE control registers 8..12, the block that
 * packs the 3x3 light source matrix (9 halfwords: (L11,L12), (L13,L21),
 * (L22,L23), (L31,L32), L33). SetColorMatrix writes 16..20, SetRotMatrix
 * (the back-to-back sibling this copy shares the row tail with) writes
 * 0..4: one template, three register files, three LIBGTE members.
 *
 * The site: mainmenu_jp file 0x3F018 (VA 0x8005E818), ending exactly at
 * the data_8005E6A0 row end 0x3F048 where the landed SetColorMatrix row
 * begins - the three members sit back-to-back-to-back in the retail
 * image, the SDK library's own set-matrix cluster.
 *
 * The five moves assemble NATIVELY (ctc2 mnemonic, the ApplyMatrixSV
 * precedent; control register numbers 8..12 parse the same as that
 * member's 0..4). The loads and moves stay in ONE asm block so the
 * retail order (all five loads first, then all five moves) is
 * guaranteed.
 *
 * psyq prototype: void SetLightMatrix(MATRIX *m); the record pointer
 * passes through $4 untouched.
 */
void SetLightMatrix(long *m)
{
    __asm__ volatile(
        "lw $8, 0($4)\n"
        "\tlw $9, 4($4)\n"
        "\tlw $10, 8($4)\n"
        "\tlw $11, 12($4)\n"
        "\tlw $12, 16($4)\n"
        "\tctc2 $8, $8\n"
        "\tctc2 $9, $9\n"
        "\tctc2 $10, $10\n"
        "\tctc2 $11, $11\n"
        "\tctc2 $12, $12\n"
    );
}

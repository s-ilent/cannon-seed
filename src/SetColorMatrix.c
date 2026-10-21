/* Matched 2026-10-21 through the judge oracle (byte-identical pair from
 * the in-repo near-twin census: file offsets 0x15664 slps_00270, 0x2A54C
 * g3_eu - both the 0x30 sdk rows at the pinned LIBGTE member addresses;
 * the sces/g3org copies of the same member sit inside merged parent rows
 * and stay parked for the split pattern).
 *
 * LIBGTE SetColorMatrix: the argument is the 0x14-byte matrix record,
 * five word loads into $8-$12 and five move-to-GTE-data-register forms
 * into registers 16..20 (the color matrix plus its trailing light
 * registers), then the stock frameless jr $ra with a nop delay slot.
 *
 * The five moves are banked as their exact retail .word encodings: this
 * member's retail copies carry the rs=6 cop2 form, while the landed
 * AverageZ3/AverageZ4 members and GNU as's own mtc2 mnemonic carry rs=4
 * - the retail binary mixes both provences across sdk members, so the
 * mnemonic cannot reproduce this one (the avsz3 .word precedent). The
 * loads and the moves stay in ONE asm block so the retail order (all
 * five loads first, then all five moves) is guaranteed.
 *
 * psyq prototype: void SetColorMatrix(MATRIX *m); the record pointer
 * passes through $4 untouched.
 */
void SetColorMatrix(long *m)
{
    __asm__ volatile(
        "lw $8, 0($4)\n"
        "\tlw $9, 4($4)\n"
        "\tlw $10, 8($4)\n"
        "\tlw $11, 12($4)\n"
        "\tlw $12, 16($4)\n"
        "\t.word 0x48C88000\n" /* $8  -> reg 16 (rs=6 form) */
        "\t.word 0x48C98800\n" /* $9  -> reg 17 (rs=6 form) */
        "\t.word 0x48CA9000\n" /* $10 -> reg 18 (rs=6 form) */
        "\t.word 0x48CB9800\n" /* $11 -> reg 19 (rs=6 form) */
        "\t.word 0x48CCA000\n" /* $12 -> reg 20 (rs=6 form) */
    );
}

/* Matched 2026-10-21 through the judge oracle (byte-identical x8 in the
 * baseline scan, always the word run at file offset +0x30 after the
 * SetColorMatrix copies; the link-map report banks the identity - in the
 * LIBGTE member sequence SetTransMatrix sits immediately after
 * SetColorMatrix at +0x30 in every target where the pair is located).
 * Landed this window: 0x15694 slps_00270, 0x1515C sces_00269 (split out
 * of the merged parent), 0x279D0 g3org_eu (same), 0x2A57C g3_eu (the
 * old 0x24 asm row split into the 0x20 body plus a 0x4 boundary pad).
 * The mainmenu_jp/mainmenu_eu/g3_jp/g3org_jp copies sit inside data or
 * parent rows and stay parked for the data-row split pattern.
 *
 * LIBGTE SetTransMatrix: three word loads from the record at +0x14,
 * +0x18, +0x1c into $8-$10, then three move-to-gte forms into the
 * translation registers 5/6/7 (TRX/TRY/TRZ, the registers the landed
 * map gives as $5/$6/$7: SetBackColor owns $13-$15, SetFarColor $21-$23,
 * SetGeomOffset $24/$25, SetDQA $27), then the stock frameless jr $ra
 * with a nop delay slot.
 *
 * The three moves are banked as their exact retail .word encodings per
 * the banked cop2 law: this member family's retail copies carry the
 * rs=6 form while GNU as's own mtc2 mnemonic carries rs=4 (the
 * SetColorMatrix/SetDQA precedent; the g3org_jp +0x30 neighbor's retail
 * words 0x48C82800/0x48C93000/0x48CA3800 are the rs=6 forms). The loads
 * and the moves stay in ONE asm block so the retail order (all three
 * loads first, then all three moves) is guaranteed.
 *
 * psyq prototype: void SetTransMatrix(MATRIX *m); the record pointer
 * passes through $4 untouched.
 */
void SetTransMatrix(long *m)
{
    __asm__ volatile(
        "lw $8, 20($4)\n"
        "\tlw $9, 24($4)\n"
        "\tlw $10, 28($4)\n"
        "\t.word 0x48C82800\n" /* $8  -> reg 5  (rs=6 form) */
        "\t.word 0x48C93000\n" /* $9  -> reg 6  (rs=6 form) */
        "\t.word 0x48CA3800\n" /* $10 -> reg 7  (rs=6 form) */
    );
}

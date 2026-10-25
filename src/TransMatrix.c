/* Matched 2026-10-25 (window cron-202610251051) - the TransMatrix member
 * of the LIBGTE matrix SDK set, x8 across every executable. The identity
 * is banked in config/sdk_anchors.txt at two independent sites:
 *
 *   0x8005E6A0 0x24  TransMatrix ? LIBGTE@3.3 window-verbatim  (mainmenu_jp)
 *   0x8004A18C 0x24  TransMatrix ? LIBGTE@3.3 window-verbatim  (g3_jp)
 *
 * and the census's full reference pool scores all eight retail copies at
 * full word-eq 9/9 (the mini-function that opens the GTE graveyard rows:
 * mainmenu_jp's copy sits at the head of data_8005E6A0, the other seven
 * targets carry it as its own sdk-annotated asm row immediately before
 * the ScaleMatrix row).
 *
 * The body is frameless pure CPU code: three word loads from the record
 * at ($5), three word stores to the translation slots the landed
 * SetTransMatrix note banks at +0x14, +0x18, +0x1c of the record at $4,
 * then the stock addu $2,$4,$0 return of the record pointer. psyq's
 * TransMatrix takes the VECTOR by value; under the o32 ABI a 12-byte
 * aggregate arrives by reference, so the callee reads ($5) - the same
 * convention every landed SDK row documents.
 *
 * The loads and the stores stay in ONE asm block so the retail order
 * (all three loads first, then all three stores) is guaranteed; the
 * return tail follows the landed ApplyMatrixLV pattern (addu $2 inside
 * the asm, captured through the "=r" operand).
 *
 * psyq prototype: MATRIX *TransMatrix(MATRIX *m, VECTOR v);
 *
 * Landed this window: whole-row asm->c flips at 0x2A98C g3_jp,
 * 0x2A3A4 g3_eu, 0x27E28 g3org_jp, 0x277F8 g3org_eu, 0x3E880
 * mainmenu_eu, 0x154BC slps_00270, 0x14F84 sces_00269, plus the
 * mainmenu_jp data-row split that opens data_8005E6A0 (the row's
 * remaining 0x124 at 0x3EEC4 is ScaleMatrix, parked for its own wave).
 */
long *TransMatrix(long *m, long *v)
{
    long *ret;
    __asm__ volatile(
        "lw $8, 0($5)\n"
        "\tlw $9, 4($5)\n"
        "\tlw $10, 8($5)\n"
        "\tsw $8, 20($4)\n"
        "\tsw $9, 24($4)\n"
        "\tsw $10, 28($4)\n"
        "\taddu $2, $4, $0"
        : "=r"(ret));
    return ret;
}

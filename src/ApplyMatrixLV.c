/* Matched 2026-10-25 through the D-MID-ROW SDK resolution (queue item b):
 * the census's parked mainmenu_jp candidate voting 9 with eq 14/23 against
 * the landed ApplyMatrixSV row is NOT an ApplyMatrixSV copy - it shares
 * the body's 14-word head exactly (five lw into $8-$12, five ctc2 into
 * the rotation registers 0..4, two lwc2 into VXY0/VZ0, the mvmva .word)
 * and then diverges for good: the tail stores the GTE results DIRECTLY to
 * the output vector as three longs (swc2 $25/$26/$27 through $6 at
 * 0x0/0x4/0x8) where ApplyMatrixSV rounds them to shorts first (mfc2
 * $8-$10, then three sh through $6). Long stores, no rounding: this is
 * LIBGTE ApplyMatrixLV - the long-vector twin of ApplyMatrixSV, exactly
 * the sibling_finder query the queue item asked to resolve through the
 * landed src rows.
 *
 * The site: mainmenu_jp file 0x3EDF4 (VA 0x8005E5F4), the last 0x50 bytes
 * of the data_80066CF4 data row (the walk had claimed them as their own
 * nonmatching block at the row tail); the landed ApplyMatrixSV row begins
 * at the very next byte (0x3EE44) - the short- and long-vector twins sit
 * back-to-back in the retail image.
 *
 * The swc2 forms assemble NATIVELY (the lwc2 precedent in the landed
 * ApplyMatrixSV; swc2 is its store-side mirror), the mvmva stays banked
 * as its exact retail .word (GNU as has no GTE mnemonics), and the out
 * pointer returns via addu $2,$6,$0 in the asm block (the $2 register-var
 * output needs no post-block move) with the stock frameless jr $ra +
 * nop epilogue.
 *
 * psyq prototype: VECTOR *ApplyMatrixLV(MATRIX *m, VECTOR *v, VECTOR *ov);
 * args stay long* so gcc emits no caller-side extensions.
 */
long *ApplyMatrixLV(long *m, long *v, long *out)
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
        "\tswc2 $25, 0x0($6)\n"
        "\tswc2 $26, 0x4($6)\n"
        "\tswc2 $27, 0x8($6)\n"
        "\taddu $2, $6, $0"
        : "=r"(ret));
    return ret;
}

/* ApplyMatrixSV probe draft (window cron-202610211628): the 0x5c LIBGTE
 * member, byte-identical across all eight targets (found by byte search,
 * sha1 cb189d4e). Retail body: five lw from the matrix record ($4), five
 * ctc2 into GTE regs 0..4, two lwc2 from the vector ($5), nop, mvmva
 * 1,0,0,3,0 (0x4A486012 - GNU as has no GTE mnemonics, .word banked),
 * three mfc2 from IR1/IR2/IR3, three sh through the out pointer ($6),
 * addu $2,$6,$0 return of the out pointer, stock frameless jr.
 * ctc2/mfc2/lwc2/sh retail words match gas's own encodings (verified
 * arithmetically in the render: 0x48C80000 etc.) - only mvmva needs the
 * .word. The return rides the $2 register-var output, so the epilogue is
 * gcc's stock frameless jr $ra + nop.
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

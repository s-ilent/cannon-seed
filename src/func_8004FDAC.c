/* MulMatrix2 - LIBGTE member, x2 byte-identical own-row wave (0x10C).
 * One src unit per row under the row's own walk name; two members, both
 * curated psyq pins (slps, g3_eu). Sits between MulMatrix (0x10C) and the
 * landed ApplyMatrixLV c row in both carriers (cross-target identities
 * live in the yaml, the symbols file and the landing commit, not repeated
 * here: the headers name no siblings).
 *
 * Decode (20th-return NEXT 3, offline window cron-202610291255): the SAME
 * GTE body as MulMatrix - word-diff proves the pair differs in exactly six
 * words, all in the store/return phase: the four sw and the swc2 base
 * moves $4 -> $5 and the return move $4 -> $5, i.e. the product stores
 * into m1 (overwriting it) and returns m1 (psyq's documented two-matrix
 * form). The identical asm block minus those six slots; everything else in
 * the MulMatrix decode comment applies verbatim (ctc2 control load,
 * column-wise m1 feeds, three .word-banked mvmva 1,0,0,3,0 passes, IR
 * reassembly, the SetLightMatrix one-block law, the TransposeMatrix
 * return-staging law).
 *
 * psyq prototype: MATRIX *MulMatrix2(MATRIX *m0, MATRIX *m1) - the two
 * record pointers pass through $4/$5 and the result returns in $2.
 */
long *func_8004FDAC(long *m0, long *m1)
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
        "\tlhu $8, 0x0($5)\n"
        "\tlw $9, 0x4($5)\n"
        "\tlw $10, 0xc($5)\n"
        "\tlui $at, (0xFFFF0000 >> 16)\n"
        "\tand $9, $9, $at\n"
        "\tor $8, $8, $9\n"
        "\tmtc2 $8, $0\n"
        "\tmtc2 $10, $1\n"
        "\tnop\n"
        "\t.word 0x4A486012\n" /* mvmva 1,0,0,3,0 */
        "\tlhu $8, 0x2($5)\n"
        "\tlw $9, 0x8($5)\n"
        "\tlh $10, 0xe($5)\n"
        "\tsll $9, $9, 16\n"
        "\tor $8, $8, $9\n"
        "\tmfc2 $11, $9\n"
        "\tmfc2 $12, $10\n"
        "\tmfc2 $13, $11\n"
        "\tmtc2 $8, $0\n"
        "\tmtc2 $10, $1\n"
        "\tnop\n"
        "\t.word 0x4A486012\n" /* mvmva 1,0,0,3,0 */
        "\tlhu $8, 0x4($5)\n"
        "\tlw $9, 0x8($5)\n"
        "\tlw $10, 0x10($5)\n"
        "\tlui $at, (0xFFFF0000 >> 16)\n"
        "\tand $9, $9, $at\n"
        "\tor $8, $8, $9\n"
        "\tmfc2 $14, $9\n"
        "\tmfc2 $15, $10\n"
        "\tmfc2 $24, $11\n"
        "\tmtc2 $8, $0\n"
        "\tmtc2 $10, $1\n"
        "\tnop\n"
        "\t.word 0x4A486012\n" /* mvmva 1,0,0,3,0 */
        "\tandi $11, $11, 0xffff\n"
        "\tsll $14, $14, 16\n"
        "\tor $14, $14, $11\n"
        "\tsw $14, 0x0($5)\n"
        "\tandi $13, $13, 0xffff\n"
        "\tsll $24, $24, 16\n"
        "\tor $24, $24, $13\n"
        "\tsw $24, 0xc($5)\n"
        "\tmfc2 $8, $9\n"
        "\tmfc2 $9, $10\n"
        "\tandi $8, $8, 0xffff\n"
        "\tsll $12, $12, 16\n"
        "\tor $8, $8, $12\n"
        "\tsw $8, 0x4($5)\n"
        "\tandi $15, $15, 0xffff\n"
        "\tsll $9, $9, 16\n"
        "\tor $9, $9, $15\n"
        "\tsw $9, 0x8($5)\n"
        "\tswc2 $11, 0x10($5)\n"
        "\taddu $2, $5, $0"
        : "=r"(ret));
    return ret;
}

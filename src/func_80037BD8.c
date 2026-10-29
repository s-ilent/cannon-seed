/* MulMatrix - LIBGTE member, x3 byte-identical own-row wave (0x10C).
 * One src unit per row under the row's own walk name; three members, two
 * curated psyq pins (slps, g3_eu) + the census-missed member the C8-wave
 * lesson confirmed (mainmenu_eu). Immediately precedes MulMatrix2 (0x10C)
 * and then the landed ApplyMatrixLV c row in every carrier - the SDK's own
 * GTE matrix cluster (cross-target identities live in the yaml, the
 * symbols file and the landing commit, not repeated here: the headers name
 * no siblings).
 *
 * Decode (20th-return NEXT 3, offline window cron-202610291255):
 * in-place GTE matrix product m0 = m0 * m1, returns m0. The five words of
 * m0's rotation block go straight into GTE control $0..$4 via ctc2 (the
 * offset-0x10 load carries the m[2][2]+t[0] word; the t[0] half in $4's
 * high bits is never read - R33 is the low half). m1 is fed to the vector
 * regs COLUMN-WISE in three passes (VXY0/VZ0 = m1[0][j], m1[1][j],
 * m1[2][j]; the pass-1/3 X words are rebuilt from an lhu + a masked lw via
 * lui $at,0xFFFF/and/or because the needed halves sit at 4-byte strides),
 * each pass mvmva 1,0,0,3,0 (SF=1, MX=0 = the rotation matrix, V=0,
 * CV=3 = no add, LM=0) multiplies m0's rows by m1's column j; the IR1-3
 * results collected per pass reassemble the nine halfwords of the product
 * into m0 (sw pairs + the swc2 $11 tail for m[2][2]), and the return is
 * the record pointer. The GTE commands are .word-banked (GNU as has no GTE
 * mnemonics, the AverageZ4 law); mvmva 1,0,0,3,0 = 0x4A486012.
 *
 * The whole body is ONE asm block (the SetLightMatrix order law): the
 * three passes read MAC2/MAC3/IR1 across blocks ($11..$15,$24 live from
 * the mfc2s into the store phase), so no compiler register allocation may
 * interleave. The return is staged inside the block (the TransposeMatrix
 * register-var law - ret is already in $2, so gcc emits only jr $ra with
 * an unfilled slot, exactly retail's nop delay).
 *
 * psyq prototype: MATRIX *MulMatrix(MATRIX *m0, MATRIX *m1) - the two
 * record pointers pass through $4/$5 and the result returns in $2.
 */
long *func_80037BD8(long *m0, long *m1)
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
        "\tsw $14, 0x0($4)\n"
        "\tandi $13, $13, 0xffff\n"
        "\tsll $24, $24, 16\n"
        "\tor $24, $24, $13\n"
        "\tsw $24, 0xc($4)\n"
        "\tmfc2 $8, $9\n"
        "\tmfc2 $9, $10\n"
        "\tandi $8, $8, 0xffff\n"
        "\tsll $12, $12, 16\n"
        "\tor $8, $8, $12\n"
        "\tsw $8, 0x4($4)\n"
        "\tandi $15, $15, 0xffff\n"
        "\tsll $9, $9, 16\n"
        "\tor $9, $9, $15\n"
        "\tsw $9, 0x8($4)\n"
        "\tswc2 $11, 0x10($4)\n"
        "\taddu $2, $4, $0"
        : "=r"(ret));
    return ret;
}

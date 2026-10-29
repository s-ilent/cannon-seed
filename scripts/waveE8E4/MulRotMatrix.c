/* MulRotMatrix - LIBGTE member, x7 byte-identical own-row wave (0xE8).
 * Identities: slps func_80034328, sces func_80033DF0, mainmenu_eu func_8005D6EC,
 * g3_jp func_800497F8, g3_eu func_80049210, g3org_jp func_80046C94,
 * g3org_eu func_80046664. Immediately follows MulRotMatrix0 (0xE4) and
 * immediately precedes the landed func_800492F8 (0x110) row in every target -
 * the SDK's own GTE matrix cluster.
 *
 * Decode (eighteenth-return NEXT 1, offline window cron-202610291025):
 * in-place GTE matrix product. Three mvmva 1,0,0,3,0 passes (SF=1, MX=0,
 * V=0, CV=3, LM=0); each pass feeds one (column, next-column) pair-pair of
 * the caller's matrix into GTE R11R12/R13R21 and collects {MAC2, MAC3, IR1}
 * back; the store phase reassembles nine halfword results into m[0..2][*]
 * (sw/swc2 tail), returns the record pointer (addu $v0,$a0,$zero inside the
 * block, retail position). The GTE commands are .word-banked (GNU as has no
 * GTE mnemonics, the AverageZ4 law); mvmva 1,0,0,3,0 = 0x4A486012.
 *
 * The whole body is ONE asm block (the SetLightMatrix order law): the three
 * passes read MAC2/MAC3/IR1 across blocks ($11..$15,$24 live from the mfc2s
 * into the store phase), so no compiler register allocation may interleave.
 * The return is staged inside the block (the TransposeMatrix register-var
 * law - ret is already in $2, so gcc emits only jr $ra with an unfilled
 * slot, exactly retail's nop delay).
 *
 * psyq prototype: MATRIX *MulRotMatrix(MATRIX *m); the record pointer
 * passes through $4 and returns in $2.
 */
long *MulRotMatrix(long *m)
{
    register long *ret asm("$2");
    __asm__ volatile(
        "lw $8, 0x0($4)\n"
        "\tlw $9, 0x4($4)\n"
        "\tlw $10, 0xc($4)\n"
        "\tandi $8, $8, 0xffff\n"
        "\tlui $at, (0xFFFF0000 >> 16)\n"
        "\tand $9, $9, $at\n"
        "\tor $8, $8, $9\n"
        "\tmtc2 $8, $0\n"
        "\tmtc2 $10, $1\n"
        "\tnop\n"
        "\t.word 0x4A486012\n" /* mvmva 1,0,0,3,0 */
        "\tlhu $8, 0x2($4)\n"
        "\tlw $9, 0x8($4)\n"
        "\tlh $10, 0xe($4)\n"
        "\tsll $9, $9, 16\n"
        "\tor $8, $8, $9\n"
        "\tmfc2 $11, $9\n"
        "\tmfc2 $12, $10\n"
        "\tmfc2 $13, $11\n"
        "\tmtc2 $8, $0\n"
        "\tmtc2 $10, $1\n"
        "\tnop\n"
        "\t.word 0x4A486012\n" /* mvmva 1,0,0,3,0 */
        "\tlhu $8, 0x4($4)\n"
        "\tlw $9, 0x8($4)\n"
        "\tlw $10, 0x10($4)\n"
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

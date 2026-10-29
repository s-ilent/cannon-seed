/* MulRotMatrix0 - LIBGTE member, x7 byte-identical own-row wave (0xE4).
 * One src unit per row under the row's own walk name; the seven members are
 * byte-identical 0xE4 rows, one per game target except mainmenu_jp. Each
 * unit immediately precedes its target's MulRotMatrix (0xE8) row - the
 * SDK's own GTE matrix cluster (cross-target identities live in the yaml,
 * the symbols file and the landing commit, not repeated here: the headers
 * name no siblings).
 *
 * Decode (eighteenth-return NEXT 1, offline window cron-202610291025): the
 * two-argument sibling of MulRotMatrix - reads the source matrix through
 * $a0, writes the product through $a1 (all nine stores target $a1, the
 * swc2 tail included), returns the DESTINATION pointer (addu $v0,$a1,$zero
 * inside the block, retail position). Three mvmva 1,0,0,3,0 passes; the
 * first source load is lhu m[0][0] where the in-place variant reads the
 * full word + andi (same effect, one word shorter: 0xE4 vs 0xE8).
 * GTE commands .word-banked; mvmva 1,0,0,3,0 = 0x4A486012.
 *
 * Whole body ONE asm block (the SetLightMatrix order law); return staged
 * inside the block (the TransposeMatrix register-var law - gcc emits only
 * jr $ra with an unfilled slot, exactly retail's nop delay).
 *
 * psyq prototype: MATRIX *MulRotMatrix0(MATRIX *src, MATRIX *dst);
 * $4 = src, $5 = dst, returns $2 = dst.
 */
long *func_8004912C(long *src, long *dst)
{
    register long *ret asm("$2");
    __asm__ volatile(
        "lhu $8, 0x0($4)\n"
        "\tlw $9, 0x4($4)\n"
        "\tlw $10, 0xc($4)\n"
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

/* Matched 2026-10-29 through the live-oracle judge loop (g3_eu).
 *
 * The #0x160 GTE transform host, whole-row class at the g3_eu/g3_jp
 * boundaries: a complete frameless leaf (no callee-saved traffic, no
 * branches, jr $ra tail) whose first 0x28 bytes are the SetRotMatrix
 * template (5-lw + 5-ctc2 into GTE control regs 0..4) and whose body
 * transforms four packed vectors with the MVMVA 1,0,0,3,0 kick
 * (0x4A486012, the ApplyMatrixSV spelling) then folds the matrix's
 * translation row (a0[0x14/0x18/0x1c]) into the MAC results and stores
 * four packed XY + three Z words to (a2), returning a2.
 *
 * Census context (updates the cron-202610251936 interior record): the
 * 2026-10-25 record read this class through mainmenu_jp's walk
 * boundaries, where the same linear code is carved into slices ending
 * mid-expression, and parked the recipes as mid-row-split work. The
 * g3_eu walk keeps one 0x160 row ending at a real function boundary,
 * so the whole-row flip class applies here; the row is byte-identical
 * across g3_eu/g3_jp/mainmenu_jp (retail bytes re-checked equal before
 * the flip), so the cross-target copies follow the wave-2 law.
 *
 * The body stays in ONE asm block: the retail order is all-GTE-sequence
 * and GNU as has no GTE mnemonics (the ApplyMatrixSV law), so the
 * MVMVA kicks are .word spellings; the ctc2 moves assemble natively
 * (the SetRotMatrix law). psyq prototype unattested - auto name kept.
 */
long *func_80048EC0(long *m, char *v, long *out)
{
    __asm__ volatile(
        "lw $8, 0($4)\n"
        "\tlw $9, 4($4)\n"
        "\tlw $10, 8($4)\n"
        "\tlw $11, 12($4)\n"
        "\tlw $12, 16($4)\n"
        "\tctc2 $8, $0\n"
        "\tctc2 $9, $1\n"
        "\tctc2 $10, $2\n"
        "\tctc2 $11, $3\n"
        "\tctc2 $12, $4\n"
        "\tlhu $8, 0($5)\n"
        "\tlw $9, 4($5)\n"
        "\tlw $10, 12($5)\n"
        "\tlui $1, 0xffff\n"
        "\tand $9, $9, $1\n"
        "\tor $8, $8, $9\n"
        "\tmtc2 $8, $0\n"
        "\tmtc2 $10, $1\n"
        "\tnop\n"
        "\t.word 0x4A486012\n" /* mvmva 1,0,0,3,0 */
        "\tlhu $8, 2($5)\n"
        "\tlw $9, 8($5)\n"
        "\tlh $10, 14($5)\n"
        "\tsll $9, $9, 16\n"
        "\tor $8, $8, $9\n"
        "\tmfc2 $11, $9\n"
        "\tmfc2 $12, $10\n"
        "\tmfc2 $13, $11\n"
        "\tmtc2 $8, $0\n"
        "\tmtc2 $10, $1\n"
        "\tnop\n"
        "\t.word 0x4A486012\n" /* mvmva 1,0,0,3,0 */
        "\tlhu $8, 4($5)\n"
        "\tlw $9, 8($5)\n"
        "\tlw $10, 16($5)\n"
        "\tlui $1, 0xffff\n"
        "\tand $9, $9, $1\n"
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
        "\tsw $14, 0($6)\n"
        "\tandi $13, $13, 0xffff\n"
        "\tsll $24, $24, 16\n"
        "\tor $24, $24, $13\n"
        "\tsw $24, 12($6)\n"
        "\tmfc2 $8, $9\n"
        "\tmfc2 $9, $10\n"
        "\tswc2 $11, 16($6)\n"
        "\tlhu $13, 20($5)\n"
        "\tlw $14, 24($5)\n"
        "\tlw $10, 28($5)\n"
        "\tsll $14, $14, 16\n"
        "\tor $13, $13, $14\n"
        "\tmtc2 $13, $0\n"
        "\tmtc2 $10, $1\n"
        "\tnop\n"
        "\t.word 0x4A486012\n" /* mvmva 1,0,0,3,0 */
        "\tsll $12, $12, 16\n"
        "\tandi $8, $8, 0xffff\n"
        "\tor $8, $8, $12\n"
        "\tsw $8, 4($6)\n"
        "\tandi $15, $15, 0xffff\n"
        "\tsll $9, $9, 16\n"
        "\tor $9, $9, $15\n"
        "\tsw $9, 8($6)\n"
        "\tmfc2 $8, $25\n"
        "\tmfc2 $9, $26\n"
        "\tmfc2 $10, $27\n"
        "\tlw $11, 20($4)\n"
        "\tlw $12, 24($4)\n"
        "\tlw $13, 28($4)\n"
        "\tadd $8, $8, $11\n"
        "\tadd $9, $9, $12\n"
        "\tadd $10, $10, $13\n"
        "\tsw $8, 20($6)\n"
        "\tsw $9, 24($6)\n"
        "\tsw $10, 28($6)\n"
    );
    return out;
}

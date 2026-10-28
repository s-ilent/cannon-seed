/* Matched 2026-10-29 through the live-oracle judge loop (g3_eu).
 *
 * The #0x110 GTE rotation-matrix composer, whole-row class at the g3_eu
 * boundary: ONE frameless linear function (no branches, addu $2 tail),
 * currently carved as [0x29AF8 0xe0 asm func_800492F8] + [0x29BD8 0x30 c
 * func_8005DED4]. The split is the 2026-10-25 mega-row tail cut
 * (cron-202610251706): the 0x30 tail landed alone as the shared
 * func_8005DED4 unit (byte-identical in all eight executables at rel
 * +0xE0), leaving the 0xe0 head asm pending "its own decode" (the
 * twelfth-return NEXT). This decode closes that item: the head is NOT
 * opaque staging - it is the SetRotMatrix template (5-lw + 5-ctc2 into
 * the rotation-matrix control regs c0..c4, byte-identical to the landed
 * #0x160 host's first 0x28) followed by THREE strided-vector MVMVA
 * 1,0,0,3,0 transforms (0x4A486012, the ApplyMatrixSV spelling) whose
 * IR1/IR2/IR3 results the tail packs into six lo|hi pairs and commits
 * BACK into c0..c4 (ctc2 $14/$8/$9/$24/$10) - the function composes the
 * GTE rotation matrix from three basis vectors transformed by m, then
 * returns m. Register continuity proves the unit: the head's last two
 * words (andi $8,0xffff; sll $12,16) are consumed by the tail's first
 * word (or $8,$8,$12), and the 0xe0 row ends mid-expression with no
 * store and no jr; nothing jal's the 0x30 row's VA (0x800493D8) in
 * g3_eu's asm - the walk's cut, not a call boundary.
 *
 * The whole body stays in ONE asm block: the retail order is
 * all-GTE-sequence and the MVMVA kicks are .word spellings (GNU as has
 * no GTE mnemonics, the ApplyMatrixSV law); the ctc2/mfc2/mtc2 moves
 * assemble natively (the SetRotMatrix law). The block ends at the addu
 * (the func_8005DED4 tail law): `return ret` through the register-var
 * output emits the frameless jr $31 + nop delay exactly as retail (the
 * gcc's-own-return lesson: ending the block early lets cc1 emit it).
 *
 * The shared func_8005DED4 unit stays landed for the seven targets
 * whose mega-row tails are still cut; g3_eu is the first target where
 * the whole 0x110 lands as one row, retiring its tail row (yaml-only:
 * ratchets hold except the new unit's own mention). psyq prototype
 * unattested - auto name kept.
 */
long *func_800492F8(long *m, char *b)
{
    register long *ret asm("$2");
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
        "\tandi $13, $13, 0xffff\n"
        "\tsll $24, $24, 16\n"
        "\tor $24, $24, $13\n"
        "\tmfc2 $8, $9\n"
        "\tmfc2 $9, $10\n"
        "\tmfc2 $10, $11\n"
        "\tandi $8, $8, 0xffff\n"
        "\tsll $12, $12, 16\n"
        "\tor $8, $8, $12\n"
        "\tandi $15, $15, 0xffff\n"
        "\tsll $9, $9, 16\n"
        "\tor $9, $9, $15\n"
        "\tctc2 $14, $0\n"
        "\tctc2 $8, $1\n"
        "\tctc2 $9, $2\n"
        "\tctc2 $24, $3\n"
        "\tctc2 $10, $4\n"
        "\taddu $2, $4, $0"
        : "=r"(ret));
    return ret;
}

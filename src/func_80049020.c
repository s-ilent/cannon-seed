/* The compose-rotation writer family's third form - the commit-at-out
 * variant (g3_eu row, one src unit per row under the row's own walk
 * name; the seven members are byte-identical 0x10c rows, one per target
 * except mainmenu_jp). Body = the landed compose-rotation anchor's
 * transcription (the two-arg commit-at-(a0) form) with the commit moved to
 * the THIRD pointer: the head still loads the current rotation matrix from
 * (a0) via ctc2 into c0..c4, the three MVMVA 1,0,0,3,0 passes multiply the
 * packed three-vector record at (a1) exactly as the anchor schedules them
 * (staging interleaved with the previous pass's mfc2 reads), then the five
 * packed product words store at (a2) - halfword interleave
 * [w0=v1.x|v2.x, w1=v3.x|v2.x, w2=v3.y|v2.y, w3=v1.z|v2.z, w4=v3.z],
 * IR3 of the third pass stored raw as swc2 - and the return value is the
 * out pointer. Word-level identity: the pre-check (scripts/e3dcv_check.py)
 * proves the seven retail rows byte-identical and the delta vs the landed
 * anchor exactly the six commit-destination words (five stores + return
 * addu, $4 -> $6).
 *
 * psyq prototype: long *<row>(long *m, long *rec, long *out); args
 * stay long* so gcc emits no caller-side extensions; the record's packed
 * interleave is the caller's contract (this body never unmasks it).
 */
long *func_80049020(long *m, long *rec, long *out)
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
        "\tlui $1, 0xffff\n"
        "\tand $9, $9, $1\n"
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
        "\tsw $14, 0x0($6)\n"
        "\tandi $13, $13, 0xffff\n"
        "\tsll $24, $24, 16\n"
        "\tor $24, $24, $13\n"
        "\tsw $24, 0xc($6)\n"
        "\tmfc2 $8, $9\n"
        "\tmfc2 $9, $10\n"
        "\tandi $8, $8, 0xffff\n"
        "\tsll $12, $12, 16\n"
        "\tor $8, $8, $12\n"
        "\tsw $8, 0x4($6)\n"
        "\tandi $15, $15, 0xffff\n"
        "\tsll $9, $9, 16\n"
        "\tor $9, $9, $15\n"
        "\tsw $9, 0x8($6)\n"
        "\tswc2 $11, 0x10($6)\n"
        "\taddu $2, $6, $0"
        : "=r"(ret));
    return ret;
}

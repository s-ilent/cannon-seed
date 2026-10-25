/* Staged 2026-10-25 (window cron-202610252321) - the graveyard pair's
 * SECOND half (func_8005E4E8, 0x8005E4E8..0x8005E5F4, 0x10c), the walk's
 * "double-rotate mega-host" resolved by the boundary probe into TWO whole
 * 0x10c functions back to back (window cron-202610252051). Byte-identical
 * to the twin src/func_8005E3DC.c except SIX words - the commit base and
 * the return: this unit stages from (a1) and COMMITS AT (a1) IN PLACE,
 * returning a1 (the twin commits at (a0) and returns a0). The record is
 * pre-multiplied by the CURRENT rotation matrix (loaded from (a0) first,
 * read-only here): the compose-rotation member of the SetRotMatrix-shaped
 * writer family, in-place form.
 *
 * Body decode: identical pipeline to the twin's header (SetRotMatrix head
 * from (a0) -> c0..c4; three MVMVA 0x4A486012 passes over the packed
 * three-vector record at (a1), the pass staging interleaved with the
 * previous pass's mfc2 reads; the five packed result words committed at
 * (a1), the halfword interleave [w0=v1.x|v2.x, w1=v3.x|v1.y, w2=v3.y|v2.y,
 * w3=v1.z|v2.z, w4=v3.z], IR3 of pass 3 raw as swc2 $11) - then addu
 * $2,$5,$0 + jr + nop (return the record pointer).
 *
 * True extent inside mainmenu_jp's data_8005E1B8 graveyard tail row
 * (yaml 0x3E9B8 # 0x43c; file offset 0x3ECE8): ROW1 of the pair ends
 * exactly where this unit starts, and this unit's end 0x3EDF4 is the row
 * end = the next yaml entry (ApplyMatrixLV's start). The yaml three-way
 * split is scripts/surgery_e3dc_pair.py (independent of the staged DED4
 * wave - different row).
 *
 * Proof basis (window cron-202610252321, oracle DOWN): all 67 words are
 * WORD-IDENTICAL to the committed row's encoding
 * (scripts/prove_e3dc_pair.py, offline, zero oracle - the committed-row
 * class). No reloc slots: frameless leaf, the dw=0 class. The x8 twin
 * word-search is the oracle's first decoding job on the disc-return
 * (--sites, witness-gated in the prove script).
 *
 * The block carries the retail words 1:1 (ctc2/mtc2/mfc2/swc2 assemble
 * natively per the landed precedents; the mvmva stays .word-encoded
 * exactly as ApplyMatrixLV banked it; the return tail is the landed
 * register-var pattern).
 *
 * psyq prototype: long *func_8005E4E8(long *m, long *rec); args stay
 * long* so gcc emits no caller-side extensions.
 */
long *func_8005E4E8(long *m, long *rec)
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

/* Staged 2026-10-25 (window cron-202610252321) - the graveyard pair's
 * FIRST half (func_8005E3DC, 0x8005E3DC..0x8005E4E8, 0x10c), the walk's
 * "double-rotate mega-host" resolved by the boundary probe into TWO whole
 * 0x10c functions back to back (window cron-202610252051: the
 * instruction-level confirmation of the 1551 census measurement). Both
 * halves carry byte-identical instruction streams except the commit
 * destination and the return - this unit stages from (a1) and COMMITS AT
 * (a0), returning a0; the twin src/func_8005E4E8.c commits at (a1) in
 * place and returns a1.
 *
 * Body decode (register level, the 2051 record + this window's
 * transcription): a SetRotMatrix-shaped rotation COMPOSER through the
 * GTE -
 *
 *   head:  lw $8..$12, 0x0..0x10($4)  + ctc2 into c0..c4
 *          (the ten-word SetRotMatrix head: (a0)'s five matrix words
 *          become the CURRENT rotation matrix)
 *   then three passes over the packed three-vector record at (a1), one
 *   MVMVA 0x4A486012 each (multiply by the current rotation, no
 *   translation), the pass staging interleaved with the previous pass's
 *   mfc2 reads exactly as retail scheduled it:
 *     pass 1: VXY0 = lhu +0x0($5) | (lw +0x4($5) & 0xffff0000),
 *             VZ0 = lw +0xc($5) raw (the GTE reads VZ0's low half)
 *     pass 2: VXY0 = lhu +0x2($5) | (lw +0x8($5) low << 16),
 *             VZ0 = lh +0xe($5) sign-extended; reads IR1-3 -> $11/$12/$13
 *     pass 3: VXY0 = lhu +0x4($5) | (lw +0x8($5) & 0xffff0000),
 *             VZ0 = lw +0x10($5) raw;  reads IR1-3 -> $14/$15/$24
 *   commit: the five packed result words at (a0), the halfword
 *   interleave of the three IR lanes across the five-word layout
 *   [w0=v1.x|v2.x, w1=v3.x|v1.y, w2=v3.y|v2.y, w3=v1.z|v2.z, w4=v3.z],
 *   IR3 of pass 3 stored raw as swc2 $11; then addu $2,$4,$0 + jr + nop
 *   (return the matrix pointer).
 *
 * Semantically: the record at (a1) is a rotation in the walk's packed
 * interleave; the body multiplies it by the CURRENT rotation matrix
 * (loaded from (a0) first) and overwrites (a0) with the product -
 * the compose-rotation member of the SetRotMatrix-shaped writer family
 * the graveyard law names, copy-form (the twin func_8005E4E8 is the
 * in-place form).
 *
 * True extent inside mainmenu_jp's data_8005E1B8 graveyard tail row
 * (yaml 0x3E9B8 # 0x43c; file offset 0x3EBDC): ROW2 = the three
 * mainmenu_jp singletons 0x224 + THIS unit 0x10c + the twin 0x10c =
 * 0x43c EXACT (the probe's boundary table). The yaml three-way split is
 * scripts/surgery_e3dc_pair.py (independent of the staged DED4 wave -
 * different row).
 *
 * Proof basis (window cron-202610252321, oracle DOWN): all 67 words are
 * WORD-IDENTICAL to the committed row's encoding
 * (scripts/prove_e3dc_pair.py, offline, zero oracle - the committed-row
 * class). No reloc slots: frameless leaf, no jal, no lui/%lo outside the
 * 0xffff mask constant (the lui $1 is position-independent), the dw=0
 * class first-shot landings want. The x8 twin word-search is the
 * oracle's first decoding job on the disc-return (--sites, witness-gated
 * in the prove script): in the seven non-mainmenu_jp targets the twins
 * sit INSIDE the five walk mega-row sizes (0x10c IS one of the five row
 * sizes, so the search must also decide head-vs-interior per target).
 *
 * The block carries the retail words 1:1 (ctc2/mtc2/mfc2/swc2 assemble
 * natively per the landed precedents; the mvmva stays .word-encoded
 * exactly as ApplyMatrixLV banked it; the return tail is the landed
 * register-var pattern).
 *
 * psyq prototype: long *func_8005E3DC(long *m, long *rec); args stay
 * long* so gcc emits no caller-side extensions; the record's packed
 * interleave is the caller's contract (this body never unmasks it).
 */
long *func_8005E3DC(long *m, long *rec)
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

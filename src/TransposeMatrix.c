/* Matched 2026-10-26 (window cron-202610252019) - the TransposeMatrix
 * member of the LIBGTE matrix SDK set, x6 across the region pairs. The
 * identity is banked in config/sdk_anchors.txt at one site per module
 * ("TransposeMatrix ? LIBGTE unique"), and this window's pair-report
 * sweep (the row-family-normalized gate's first pool read) proves every
 * region pair byte-identical at 100.00% while both sides are still asm:
 *
 *   slps_00270   file 0x14668, VA 0x80033E68
 *   sces_00269   file 0x14130, VA 0x80033930
 *   g3_jp        file 0x30ADC, VA 0x800502DC
 *   g3_eu        file 0x30418, VA 0x80056E18
 *   g3org_jp     file 0x2DF78, VA 0x8004D778
 *   g3org_eu     file 0x2D86C, VA 0x80053C7C
 *
 * (each site was its own sdk-annotated whole asm row under a woven-era
 * scanner label before this flip; scripts/land_transposematrix.sh and
 * scripts/prove_transposematrix.py carry the per-target name mapping.)
 *
 * mainmenu_jp/eu carry no copy (the pair pool lists none and the yaml
 * has no sdk-annotated 0x50 row) - the member is x6, not x8.
 *
 * The body is frameless pure CPU code: a software-pipelined 3x3
 * halfword transpose. The register rotation $9/$10/$11 keeps one to two
 * loads ahead of the stores - the load for element k+1 issues before
 * the store of element k - and the return value is staged early as
 * addu $2,$5,$0 (dst, the ApplyMatrixLV register-var pattern). The last
 * load (m[2][2] at +0x10) lands in $9 and its store is the full retail
 * tail: the branch-delay-slot sh of the frameless jr $ra return.
 *
 * dst[i][j] = src[j][i] over the nine MATRIX rotation halfwords
 * (element r,c lives at offset 2*(3r+c)): dst +0x00,+0x04,+0x08 take
 * the src column words 0x0/0x6/0xC read as halfwords, dst +0x02,+0x06,
 * +0x0A take 0x2/0x8/0xE reversed, and the +0x0E/+0x10 tail swaps the
 * last two off-diagonal pairs. No multiply, no GTE - pure CPU.
 *
 * The block carries the retail words 0..17 1:1 (lh/sh/addu assemble
 * natively; no reloc slots - frameless leaf, no jal, no lui/%lo). The
 * final store is real C: `((short *)dst)[8] = last` with last bound to
 * $9, so GCC's delayed-branch fill places the halfword store into the
 * return jump's delay slot exactly as retail does (the value is
 * produced by the block's second-to-last load, the store depends on
 * nothing else, and the cc_post return-move unfill does not fire - ret
 * is already in $2 via the register var). The word count: 18 block
 * words + jr + delay sh = 0x50.
 *
 * psyq prototype: MATRIX *TransposeMatrix(MATRIX *m, MATRIX *mt);
 * transposes m INTO mt and returns mt (the retail body returns $5 via
 * the early addu). Args stay long* so gcc emits no caller-side
 * extensions; the one halfword store is typed through the short* cast.
 */
long *TransposeMatrix(long *src, long *dst)
{
    register long *ret asm("$2");
    register long last asm("$9");
    __asm__ volatile(
        "lh $9, 0x0($4)\n"
        "\taddu $2, $5, $0\n"
        "\tsh $9, 0x0($5)\n"
        "\tlh $10, 0x6($4)\n"
        "\tlh $9, 0xc($4)\n"
        "\tsh $10, 0x2($5)\n"
        "\tlh $11, 0x2($4)\n"
        "\tsh $9, 0x4($5)\n"
        "\tlh $10, 0x8($4)\n"
        "\tsh $11, 0x6($5)\n"
        "\tlh $9, 0xe($4)\n"
        "\tsh $10, 0x8($5)\n"
        "\tlh $11, 0x4($4)\n"
        "\tsh $9, 0xa($5)\n"
        "\tlh $10, 0xa($4)\n"
        "\tsh $11, 0xc($5)\n"
        "\tlh $9, 0x10($4)\n"
        "\tsh $10, 0xe($5)"
        : "=r"(ret), "=r"(last));
    ((short *)dst)[8] = (short)last;
    return ret;
}

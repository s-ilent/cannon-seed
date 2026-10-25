/* Matched 2026-10-25 (window cron-202610251206) - the ScaleMatrix member
 * of the LIBGTE matrix SDK set, x8 across every executable. The identity
 * is banked in config/sdk_anchors.txt at two independent sites:
 *
 *   0x80049BC8 0x124  ScaleMatrix ? LIBGTE@3.3 window-verbatim
 *   0x8004A1B0 0x124  ScaleMatrix ? LIBGTE@3.3 window-verbatim  (g3_jp)
 *
 * and the TransMatrix wave's twin scan proved the 0x124 body byte-
 * identical in all eight executables: seven targets carry it as its own
 * sdk-annotated asm row immediately after the TransMatrix row (the
 * graveyard pair), mainmenu_jp's copy was re-homed last window as the
 * data_8005E6C4 data row when the data_8005E6A0 split opened TransMatrix.
 *
 * The body is frameless pure CPU code: five unrolled product blocks over
 * the record's 3x3 rotation halfwords and the vector at ($5). Each block
 * sign-extends the record word's low half (andi 0xffff / sll 16 / sra 16),
 * multiplies it unsigned against the next vector word's low component
 * (multu, the multiplier registers $11/$12/$13 cycle vx, vy, vz, vx, vy
 * across the five stores), then merges the two scaled halves of the
 * record word as (mflo >> 12 low half) | (mflo >> 12) << 16 through the
 * andi/or pair and stores the product word back. The fifth block carries
 * only one product and its store is the full sra-12 word written by the
 * branch-delay-slot sw of the frameless jr $ra return - it overwrites the
 * matrix's +0x10 tail word (m[2][2] plus the +0x12 pad halfword, which
 * receives the sign extension of the final product). The return value is
 * the record pointer, staged early as addu $2,$4,$0 (the ApplyMatrixLV
 * register-var pattern).
 *
 * The block carries the retail words 1:1 (multu/mflo/sra assemble
 * natively; no reloc slots - frameless leaf, no jal, no lui/%lo). The
 * final store is real C: `m[4] = last` with the product register-bound
 * to $9, so GCC's delayed-branch fill places it into the return jump's
 * delay slot exactly as retail does (the value is produced by the
 * block's last sra, the store depends on nothing else, and the cc_post
 * return-move unfill does not fire - ret is already in $2 via the
 * register var). The word counts: 71 block words + jr + delay sw = 0x124.
 *
 * psyq prototype: MATRIX *ScaleMatrix(MATRIX *m, VECTOR v); the vector
 * aggregate arrives by reference under the o32 ABI, so the callee reads
 * ($5) - the same convention every landed SDK row documents. Args stay
 * long* so gcc emits no caller-side extensions.
 */
long *ScaleMatrix(long *m, long *v)
{
    register long *ret asm("$2");
    register long last asm("$9");
    __asm__ volatile(
        "lw $8, 0x0($4)\n"
        "\tlw $11, 0x0($5)\n"
        "\tandi $9, $8, 0xffff\n"
        "\tsll $9, $9, 16\n"
        "\tsra $9, $9, 16\n"
        "\tmultu $9, $11\n"
        "\tlw $12, 0x4($5)\n"
        "\tsra $10, $8, 16\n"
        "\tlw $13, 0x8($5)\n"
        "\tlw $8, 0x4($4)\n"
        "\taddu $2, $4, $0\n"
        "\tmflo $9\n"
        "\tsra $9, $9, 12\n"
        "\tandi $9, $9, 0xffff\n"
        "\tmultu $10, $12\n"
        "\tmflo $10\n"
        "\tsra $10, $10, 12\n"
        "\tsll $10, $10, 16\n"
        "\tor $9, $9, $10\n"
        "\tsw $9, 0x0($4)\n"
        "\tandi $9, $8, 0xffff\n"
        "\tsll $9, $9, 16\n"
        "\tsra $9, $9, 16\n"
        "\tmultu $9, $13\n"
        "\tsra $10, $8, 16\n"
        "\tlw $8, 0x8($4)\n"
        "\tmflo $9\n"
        "\tsra $9, $9, 12\n"
        "\tandi $9, $9, 0xffff\n"
        "\tmultu $10, $11\n"
        "\tmflo $10\n"
        "\tsra $10, $10, 12\n"
        "\tsll $10, $10, 16\n"
        "\tor $9, $9, $10\n"
        "\tsw $9, 0x4($4)\n"
        "\tandi $9, $8, 0xffff\n"
        "\tsll $9, $9, 16\n"
        "\tsra $9, $9, 16\n"
        "\tmultu $9, $12\n"
        "\tsra $10, $8, 16\n"
        "\tlw $8, 0xc($4)\n"
        "\tmflo $9\n"
        "\tsra $9, $9, 12\n"
        "\tandi $9, $9, 0xffff\n"
        "\tmultu $10, $13\n"
        "\tmflo $10\n"
        "\tsra $10, $10, 12\n"
        "\tsll $10, $10, 16\n"
        "\tor $9, $9, $10\n"
        "\tsw $9, 0x8($4)\n"
        "\tandi $9, $8, 0xffff\n"
        "\tsll $9, $9, 16\n"
        "\tsra $9, $9, 16\n"
        "\tmultu $9, $11\n"
        "\tsra $10, $8, 16\n"
        "\tlw $8, 0x10($4)\n"
        "\tmflo $9\n"
        "\tsra $9, $9, 12\n"
        "\tandi $9, $9, 0xffff\n"
        "\tmultu $10, $12\n"
        "\tmflo $10\n"
        "\tsra $10, $10, 12\n"
        "\tsll $10, $10, 16\n"
        "\tor $9, $9, $10\n"
        "\tsw $9, 0xc($4)\n"
        "\tandi $9, $8, 0xffff\n"
        "\tsll $9, $9, 16\n"
        "\tsra $9, $9, 16\n"
        "\tmultu $9, $13\n"
        "\tmflo $9\n"
        "\tsra $9, $9, 12"
        : "=r"(ret), "=r"(last));
    m[4] = last;
    return ret;
}

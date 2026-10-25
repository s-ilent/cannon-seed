/* Matched 2026-10-25 (window cron-202610251321) - the ScaleMatrixL member
 * of the LIBGTE matrix SDK set, x8 across every executable. All eight
 * sites are anchor-banked verbatim ("ScaleMatrixL ? LIBGTE unique"),
 * including mainmenu_jp's copy inside the data_80066CF4 graveyard row and
 * sces_00269's whole row (invisible to the census - its refusal stands -
 * but banked by the anchors and word-proven here like every other site).
 *
 * The body is the ScaleMatrix template (landed last window, x8 first
 * shot) under the family's twin-scan law: eq 65/73, dw=8/73, votes 11 at
 * every site, and the eight differing words are UNIFORM across all eight
 * copies. The delta decodes as the transpose law:
 *
 *   - ScaleMatrix multiplies each COLUMN j of the packed rotation
 *     matrix by v[j] (right scaling): the $11/$12/$13 multiplier cycle
 *     vx,vy | vz,vx | vy,vz | vx,vy | vz.
 *   - ScaleMatrixL multiplies each ROW i by v[i] (left scaling - the
 *     "L"): the same five product blocks, but the cycle reads
 *     vx,vx | vx,vy | vy,vy | vz,vz | vz, i.e. row0 (R11,R12,R13) by vx,
 *     row1 (R21,R22,R23) by vy, row2 (R31,R32,R33) by vz. Six multu
 *     rt operands flip; nothing else in the product machinery moves.
 *   - one schedule swap at block 1: retail issues sra $10,$8,16 BEFORE
 *     lw $12,0x4($5) (ScaleMatrix orders the load first) - independent
 *     instructions, pure schedule, carried verbatim below.
 *
 * The frameless jr+delay-store tail is real C exactly as ScaleMatrix:
 * `m[4] = last` with the product register-bound to $9, so GCC's
 * delayed-branch fill places the store into the return jump's delay
 * slot; the return value is the record pointer staged early as
 * addu $2,$4,$0. The block carries the first 71 retail words verbatim
 * (multu/mflo/sra assemble natively; no reloc slots - frameless leaf,
 * no jal, no lui/%lo); word counts 71 + jr + delay sw = 0x124.
 *
 * psyq prototype: MATRIX *ScaleMatrixL(MATRIX *m, VECTOR v); the vector
 * aggregate arrives by reference under the o32 ABI, so the callee reads
 * ($5) - the same convention every landed SDK row documents. Args stay
 * long* so gcc emits no caller-side extensions.
 */
long *ScaleMatrixL(long *m, long *v)
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
        "\tsra $10, $8, 16\n"
        "\tlw $12, 0x4($5)\n"
        "\tlw $13, 0x8($5)\n"
        "\tlw $8, 0x4($4)\n"
        "\taddu $2, $4, $0\n"
        "\tmflo $9\n"
        "\tsra $9, $9, 12\n"
        "\tandi $9, $9, 0xffff\n"
        "\tmultu $10, $11\n"
        "\tmflo $10\n"
        "\tsra $10, $10, 12\n"
        "\tsll $10, $10, 16\n"
        "\tor $9, $9, $10\n"
        "\tsw $9, 0x0($4)\n"
        "\tandi $9, $8, 0xffff\n"
        "\tsll $9, $9, 16\n"
        "\tsra $9, $9, 16\n"
        "\tmultu $9, $11\n"
        "\tsra $10, $8, 16\n"
        "\tlw $8, 0x8($4)\n"
        "\tmflo $9\n"
        "\tsra $9, $9, 12\n"
        "\tandi $9, $9, 0xffff\n"
        "\tmultu $10, $12\n"
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
        "\tmultu $10, $12\n"
        "\tmflo $10\n"
        "\tsra $10, $10, 12\n"
        "\tsll $10, $10, 16\n"
        "\tor $9, $9, $10\n"
        "\tsw $9, 0x8($4)\n"
        "\tandi $9, $8, 0xffff\n"
        "\tsll $9, $9, 16\n"
        "\tsra $9, $9, 16\n"
        "\tmultu $9, $13\n"
        "\tsra $10, $8, 16\n"
        "\tlw $8, 0x10($4)\n"
        "\tmflo $9\n"
        "\tsra $9, $9, 12\n"
        "\tandi $9, $9, 0xffff\n"
        "\tmultu $10, $13\n"
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

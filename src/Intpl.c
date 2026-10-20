/* Matched 2026-10-20 through the round-trip oracle (g3_jp first;
 * region-pair 100.00% byte twins across g3_jp/g3_eu, the matching
 * lane's libgte math cluster queue item).
 *
 * LIBGTE Intpl: the source color triple (a0) loads into IR1/IR2/IR3
 * ($9/$10/$11), the interpolation parameter (a1, cpu $5) into IR0
 * ($8), and the intpl command (0x4A980011 - GNU as has no GTE
 * mnemonics, banked as its exact retail .word) interpolates the
 * linear-light result into RGB2 ($22), which stores through a2. Void;
 * the epilogue is the plain jr $ra with a nop delay slot.
 *
 * psyq prototype: void Intpl(CVECTOR *color0, long p, CVECTOR *out);
 * args stay long* so gcc emits no caller-side extensions. One
 * volatile asm block with the retail register assignments hardcoded
 * (the cop2 ops are not reachable from plain C).
 */
void Intpl(long *a0, long a1, long *a2)
{
    __asm__ volatile(
        "lwc2 $9, 0x0($4)\n"
        "\tlwc2 $10, 0x4($4)\n"
        "\tlwc2 $11, 0x8($4)\n"
        "\tmtc2 $5, $8\n"
        "\tnop\n"
        "\t.word 0x4A980011\n" /* intpl */
        "\tswc2 $22, 0x0($6)\n");
}

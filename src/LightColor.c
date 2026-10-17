/* Matched 2026-10-17 through the round-trip oracle (g3_eu first;
 * cross-target byte-identical in g3_eu, g3_jp, slps_00270 - the matching
 * lane's GTE families queue item).
 *
 * LIBGTE LightColor: the source color (a0) goes into IR1/IR2/IR3
 * ($9/$10/$11), mvmva 1,2,3,1,1 (0x4A4DA412 - GNU as has no GTE
 * mnemonics, banked as its exact retail .word) multiplies the local
 * color matrix over them, and the lit IR1/IR2/IR3 results store through
 * a1. Void; the epilogue is the plain jr $ra with a nop delay slot.
 *
 * psyq prototype: void LightColor(CVECTOR *color, CVECTOR *colorout);
 * args stay long* so gcc emits no caller-side extensions.
 */
void LightColor(long *a0, long *a1)
{
    __asm__ volatile(
        "lwc2 $9, 0x0($4)\n"
        "\tlwc2 $10, 0x4($4)\n"
        "\tlwc2 $11, 0x8($4)\n"
        "\tnop\n"
        "\t.word 0x4A4DA412\n" /* mvmva 1,2,3,1,1 */
        "\tswc2 $9, 0x0($5)\n"
        "\tswc2 $10, 0x4($5)\n"
        "\tswc2 $11, 0x8($5)");
}

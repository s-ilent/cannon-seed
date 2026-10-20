/* Matched 2026-10-20 through the round-trip oracle (g3_jp first;
 * region-pair 100.00% byte twins across g3_jp/g3_eu, the matching
 * lane's libgte math cluster queue item).
 *
 * LIBGTE DpqColor3: the three source colors (a0/a1/a2) load into
 * RGB0/RGB1/RGB2 ($20/$21/$22), the a2 word also reloads into the RGB
 * field ($6 - retail re-reads the same pointer), the depth-cue
 * parameter (a3, cpu $7) into IR0 ($8), and the dpct command
 * (0x4AF8002A - GNU as has no GTE mnemonics, banked as its exact
 * retail .word) interpolates all three through the depth cue; the
 * results store through the caller's stacked output pointers (o32
 * args 5-7 at 0x10/0x14/0x18($sp)), loaded after the command exactly
 * as retail schedules them.
 *
 * psyq prototype: void DpqColor3(CVECTOR *c0, CVECTOR *c1,
 * CVECTOR *c2, long p, CVECTOR *o0, CVECTOR *o1, CVECTOR *o2); args
 * stay long* so gcc emits no caller-side extensions. The stacked-arg
 * loads need the one-block volatile shape (gcc's scheduler floats
 * sp-relative loads across plain volatile asms; one block pins the
 * retail order).
 */
void DpqColor3(long *a0, long *a1, long *a2, long a3, long *o0,
               long *o1, long *o2)
{
    __asm__ volatile(
        "lwc2 $20, 0x0($4)\n"
        "\tlwc2 $21, 0x0($5)\n"
        "\tlwc2 $22, 0x0($6)\n"
        "\tlwc2 $6, 0x0($6)\n"
        "\tmtc2 $7, $8\n"
        "\tnop\n"
        "\t.word 0x4AF8002A\n" /* dpct */
        "\tlw $8, 0x10($sp)\n"
        "\tlw $9, 0x14($sp)\n"
        "\tlw $10, 0x18($sp)\n"
        "\tswc2 $20, 0x0($8)\n"
        "\tswc2 $21, 0x0($9)\n"
        "\tswc2 $22, 0x0($10)\n"
        : : : "8", "9", "10");
}

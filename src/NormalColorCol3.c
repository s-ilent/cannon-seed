/* Matched 2026-10-20 through the round-trip oracle (g3org_jp first;
 * region-pair 100.00% byte twins across g3org_jp/g3org_eu, and
 * mainmenu_jp's own rows at true 0x80079F6C/0x80079FD4 prove 100.00%
 * byte twins of the same two functions - the pair-report pick list's
 * next real compiler-output cluster in g3org, landed across all three
 * targets in one wave; the mainmenu_eu copies sit in a not-yet-walked
 * zone of the eu basis and stay asm until that layout work).
 *
 * LIBGTE NormalColorCol3: the three vertices (a0/a1/a2) load into
 * the V registers ($0-$5) and the colour (a3) into RGB ($6); the
 * ncct command (0x4B18043F - GNU as has no GTE mnemonics, banked as
 * its exact retail .word) lights all three normals into RGB0/1/2
 * ($20/$21/$22), which store through the caller's stacked output
 * pointers (args 5-7 at 0x10/0x14/0x18($sp)), loaded after the
 * command exactly as retail schedules them. The Col sister has no
 * depth-cue parameter - the slot before the command is a plain nop
 * where Dpq3 loads IR0.
 *
 * psyq prototype: void NormalColorCol3(CVECTOR *v0, CVECTOR *v1,
 * CVECTOR *v2, CVECTOR *rgb, CVECTOR *o0, CVECTOR *o1, CVECTOR *o2);
 * args stay long* so gcc emits no caller-side extensions. The
 * stacked-arg loads need the one-block volatile shape (gcc's
 * scheduler floats sp-relative loads across plain volatile asms; one
 * block pins the retail order). Frameless leaf - the caller's
 * 0x10($sp) window is read exactly as retail.
 */
void NormalColorCol3(long *a0, long *a1, long *a2, long *a3, long *o0,
                     long *o1, long *o2)
{
    __asm__ volatile(
        "lwc2 $0, 0x0($4)\n"
        "\tlwc2 $1, 0x4($4)\n"
        "\tlwc2 $2, 0x0($5)\n"
        "\tlwc2 $3, 0x4($5)\n"
        "\tlwc2 $4, 0x0($6)\n"
        "\tlwc2 $5, 0x4($6)\n"
        "\tlwc2 $6, 0x0($7)\n"
        "\tnop\n"
        "\t.word 0x4B18043F\n" /* ncct */
        "\tlw $8, 0x10($sp)\n"
        "\tlw $9, 0x14($sp)\n"
        "\tlw $10, 0x18($sp)\n"
        "\tswc2 $20, 0x0($8)\n"
        "\tswc2 $21, 0x0($9)\n"
        "\tswc2 $22, 0x0($10)\n"
        : : : "8", "9", "10");
}

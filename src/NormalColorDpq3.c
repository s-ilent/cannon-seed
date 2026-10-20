/* Matched 2026-10-20 through the round-trip oracle (g3org_jp first;
 * region-pair 100.00% byte twins across g3org_jp/g3org_eu, and
 * mainmenu_jp's own rows at true 0x80079F6C/0x80079FD4 prove 100.00%
 * byte twins of the same two functions - the pair-report pick list's
 * next real compiler-output cluster in g3org, landed across all three
 * targets in one wave; the mainmenu_eu copies sit in a not-yet-walked
 * zone of the eu basis and stay asm until that layout work).
 *
 * LIBGTE NormalColorDpq3: the three vertices (a0/a1/a2) load into
 * the V registers ($0-$5), the colour (a3) into RGB ($6), and the
 * depth-cue parameter (stack arg at 0x10($sp)) straight into IR0
 * ($8) with one lwc2 - no cpu register round-trip; the ncdt command
 * (0x4AF80416 - GNU as has no GTE mnemonics, banked as its exact
 * retail .word) lights all three normals through the depth cue and
 * the results store through the caller's stacked output pointers
 * (args 6-8 at 0x14/0x18/0x1C($sp)), loaded after the command
 * exactly as retail schedules them.
 *
 * psyq prototype: void NormalColorDpq3(CVECTOR *v0, CVECTOR *v1,
 * CVECTOR *v2, CVECTOR *rgb, long p, CVECTOR *o0, CVECTOR *o1,
 * CVECTOR *o2); args stay long* so gcc emits no caller-side
 * extensions. The stacked-arg loads need the one-block volatile
 * shape (gcc's scheduler floats sp-relative loads across plain
 * volatile asms; one block pins the retail order). Frameless leaf -
 * the caller's 0x10($sp) window is read exactly as retail.
 */
void NormalColorDpq3(long *a0, long *a1, long *a2, long *a3, long a4,
                     long *o0, long *o1, long *o2)
{
    __asm__ volatile(
        "lwc2 $0, 0x0($4)\n"
        "\tlwc2 $1, 0x4($4)\n"
        "\tlwc2 $2, 0x0($5)\n"
        "\tlwc2 $3, 0x4($5)\n"
        "\tlwc2 $4, 0x0($6)\n"
        "\tlwc2 $5, 0x4($6)\n"
        "\tlwc2 $6, 0x0($7)\n"
        "\tlwc2 $8, 0x10($sp)\n"
        "\tnop\n"
        "\t.word 0x4AF80416\n" /* ncdt */
        "\tlw $8, 0x14($sp)\n"
        "\tlw $9, 0x18($sp)\n"
        "\tlw $10, 0x1C($sp)\n"
        "\tswc2 $20, 0x0($8)\n"
        "\tswc2 $21, 0x0($9)\n"
        "\tswc2 $22, 0x0($10)\n"
        : : : "8", "9", "10");
}

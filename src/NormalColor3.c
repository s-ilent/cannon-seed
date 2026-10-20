/* Matched 2026-10-20 through the round-trip oracle (mainmenu_jp first;
 * the cross-target twin probe pre-banked the exact twins, so one decode
 * lands 4 rows in one wave: mainmenu_jp true 0x8006E49C (the eighth row
 * of the single-light run, the only one without a landed twin),
 * g3org_jp 0x80057424, g3org_eu 0x80056E20 and g3_eu 0x800599CC - all
 * four 100.00% byte twins of each other).
 *
 * LIBGTE NormalColor3: the three vertices (a0/a1/a2) load into the V
 * registers ($0-$5) and the nct command (0x4AD80420 - GNU as has no
 * GTE mnemonics, banked as its exact retail .word) lights all three
 * normals into RGB0/1/2 ($20/$21/$22) with no per-call colour and no
 * depth cue: the slot before the command is a plain nop where the Col
 * sisters load RGB ($6) from a3 and the Dpq sisters load IR0 - NCT
 * takes the colour from the light matrix's background colour. RGB0
 * stores through a3; RGB1/RGB2 store through the caller's stacked
 * output pointers (args 5-6 at 0x10/0x14($sp)), loaded after the
 * command exactly as retail schedules them.
 *
 * psyq prototype: void NormalColor3(CVECTOR *v0, CVECTOR *v1,
 * CVECTOR *v2, CVECTOR *rgb0, CVECTOR *o1, CVECTOR *o2);
 * args stay long* so gcc emits no caller-side extensions. The
 * stacked-arg loads need the one-block volatile shape (gcc's
 * scheduler floats sp-relative loads across plain volatile asms; one
 * block pins the retail order). Frameless leaf - the caller's
 * 0x10($sp) window is read exactly as retail.
 */
void NormalColor3(long *a0, long *a1, long *a2, long *a3, long *o1,
                  long *o2)
{
    __asm__ volatile(
        "lwc2 $0, 0x0($4)\n"
        "\tlwc2 $1, 0x4($4)\n"
        "\tlwc2 $2, 0x0($5)\n"
        "\tlwc2 $3, 0x4($5)\n"
        "\tlwc2 $4, 0x0($6)\n"
        "\tlwc2 $5, 0x4($6)\n"
        "\tnop\n"
        "\t.word 0x4AD80420\n" /* nct */
        "\tlw $8, 0x10($sp)\n"
        "\tlw $9, 0x14($sp)\n"
        "\tswc2 $20, 0x0($7)\n"
        "\tswc2 $21, 0x0($8)\n"
        "\tswc2 $22, 0x0($9)\n"
        : : : "8", "9");
}

/* Matched 2026-10-24 through the round-trip oracle (g3_eu / g3org_eu /
 * mainmenu_eu, one census wave).
 *
 * LIBGS MATRIX3 member .text+0x580 (extent 0x1c; curated `len_param`,
 * sdk_members.py unique placement). Frameless leaf: bit length of a
 * positive int — v0 = floor(log2(n)) + 1 for n > 0, else 0. GCC 2.6.3
 * -O2 shape, first compile: guard `blez $a0` over the do-while, loop
 * `sra $a0,$a0,1` + `bgtz` back with the `addiu $v0,$v0,1` increment
 * in the branch delay slot (unconditional inside the loop, so the
 * scheduler fills the slot with it), `jr $ra` + nop.
 *
 * The three EU copies land as c-at-row-end single cuts of the MATRIX3
 * data rows (head 0x580 + this 0x1C row, no tail). The build compiles
 * src/<row>.c only for targets whose yaml lists the row, so this unit
 * coexists with the slps_00270 / g3org_jp / mainmenu_jp MATRIX3
 * .text+0x580 placements (each that target's own src row) without a
 * second definition in any one target.
 */
int len_param(int n)
{
    int len = 0;

    if (n <= 0)
        return 0;
    do {
        n >>= 1;
        len++;
    } while (n > 0);
    return len;
}

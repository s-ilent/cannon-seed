/* Matched 2026-10-13 through the round-trip oracle (slps_00270).
 *
 * LIBGS MATRIX3 member .text+0x580 (extent 0x1c; curated `len_param`,
 * sdk_members.py unique placement). Frameless leaf: bit length of a
 * positive int — v0 = floor(log2(n)) + 1 for n > 0, else 0. GCC 2.6.3
 * -O2 shape, first compile: guard `blez $a0` over the do-while, loop
 * `sra $a0,$a0,1` + `bgtz` back with the `addiu $v0,$v0,1` increment
 * in the branch delay slot (unconditional inside the loop, so the
 * scheduler fills the slot with it), `jr $ra` + nop.
 *
 * Same LIBGS member as the mainmenu_jp and g3org_jp placements (all
 * three matched this session; the g3org copy was matched second).
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

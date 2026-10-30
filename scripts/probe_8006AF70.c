/* window-35 probe for the func_8006AF70 row decode (offline, cc.sh -S only).
 * Three retail shapes to reproduce:
 *  1. the bgez countdown spin with the decrement in the BRANCH DELAY SLOT
 *     (func_8006B108/2D8/2E8: init 0x3E7-1, `bgez $v0, self; addiu $v0,$v0,-1`)
 *  2. the signed-division guard pair (func_8006B1C0/248: div, bnez/break 7,
 *     the -1/INT_MIN check, break 6, mflo)
 *  3. the assign-then-early-return whose lui rides the bnez delay slot
 *     (func_8006B1C0 head: `bnez $v0, exit; lui $s1, %hi(0xF2000002)`)
 */
extern long D_800ABA50[];
extern long D_800ABA54[];
extern long D_800ABA40[];

long probe_spin(void)
{
    long i;
    long v1;

    i = 0x3E7;
    i = i - 1;
    while (i-- >= 0)
        ;
    v1 = D_800ABA50[0];
    D_800ABA40[0] = D_800ABA40[0] + 1;
    return v1 + i;
}

long probe_div(long v1)
{
    long s0;

    if (v1 < 0x46)
        s0 = 0x204CC0 / v1;
    else
        s0 = 0x409980 / v1;
    return s0;
}

long probe_delay_lui(void)
{
    long s1;

    s1 = 0xF2000002;
    if (D_800ABA54[0] != 0)
        return 0;
    D_800ABA50[0] = 6;
    return s1;
}

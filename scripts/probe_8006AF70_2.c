/* window-35 probe round 2: the two remaining shape questions for the
 * func_8006AF70 row landing.
 *  1. spin init typing: does the single-constant init (i = 998) with a DEAD
 *     loop var emit retail's `addiu $v0,$v0,-1` delay-slot decrement
 *     (probe round 1 emitted `addu $5,$5,-1` with the live-var copy)?
 *  2. the case-0/5 select: does `v = (state == 1) ? 0x32 : 0x3C; store`
 *     reproduce retail's three-path branch chain (beqz state -> 0x3C,
 *     bne state,1 -> 0x3C, fall -> 0x32, single store at the merge)?
 */
extern long D_800ABA44[];
extern long D_80171E08[];

long probe_spin_dead(void)
{
    long i;

    i = 998;
    while (i-- >= 0)
        ;
    return 0;
}

void probe_select(void)
{
    long v;

    v = (D_800ABA44[0] == 1) ? 0x32 : 0x3C;
    D_80171E08[0] = v;
}

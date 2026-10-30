/* cc-post: keep-epilogue
 *
 * Eleventh real-decompiled-C game function of the real-C pivot (g3_eu,
 * 0x10, one yaml row): the fixed-slot long store - the caller hands the
 * value, the row commits it to D_80171EA0 and returns. Reached from
 * func_80022B5C (the g3_eu main game row). The array-declared extern keeps
 * cc1 on the fused lui/%lo pair with $at as the materialization register.
 */
extern long D_80171EA0[];

void func_8005E16C(long value)
{
    D_80171EA0[0] = value;
}

/* minimal twin-chain repro: two three-path goto chains in one function */
extern long S;
extern long T;
extern long jtbl[];

void twin(long a0, long v1)
{
    long vt;
    long v5;

    __asm__ ("" : : "i"(&&L_a), "i"(&&L_b));
    if ((unsigned long)v1 < 6)
        goto *((void **)jtbl)[v1];
    goto L_def;

L_a:                                /* chain A (c5-polarity) */
    v5 = S;
    if (v5 == 0)
        goto L_def5;
    if (v5 == 1) {
        vt = 0x32;
        goto L_st32;
    }
    vt = 0x3C;
    goto L_st3C;

L_b:                                /* chain B (c0-polarity) */
    v1 = S;
    if (v1 == 0)
        goto L_def;
    if (v1 != 1) {
        vt = 0x3C;
        goto L_st3C;
    }
    vt = 0x32;
L_st32:
    T = vt;
    return;
L_def:
    vt = 0x3C;
L_st3C:
    T = vt;
    return;

L_def5:                             /* chain A's private def/store */
    vt = 0x3C;
L_st3C5:
    T = vt;
    return;
}

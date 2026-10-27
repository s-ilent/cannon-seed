/* gmd_v2.c - int*-cursor form: all pointer steps in 4-byte units so gcc
 * emits addiu (retail spells every walk addiu; addu would byte-diff).
 * Fields are long-width accesses through casts; statement order [w0,w4,w2]
 * (round 4's bundle order). See gmd_v1.c for the retail map.
 */
void GsMapModelingData(int *mdata)
{
    long i;
    long n;
    int *r;

    if (!(*(long *)mdata & 1)) {
        *(long *)mdata |= 1;
        mdata++;
        i = 0;
        n = *(long *)mdata;
        mdata++;
        r = mdata;
        for (; i < n; i++) {
            *(long *)(r + 0) += (long)mdata;
            *(long *)(r + 4) += (long)mdata;
            *(long *)(r + 2) += (long)mdata;
            r += 7;
        }
    }
}

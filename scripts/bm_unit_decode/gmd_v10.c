/* gmd_v10.c - the 0704 k-index one-cursor shape with the 1342 ascending
 * statement-order fix.  0704's k-index (int* r, k += 7) solved the
 * one-cursor body + a0-a3 register assignment but kept the wrong load
 * bundle (statements [k, k+4, k+2]); the 1342 law says ascending byte
 * order [+0x00, +0x08, +0x10] hoists the 3rd load correctly, so the index
 * statements go [k, k+2, k+4].  int* keeps the 28-byte stride (4 bytes *
 * k-step 7); the count/flag stay long-width via casts.
 */
void GsMapModelingData(long *mdata)
{
    long k;
    long n;
    int *r;

    if (!(*(long *)mdata & 1)) {
        *(long *)mdata |= 1;
        mdata++;
        n = *(long *)mdata;
        mdata++;
        r = (int *)mdata;
        for (k = 0; k < n * 7; k += 7) {
            r[k] += (long)mdata;
            r[k + 2] += (long)mdata;
            r[k + 4] += (long)mdata;
        }
    }
}

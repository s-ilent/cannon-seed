/* gmd_v8.c - HEAD PROBE: v7's post-increment load spelling in a do-while.
 *
 * Completes the 2x2 matrix (fold-kill spelling x loop form): v5/v7 are the
 * for-forms, v6/v8 the do-whiles.  See gmd_v1.c for the retail map,
 * gmd_v6.c for the do-while notes, gmd_v7.c for the post-inc rationale.
 */
void GsMapModelingData(long *mdata)
{
    long i;
    long n;
    long *r;

    if (!(*mdata & 1)) {
        *mdata |= 1;
        mdata++;
        i = 0;
        n = *mdata++;
        r = mdata;
        if (n > 0) {
            do {
                i++;
                r[0] += (long)mdata;
                r[4] += (long)mdata;
                r[2] += (long)mdata;
                r += 7;
            } while (i < n);
        }
    }
}

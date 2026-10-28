/* gmd_v6.c - HEAD PROBE: v5's fold-kill spelling in a do-while loop.
 *
 * The do-while needs no rotation (test at bottom = retail's slt/bnez tail,
 * the blez guard is the explicit n > 0 if) and keeps i++ as the first body
 * statement.  Watch the 8-byte frame: the v1 comment banks that the for-form
 * provides the strength-reduce pad; if the do-while drops the frame the
 * head/tail sp adjustments disappear and the form is wrong.
 * See gmd_v1.c for the retail map, gmd_v5.c for the fold-kill rationale.
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
        n = *mdata;
        r = ++mdata;
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

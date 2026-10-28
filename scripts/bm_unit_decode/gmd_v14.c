/* gmd_v14.c - v9 with the ADDEND spelled through the fixed base r.
 *
 * (long)r is semantically identical to (long)mdata (r = mdata_final), but
 * it changes the liveness landscape: mdata is DEAD after r's init, so gcc
 * may reuse $4 freely and the loop's register roles (a0 = fixed addend,
 * a1 = stepping giv) fall out of the r variable alone.  Retail's addend
 * register $4 holds m+8 = r's value either way.  Classic two-walk head
 * kept; only the addend spelling changes.
 */
void GsMapModelingData(long *mdata)
{
    struct gmdrec { long f00, f04, f08, f0c, f10, f14, f18; };
    long n;
    long i;
    struct gmdrec *r;

    if (!(*mdata & 1)) {
        *mdata |= 1;
        mdata++;
        n = *mdata;
        mdata++;
        r = (struct gmdrec *)mdata;
        for (i = 0; i < n; i++) {
            r[i].f00 += (long)r;
            r[i].f08 += (long)r;
            r[i].f10 += (long)r;
        }
    }
}

/* gmd_v13.c - v9 with ALL the pre-loop init expressions in the for-header
 * (comma-init).  1227 tried the comma-init on the WALKING body only
 * ("canonicalizes to the separate-load form"); the indexed body's giv
 * landscape differs, so the init-placement decision may differ too.  The
 * statement order inside the header preserves the retail semantic order:
 * walk1, count load, walk2, r init, i init.
 */
void GsMapModelingData(long *mdata)
{
    struct gmdrec { long f00, f04, f08, f0c, f10, f14, f18; };
    long n;
    long i;
    struct gmdrec *r;

    if (!(*mdata & 1)) {
        *mdata |= 1;
        for (mdata++, n = *mdata, mdata++,
             r = (struct gmdrec *)mdata, i = 0; i < n; i++) {
            r[i].f00 += (long)mdata;
            r[i].f08 += (long)mdata;
            r[i].f10 += (long)mdata;
        }
    }
}

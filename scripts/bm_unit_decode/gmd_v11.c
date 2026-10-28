/* gmd_v11.c - v9 with the explicit i=0 statement + empty-init for.
 *
 * 1227 tried the explicit-init shape on the WALKING body only; the indexed
 * body changes the giv landscape (the giv init takes the copy role, loop.c
 * has one fewer init to place), so the sink decision may differ.  The pad
 * law needs the for-form; the increment stays in the canonical slot.
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
        i = 0;
        n = *mdata;
        mdata++;
        r = (struct gmdrec *)mdata;
        for (; i < n; i++) {
            r[i].f00 += (long)mdata;
            r[i].f08 += (long)mdata;
            r[i].f10 += (long)mdata;
        }
    }
}

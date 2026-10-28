/* gmd_v7.c - HEAD PROBE: fold-kill via the post-increment count load.
 *
 * n = *mdata++ ties walk2 to the load's address expression (MIPS has no
 * auto-inc addressing, so gcc materializes the increment as a standalone
 * addiu AFTER the load) and r = mdata copies the final pointer; there is no
 * separate giv-init expression left for loop.c to fold into.  RTL order
 * becomes [walk1][i=0][lw][walk2][copy] with walk2 the closest eligible
 * blez-slot filler -> retail's exact head incl. the unfilled count-load
 * delay (nop).
 * Loop: for-form, i++ first body statement.  See gmd_v1.c for the retail
 * map, gmd_v5.c for the fold-kill rationale.
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
        for (; i < n;) {
            i++;
            r[0] += (long)mdata;
            r[4] += (long)mdata;
            r[2] += (long)mdata;
            r += 7;
        }
    }
}

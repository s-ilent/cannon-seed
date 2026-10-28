/* gmd_v5.c - HEAD PROBE: fold-kill via the combined pre-increment assignment.
 *
 * v1-v4 residual (banked cron-20261027-2248): gcc's loop.c folds walk2
 * (mdata++) into the r-giv init temp (addu $6,$4,4 + copy-back addu
 * $4,$6,$0), which costs +1 insn, forces i=0 into the blez delay slot and
 * splits the cursor giv (addu $5,$6,8).  Hypothesis: spelling walk2 + the
 * giv init as ONE statement (r = ++mdata) makes the dependency explicit so
 * the fold has no separate giv-init expression to fold into; walk2 survives
 * as a standalone addiu and becomes dbr_schedule's closest eligible filler
 * for the blez slot (retail's exact arrangement, incl. the unfilled count-
 * load delay -> nop).
 * Loop: for-form, i++ as the FIRST body statement (retail order), the
 * increment slot left empty.  See gmd_v1.c for the retail map.
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
        for (; i < n;) {
            i++;
            r[0] += (long)mdata;
            r[4] += (long)mdata;
            r[2] += (long)mdata;
            r += 7;
        }
    }
}

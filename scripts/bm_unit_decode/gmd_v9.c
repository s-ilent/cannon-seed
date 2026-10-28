/* gmd_v9.c - THE BANKED SOLVED BODY (cron-20261017-1342) in the canonical
 * for-form (the 1227 pad law: for (i = 0; ...) generates the vars=8 pad).
 *
 * 1342 laws: indexed r[i] struct fields in ASCENDING statement order
 * [+0x00, +0x08, +0x10] compile register-for-register exact to retail's
 * 12-insn loop (i in a2 addiu at body head, records a1 disps 0/0x10/8,
 * base a0, slt a2-vs-a3, backedge addiu a1,0x1c in the delay slot); the
 * ascending order makes the 3rd statement's load hoist above the 1st
 * store = retail's f0/f10/f8 load bundle; the indexed form reduces to ONE
 * address giv (kills the walking-pointer twin) and dissolves the walk2
 * temperization.  The head (i=0 above the count load vs sunk) is the last
 * corner; this combination (canonical-for head x indexed body) is banked
 * as never-run through the offline screen.
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
            r[i].f00 += (long)mdata;
            r[i].f08 += (long)mdata;
            r[i].f10 += (long)mdata;
        }
    }
}

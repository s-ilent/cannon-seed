/* gmd_v15.c - walk2 FUSED into r's init: r = mdata + 1.
 *
 * Retail's second addiu $4,$4,4 (walk2, in the blez delay slot) updates the
 * SAME register the addend reads, and the giv copy $5=$4 follows the slot.
 * Spelling walk2 as r's init (mdata is dead after) asks gcc to reuse $4 for
 * r's value: addiu $4,$4,4 then the giv copy - structurally identical, but
 * the RTL is one expression tree, which may change where the insn lands
 * relative to the count load and the branch.  Addend via r (v14's law);
 * mdata never reaches m+8, matching retail's register semantics ($4 = m+4
 * only between the walks).
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
        r = (struct gmdrec *)(mdata + 1);
        for (i = 0; i < n; i++) {
            r[i].f00 += (long)r;
            r[i].f08 += (long)r;
            r[i].f10 += (long)r;
        }
    }
}

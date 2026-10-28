/* gmd_v12.c - v9's indexed body on the integer-address head (the never-run
 * "documented v3 for-head x exact body" combination from the 1342 next
 * queue).  The walks/counter/cursor are plain integer arithmetic; the loop
 * indexes via the integer base (r + i*28 per access) which strength-reduce
 * collapses into the single 28-byte-stride address giv.  Any difference in
 * the head's RTL emission order vs the pointer form is what this probe
 * measures.
 */
void GsMapModelingData(long mdata)
{
    struct gmdrec { long f00, f04, f08, f0c, f10, f14, f18; };
    long i;
    long n;
    long r;

    if (!(*(long *)mdata & 1)) {
        *(long *)mdata |= 1;
        mdata += 4;
        n = *(long *)mdata;
        mdata += 4;
        r = mdata;
        for (i = 0; i < n; i++) {
            *(long *)(r + i * 28) += mdata;
            *(long *)(r + i * 28 + 8) += mdata;
            *(long *)(r + i * 28 + 16) += mdata;
        }
    }
}

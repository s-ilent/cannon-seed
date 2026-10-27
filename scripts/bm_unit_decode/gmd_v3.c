/* gmd_v3.c - integer-address form: the walks/counter/cursor step are plain
 * integer arithmetic (gcc emits addiu for int adds, addu only for pointer
 * arithmetic; retail spells every walk addiu). Memory access via casts.
 * See gmd_v1.c for the retail map.
 */
void GsMapModelingData(long mdata)
{
    long i;
    long n;
    long r;

    if (!(*(long *)mdata & 1)) {
        *(long *)mdata |= 1;
        mdata += 4;
        i = 0;
        n = *(long *)mdata;
        mdata += 4;
        r = mdata;
        for (; i < n; i++) {
            *(long *)(r + 0) += mdata;
            *(long *)(r + 16) += mdata;
            *(long *)(r + 8) += mdata;
            r += 28;
        }
    }
}

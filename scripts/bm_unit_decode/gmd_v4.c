/* gmd_v4.c - k-index form (round 4's leader formulation): the record cursor
 * comes from strength-reducing k += 7 into a single 0x1C-stride pointer (no
 * giv twin), the addend is the walked integer address, field statement order
 * [w0, w4, w2] for the retail load bundle. See gmd_v1.c for the retail map.
 */
void GsMapModelingData(long mdata)
{
    long *mp;
    long k;
    long n;

    if (!(*(long *)mdata & 1)) {
        *(long *)mdata |= 1;
        mdata += 4;
        n = *(long *)mdata;
        mdata += 4;
        mp = (long *)mdata;
        for (k = 0; k < n * 7; k += 7) {
            mp[k] += mdata;
            mp[k + 4] += mdata;
            mp[k + 2] += mdata;
        }
    }
}

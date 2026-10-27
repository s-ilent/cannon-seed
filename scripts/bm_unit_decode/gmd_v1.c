/* gmd_v1.c - GsMapModelingData leader reconstruction, natural for-form.
 *
 * Retail map (asm/g3org_jp/nonmatchings/func_80053528.s, 30 insns):
 *   flag block : lw v1,0(a0); nop; andi v0,v1,1; bnez .Lret (delay addiu sp,-8);
 *                ori v0,v1,1; sw v0,0(a0)
 *   head       : addiu a0,4 (walk1); addu a2,zero,zero (i=0); lw a3,0(a0); nop;
 *                blez a3,.Lret (delay addiu a0,4 = walk2); addu a1,a0,zero (giv copy)
 *   body       : addiu a2,1 (i++ at head); lw v0,0(a1); lw v1,10(a1); addu; sw 0(a1);
 *                lw v0,8(a1); addu v1; sw 10(a1); addu v0; sw 8(a1)
 *   tail       : slt v0,a2,a3; bnez .Lloop (delay addiu a1,1c); .Lret: addiu sp,8; jr; nop
 *
 * Laws applied (rounds 1/3/4):
 *   - the flag word IS mdata[0] (not a global)
 *   - parameter-register walks stay split: mdata++ twice, count load disp-0
 *   - statement order [w0, w4, w2] (round 4's k-index order) for the load bundle
 *   - for-form biv slot for the 8-byte strength-reduce pad (frameless otherwise)
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
        mdata++;
        r = mdata;
        for (; i < n; i++) {
            r[0] += (long)mdata;
            r[4] += (long)mdata;
            r[2] += (long)mdata;
            r += 7;
        }
    }
}

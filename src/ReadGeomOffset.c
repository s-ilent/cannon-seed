/* Matched 2026-10-17 through the round-trip oracle (g3org_jp first;
 * region-pair 100.00% twins across the sdk lanes, see the pair-report
 * matching lane).
 *
 * LIBGTE reader member: unpacks the GTE control registers OFX/OFY
 * (C24/C25) - cfc2 into $t0/$t1, two arithmetic right shifts by 16
 * (the control words are the packed 16-bit pairs in the upper
 * halfword, sign-extended on read-out), two 32-bit stores.
 *
 * The local register asm variables pin the cfc2 destinations to $8/$9
 * exactly as retail; volatile keeps the cfc2/store order fixed. The
 * shifts are plain signed C so the compiler emits sra.
 */
void ReadGeomOffset(long *a0, long *a1)
{
    register long x asm("$8");
    register long y asm("$9");
    __asm__ volatile("cfc2 %0, $24" : "=r"(x));
    __asm__ volatile("cfc2 %0, $25" : "=r"(y));
    *a0 = x >> 16;
    *a1 = y >> 16;
    /* Retail keeps the second store BEFORE the return jump with a nop
     * delay slot; without this barrier gcc sinks the independent store
     * into the jr delay slot and the body shrinks a word. */
    __asm__ volatile("" ::: "memory");
}

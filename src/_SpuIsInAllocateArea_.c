/* cc-post: sdk-aspsx
 * cc-post: cc1-O1
 *
 * LIBSPU S_M_UTIL member: the allocate-area walk's unit-converting twin
 * (the trailing-underscore psyq duality). Identical walk to
 * _SpuIsInAllocateArea over the (attr, size) pair table at D_800B7F1C
 * (8 bytes per step; attr bit31 = skip, bit30 = terminator/break, live
 * attr masks to 0x0FFFFFFF, return 1 when addr <= start OR
 * addr < start + size) - the difference is the PROLOGUE: the incoming
 * address converts to byte units first, shifted left by the shift
 * amount held in D_800B75E8 (sllv, in place on the a0 param), loaded
 * BETWEEN the mask block and the table-cursor load in program order
 * (retail: t0/a3/a2 masks, v0 = lw D_800B75E8, a1 = lw D_800B7F1C,
 * sllv a0,a0,v0). That order needs an explicit shift local -
 * shift = D_800B75E8, then the cursor load, THEN `addr <<= shift` -
 * because a direct `addr <<= D_800B75E8;` before the cursor load emits
 * the sllv two words early and costs 2 nops (128 vs 120).
 *
 * Identity PROVEN by sdk_members.py unique placement + sig-db agree
 * (LIBSPU S_M_UTIL, g3org_jp 0x8006C7A4, adoptable; the trailing-
 * underscore twin of the landed 0x8006C734 row).
 *
 * Shape notes: the landed twin's laws all carry over (source-order
 * pre-loop mask locals, goto-advance shared bottom increment with the
 * stride-2 p += 2, break-form terminator keeping the post-loop
 * return-0 block, cc1-O1 + sdk-aspsx, sltu compares, delay-slot
 * return-1 constants).
 */
extern unsigned long *D_800B7F1C;
extern unsigned long D_800B75E8;

long _SpuIsInAllocateArea_(unsigned long addr)
{
    unsigned long m_skip = 0x80000000;
    unsigned long m_end = 0x40000000;
    unsigned long m_addr = 0x0FFFFFFF;
    unsigned long *p;
    unsigned long v;
    unsigned long shift;

    shift = D_800B75E8;
    p = D_800B7F1C;
    addr <<= shift;
    while (1) {
        v = *p;
        if (v & m_skip)
            goto advance;
        if (v & m_end)
            break;
        v &= m_addr;
        if (v >= addr)
            return 1;
        if (addr < v + p[1])
            return 1;
    advance:
        p += 2;
    }
    return 0;
}

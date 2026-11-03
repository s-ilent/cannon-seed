/* cc-post: sdk-aspsx
 * cc-post: cc1-O1
 *
 * LIBSPU S_M_UTIL member: the allocate-area walk. The table cursor
 * D_800B7F1C holds the head of (attr, size) entry pairs (8 bytes per
 * step); each attr word carries flag bits above the 28-bit address
 * field: bit31 = skip (advance to the next pair), bit30 = terminator
 * (break out of the loop - not in the allocate area). A live attr
 * masks to 0x0FFFFFFF and answers: return 1 when addr <= start, else
 * compute end = start + entry size and return 1 when addr < end;
 * otherwise fall through to the shared bottom increment and loop.
 *
 * Identity PROVEN by sdk_members.py unique placement + sig-db agree
 * (LIBSPU S_M_UTIL, g3org_jp 0x8006C734, adoptable).
 *
 * Shape notes: the three mask materializations precede the table-cursor
 * load in program order (retail t0/a3/a2 then a1 = lw D_800B7F1C); the
 * skip path and the fall-through SHARE one bottom increment (goto
 * advance) so the increment rides the backedge jump's delay slot and
 * the skip branch lands on the backedge block; the terminator exits
 * via BREAK so the return-0 move stays in its own post-loop block
 * between the loop and the shared jr (in-loop `return 0` gets its move
 * pulled into the branch delay slot by gcc's cross-block fill, 15
 * words off); the param a0 is never spilled; both range compares are
 * sltu (unsigned); the return-1 constant rides the branch delay slots
 * (ori v0,1).
 */
extern unsigned long *D_800B7F1C;

long _SpuIsInAllocateArea(unsigned long addr)
{
    unsigned long m_skip = 0x80000000;
    unsigned long m_end = 0x40000000;
    unsigned long m_addr = 0x0FFFFFFF;
    unsigned long *p;
    unsigned long v;

    p = D_800B7F1C;
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

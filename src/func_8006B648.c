/* cc-post: keep-epilogue
 *
 * Fifth/sixth/seventh real-decompiled-C game functions of the twenty-ninth
 * window (cron-202610300053). One yaml row, 0x78 bytes, a spimdisasm
 * multi-piece listing: func_8006B648 (with the func_8006B674/func_8006B678
 * branch-tail pieces - no external callers, symbols.txt marks both as plain
 * branch targets) plus the standalone wrappers func_8006B680 and
 * func_8006B6A0 (both jal'd from func_8006AC04, the reset/init driver;
 * func_8006B648 itself is reached from func_8006AF70, 0x590 untagged).
 *
 * func_8006B648: range-guarded slot clear - zero-extend the index halfword
 * (andi), the early guard `idx >= 3 -> return 0` is the source form that
 * keeps GCC 2.6.3's beqz branching FORWARD over the whole clear body to the
 * return-0 tail (the inverted `if (v1 < 3) {...}` form hoists the return-0
 * ahead of the body and misses the explicit tail jump retail shows). The
 * clear writes the halfword at tblbase + idx*16 where tblbase is the
 * pointer word at D_800ABA5C (array-declared extern so cc1 emits the fused
 * lui/%lo pair, not the bare-symbol small-data form); returns 1 when the
 * clear ran (the ori lands in the beqz delay slot), 0 otherwise.
 * The wrappers feed func_800653AC the constants 1 and 0 through the jal
 * delay slot (same GCC 2.6.3 wrapper frame as the func_8006AD50 pair).
 */
extern long D_800ABA5C[];
extern void func_800653AC(long);

long func_8006B648(long idx)
{
    long v1;
    long tbl;

    v1 = idx & 0xFFFF;
    if (v1 >= 3)
        return 0;
    tbl = D_800ABA5C[0];
    v1 = (v1 << 4) + tbl;
    *(volatile short*)v1 = 0;
    return 1;
}

void func_8006B680(void)
{
    func_800653AC(1);
}

void func_8006B6A0(void)
{
    func_800653AC(0);
}

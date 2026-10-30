/* cc-post: keep-epilogue
/* Real-decompiled-C game function #8 (window 30, cron-202610300229). One
 * yaml row, 0xc0 bytes, spimdisasm splits it into six pieces: the main body
 * (0x44) plus the chunk-select tail (0xc), the call piece (0x24), the
 * post-call piece (0x1c), the return-total tail (0x4) and the epilogue
 * (0x2c) - one C function's straight-line do-while layout, all pieces share
 * the single body below. Caller: func_80022B5C (verified game row, the
 * mainmenu launcher driver); callee: _SN_write, the psyq LIBSN host-file
 * member landed as C at 0x800489C8 (its body ignores the registers it is
 * handed - the host reads a0..a2 where they sit - so the game call site's
 * four-register staging (0, handle, chunk, buf) is ABI-visible only).
 *
 * The function is a write-all loop: feed the host at most 0x8000 bytes per
 * call (the sltu guard is UNSIGNED - retail picks the chunk with
 * sltu against the ori'd 0x8000 constant, so len is unsigned in the source),
 * accumulate what was written, bail -1 if the host reports failure, stop
 * and return the total on a short write (slt is the SIGNED w < chunk test),
 * else loop until len drains. The len==0 entry shares the return-total tail
 * (retail's beqz jumps straight at `v0 = s2` with total already zero) - the
 * source wraps the loop in `if (len != 0)` so `return total` exists exactly
 * once: GCC then branches to the shared tail instead of constant-folding a
 * private v0=0 block.
 */
extern long _SN_write(long, long, long, char *);

long func_80048908(long handle, char *buf, unsigned long len)
{
    long chunk;
    long w;
    /* total is pinned to $18: GCC's allocator ties total with the buf
     * param (two reads each) and hands the tie to the param, which puts
     * buf in s2 and total in s3 - the exact mirror of retail (total s2,
     * buf s3). One explicit-asm register var (the banked _SN_write
     * idiom) occupies s2 and pushes buf to the next free callee-saved
     * reg; every other allocation then lands where retail has it. */
    register long total asm("$18") = 0;

    if (len != 0) {
        do {
            chunk = (len > 0x8000) ? 0x8000 : len;
            w = _SN_write(0, handle, chunk, buf);
            total += w;
            if (w == -1)
                return -1;
            buf += w;
            len -= w;
            if (w < chunk)
                break;
        } while (len != 0);
    }
    return total;
}

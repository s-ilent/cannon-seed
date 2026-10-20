/* GsClearOt - LIBGS SCLIB member (extent 0x58), near-twin wave probe.
 * cc-post: keep-epilogue - retail keeps GCC's own epilogue order
 * (lw ra; addiu sp; jr; nop), not the maspsx branch-delay swap.
 *
 * Eight-target near-twin wave: every region pair's 0x58 member rows are
 * word-identical except the single jal slot at word 0x40 (the per-target
 * callee address; the callee body is the same 0x98 member everywhere,
 * differing only in its own per-target data refs, and this member is its
 * only caller - fan-in 1 in the baseline scan).
 *
 * Shape: zero-extend both short params into the two long bookkeeping
 * fields, then derive the table-end cursor as org + (4 << width) - 4
 * bytes (the 4 << width is the table size in bytes: 1 << width entries
 * of 4 bytes), and hand the callee the table origin and the entry count
 * 1 << width (the second width read is a true reload - the stores may
 * alias it - which is what puts the shift amount in a1 for the sllv
 * whose destination is the call's second arg register).
 */
typedef struct {
    long width;              /* +0x00 */
    unsigned char *org;      /* +0x04 */
    long top;                /* +0x08 */
    long bottom;             /* +0x0c */
    unsigned char *tail;     /* +0x10 */
} GsOT_W;

void GsClearOt_tag(unsigned char *org, long n);

void GsClearOt(unsigned short top, unsigned short bottom, GsOT_W *ot)
{
    ot->top = top;
    ot->bottom = bottom;
    ot->tail = ot->org + (4 << ot->width) - 4;
    GsClearOt_tag(ot->org, 1 << ot->width);
}

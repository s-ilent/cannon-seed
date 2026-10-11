/* Matched 2026-10-11 through the round-trip oracle (g3_eu).
 *
 * Sequence-reset wrapper: one no-arg call into the palette/UV reset
 * helper, then two immediate triples into the same palette-fade helper
 * the wrapper cluster at 0x8004C4CC drives (0x3EE/0x3EF x keys,
 * 0x3C/0x73 y keys, -0x5E third argument).
 *
 * Shaping notes (GCC 2.6.3 -O2 -G8, MIPS1):
 * - Real frame this time (0x18, ra saved at 0x10): three calls deep, so
 *   cc1 keeps the return address across both helper calls; the wrapper
 *   cluster at 0x8004C4CC had none.
 * - Immediate triples: positive 16-bit values load with ori, the
 *   negative third argument with addiu, and it materializes in the jal
 *   delay slot - same movsi selection as the cluster.
 * - Epilogue: lw $ra, nop (load-delay), jr $ra with the frame release
 *   in the delay slot - the cc_post.py rule-1 swap.
 *
 * The following asm block (the >= 0x64 guard with the div-by-10 checked
 * expansion) stays assembly: its final `j` leaves the frame allocated
 * and $ra never reloaded - not C call codegen (a compiler tail call
 * deallocates the frame first), so the original was hand-written asm or
 * a macro layer. The j targets 0x80047924, whose bytes decode as real
 * code the scanner cannot yet vouch for (its walk dies on a garbage
 * patch the block's own branches jump over).
 */
extern void func_80047844(void);
extern void func_8004427C(short, short, short);

void func_8004D704(void)
{
    func_80047844();
    func_8004427C(0x3EE, 0x3C, -0x5E);
    func_8004427C(0x3EF, 0x73, -0x5E);
}

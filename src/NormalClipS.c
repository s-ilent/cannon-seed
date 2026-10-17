/* Matched 2026-10-17 through the round-trip oracle (g3org_jp first;
 * cross-target byte-identical in mainmenu_jp, g3_eu, g3org_jp, g3org_eu,
 * see the matching lane's GTE families queue item).
 *
 * LIBGTE NormalClipS: the FIFO-only half of NormalClip - runs NCLIP
 * (0x4b400006, banked as its exact retail .word) on the GTE registers a
 * prior load already set, then reads MAC0 ($24) back as the return value.
 *
 * The mfc2 output lands on a $2 register-var (the RotTransPers4 return
 * law) so gcc emits jr $ra straight after the block: .word, mfc2, jr,
 * nop - the retail four-insn body.
 */
long NormalClipS(void)
{
    register long r asm("$2");
    __asm__ volatile(".word 0x4b400006\n\tmfc2 %0, $24" : "=r"(r));
    return r;
}

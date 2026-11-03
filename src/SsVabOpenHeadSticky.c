/* cc-post: sdk-aspsx
 *
 * LIBSND VS_VH member: SsVabOpenHeadSticky (the member's .text+0x30
 * piece). The sticky-head opener: forwards to SsVabOpenHeadWithMode
 * with the fake-head mode 1 and the caller's record count passed
 * through raw (a3 = a2, the count rides as the fourth argument); the
 * mode constant 1 materializes in the jal DELAY slot. The vabid takes
 * the sll16/sra16 extend-in-place (short vabid); the return value is
 * the callee's short result sign-extended on the way out.
 *
 * Identity PROVEN by sdk_members.py unique placement + sig-db agree
 * (LIBSND VS_VH, g3org_jp 0x80067FFC = member .text+0x30, adoptable;
 * the game row carries 0x4 tail slack over the member's 0x30, extent
 * 0x34 - the game's own cc1 2.6.3-PSX compiled copy). Instruction-
 * identical to the landed SsVabFakeHead registrar
 * src/g3org_jp/func_80068030.c (the psyq duality: two same-shaped
 * members in one VS_VH blob, both forwarding SsVabOpenHeadWithMode
 * with mode 1 and a raw count).
 *
 * Externs: SsVabOpenHeadWithMode is the VS_VH .text+0x90 member
 * (0x80068064, landed this window). No D_ externs, no symbol loads -
 * no maspsx flag needed.
 */

extern long SsVabOpenHeadWithMode();

long SsVabOpenHeadSticky(long addr, short vabid, long fake_count)
{
    return (short)SsVabOpenHeadWithMode(addr, vabid, 1, fake_count);
}

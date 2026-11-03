/* cc-post: sdk-aspsx
 *
 * LIBSND VS_VH member: SsVabOpenHead (the member's .text+0x0 piece).
 * The default-head opener: forwards to SsVabOpenHeadWithMode with the
 * explicit-placement mode 0 and a zero fake-count, i.e. the plain
 * "open the VAB head and place it" entry point. The vabid takes the
 * sll16/sra16 extend-in-place (short vabid); both trailing constants
 * materialize as addu rt,zero,zero with the second riding the jal's
 * delay slot; the return value is the callee's short result
 * sign-extended on the way out (the SsVabTransCompleted short-return
 * law).
 *
 * Identity PROVEN by sdk_members.py unique placement + sig-db agree
 * (LIBSND VS_VH, g3org_jp 0x80067FC8 = member .text+0x0, adoptable;
 * the game row carries 0x4 tail slack over the member's 0x30, extent
 * 0x34 - the game's own cc1 2.6.3-PSX compiled copy). Byte-shape twin
 * of the landed SsVabFakeHead registrar src/g3org_jp/func_80068030.c
 * (same addu a3,a2 / extend / jal / ori a2,1-delay skeleton, here with
 * zero constants instead of the forwarded mode 1).
 *
 * Externs: SsVabOpenHeadWithMode is the VS_VH .text+0x90 member
 * (0x80068064, landed this window). No D_ externs, no symbol loads -
 * no maspsx flag needed.
 */

extern long SsVabOpenHeadWithMode();

long SsVabOpenHead(long addr, short vabid)
{
    return (short)SsVabOpenHeadWithMode(addr, vabid, 0, 0);
}

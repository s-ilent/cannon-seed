/* cc-post: sdk-aspsx
 *
 * Real-decompiled-C game function #21 - the func_80068030 row (g3org_jp,
 * 0x80068030..0x80068064, extent 0x34) lands as the psyq libsnd VAB
 * fake-head registrar, identity PROVEN by the sdk_members.py unique
 * VS_VH placement + sig-db agrees on all eight targets (pinned member
 * row SsVabFakeHead = 0x80068030, the VS_VH member's .text+0x60 piece,
 * extent 0x30 - the game row carries 0x4 tail slack, the game's own
 * cc1 2.6.3-PSX compiled copy; the member's big .text+0x90 piece
 * SsVabOpenHeadWithMode = 0x80068064 is the 0x448 sdk row this wrapper
 * forwards to, landed as real C this window).
 *
 * Decode (the listing is the only authority): the wrapper shuffles the
 * raw argument registers around the single call - a3 = a2 (the fake
 * count rides as the fourth argument), a2 = 1 materializes in the jal
 * DELAY slot (the mode constant 1 = the fake-head mode), a1 takes the
 * sll16/sra16 extend-in-place (short vabid), a0 passes through as the
 * VAB header address; the return value is the callee's short result
 * sign-extended on the way out (sll16/sra16 on v0 - the SsVabTrans-
 * Completed short-return law).
 *
 * Externs: SsVabOpenHeadWithMode is the VS_VH .text+0x90 member
 * (0x80068064, landed as real C this window; the row name
 * SsVabOpenHeadWithMode replaced the func_80068064 auto name). No
 * D_ externs, no symbol loads - no maspsx flag needed (no indexed
 * access, no at-split).
 */

extern long SsVabOpenHeadWithMode();

long func_80068030(long addr, short vabid, long fake_count)
{
    return (short)SsVabOpenHeadWithMode(addr, vabid, 1, fake_count);
}

/* cc-post: sdk-aspsx
 *
 * Real-decompiled-C game function #22 - the func_80078700 row (mainmenu_eu,
 * 0x80078700..0x80078724, extent 0x24) lands as the psyq libcd TOC reader
 * CdGetToc, identity PROVEN by the sdk_members.py unique TOC placement +
 * sig-db agrees on all eight targets (pinned member rows CdGetToc =
 * 0x80078700 / CdGetToc2 = 0x80078724 stand in config/symbols.curated.txt
 * for mainmenu_eu and mainmenu_jp alike; this row IS the member's .text+0x0
 * piece, extent 0x24 exact). CdGetToc2 stays the unbanked 0x224 sdk asm row
 * this wrapper forwards to - its own landing is the ladder's next rung.
 *
 * Decode (the listing is the only authority): a pure argument-shuffle
 * wrapper, the twin of landed #21 (func_80068030 SsVabFakeHead) - a1 = a0
 * (the toc buffer pointer rides as the callee's SECOND argument; the
 * callee's own prologue confirms it: addu s4,a1,zero, the toc store base),
 * the constant 1 materializes in the jal DELAY slot (ori a0,zero,0x1); the
 * callee never reads its incoming a0 (zeroed in the prologue before its
 * first call), so the 1 is the vestigial count argument of the psyq
 * CdGetToc(toc) = CdGetToc2(1, toc) law. The return passes through v0
 * unmodified (no sll16/sra16 on either side - word return, not the short
 * law of #21). No D_ externs, no symbol loads - no maspsx flag needed.
 */

extern long func_80078724();

long func_80078700(long toc)
{
    return func_80078724(1, toc);
}

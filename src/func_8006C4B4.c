/* Matched 2026-10-13 through the round-trip oracle (mainmenu_jp).
 *
 * LIBETC VMODE member .text+0x18 (extent 0x10; curated `GetVideoMode`,
 * sdk_members.py unique placement + sig-db agrees). One-load getter on
 * the member's backing static `video_mode`: lui $v0,%hi + lw $v0,%lo($v0)
 * (address and load share the return register), jr $ra + nop.
 */
extern long video_mode;

long GetVideoMode(void)
{
    return video_mode;
}

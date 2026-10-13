/* Matched 2026-10-13 through the round-trip oracle (g3org_eu).
 *
 * LIBETC VMODE member .text+0x18 (curated `GetVideoMode`, sdk_members.py
 * unique placement + sig-db agrees). One-load getter on the backing
 * static `video_mode`: lui $v0,%hi + lw $v0,%lo($v0), jr $ra + nop.
 */
extern long video_mode;

long GetVideoMode(void)
{
    return video_mode;
}

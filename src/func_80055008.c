/* Matched 2026-10-13 through the round-trip oracle (g3_jp).
 *
 * LIBETC VMODE member .text+0x0 (curated `SetVideoMode`, sdk_members.py
 * unique placement + sig-db agrees). Returns the previous video mode and
 * installs the new one: reads the backing static `video_mode` into $v0
 * (lui+lw on the return register), stores $a0 through $at, jr $ra + nop.
 * Same source shape as the mainmenu_jp match that landed first.
 */
extern long video_mode;

long SetVideoMode(long mode)
{
    long old = video_mode;

    video_mode = mode;
    return old;
}

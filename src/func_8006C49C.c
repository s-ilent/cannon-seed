/* Matched 2026-10-13 through the round-trip oracle (mainmenu_jp).
 *
 * LIBETC VMODE member .text+0x0 (extent 0x18; curated `SetVideoMode`,
 * sdk_members.py unique placement + sig-db agrees). Returns the previous
 * video mode and installs the new one: reads the member's backing static
 * `video_mode` into $v0 (the return register, lui+lw on the same
 * register), then stores $a0 through $at (lui+sw), jr $ra + nop.
 * The Psy-Q 3.3 archive carries no symbol for the static (see the
 * curated evidence block); `video_mode` is the role-descriptive name.
 */
extern long video_mode;

long SetVideoMode(long mode)
{
    long old = video_mode;

    video_mode = mode;
    return old;
}

/* cc-post: keep-epilogue
 *
 * GsSetLightMode - LIBGS SCLIB member (extent 0x8c), landed as ONE source
 * across SIX curated placements in window cron-20261020-1112 (file
 * offsets 0x3E5E8 g3_jp, 0x3EC4C g3_eu, 0x3BA84 g3org_jp, 0x3C0A0
 * g3org_eu, 0x53418 mainmenu_jp, 0x53A44 mainmenu_eu - all six the
 * 0x8c sdk rows at the pinned LIBGS SCLIB member addresses). Decoded offline in windows
 * cron-20261020-0957 (34/35) and cron-20261020-1112 (35/35): probes/
 * gcc263/GsSetLightMode.c carries the full shape story (the goto-leg
 * equality chain, the SDK/ASPSX epilogue, and the entry addu a1,a0,zero
 * which is the SECOND printf argument - printf(msg, mode) homes mode in
 * $a1 for its whole live range). tools/lm_probe_diff.py proved 35/35
 * against the g3org_jp retail words before landing.
 *
 * The data references use shared alias names (curated per target) because
 * the six copies' static and string live at different addresses:
 *   GsSetLightMode_lmode: g3_jp 0x80171D7C, g3_eu 0x80171E9C,
 *     g3org_jp 0x8017FA30, g3org_eu 0x8017FB14, mainmenu_jp 0x80194D6C,
 *     mainmenu_eu 0x80194E80.
 *   GsSetLightMode_msg: g3_jp 0x80021C34, g3_eu 0x80021C14,
 *     g3org_jp 0x8002256C, g3org_eu 0x80022568, mainmenu_jp 0x800231DC,
 *     mainmenu_eu 0x80023190.
 */
extern int GsSetLightMode_lmode;
extern char GsSetLightMode_msg[];
extern int printf(const char *, ...);

void GsSetLightMode(long mode)
{
    if (mode == 1) goto store;
    if (mode >= 2) goto range;
    if (mode == 0) goto zero;
    goto err;
range:
    if (mode == 2) goto store;
    if (mode == 3) goto store;
    goto err;
zero:
    GsSetLightMode_lmode = 0;
    return;
store:
    GsSetLightMode_lmode = mode;
    return;
err:
    printf(GsSetLightMode_msg, mode);
}

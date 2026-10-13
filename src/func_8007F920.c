/* Matched 2026-10-13 through the round-trip oracle (mainmenu_eu).
 *
 * LIBGS GS_002 member .text+0x0 (extent 0x10; curated `GsGetActiveBuff`,
 * sdk_members.py unique placement + Psy-Q 3.3 sig-db agrees: GS_002.OBJ
 * labels it at offset 0 and its signature bytes match retail exactly -
 * lui/lh on the backing static, jr $ra + nop). Returns the active draw
 * buffer index: lh-loads the member's own bss static `PSDIDX` straight
 * into $v0 (address and load share the return register). PSDIDX sits
 * beyond the payload segment (EXE bss; no dlabel renders) and resolves
 * extern. Full evidence block under target: mainmenu_jp. The same
 * member is placed in every other target as well.
 */
extern short PSDIDX;

long GsGetActiveBuff(void)
{
    return PSDIDX;
}

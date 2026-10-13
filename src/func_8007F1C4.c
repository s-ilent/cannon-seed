/* Matched 2026-10-13 through the round-trip oracle (mainmenu_jp).
 *
 * LIBGS GS_002 member .text+0x0 (extent 0x10; curated `GsGetActiveBuff`,
 * sdk_members.py unique placement + Psy-Q 3.3 sig-db agrees: GS_002.OBJ
 * labels it at offset 0 and its signature bytes match retail exactly -
 * lui/lh on the backing static, jr $ra + nop). Returns the active draw
 * buffer index: lh-loads the member's own bss static `PSDIDX` straight
 * into $v0 (address and load share the return register). GsSetDrawBuff
 * Offset re-reads the same index and scales it by two to pick a slot in
 * a two-entry offset table, confirming index semantics. PSDIDX is the
 * only halfword-sized bss symbol that OBJ carries. It sits beyond the
 * payload segment (EXE bss; no dlabel renders) and is resolved extern.
 * The same member is placed in the other seven targets as well.
 */
extern short PSDIDX;

long GsGetActiveBuff(void)
{
    return PSDIDX;
}

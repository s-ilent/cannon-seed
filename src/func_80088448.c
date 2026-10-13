/* Matched 2026-10-13 through the round-trip oracle (mainmenu_eu).
 *
 * LIBSPU S_ITC member .text+0xdc (extent 0x10; curated
 * `_spu_getInTransfer`; the Psy-Q 2.60/3.00 sig-db's S_ITC.OBJ carries
 * the member at offset 0xdc and its signature bytes match retail
 * exactly - lui/lw on the backing flag, jr $ra with the sltiu in the
 * delay slot). Returns whether no SPU transfer is in flight: loads the
 * S_INI-defined flag `_spu_inTransfer` and returns (flag == 0), the
 * compiler placing the sltiu in the jr's delay slot. The flag sits
 * beyond the payload segment (EXE bss; no dlabel renders) and resolves
 * extern. Full evidence block under target: mainmenu_jp. The same
 * member is placed in every other target as well.
 */
extern long _spu_inTransfer;

long _spu_getInTransfer(void)
{
    return _spu_inTransfer == 0;
}

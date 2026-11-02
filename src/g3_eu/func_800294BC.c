/* cc-post: sdk-aspsx
 *
 * Real-decompiled-C game function #27 - the func_800294BC row (g3_eu,
 * 0x8002808C, extent 0x14) lands as the psyq libsnd VM_DON member
 * SpuVmDamperOn (the game's own cc1 2.6.3-PSX compiled copy; identity
 * PROVEN by sdk_members.py unique placement + sig-db agrees - the copy
 * at the VM_DON pinned address 0x8002808C).
 *
 * Decode: a single store leaf - the damper-on state constant 2 is
 * materialized in v0 (ori v0,zero,0x2, the value temp the sh consumes)
 * and stored as an UNSIGNED HALFWORD into the per-module damper-state
 * static D_800AC390 (the address temp rides $at: gcc's %hi/%lo expansion
 * for a single-use extern store destination - no destination register
 * exists for a store, so the address goes through the assembler temp).
 * No frame, no callees, no register saves - v0 is left holding the 2
 * the store used.  The same member is compiled three times in g3_eu
 * (this copy, func_80049E50 -> D_800AC6C4, func_8007C394 ->
 * D_8016AC24): one per module overlay, each writing its own damper
 * halfword.
 */

extern unsigned short D_800AC390;

void func_800294BC(void)
{
    D_800AC390 = 2;
}

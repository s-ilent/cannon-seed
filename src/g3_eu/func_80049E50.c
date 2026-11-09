/* cc-post: sdk-aspsx
 *
 * Real-decompiled-C game function #28 - the func_80049E50 row (g3_eu,
 * 0x800447A0, extent 0x14) lands as the psyq libsnd VM_DON member
 * SpuVmDamperOn (the game's own cc1 2.6.3-PSX compiled copy; identity
 * PROVEN by sdk_members.py unique placement + sig-db agrees - the copy
 * at the VM_DON pinned address 0x800447A0).
 *
 * Decode: the byte-twin of this window's SpuVmDamperOn landing - the
 * same damper-on store leaf (ori v0,zero,0x2 into the value temp, the
 * $at-addressed unsigned-halfword store), differing only in the target
 * static: D_800AC6C4, the second module overlay's damper-state
 * halfword.  No frame, no callees, no register saves.
 */

extern unsigned short D_800AC6C4;

void func_80049E50(void)
{
    D_800AC6C4 = 2;
}

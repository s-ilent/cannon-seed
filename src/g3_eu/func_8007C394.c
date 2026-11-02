/* cc-post: sdk-aspsx
 *
 * Real-decompiled-C game function #29 - the func_8007C394 row (g3_eu,
 * 0x80070464, extent 0x14) lands as the psyq libsnd VM_DON member
 * SpuVmDamperOn (the game's own cc1 2.6.3-PSX compiled copy; identity
 * PROVEN by sdk_members.py unique placement + sig-db agrees - the copy
 * at the VM_DON pinned address 0x80070464).
 *
 * Decode: the third byte-twin of the VM_DON store leaf (ori
 * v0,zero,0x2 into the value temp, the $at-addressed unsigned-halfword
 * store), target static D_8016AC24 - the third module overlay's
 * damper-state halfword.  No frame, no callees, no register saves.
 */

extern unsigned short D_8016AC24;

void func_8007C394(void)
{
    D_8016AC24 = 2;
}

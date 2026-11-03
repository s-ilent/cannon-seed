/* cc-post: sdk-aspsx
 *
 * Real-decompiled-C game function - the func_8007B6CC row (g3_jp) lands as the
 * psyq libsnd VM_DON member SpuVmDamperOn (the game's own cc1
 * 2.6.3-PSX compiled copy; identity PROVEN by sdk_members.py unique
 * placement + sig-db agrees).
 *
 * Decode: the byte-twin of the landed g3_eu trio (869607c9) - the same
 * damper-on store leaf: the damper-on state constant 2 materializes in
 * v0 (ori v0,zero,0x2, the value temp the sh consumes) and stores as an
 * UNSIGNED HALFWORD into the per-module damper-state static D_8016AAF8 (the
 * address temp rides $at: gcc's %hi/%lo expansion for a single-use
 * extern store destination - no destination register exists for a
 * store, so the address goes through the assembler temp).  No frame,
 * no callees, no register saves - v0 is left holding the 2 the store
 * used.
 */

extern unsigned short D_8016AAF8;

void func_8007B6CC(void)
{
    D_8016AAF8 = 2;
}

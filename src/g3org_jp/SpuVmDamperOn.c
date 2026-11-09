/* cc-post: sdk-aspsx
 *
 * Real-decompiled-C game function - the sdk c row at yaml 0x9538 (g3org_jp) lands as the psyq
 * libsnd VM_DON member SpuVmDamperOn (the game's own cc1 2.6.3-PSX
 * compiled copy; identity PROVEN by sdk_members.py unique placement +
 * sig-db agrees).
 *
 * Decode: the byte-twin of the landed g3_eu trio (869607c9) - the same
 * damper-on store leaf: the damper-on state constant 2 materializes in
 * v0 (ori v0,zero,0x2, the value temp the sh consumes) and stores as an
 * UNSIGNED HALFWORD into the per-module damper-state static D_800B8A30 (the
 * address temp rides $at: gcc's %hi/%lo expansion for a single-use
 * extern store destination - no destination register exists for a
 * store, so the address goes through the assembler temp).  No frame,
 * no callees, no register saves - v0 is left holding the 2 the store
 * used.
 */

extern unsigned short D_800B8A30;

void SpuVmDamperOn(void)
{
    D_800B8A30 = 2;
}

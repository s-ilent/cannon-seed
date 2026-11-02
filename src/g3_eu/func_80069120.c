/* cc-post: sdk-aspsx
 *
 * Real-decompiled-C game function #23 - the func_80069120 row (g3_eu,
 * 0x80069120, extent 0x54) lands as the psyq libsnd VM_PROG member
 * SpuVmGetProgVol, identity PROVEN by sdk_members.py unique placement
 * (config/symbols.curated.txt: SpuVmGetProgVol = 0x80069120).
 *
 * Decode: both arguments are sign-extended halfwords (sll 16 + sra 16
 * pairs - the psyq VM API's short-arg law); the first rides a0 into
 * SpuVmVSetUp, the second is pinned in s0 (it is REUSED for the table
 * index after the call).  A non-zero SetUp verdict returns -1 (the
 * addiu v0,-1 rides the bnez delay).  Success indexes the VM record
 * table: v1 = the table pointer loaded from D_8016AD38, v0 = s0*16 +
 * v1, and the return is the UNSIGNED BYTE at +1 - the per-record
 * program-volume field (record stride 0x10, +0 is the next field).
 */

extern long SpuVmVSetUp();
extern long D_8016AD38;

long func_80069120(long prog, long voice)
{
    long pv;
    long sv;

    pv = (short)prog;
    sv = (short)voice;
    if (SpuVmVSetUp(pv, sv) != 0)
        return -1;
    return *(unsigned char *)(sv * 16 + D_8016AD38 + 1);
}

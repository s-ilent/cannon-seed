/* cc-post: sdk-aspsx
 *
 * Real-decompiled-C game function #26 - the func_80069174 row (g3_eu,
 * 0x80069174, extent 0x74) lands as the psyq libsnd VM_PROG member
 * SpuVmSetProgPan, identity PROVEN by sdk_members.py unique placement
 * (config/symbols.curated.txt: SpuVmSetProgPan = 0x80069174).
 *
 * Decode: the byte-twin of landed #25 (func_800690AC SpuVmSetProgVol) -
 * instruction-for-instruction identical except the record field offset:
 * +4 (the per-record program-pan byte) instead of +1 (the volume byte).
 * Same raw third argument pinned into s1 across the SpuVmVSetUp call,
 * same -1 verdict exit in the bnez delay, same aliased base-pointer
 * reload after the sb with the empty load-delay nop, same unsigned
 * write-verify return.
 */

extern long SpuVmVSetUp();
extern long D_8016AD38;

long func_80069174(long prog, long voice, long pan)
{
    long pv;
    long sv;

    pv = (short)prog;
    sv = (short)voice;
    if (SpuVmVSetUp(pv, sv) != 0)
        return -1;
    *(unsigned char *)(sv * 16 + D_8016AD38 + 4) = (unsigned char)pan;
    return *(unsigned char *)(sv * 16 + D_8016AD38 + 4);
}

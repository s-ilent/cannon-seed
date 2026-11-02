/* cc-post: sdk-aspsx
 *
 * Real-decompiled-C game function #24 - the func_800691E8 row (g3_eu,
 * 0x800691E8, extent 0x54) lands as the psyq libsnd VM_PROG member
 * SpuVmGetProgPan, identity PROVEN by sdk_members.py unique placement
 * (config/symbols.curated.txt: SpuVmGetProgPan = 0x800691E8).
 *
 * Decode: the byte-twin of landed #23 (func_80069120 SpuVmGetProgVol) -
 * the same prologue (frame 0x18, the sll16/sra16 extend pairs, sv pinned
 * in s0 and reused as the table index), the same SpuVmVSetUp call with
 * the addu a1,s0,zero delay, the same non-zero-verdict -1 exit (addiu
 * v0,-1 riding the bnez delay), the same D_8016AD38 record-table walk
 * (v1 = the pointer word, v0 = s0*4*4 = sv*16, addu v0,v0,v1 = the
 * off + base operand order, the sll filling the pointer load's delay) -
 * differing ONLY in the returned field offset: +4 instead of +1, the
 * per-record program-pan byte (record stride 0x10; +1 is the volume
 * field #23 returns).  Unsigned byte return (lbu).
 */

extern long SpuVmVSetUp();
extern long D_8016AD38;

long func_800691E8(long prog, long voice)
{
    long pv;
    long sv;

    pv = (short)prog;
    sv = (short)voice;
    if (SpuVmVSetUp(pv, sv) != 0)
        return -1;
    return *(unsigned char *)(sv * 16 + D_8016AD38 + 4);
}

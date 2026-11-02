/* cc-post: sdk-aspsx
 *
 * Real-decompiled-C game function #25 - the func_800690AC row (g3_eu,
 * 0x800690AC, extent 0x74) lands as the psyq libsnd VM_PROG member
 * SpuVmSetProgVol, identity PROVEN by sdk_members.py unique placement
 * (config/symbols.curated.txt: SpuVmSetProgVol = 0x800690AC).
 *
 * Decode: the write side of landed #23/#24's VM_PROG getter pair.  Both
 * leading arguments sign-extend (the psyq VM short-arg law, sll16/sra16
 * with sv pinned in s0 for reuse); the THIRD argument is used raw - no
 * extend anywhere, gcc pins it into s1 in the prologue (the param-web
 * coalescing: a2 is caller-saved and dead after the copy) and the sb
 * truncates it to the record byte.  Non-zero SpuVmVSetUp verdict
 * returns -1 in the bnez delay; success stores the byte at +1 (the
 * per-record program-volume field, stride 0x10, off + base operand
 * order) and returns the byte READ BACK - the base pointer word
 * D_8016AD38 is RELOADED after the store (the store may alias the
 * global pointer word itself - the func_80069740 reload law), v1 =
 * sv*16 survives across it, the reloaded base folds into a fresh addu
 * v1,v1,v0 with the load's delay slot EMPTY (nothing to schedule - the
 * one nop), and the return is the UNSIGNED byte at +1 (lbu) - the psyq
 * setter family's write-verify return.
 */

extern long SpuVmVSetUp();
extern long D_8016AD38;

long func_800690AC(long prog, long voice, long vol)
{
    long pv;
    long sv;

    pv = (short)prog;
    sv = (short)voice;
    if (SpuVmVSetUp(pv, sv) != 0)
        return -1;
    *(unsigned char *)(sv * 16 + D_8016AD38 + 1) = (unsigned char)vol;
    return *(unsigned char *)(sv * 16 + D_8016AD38 + 1);
}

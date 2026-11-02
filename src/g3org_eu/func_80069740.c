/* cc-post: sdk-aspsx
 *
 * Real-decompiled-C game function #20 - the func_80069740 row (g3org_eu,
 * 0x80069740..0x80069980, extent 0x240) lands as the psyq libsnd VAG
 * attribute reader, identity PROVEN by the sdk_members.py unique UT_GVA
 * placement + sig-db agrees on all eight targets (pinned member row
 * SsUtGetVagAtr = 0x80069740 in the curated file's g3org_eu section,
 * extent 0x23c - the game row carries 0x4 tail slack to the next member
 * boundary, the game's own cc1 2.6.3-PSX compiled copy, same class as
 * the landed SsSetMVol / SsVabTransBodyPartly rows; only g3org_eu gives
 * the copy its own yaml row, the other seven carry it as an interior
 * pinned label of their composite sdk rows).
 *
 * Decode (the listing is the only authority; psyq LIBSND statics):
 *  - guard: the per-vab status byte D_8017E120[(short)vabid] must read 1
 *    (vab head loaded - the 79758 guard's sibling table; lbu + ori 1
 *    compare, the sll16/sra16 extend-in-place rides the raw a0), else
 *    return -1 through the shared epilogue (j + v0 = -1 in the delay);
 *  - func_80067F84(vabid, prog) is called for side effects only, its
 *    return value is never read (the (short)prog extend rides the jal:
 *    sll a1,16 before, sra a1,16 in the delay slot);
 *  - after the call the prog*16+tone record offset is built: the byte
 *    D_8017E107 (set by the callee - the current prog bookkeeping) is
 *    shifted left 4 (16 VAGs per prog), added to the RAW tone (s1 = a2,
 *    never sign-extended on its own) and the SUM takes the fused
 *    sll16/sra11 = (short)sum * 32, the 0x20-byte VAG attribute record
 *    stride;
 *  - D_80178A00 = the VAG attribute table base pointer (word extern);
 *    the 0x20-byte record at base + off is copied FIELD BY FIELD into
 *    attr (a3, held in s0): 14 single bytes at 0x00..0x0D - gcc reads
 *    byte 7 BEFORE byte 6 - then four halfwords at 0x10..0x16; the
 *    record's 0x0E/0x0F hole is never read on either side;
 *  - the D_80178A00 word is RELOADED before every byte copy (the
 *    preceding sb to the arbitrary attr pointer may alias it - char
 *    stores alias all), 14 reloads; after the last sb one final reload
 *    folds the base into the offset register (addu v1, v1, v0) and the
 *    four lhu/sh pairs reuse it with no further reload (the u16 stores
 *    do not clobber the u32 word under gcc 2.6.3's alias rules);
 *  - return 0 (v0 = 0 materializes between the last lhu and its sh).
 *
 * Source-shape laws (probe 144/144, scripts/probe697_diff.py): the
 * record-offset addition MUST read `off + D_80178A00`, never
 * `D_80178A00 + off` - the operand order is gcc 2.6.3's register-pick
 * law for the chain: `off + base` allocates the byte-load chain in v1
 * (retail) with the final addu in (off, base) order; `base + off` puts
 * the chain in a0 with addu (base, off) - a whole-image byte diff. The
 * positive-guard form (if == 1 { body; return 0; } return -1;) keeps
 * the retail branch polarity (beq to the body, the fail path as the
 * out-of-line j + v0 = -1 delay pair); the bne/early-return form
 * inverts both. The bare-symbol loads (lbu $v1,D_8017E107 etc.) expand
 * to the retail self-register lui/%lo pairs in the assembler.
 *
 * Externs: func_80067F84 is the unbanked 0xd4 sdk asm row at 0x80067F84
 * (roles structural, auto names stay sdk-lane-gated);
 * D_8017E120/D_8017E107/D_80178A00 ride the auto extern path.
 */

extern unsigned char D_8017E120[];
extern unsigned char D_8017E107;
extern unsigned long D_80178A00;
extern long func_80067F84();

long func_80069740(short vabid, short prog, long tone, unsigned char *attr)
{
    long off;

    if (D_8017E120[vabid] == 1) {
        func_80067F84(vabid, prog);
        off = (short)(tone + (D_8017E107 << 4)) * 32;
        attr[0x0] = *(unsigned char *)(off + D_80178A00 + 0x0);
        attr[0x1] = *(unsigned char *)(off + D_80178A00 + 0x1);
        attr[0x2] = *(unsigned char *)(off + D_80178A00 + 0x2);
        attr[0x3] = *(unsigned char *)(off + D_80178A00 + 0x3);
        attr[0x4] = *(unsigned char *)(off + D_80178A00 + 0x4);
        attr[0x5] = *(unsigned char *)(off + D_80178A00 + 0x5);
        attr[0x7] = *(unsigned char *)(off + D_80178A00 + 0x7);
        attr[0x6] = *(unsigned char *)(off + D_80178A00 + 0x6);
        attr[0x8] = *(unsigned char *)(off + D_80178A00 + 0x8);
        attr[0x9] = *(unsigned char *)(off + D_80178A00 + 0x9);
        attr[0xA] = *(unsigned char *)(off + D_80178A00 + 0xA);
        attr[0xB] = *(unsigned char *)(off + D_80178A00 + 0xB);
        attr[0xC] = *(unsigned char *)(off + D_80178A00 + 0xC);
        attr[0xD] = *(unsigned char *)(off + D_80178A00 + 0xD);
        *(unsigned short *)(attr + 0x10) = *(unsigned short *)(off + D_80178A00 + 0x10);
        *(unsigned short *)(attr + 0x12) = *(unsigned short *)(off + D_80178A00 + 0x12);
        *(unsigned short *)(attr + 0x14) = *(unsigned short *)(off + D_80178A00 + 0x14);
        *(unsigned short *)(attr + 0x16) = *(unsigned short *)(off + D_80178A00 + 0x16);
        return 0;
    }
    return -1;
}

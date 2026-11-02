/* cc-post: sdk-aspsx
 *
 * Real-decompiled-C game function #19 - the func_80079758 row (mainmenu_eu,
 * 0x80079758..0x800798C8, extent 0x170) lands as the psyq libsnd VAB body
 * partial-transfer stager, identity PROVEN by the sdk_members.py unique
 * VS_VTBP placement + sig-db agrees on all eight targets (pinned member
 * row SsVabTransBodyPartly in seven symbols files already; only mainmenu_eu
 * gives the copy its own yaml row - the other seven carry it as an interior
 * pinned label of their composite sdk rows). The archive member extent is
 * 0x160; the game's row is 0x170 (0x10 tail slack to the next member
 * boundary, the game's own cc1 2.6.3-PSX compiled copy, same class as the
 * landed SsVabTransCompleted / func_8006AC04 / func_80067690 rows).
 *
 * Decode (the listing is the only authority; psyq LIBSND statics):
 *  - D_8019344C = per-vab status byte array (1 = body transferred,
 *    2 = head loaded, body pending); D_80195760/D_801957A4 = the two
 *    adjacent 17-word per-vab tables (0x80195760 + 0x44 = 0x801957A4):
 *    body transfer size and body SPU-RAM destination;
 *  - D_800C8930 = the remaining-byte word of the active body transfer
 *    (0 = idle), D_800C8934 = the active vabid halfword (-1 = none);
 *  - guard 1: (vabid & 0xFFFF) < 0x11 unsigned (andi + sltiu, 17 vabs);
 *  - guard 2: status byte == 2 (lbu + ori 2 compare) - only a head-loaded
 *    vab accepts a body part; the sign-extended vabid (sll/sra into s1,
 *    read off the raw incoming a2) is the guard-2 index and lives to the
 *    pending compare - v is the raw-param copy PINNED to a1 (the parm
 *    shuffle addu a1,a2; gcc 2.6.3 coalesces an unpinned local into the
 *    param web, retail kept two webs) feeding the guard-1 andi and the
 *    arm-block pending store; the sequential goto-fail form keeps the
 *    sll/sra between the two guard branches and the shared fail tail
 *    (.L80079818) mid-function with the pending beq falling into it;
 *  - the arm block (idle only): pending halfword = v (sh), remaining =
 *    D_80195760[vab] (the sll vab*4 index is shared with the SpuSetTransfer
 *    StartAddr table read - gcc hoists it into the bnez delay slot),
 *    SpuSetTransferMode(0), SpuSetTransferStartAddr(D_801957A4[vab]);
 *  - the pending halfword is re-read (lh) and must equal vab again - the
 *    positive form (beq s2,s1 forward to the transfer block, the beq's
 *    delay carries chunk = size) falls through into the shared fail tail;
 *  - the clamp is UNSIGNED (sltu): chunk = min(size, remaining);
 *  - _spu_setInTransfer(1) + SpuWritePartly(addr, chunk); the remaining
 *    word is RELOADED fresh after the call and updated in place
 *    (D_800C8930 -= chunk: lw/subu/sw/bnez share one register); non-zero
 *    = return -2 (more parts to come);
 *  - completion: pending = -1, remaining = 0, status byte = 1 (body done),
 *    return the vab id (the pending re-read, addu v0,s2).
 *
 * Externs: SpuSetTransferMode/SpuSetTransferStartAddr/_spu_setInTransfer/
 * SpuWritePartly are pinned member rows in config/symbols.mainmenu_eu.txt
 * (0x800798C8 / 0x8007ABC0 / 0x8007ABFC / 0x8007AC38); D_800C8930/D_800C8934
 * are dlabels of the data_800C35B8 listing; D_8019344C/D_80195760/D_801957A4
 * ride the auto extern path (SHN_ABS).
 */
extern unsigned char D_8019344C[];
extern unsigned long D_80195760[];
extern unsigned long D_801957A4[];
extern unsigned long D_800C8930;
extern short D_800C8934;
extern long SpuSetTransferMode(long mode);
extern long SpuSetTransferStartAddr(unsigned long addr);
extern long _spu_setInTransfer(long flag);
extern long SpuWritePartly(unsigned char *addr, long size);

long func_80079758(unsigned char *addr, long size, long vabid)
{
    register long v asm("$5");
    long vab;
    long pending;
    long chunk;
    unsigned long left;

    v = vabid;
    if ((v & 0xFFFF) >= 0x11u)
        goto fail;
    vab = (vabid << 0x10) >> 0x10;
    if (D_8019344C[vab] != 2)
        goto fail;
    if (D_800C8930 == 0) {
        D_800C8934 = (short)v;
        D_800C8930 = D_80195760[vab];
        SpuSetTransferMode(0);
        SpuSetTransferStartAddr(D_801957A4[vab]);
    }
    pending = D_800C8934;
    if (pending == vab)
        goto transfer;
fail:
    _spu_setInTransfer(0);
    return -1;
transfer:
    chunk = size;
    left = D_800C8930;
    if (left < chunk)
        chunk = left;
    _spu_setInTransfer(1);
    SpuWritePartly(addr, chunk);
    D_800C8930 -= chunk;
    if (D_800C8930 != 0)
        return -2;
    D_800C8934 = -1;
    D_800C8930 = 0;
    D_8019344C[pending] = 1;
    return pending;
}

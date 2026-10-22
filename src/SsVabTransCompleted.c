/* cc-post: sdk-aspsx
 *
 * LIBSND SSVABTC member .text+0x0 (extent 0x2c) - sign-extends the mode
 * argument and forwards it to the LIBSPU transfer-status query (the
 * S_ITC member, pinned per target), then truncates the answer back to
 * 16 bits on return. psyq prototype: short SsVabTransCompleted(long
 * mode). Six of the seven pinned copies jal-target the pinned S_ITC
 * row; the g3_jp copy targets an inner SpuSetCommonAttr entry
 * (SCA+0x320) and stays asm for now.
 */
extern long SpuIsTransferCompleted(long mode);

short SsVabTransCompleted(long mode)
{
    return (short)SpuIsTransferCompleted((short)mode);
}

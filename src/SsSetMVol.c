/* cc-post: sdk-aspsx
 *
 * LIBSND SsSetMVol member (extent 0x50, all eight targets dw=0
 * modulo the per-target SCA jal) - builds the 8-byte mvol head of the
 * 0x28-byte attr record at sp+0x10 and forwards it to the pinned
 * SpuSetCommonAttr member. Short params keep the sll16/sra16
 * extend-in-place on the raw argument registers; the *0x81 multiply
 * strength-reduces to sll7+addu; the right-volume store rides the jal
 * delay slot. mask 3 = SPU_COMMON_MVOLL|SPU_COMMON_MVOLR.
 */
extern long SpuSetCommonAttr(void *attr);

void SsSetMVol(short voll, short volr)
{
    struct {
        long mask;
        short left;
        short right;
        char pad[0x20];
    } attr;

    attr.mask = 3;
    attr.left = voll * 0x81;
    attr.right = volr * 0x81;

    SpuSetCommonAttr(&attr);
}

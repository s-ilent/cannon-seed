/* cc-post: sdk-aspsx
 *
 * LIBSND SSSETSV member (extent 0x160) - builds the 0x28-byte attr
 * record at sp+0x10 and forwards it to the pinned SCA member. Short
 * vl/vr locals keep the arm-1 clamp tests on the raw params (a1/a2).
 */
extern long SpuSetCommonAttr(void *attr);

void SsSetSerialVol(long serial, long voll, long volr)
{
    struct {
        long mask;
        char pad0[0x0C];
        short cd_left;
        short cd_right;
        char pad1[0x08];
        short serial_left;
        short serial_right;
        char pad2[0x08];
    } attr;

    long ser;
    short vl;
    short vr;

    ser = serial;
    vl = voll;
    vr = volr;

    if ((ser & 0xFF) == 0) {
        attr.mask = 0xC0;
        if ((short)voll >= 0x80) {
            vl = 0x7F;
        }
        if ((short)volr >= 0x80) {
            vr = 0x7F;
        }
        attr.cd_left = (vl * 0x7FFF) / 0x7F;
        attr.cd_right = (vr * 0x7FFF) / 0x7F;
    }
    if ((ser & 0xFF) == 1) {
        attr.mask = 0xC00;
        if (vl >= 0x80) {
            vl = 0x7F;
        }
        if (vr >= 0x80) {
            vr = 0x7F;
        }
        attr.serial_left = (vl * 0x7FFF) / 0x7F;
        attr.serial_right = (vr * 0x7FFF) / 0x7F;
    }

    SpuSetCommonAttr(&attr);
}

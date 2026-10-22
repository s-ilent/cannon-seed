/* cc-post: sdk-aspsx
 *
 * LIBSND SsSetSerialAttr member (extent 0x94, all eight targets dw=0
 * modulo the per-target SCA jal) - builds the 0x28-byte attr record
 * at sp+0x10 and forwards it to the pinned SpuSetCommonAttr member.
 * Field provenance (evidence: the four sw sites): +0x14 <- serial 0,
 * attr 1, mask 0x100; +0x18 <- serial 0, attr 0, mask 0x200; +0x20 <-
 * serial 1, attr 1 (the attr==serial compare gcc lowers to bne a1,a0),
 * mask 0x1000; +0x24 <- serial 1, attr 0, mask 0x2000. Two SEPARATE
 * ifs per serial block, not else-if - the else-if form makes gcc emit
 * skip jumps retail does not have (the attr==0 body falls straight
 * into the re-test). Unrecognized (serial, attr) combos still reach
 * the call with the record unwritten - retail behaviour, preserved.
 */
extern long SpuSetCommonAttr(void *attr);

void SsSetSerialAttr(long serial, long attr, long mode)
{
    struct {
        long mask;
        char pad0[0x10];
        long f14;
        long f18;
        char pad1[4];
        long f20;
        long f24;
    } cattr;

    if ((serial & 0xFF) == 0) {
        if ((attr & 0xFF) == 0) {
            cattr.mask = 0x200;
            cattr.f18 = mode & 0xFF;
        }
        if ((attr & 0xFF) == 1) {
            cattr.mask = 0x100;
            cattr.f14 = mode & 0xFF;
        }
    }
    if ((serial & 0xFF) == 1) {
        if ((attr & 0xFF) == 0) {
            cattr.mask = 0x2000;
            cattr.f24 = mode & 0xFF;
        }
        if ((attr & 0xFF) == (serial & 0xFF)) {
            cattr.mask = 0x1000;
            cattr.f20 = mode & 0xFF;
        }
    }

    SpuSetCommonAttr(&cattr);
}

/* cc-post: sdk-aspsx
 *
 * LIBGPU Set-family member: the polygon initializer writes the
 * primitive's length byte (9, at offset 3 - the len field of word 0)
 * and its primitive-ID byte (0x34, at offset 7 - the code byte
 * of word 1), both as single BYTES (sb).  The second store rides the jr
 * delay slot.  Identity PROVEN by sdk_members.py unique placements +
 * sig-db agrees; the (len, code) constants are the official psyq
 * primitive table values.
 *
 * Byte-identical copies across g3_jp, g3org_jp and slps_00270.
 */
void SetPolyGT3(unsigned char *p)
{
    p[3] = 9;
    p[7] = 0x34;
}

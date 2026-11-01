/* mainmenu_jp func_80084924 row alabel - the staged directory-stream
 * loader (listing 0x80077CD4..0x80077D3C, 0x28 frame, ra+s0+s1); offline
 * decode, cron-20261101-0621 window, oracle DOWN.
 *
 * SEMANTICS: stage a stream by selector a1, then run the loader family;
 * the bool return is func_80074F8C(0, 0) == 0 (sltiu $v0, $v0, 1):
 *   buf = sp+0x10 (8 bytes free before s0@0x18/s1@0x1C/ra@0x20)
 *   func_8007502C(a1, buf);
 *   func_80074B28(2, buf, 0);
 *   func_80074FAC(a0, a2, 0x80);
 *   return func_80074F8C(0, 0) == 0;
 * a0 is always the constant 1 at every known site.
 *
 * CALL SITES (jal 0x0C01DF35 sweep, 3 total; all stage &D_80149484):
 *   func_80077678 (data row, the PVD head) 0x800776A8: (1, 0x10, s0)
 *       - a1 = SECTOR 16, the ISO9660 Primary Volume Descriptor;
 *   func_80077678 second call 0x80077754: (1, *(u32*)&D_80159510, s0)
 *       - a1 = the LBA word read (misaligned lwl 3/lwr 0) out of the
 *         descriptor buffer D_80159510 - the root directory;
 *   fn3 0x80077A7C: (1, *(u32*)(&D_80147E60 + id*0x2C), s0)
 *       - a1 = the dir id's LBA word from the 0x2C-stride descriptor
 *         table D_80147E60.
 * So a1 is a stream selector / sector number, NEVER a pointer.
 *
 * The four callees are unbanked (no sdk hit in this window); their roles
 * are structural only: 7502C = stage/seek by selector, 74B28(2, buf, 0)
 * = command with the staged selector echo, 74FAC(dst=&D_80149484, 0x80)
 * = the transfer, 74F8C(0, 0) = the completion probe inverted to bool.
 *
 * STAGING: own row after the yaml split (step 6, parked plan); judge live.
 */

s32 func_80077CD4(s32 a0, s32 a1, s32 a2) {
    /* volatile-free; buf is only 8 bytes of stack (sp+0x10..sp+0x17) */
    u32 buf[2];

    func_8007502C(a1, buf);
    func_80074B28(2, buf, 0);
    func_80074FAC(a0, a2, 0x80);
    return func_80074F8C(0, 0) == 0;
}

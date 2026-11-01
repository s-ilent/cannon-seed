/* cc-post: keep-epilogue
 *
 * The func_80077CD4 row (mainmenu_jp, 0x80077CD4..0x80077D40, extent 0x6c)
 * - the LIBCD ISO9660 family's staged directory-stream loader, landed as
 * real C in the cron-20261101-1258 split window (runbook phase F step 6).
 * buf is 8 stack bytes at sp+0x10 (frame 0x28: ra + s0 + s1); gcc hoists
 * the s1 = a0 / a0 = a1 / s0 = a2 (delay slot) argument shuffle around
 * the four calls:
 *   func_8007502C(selector a1, buf)      - stage/seek by sector selector
 *   func_80074B28(2, buf, 0)             - command with the staged echo
 *   func_80074FAC(a0, dst a2, 0x80)      - the 0x800-byte transfer
 *   return func_80074F8C(0, 0) == 0      - completion probe, sltiu bool
 * Call sites (jal 0x0C01DF35 sweep, 3): CD_newmedia 0x800776A8 stages the
 * PVD (selector 0x10), its second call stages the root-dir LBA word read
 * misaligned out of D_80159510, CD_cachefile 0x80077A7C stages the dir
 * id's LBA from the 0x2C-stride descriptor table D_80147E60 - a1 is
 * ALWAYS a sector selector, never a pointer. The four callees are the
 * unbanked cd_read family internals (roles structural); auto names stay
 * until the sdk lane banks them.
 */
extern int func_8007502C();
extern int func_80074B28();
extern int func_80074FAC();
extern int func_80074F8C();

int func_80077CD4(int a0, int a1, int a2)
{
    char buf[8];

    func_8007502C(a1, buf);
    func_80074B28(2, buf, 0);
    func_80074FAC(a0, a2, 0x80);
    return func_80074F8C(0, 0) == 0;
}

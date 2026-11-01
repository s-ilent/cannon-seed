/* cc-post: (none)
 *
 * memcpy_iso9660 - the psyq 3.3 LIBCD ISO9660 member's own copy of memcpy
 * (mainmenu_jp 0x80077D40..0x80077D74, extent 0x34), landed as real C in
 * the cron-20261101-1258 split window (runbook phase F step 6; the curated
 * rename rides the row's c flip per the banked plan - the seven sibling
 * own-row copies keep their asm rows until their own landings). Family
 * shape, byte-identical across all seven sibling rows (census sha
 * f3e0fb2d): len==0 early-out, t = len-1, do { *dst++ = *src++; } while
 * (--t != -1). Source-shape laws this body reproduces (both banked for the
 * six sibling rows' future C flips):
 *  - the retail 8-byte leaf frame (addiu sp,-8 / addiu sp,8, no ra save)
 *    needs an address-used pad local (char pad[8]; asm("" :: "r"(pad)))
 *    - plain C lets gcc elide the frame entirely (built 48 vs row 52);
 *  - the counter lives in $3 (v1) via a register-asm pin and the -1 cap
 *    materializes in n's dead register a2 (addiu a2,zero,-1); unpinned,
 *    gcc swaps the roles (t in a2, cap in v1) and the bne pair flips.
 */
void memcpy_iso9660(void *dst, const void *src, int n)
{
    register int t asm("$3");
    char pad[8];

    __asm__ ("" : : "r"(pad));
    if (n == 0)
        return;
    t = n - 1;
    do {
        *(char *)dst++ = *(const char *)src++;
    } while (--t != -1);
}

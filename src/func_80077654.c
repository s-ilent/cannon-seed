/* cc-post: keep-epilogue
 *
 * The func_80077654 row (mainmenu_jp, 0x80077654..0x80077678, extent 0x24)
 * - the LIBCD ISO9660 member's _cmp match leaf, landed as real C in the
 * cron-20261101-1258 split window (runbook phase F). Nine instructions:
 * addiu sp,-0x18 / sw ra,0x10 / jal strncmp (delay ori a2,0xC) /
 * sltiu v0,1 / lw ra / addiu sp,0x18 / jr ra / nop. Identity: sdk_members
 * places LIBCD _cmp between CdSearchFile and CD_newmedia in all eight
 * targets at stride 0x24 from CdSearchFile's end (g3_jp 0x800622B4,
 * g3_eu 0x80062C44, g3org_jp 0x8005FE10-class); here it is the
 * strncmp-12 ISO9660 8.3 matcher the CdSearchFile cache search calls
 * through 0x80077654 (two matchers for two name spaces: fn2's repacked
 * table names use strcmp, the raw ISO9660 cache names use this).
 * Auto name kept: the sdk lane owns the curated rename pass.
 */
extern int strncmp(const char *, const char *, unsigned int);

int func_80077654(const char *a0, const char *a1)
{
    return strncmp(a0, a1, 0xC) == 0;
}

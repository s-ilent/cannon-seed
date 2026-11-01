/* cc-post: (none)
 *
 * The func_8007796C row (mainmenu_jp, 0x8007796C..0x80077A18, extent 0xac)
 * - the LIBCD ISO9660 family's cached-directory lookup leaf, landed as
 * real C in the cron-20261101-1258 split window (runbook phase F step 6).
 * Walks the CD_newmedia-built entry table (0x80 records x 0x2C stride:
 * u32 id at D_80147E88 + off, char name[0x20] at D_80147E90 + off): id 0
 * = end-of-table -> -1; id match + strcmp hit -> i + 1 (1-BASED);
 * exhausted -> -1. Exactly ONE call site: the CdSearchFile walker's
 * 8-slot component loop at 0x80077454 (a0 = the current dir id, a1 = the
 * staged component name).
 * Source-shape law banked this row: BOTH table accesses keep their own
 * integer offset IV (s1 for the ids, s2 for the names) added to the
 * SYMBOL re-materialized per iteration (lui/addiu/addu through $at at
 * .L800779A0 every round) - the two-pointer cursor draft form (offsets
 * pre-baked into the pointers) compiles to a one-time lui/addiu and
 * lw 0(cursor), which retail never does; gcc 2.6.3 strength-reduces one
 * IV per access site and does not coalesce the pair. The name-cursor
 * increment rides both mismatch paths' delay slots (gcc scheduling,
 * no source pin needed). Auto name kept: the sdk lane owns the rename.
 */
extern unsigned char D_80147E88[];
extern char D_80147E90[];
extern int strcmp(const char *, const char *);

int func_8007796C(int id, const char *name)
{
    int i;
    int idoff;
    const char *np;
    int cur;

    np = D_80147E90;
    idoff = 0;
    for (i = 0; i < 0x80; i++) {
        cur = *(int *)(D_80147E88 + idoff);
        if (cur == 0)
            return -1;
        if (cur == id && strcmp(name, np) == 0)
            return i + 1;
        idoff += 0x2C;
        np += 0x2C;
    }
    return -1;
}

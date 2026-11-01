/* cc-post: keep-epilogue
 *
 * The func_8007796C row (mainmenu_jp, 0x8007796C..0x80077A18, extent 0xac)
 * - the LIBCD ISO9660 family's cached-directory lookup leaf, landed as
 * real C in window cron-20261101-1415 (runbook phase F step 6, the
 * func_80084924 parent-row split's fourth unit). Walks the CD_newmedia-
 * built entry table (0x80 records x 0x2C stride: u32 id at D_80147E88 +
 * off, char name[0x20] at D_80147E90 + off): id 0 = end-of-table -> -1;
 * id match + strcmp hit -> i + 1 (1-BASED); exhausted -> -1. Exactly ONE
 * call site: the CdSearchFile walker's 8-slot component loop at
 * 0x80077454 (a0 = the current dir id, a1 = the staged component name).
 * Source-shape laws banked this row:
 *  - the ID side re-materializes the SYMBOL per iteration and adds its
 *    own integer offset IV ($s1) through $at: lui/addiu %lo into $at/
 *    addu/lw 0 at .L800779A0 every round. That is the aspsx < 2.30
 *    4-insn at-split, NOT a source property - gcc 2.6.3 always emits
 *    `lw $2,D_80147E88($idoff)` (symbol-displacement) and maspsx folds
 *    %lo into the lw unless the flip is on. This is a PSYQ SDK body
 *    inside the mainmenu pair (the game modules' newer aspsx takes the
 *    folded form), so the lever is the unit-scope maspsx flag
 *    `unit:func_8007796C --addiu-at on` in tools/maspsx_flags.txt -
 *    the first sdk-body row on the mainmenu pair; the family's future
 *    flips (CdSearchFile/CD_newmedia/CD_cachefile) ride the same flag.
 *  - the name side is the opposite shape: ONE lui/addiu in the prologue
 *    into the $s2 cursor, the cursor += 0x2C riding both mismatch paths'
 *    delay slots (gcc scheduling, no source pin); the offset-IV form for
 *    the names (two-pointer cursor draft) never matches.
 *  - init order i = 0 -> np -> idoff (retail prologue zeroes $s0,
 *    materializes $s2, zeroes $s1, in that order); np += 0x2C is the
 *    LAST body statement, idoff += 0x2C is the for-increment (rides the
 *    loop-back bnez delay).
 *  - retail keeps addiu-sp before jr-ra (keep-epilogue, the same class
 *    as func_80077654/func_80077CD4/func_80067690).
 * Auto name kept: the sdk lane owns the rename.
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

    i = 0;
    np = D_80147E90;
    idoff = 0;
    for (; i < 0x80; idoff += 0x2C) {
        cur = *(int *)(D_80147E88 + idoff);
        if (cur == 0)
            return -1;
        if (cur == id && strcmp(name, np) == 0)
            return i + 1;
        np += 0x2C;
        i++;
    }
    return -1;
}

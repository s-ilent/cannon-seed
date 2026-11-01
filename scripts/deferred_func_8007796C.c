/* mainmenu_jp func_80084924 row UNIT 2 - the cached-directory lookup leaf
 * (listing 0x8007796C..0x80077A14, 0x28 frame, ra+s0..s4); offline decode,
 * cron-20261101-0621 window, oracle DOWN (both links 404 at ~42.7h).
 *
 * IDENTITY: no printfs, no strings - a pure lookup. Exactly ONE call site
 * in the whole target (jal 0x0C01DE5B sweep): data_8008433C interior
 * 0x80077454, the CD_newmedia path walker's 8-slot component loop, with
 * a1 = &sp[0x10] (the walker's staged component name); a0 comes from the
 * walker body (the current directory id). Signature (id, name) -> slot+1
 * or -1.
 *
 * TABLE: the CD_newmedia-built entry table, 0x80 records x 0x2C stride
 * (base D_80147E84; full layout in docs/TASKS.md cron-20261101-0621):
 *   +0x04 (D_80147E88 + i*0x2C): u32 id, 0 = end-of-table marker
 *   +0x0C (D_80147E90 + i*0x2C): char name[0x20]
 *
 * ASM SHAPE the C must reproduce (banked from the listing): gcc keeps TWO
 * advancing cursors in saved regs (s1 = byte cursor over the id words from
 * D_80147E88, s2 = name cursor from D_80147E90; both += 0x2C once per
 * iteration - the name-cursor increment rides the branch delay slots of
 * BOTH mismatch paths), loads the id word ONCE per iteration into $v0,
 * short-circuits: beqz id -> -1; bne id,needle -> next (strcmp skipped);
 * strcmp(needle, record-name); bnez -> next; hit = j .ret with
 * `addiu $v0, $s0, 1` in the delay slot (1-BASED index); exhausted loop
 * falls to `addiu $v0, $zero, -1`.
 *
 * STAGING (witnessed window, step 6 of the parked plan): the yaml split
 * gives this unit its own row; copy to src/, judge live.
 */

s32 func_8007796C(s32 id, const char* name) {
    u8* idp;   /* walks &D_80147E88 + i*0x2C (the id words) */
    char* np;  /* walks &D_80147E90 + i*0x2C (the names)    */
    s32 i;
    s32 cur;

    idp = (u8*)&D_80147E88;
    np = (char*)&D_80147E90;
    for (i = 0; i < 0x80; i++) {
        cur = *(s32*)idp;
        if (cur == 0) {
            return -1;
        }
        if (cur == id && strcmp(name, np) == 0) {
            return i + 1;
        }
        idp += 0x2C;
        np += 0x2C;
    }
    return -1;
}

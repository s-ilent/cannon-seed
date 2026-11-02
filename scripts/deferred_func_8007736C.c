/* mainmenu_jp data_8008433C row TRUE HEAD #1 (listing 0x8007736C..
 * 0x80077650, 0x50 frame, ra+s0..s5) - CdSearchFile: the path resolver
 * that ties the whole func_80084924 cluster together. Offline decode,
 * cron-20261101-0621 window (second item), oracle DOWN.
 *
 * IDENTITY (format strings): D_800235A0 "CdSearchFile: searching %s...\n"
 * (cache phase entry, >= 2), D_800235C0 "%s:  found\n" (two spaces,
 * retail), D_800235CC "%s: not found\n" (> 0), D_80023584 "CdSearchFile:
 * disc error\n" (fn3 failure), D_80023550 "%s: path level (%d) error\n",
 * D_8002356C "%s: dir was not found\n". printf = 0x8005C62C pinned.
 *
 * SIGNATURE: a0 = out record pointer (s5; the matched 0x18-byte cache
 * record is copied here in full), a1 = path string (s3; the %s in every
 * message). Returns the matched record's pointer, or 0.
 *
 * FLOW:
 *   if (D_800D8028 != D_800C7CFC) {          // mount guard (cached state)
 *       if (CD_newmedia() == 0) return 0;    // TRUE HEAD #2, 0x80077678
 *       D_800D8028 = D_800C7CFC;
 *   }
 *   if (path[0] != '\\') return 0;           // absolute paths only
 *   id = 1;                                  // the root dir's id
 *   src = path; level = 0;
 *   // ---- component loop (head 0x800773FC; buf = sp+0x10, 8 bytes) ----
 *   while (level < 8) {
 *       if (*src == '\\') {                  // separator/lead: EMPTY hop
 *           src++;  buf[0] = 0;
 *       } else {
 *           copy chars until '\\' or NUL into buf;   // s1 = buf cursor
 *           if (*src == 0) goto final_check;         // 0x80077480
 *           src++;  buf terminate;
 *       }
 *       r = func_8007796C(id, buf);          // fn2, the table lookup
 *       if (r == -1) { buf[0] = 0; goto final_check; }   // 0x800773E4
 *       id = r;                              // the id CHAIN
 *       level++;
 *   }
 * final_check:                                // 0x8007747C
 *   if (level >= 8) { if (v) printf("%s: path level (%d) error", path, level);
 *                     return 0; }
 *   if (buf[0] == 0) { if (v) printf("%s: dir was not found", path);
 *                      return 0; }
 *   if (func_80077A18(id) == 0) {            // fn3 CD_cachefile(a0 = the
 *       if (v) printf("CdSearchFile: disc error\n");   //  containing dir)
 *       return 0;
 *   }
 *   if (D_800C7CF0 >= 2) printf("CdSearchFile: searching %s...\n", buf);
 *   // ---- cache search (head 0x80077560; the "CdSearchFile" phase) ----
 *   for (i = 0; i < 0x40; i++) {
 *       rec = &D_80147884 + i*0x18;
 *       if (rec[8] == 0) break;              // empty name = end of used slots
 *       if (func_80077654(rec + 8, buf) != 0) {          // strncmp(.., 12) == 0
 *           if (D_800C7CF0 >= 2) printf("%s:  found\n", buf);
 *           memcpy(out, rec, 0x18);          // six word-pairs, no call
 *           return rec;
 *       }
 *   }
 *   if (D_800C7CF0 > 0) printf("%s: not found\n", buf);
 *   return 0;
 *
 * THE EMPTY-NAME SENTINEL HOPS: every separator (and the lead '\') runs
 * fn2(id, "") - so each dir's table must carry an entry whose name is the
 * empty string and whose id is the dir's own id (the repacked stream's
 * name_len-0 marker); the id chain otherwise only advances on real
 * components. "\FILE" therefore resolves as fn2(1, "") -> the root's
 * sentinel -> fn3(1) -> cache the root -> search "FILE". The stream-side
 * construction of the sentinels belongs to the loader family (unbanked).
 *
 * THE TWO MATCHERS: fn2 uses FULL strcmp for dir components; the cache
 * search matches through the 0x80077654 leaf = strncmp(a, b, 0xC) == 0
 * (12 chars - the ISO9660 8.3 filename bound, version-suffix tolerant).
 * The cache records' names come from the RAW ISO9660 records (fn3's
 * parser); the table names CD_newmedia's parser built are what fn2
 * compares against.
 *
 * THE MATCH LEAF 0x80077654 (0x18 frame, this window): jal strncmp;
 * ori a2, 0xC; sltiu v0, 1 (return == 0); pure wrapper, 0x20 bytes.
 *
 * THE DEAD BRANCH (retail quirk, banked): the fn3 gate is a plain
 * bnez - the C tested `if (!CD_cachefile(id))`, but CD_cachefile returns
 * -1 (never 0) on failure, so -1 takes the SUCCESS path and the
 * "CdSearchFile: disc error" branch is UNREACHABLE; a failed cache falls
 * into the search over the stale/zeroed cache and ends as "%s: not
 * found" (or a stale false positive). Retail ships it; the C draft must
 * preserve the `== 0` test exactly.
 *
 * THE DATA ROW'S LAYOUT (0x4b8, yaml-typed data, listing head
 * 0x8007736C): [CdSearchFile 0x8007736C..0x80077650 (0x2E4)][match leaf
 * 0x80077654..0x80077674 (0x20)][CD_newmedia 0x80077678..row end,
 * continuing into the asm row's fragment] - three real functions, zero
 * data. The spill audit (step 1) decides the carve boundaries on TRUE
 * baselines; this draft + deferred_func_80077678.c carry the semantics.
 *
 * STAGING: step 6 of the parked plan (yaml split + C rows + judge live).
 *
 * LADDER PROGRESS (cron-202611021158, continues the 0621 decode; probe
 * vs the committed listing under --addiu-at on):
 *  - THE MOUNT GUARD READS D_800C8028 (not D_800D8028 - the 0621 draft's
 *    symbol was a pre-decode guess; D_800C8028 is the CD_cachefile guard
 *    word's neighbour).
 *  - buf IS 0x20 BYTES, not 8 (retail frame 0x50; the component buffer's
 *    declared extent - gcc sizes the frame from the array).
 *  - CLOSED at probe 180/186: the prologue (swap-regs $19 $20 +
 *    save-swap $19 $20 - path allocates s4-first in gcc but retail saves
 *    s3 first, a NEW save-order law, cc_post save-swap pass added) and
 *    the mount-guard store (pad-lw 3: retail pads the pre-store reload's
 *    lw because gcc's #nop was decided against the far-store use TWO
 *    slots ahead while maspsx's re-derivation looks only ONE ahead (the
 *    at-expansion prefix) - the upstream-class fix is a maspsx one-ahead
 *    hazard look, BANKED as the next tools item with the 8/8 re-verify
 *    ritual; pad-lw 3 = the mas.s occurrence of the pre-store reload).
 *  - REMAINING (3 words + shapes): (1) the component loop's ROTATION -
 *    retail enters via the separator path (j into the empty-hop region,
 *    id=1 materialized in A0 as the pure call-arg chain, the copy path
 *    out-of-line); the draft's if/else keeps the copy path inline - the
 *    77A18 goto-form class applies; (2) the rule-10 remnant (+3, marker
 *    pending the clean compile's labels); (3) the level/j cursor reg
 *    names settle with the rotation.
 *  - The fixup quartet markers pinned so far (all deterministic,
 *    loud-fail): swap-regs $19 $20, save-swap $19 $20, pad-lw 3.
 *  - tools landed this window: cc_post save-swap + pad-lw passes +
 *    cc.sh marker plumbing (with the 77A18 swap-regs/addu-commute/
 *    delay-sb-out trio from the landing).
 */
extern int D_800C8028;               /* mount guard: cached state */
extern int D_800C7CFC;               /* mount guard: expected state */
extern int D_800C7CF0;               /* trace level */
extern unsigned char D_80147884[];   /* the 0x40-entry cache table */
extern char D_80023550[];
extern char D_8002356C[];
extern char D_80023584[];
extern char D_800235A0[];
extern char D_800235C0[];
extern char D_800235CC[];
extern int func_80077678();
extern int func_8007796C();
extern int func_80077A18();
extern int func_80077654();
extern int printf();

/* cc-post: swap-regs $19 $20
 * cc-post: save-swap $19 $20
 * cc-post: pad-lw 3 */

unsigned char *func_8007736C(unsigned char *out, const char *path) {
    unsigned char buf[0x20];     /* sp+0x10 */
    const char *src;
    unsigned char *rec;
    int id;
    int r;
    int level;
    int i;
    int j;

    if (D_800C8028 != D_800C7CFC) {
        if (func_80077678() == 0) {
            return 0;
        }
        D_800C8028 = D_800C7CFC;
    }
    if (path[0] != '\\') {
        return 0;
    }
    id = 1;
    src = path;
    level = 0;
    while (1) {
        if (*src == '\\') {
            src++;
            buf[0] = 0;
        } else {
            for (j = 0; *src != '\\' && *src != 0; j++) {
                buf[j] = *src++;
            }
            if (*src == 0) {
                goto final_check;
            }
            src++;
            buf[j] = 0;
        }
        r = func_8007796C(id, buf);
        if (r == -1) {
            buf[0] = 0;
            goto final_check;
        }
        id = r;
        level++;
        if (level >= 8) {
            break;
        }
    }
final_check:
    if (level >= 8) {
        if (D_800C7CF0 > 0) {
            printf(&D_80023550, path, level);
        }
        return 0;
    }
    if (buf[0] == 0) {
        if (D_800C7CF0 > 0) {
            printf(&D_8002356C, path);
        }
        return 0;
    }
    if (func_80077A18(id) == 0) {
        if (D_800C7CF0 > 0) {
            printf(&D_80023584);
        }
        return 0;
    }
    if (D_800C7CF0 >= 2) {
        printf(&D_800235A0, buf);
    }
    for (i = 0; i < 0x40; i++) {
        rec = (unsigned char *)&D_80147884 + i * 0x18;
        if (rec[8] == 0) {
            break;
        }
        if (func_80077654(rec + 8, buf) != 0) {
            if (D_800C7CF0 >= 2) {
                printf(&D_800235C0, buf);
            }
            for (j = 0; j < 0x18; j += 4) {
                *(int*)(out + j) = *(int*)(rec + j);
            }
            return rec;
        }
    }
    if (D_800C7CF0 > 0) {
        printf(&D_800235CC, buf);
    }
    return 0;
}

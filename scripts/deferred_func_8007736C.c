/* mainmenu_jp data_8008433C row TRUE HEAD #1 (listing 0x8007736C..
 * 0x80077650, 0x50 frame, ra+s0..s5) - CdSearchFile: the path resolver
 * that ties the whole func_80084924 cluster together. Offline decode,
 * cron-20261101-0621 window (second item), oracle DOWN (links 404;
 * the disc-free witness restore covers the gates).
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
 * FLOW: mount guard (D_800C8028 vs D_800C7CFC, CD_newmedia on mismatch),
 * absolute-path check, then the component loop (separator hops run fn2
 * with the empty string; components copy into the 0x20 buf at sp+0x10
 * and chain the dir id), final_check (level/buf gates, CD_cachefile,
 * the "searching" print), the 0x40-record cache search (empty-name
 * sentinel ends the used slots; strncmp-12 leaf; the 0x18 record copy).
 *
 * THE DEAD BRANCH (retail quirk, banked): the fn3 gate is a plain
 * bnez - the C tested `if (!CD_cachefile(id))`, but CD_cachefile returns
 * -1 (never 0) on failure, so -1 takes the SUCCESS path and the
 * "CdSearchFile: disc error" branch is UNREACHABLE; a failed cache falls
 * into the search over the stale/zeroed cache and ends as "%s: not
 * found" (or a stale false positive). Retail ships it; the C draft must
 * preserve the `== 0` test exactly.
 *
 * LADDER STATE (cron-202611031758, oracle UP disc-free sixteenth
 * rehearsal; probe = judge_unit live; DIFF 170/179 -> 117/186, SIZE 716
 * -> 756 vs 744):
 *  - CLOSED (cron-202611021158): the mount guard reads D_800C8028; buf is
 *    0x20 bytes; the mount-guard store's load-use nop now derives
 *    upstream from the maspsx far-store look-past (pad-lw RETIRED).
 *  - CLOSED (cron-202611021204): the component loop's rotation (do-while
 *    with the entry pre-test, the shared tail, the a0-chain).
 *  - CLOSED this window: REMAINING (1) the cache loop's FOUR-STATE
 *    walker form - rec = (unsigned char*)&D_8014788C[-8] (s0, the addiu
 *    s0,v0,-8 setup), name = &D_8014788C[0] (s3), off = the s1 anchor-
 *    relative offset advanced in the back-edge delay, i = the 0x40
 *    counter (s2, zeroed in the searching-print skip branch's delay);
 *    the empty check reads the EXTERN D_8014788C[off] directly (the
 *    4-insn at-split), NOT a local pointer. (2) the record copy is six
 *    explicit word pairs (lw 0/4/8/C, sw 0/4/8/C, lw 10/14, sw 10/14)
 *    through the s0 walker, returning rec. (3) the copy-exit re-load -
 *    the exit NUL check and the bottom test read *(volatile char*)src
 *    so gcc cannot CSE them into the back-edge load (retail re-loads
 *    *src before the dead check). (4) the sep CSE residue - an empty
 *    asm barrier (gcc 2.6.3 form: asm("" : "=r" (sep) : "0" (sep)); the
 *    '+r' modifier does not exist yet) after sep = '\\' makes the
 *    pinned s4 value opaque so the bottom test materializes a FRESH
 *    ori v1,0x5C (retail re-reads the constant per outer iteration).
 *  - THE INTERLEAVE LAW (this window, the biggest finding): with the
 *    param imports expressed as PINNED-LOCAL INITS (register ... asm()
 *    = param), gcc 2.6.3 DOES emit the interleaved save+import prologue
 *    (sw s5,0x44/addu s5,a0, sw s3,0x3C/addu s3,a1, then ra, then the
 *    batch, s0 in the branch delay) - the shape WithMode proved
 *    unreachable for raw params. The pinned-local-init class is the
 *    rule-15 bypass for the whole interleave family.
 *  - REMAINING (probe 117/186, all localized):
 *    (5) THE IMPORT ORDER: built emits the pinned-local inits in gcc's
 *        allocation/use order (pathv/s3 first - pathv[0] is the first
 *        param use after the guard); retail emits out/s5 FIRST (param
 *        order a0-then-a1). Steering not found this window: declaration
 *        order does not drive it. Next: try an early dead use of outp
 *        before the pathv[0] read, or gcc 2.6.3 K&R register-param
 *        declarations (register ... asm() in the param list).
 *    (6) the s2 counter: the cache loop's i must reuse level's s2 (it
 *        does naturally) but built still holds +3 words (189 vs 186)
 *        - re-measure after (5): the residue sits in the loop head
 *        region 0x800773f0..0x80077420 (the cur=buf delay and the
 *        fresh-v1 placement) and single delay-slot words down the
 *        function (word 50/62/66/74/80/89/93/96/102/108/115, likely
 *        one register-cascade class), then the cache walk 120..188.
 */

extern int D_800C8028;               /* mount guard: cached state */
extern int D_800C7CFC;               /* mount guard: expected state */
extern int D_800C7CF0;               /* trace level */
extern unsigned char D_80147884[];   /* the 0x40-entry cache table */
extern unsigned char D_8014788C[];   /* cache + 8: the name-field anchor */
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

unsigned char *func_8007736C(unsigned char *out, const char *path) {
    unsigned char buf[0x20];     /* sp+0x10 */
    const char *src;
    int id;
    int level;
    int i;
    register unsigned char *cur asm("$17");   /* s1: the buf cursor */
    register int sep asm("$20");              /* s4: the head-test constant */
    register unsigned char *outp asm("$21") = out;   /* s5: the copy destination */
    register const char *pathv asm("$19") = path;    /* s3: the %s in every message */

    if (D_800C8028 != D_800C7CFC) {
        if (func_80077678() == 0) {
            return 0;
        }
        D_800C8028 = D_800C7CFC;
    }
    if (pathv[0] != '\\') {
        return 0;
    }
    id = 1;
    buf[0] = 0;
    src = pathv;
    level = 0;
    sep = '\\';
    asm("" : "=r" (sep) : "0" (sep));   /* opaque: bottom test re-materializes */
    while (1) {
        cur = buf;
        if (*src == sep) {
            goto tail;              /* the separator hop: shared tail */
        }
        do {
            if (*(volatile const char *)src == 0) {
                goto final_check;
            }
            *cur = *src;
            src++;
            cur++;
        } while (*(volatile const char *)src != '\\');
        if (*(volatile const char *)src == 0) {  /* the copy-exit re-load */
            goto final_check;
        }
tail:
        src++;
        *cur = 0;
        id = func_8007796C(id, buf);            /* the a0 chain */
        if (id == -1) {
            buf[0] = 0;
            goto final_check;
        }
        level++;
        if (level >= 8) {
            break;
        }
    }
final_check:
    if (level >= 8) {
        if (D_800C7CF0 > 0) {
            printf(&D_80023550, pathv, level);
        }
        return 0;
    }
    if (buf[0] == 0) {
        if (D_800C7CF0 > 0) {
            printf(&D_8002356C, pathv);
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
    {
        /* the four-state cache walk: s0 = the record walker (anchor-8),
         * s3 = the name walker (anchor, reusing the dead pathv reg),
         * s1 = the anchor-relative byte offset (reusing the dead cur
         * reg), s2 = the 0x40 counter (reusing level's reg); the empty
         * check reads the extern through the at-split with the running
         * offset */
        register unsigned char *rec asm("$16") =
            (unsigned char *)&D_8014788C[-8];
        register const unsigned char *name asm("$19") = &D_8014788C[0];
        register int off asm("$17") = 0;
        for (i = 0; i < 0x40; i++, off += 0x18) {
            if (D_8014788C[off] == 0) {
                break;
            }
            if (func_80077654(name, buf) != 0) {
                if (D_800C7CF0 >= 2) {
                    printf(&D_800235C0, buf);
                }
                *(int *)(outp + 0x00) = *(int *)(rec + 0x00);
                *(int *)(outp + 0x04) = *(int *)(rec + 0x04);
                *(int *)(outp + 0x08) = *(int *)(rec + 0x08);
                *(int *)(outp + 0x0C) = *(int *)(rec + 0x0C);
                *(int *)(outp + 0x10) = *(int *)(rec + 0x10);
                *(int *)(outp + 0x14) = *(int *)(rec + 0x14);
                return rec;
            }
            rec += 0x18;
            name += 0x18;
        }
    }
    if (D_800C7CF0 > 0) {
        printf(&D_800235CC, buf);
    }
    return 0;
}

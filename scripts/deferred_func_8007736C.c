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
 * LADDER STATE (cron-202611021204, the rotation window; probe metric =
 * scripts/slot_probe.py, word-slot difflib vs the committed listing,
 * --addiu-at on):
 *  - CLOSED earlier (cron-202611021158): the mount guard reads
 *    D_800C8028 (not the 0621 guess D_800D8028); buf is 0x20 bytes; the
 *    prologue (save order s5,s3,ra,s4,s2,s1,s0) and the mount-guard
 *    store's load-use nop.
 *  - THE MOUNT-GUARD NOP NOW DERIVES UPSTREAM: the maspsx far-store
 *    hazard look-past landed this window (tools/maspsx_delay_slot.patch,
 *    is_far_store_of_reg; 8/8 whole-image re-verify GREEN, witness
 *    restored) - the pad-lw cc_post marker RETIRES, do not re-add it.
 *  - CLOSED this window (probe 180 -> 144 raw but the SHAPES now match
 *    the retail loop family; the count dip is the cache-loop form, see
 *    REMAINING): the component loop's ROTATION - retail is a do-while
    *    with an entry pre-test: `if (*src == sep) goto tail;` (beq ->
 *    the shared tail out-of-line), the copy arm = do-while with the
 *    NUL exit at the top (beqz + the level<8 slti in its DELAY - the
 *    fold gcc reproduces from the goto form) and the '\\' back-edge
 *    bne with the cursor++ in its delay; the copy-exit carries the
 *    DEAD NUL check before falling into the shared tail (src++;
 *    *cur = 0; call). The tail is SHARED by the separator path and the
 *    copy exit - one sb serves buf[0]=0 (empty hop, cur=buf) and
 *    buf[j]=0 (copy, cur=buf+j).
 *  - THE ID A0-CHAIN: `id = func_8007796C(id, buf); if (id == -1)` -
 *    the self-assignment form puts id's home in a0 (addu $4,$2,$0
 *    post-call, the compare on a0, id=1 materialized in the entry
 *    branch's delay) - retail has NO s-reg for id.
 *  - THE PIN CLASS (the 77A18 block-scoped register pins apply):
 *    register unsigned char *cur asm("$17") (the s1 cursor - gcc keeps
 *    a non-call-crossing cursor in scratch otherwise) and
 *    register int sep asm("$20") (the s4 head-test constant). With the
 *    pins the save count returns to 7 and the frame to 0x50.
 *  - REMAINING (probe 144/186; all localized):
 *    (1) THE CACHE LOOP'S WALKER FORM: retail keeps FOUR loop states -
 *    s0 = the record walker (memcpy source, += 0x18 in the bnez delay),
 *    s3 = the name walker (the strncmp arg, += 0x18), s1 = the
 *    symbol-anchored byte offset (the rec[8] read compiles to the
 *    4-insn at-split D_8014788C + s1, so the empty check is an
 *    extern-array index with a running offset, NOT walker[8]), s2 =
 *    the 0x40 counter. The draft's rec = base + i*0x18 form gives the
 *    sll/addu multiply chain - rewrite as walkers + offset.
 *    (2) THE RECORD COPY IS INLINE-UNROLLED in retail: six lw/sw word
 *    pairs (lw 0/4/8/C, sw 0/4/8/C, lw 10/14, sw 10/14), not a loop -
 *    six explicit word assignments.
 *    (3) THE COPY-EXIT RE-LOAD: retail re-loads *src (lbu + nop) before
 *    the dead check; gcc CSEs it with the back-edge's load - the exit
 *    check needs its own load (open shape).
 *    (4) THE SEP CSE RESIDUE: gcc reuses the pinned s4 for the copy
 *    back-edge's bne; retail materializes a fresh v1 = 0x5C per
 *    iteration (ori $3) - the bottom test must keep its own scratch.
 *    (5) THE PARAM MAP: with the pins gcc hands out s6 (retail s5) and
 *    the save order shifts - the prologue fixup set (swap-regs/
 *    save-swap args) needs re-pinning against the final structure;
 *    the old markers RETIRED with this draft (pad-lw upstreamed, the
 *    swap pair absorbed by the pins).
 *  - tools this window: the maspsx far-store look-past (369dc0c9) and
 *    scripts/slot_probe.py (the word-slot probe the ladder runs on).
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
    unsigned char *rec;
    int id;
    int level;
    int i;
    register unsigned char *cur asm("$17");   /* s1: the buf cursor */
    register int sep asm("$20");              /* s4: the head-test constant */

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
    buf[0] = 0;
    src = path;
    level = 0;
    sep = '\\';
    while (1) {
        cur = buf;
        if (*src == sep) {
            goto tail;              /* the separator hop: shared tail */
        }
        do {
            if (*src == 0) {
                goto final_check;
            }
            *cur = *src;
            src++;
            cur++;
        } while (*src != '\\');
        if (*src == 0) {            /* retail keeps this check; gcc may
                                       fold it - see REMAINING (3) */
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
        rec = (unsigned char *)&D_80147884 + i * 0x18;   /* REMAINING (1):
                                       retail walks s0/s3 + the s1 offset */
        if (rec[8] == 0) {
            break;
        }
        if (func_80077654(rec + 8, buf) != 0) {
            if (D_800C7CF0 >= 2) {
                printf(&D_800235C0, buf);
            }
            for (i = 0; i < 0x18; i += 4) {          /* REMAINING (2):
                                       retail unrolls to six word pairs */
                *(int*)(out + i) = *(int*)(rec + i);
            }
            return rec;
        }
    }
    if (D_800C7CF0 > 0) {
        printf(&D_800235CC, buf);
    }
    return 0;
}

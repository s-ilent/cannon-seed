/* PARKED LADDER - func_80077A18 (CD_cachefile, mainmenu_jp, 0x2bc) - the row
 * is NOT landed; the yaml row stays asm. Window cron-20261101-1533 banked this
 * state; the working src/flip/flags live only in that window's sandbox.
 *
 * STATE: judge SIZE 684 built vs 700 retail; DIFF 86/171 words - and the diff
 * list is now DISPLACEMENT NOISE downstream of exactly ONE structural hole of
 * 4 words: the entry remnant before the init block - `ori $v0,$zero,0x1 /
 * beqz $v0,exit / nop` (the fold-deleted loop-guard copy that retail's cc1
 * pipeline kept and ours deletes) plus one more word in the same window.
 * Everything else structurally matches: the lwl/lwr extent triad (packed-load
 * -> swl/swr 8-byte stack pad -> plain lw a0), the packed size pair
 * memory-to-memory, the register story (s0 src, s1 off IV, s2 i, s3 rec8,
 * s4 rec, s5 recs anchor, s6 id), the init order (i=0 hoisted to the gate-2
 * delay, then recs/rec8/off/rec), the call-arg order (a0=1 hoisted before the
 * id*0x2C multiply, the buffer address last, la s0 + delay-slot copy), the
 * four symbol-form dump at-splits, the anchor-form slot 0/1 stores, the
 * slt/beqz + sltu/bnez tail, the keep-epilogue class.
 *
 * THE REMNANT HUNT (all banked negative):
 *  - 11 loop shapes compiled and swept: while(1)+bottom breaks, do-while
 *    (A&&B), for (A&&B), while (A) pre-test + src break, do-while (A) + src
 *    break, for (A) with two breaks, merged single break, hand-written
 *    `if (A && B) { do {...} while (A && B); }`, for with comma-init clause
 *    - NONE reproduces the remnant under the pinned flag set.
 *  - CC1FLAGS_EXTRA=-funroll-loops and -O3 on the five leading shapes: also
 *    negative. The PSX cc1 has NO __attribute__ (packed syntax parse-errors).
 *  - The misaligned-access mechanism IS solved without attributes: the
 *    struct s4 { char b[4]; } copy emits gcc 2.6.3's block-move lwl/lwr from
 *    the align-1 source and swl/swr through the align-1 DESTINATION TYPE,
 *    while the int local's own reload stays a plain lw (type-driven store,
 *    decl-driven reload) - do NOT regress this to plain int casts.
 *  - The EU twins (mainmenu_eu func_80077FD0 CD_cachefile, func_80078370
 *    CD_newmedia, g3_jp func_800622D8 CdSearchFile class) carry the SAME
 *    remnant at the same relative position (post-searching-gate, pre-init),
 *    so the producer is a shared libcd-source construct, not a per-target
 *    scheduling accident. CD_newmedia's copy is byte-for-byte the same
 *    skeleton (remnant + init + len-terminated loop head).
 *  - Working model: loop.c rotates the loop and the guard copy survives as
 *    materialize+test (the fold lands after the last branch-cleanup pass) -
 *    but no swept source shape triggers the rotation under the pinned flags.
 *    NEXT AXES: (a) the loop condition as an explicit temporary tested
 *    twice; (b) a `continue`-terminated final statement; (c) the len==0
 *    test expressed through the record pointer compare; (d) sweep the
 *    CD_newmedia row (func_80077678, the NEXT queue item) whose decode is
 *    already complete - if ITS landing reproduces the remnant, the construct
 *    will be visible there and back-ports to this row.
 *
 * The unit-scope maspsx flag for the landing (re-add with the yaml flip):
 *   unit:func_80077A18 --addiu-at on
 * and the curated memcpy_iso9660 entry must ride into
 * config/symbols.mainmenu_jp.txt (the C row is the first by-name caller;
 * undef_syms resolves only address-encoded names + the per-target DB).
 * The judge reserves NO ratchet impact until landing.
 */

/* cc-post: keep-epilogue
 *
 * The func_80077A18 row (mainmenu_jp, 0x80077A18..0x80077CD4, extent 0x2bc)
 * - CD_cachefile: the LIBCD ISO9660 family's raw directory-record parser
 * into the 0x40-entry cache (the func_80084924 split's fifth unit, landed
 * as real C in window cron-20261101-1533; runbook phase F step 6). Identity
 * from the format strings: "CD_cachefile: dir not found\n" (staged-load
 * failure), "CD_cachefile: searching...\n" (entry), "\t(%02x:%02x:%02x)
 * %8d %s\n" (per-record dump), "CD_cachefile: %d files found\n" (exit).
 * Flow: id guard on D_800C8024 (== a0 -> 1); staged load via
 * func_80077CD4(1, the id's LBA out of the 0x2C-stride descriptor table
 * D_80147E60, the 0x800 staging buffer D_80149484) != 1 -> "dir not found"
 * (gate > 0) and -1; "searching..." (gate >= 2); the parse loop walks RAW
 * ISO9660 records (len at +0, 0 = terminator; extent LBA misaligned at +2
 * through func_8007502C; size misaligned at +0xA straight into the cache
 * slot's +4; name at +0x21 via memcpy_iso9660), synthesizes slots 0/1 from
 * the "." / ".." constants D_800236F8/FC/FE (never copied from the stream),
 * dumps each record at gate >= 2, and tails with D_800C8024 = id, the next
 * slot's first name byte zeroed while i < 0x40, the count at gate >= 2,
 * return 1.
 * Source-shape laws banked this row:
 *  - the register story: the table base anchor (s5) never walks; the
 *    func_8007502C receiver walks its own cursor (s4, += 0x18 in the dump
 *    gate's shadow), the name cursor walks from base + 8 (s3), and the
 *    dump's byte/word reads index base + a byte-offset IV (s1) - the three
 *    forms of one index the draft's single-cursor shape cannot produce.
 *  - the misaligned stream accesses go through the char-array struct copy
 *    (the PSX cc1 has NO __attribute__): a `struct s4 { char b[4]; }`
 *    assignment emits gcc 2.6.3's block-move lwl/lwr from the align-1
 *    source and swl/swr through the align-1 DESTINATION TYPE, while the
 *    int local's own reload stays a plain lw - the extent argument's exact
 *    retail triad (lwl/lwr -> swl/swr to the 8-byte stack pad -> lw into
 *    a0); the size moves memory-to-memory packed on both sides.
 *  - the four dump loads are SYMBOL-form reads (&D_80147884/85/86/88 + off,
 *    four at-splits), not base-cursor reads - gcc keeps them distinct from
 *    the s5 forms; the size store keeps the (anchor + 4) + IV order.
 *  - the slot 0/1 stores are anchor-form fixed offsets (+8, +0x20, +0x22)
 *    with the "." read unsigned (lhu) and the ".." pair signed (lh/lb) -
 *    the constants' extern types carry the signedness.
 *  - len is RE-READ, never cached (registers s0-s6 are all live): the head
 *    test and the tail's src advance each issue their own lbu; the loop is
 *    a pre-test `while (i < 0x40 && src < end)` (gcc rotates it - the i=0
 *    conjunct folds away, the src<end conjunct leaves the ori-1/beqz
 *    never-taken entry-guard remnant) whose tail keeps the full condition;
 *    the tail's next-slot store re-derives i * 0x18 from the index (fresh
 *    multiply), NOT from the byte-offset IV.
 *  - the misaligned-symbol accesses are the SDK's own aspsx < 2.30
 *    4-insn at-split (LEVER LAW, see func_8007796C.c): the lever is the
 *    unit-scope flag `unit:func_80077A18 --addiu-at on` in
 *    tools/maspsx_flags.txt - applied from the first probe, not laddered.
 *  - retail keeps addiu-sp before jr-ra (keep-epilogue, the landed
 *    func_80077654/func_80077CD4/func_80067690 class).
 * Auto name kept: the sdk lane owns the rename.
 */
extern int printf();
extern int func_80077CD4();
extern int func_8007502C();
extern void memcpy_iso9660();
extern int D_800C8024;
extern int D_800C7CF0;
extern unsigned char D_800236BC[];
extern unsigned char D_800236DC[];
extern unsigned short D_800236F8[];
extern short D_800236FC[];
extern signed char D_800236FE[];
extern unsigned char D_80023700[];
extern unsigned char D_8002371C[];
extern unsigned char D_80147E60[];
extern unsigned char D_80149484[];
extern unsigned char D_80149C84[];
extern unsigned char D_80147884[];
extern unsigned char D_80147885[];
extern unsigned char D_80147886[];
extern unsigned char D_80147888[];
extern unsigned char D_8014788C[];

struct s4 { char b[4]; };

int func_80077A18(int id)
{
    unsigned char *src;
    unsigned char *recs;
    unsigned char *rec;
    unsigned char *rec8;
    int extent;
    int off;
    int i;

    if (id == D_800C8024) {
        return 1;
    }
    if (func_80077CD4(1, *(int *)((unsigned char *)&D_80147E60 + id * 0x2C), D_80149484) != 1) {
        if (D_800C7CF0 > 0) {
            printf(D_800236BC);
        }
        return -1;
    }
    if (D_800C7CF0 >= 2) {
        printf(D_800236DC);
    }
    src = D_80149484;
    i = 0;
    recs = D_80147884;
    rec8 = recs + 8;
    off = 0;
    rec = recs;
    while (i < 0x40 && src < D_80149C84) {
        if (src[0] == 0) {
            break;
        }
        *(struct s4 *)&extent = *(struct s4 *)(src + 2);
        func_8007502C(extent, rec);
        *(struct s4 *)((unsigned char *)recs + 4 + off) = *(struct s4 *)(src + 0xA);
        if (i == 0) {
            *(unsigned short *)(recs + 8) = D_800236F8[0];
        } else if (i == 1) {
            *(short *)(recs + 0x20) = D_800236FC[0];
            *(signed char *)(recs + 0x22) = D_800236FE[0];
        } else {
            memcpy_iso9660(rec8, src + 0x21, src[0x20]);
            rec8[src[0x20]] = 0;
        }
        if (D_800C7CF0 >= 2) {
            printf(D_80023700,
                   *(unsigned char *)((unsigned char *)&D_80147884 + off),
                   *(unsigned char *)((unsigned char *)&D_80147885 + off),
                   *(unsigned char *)((unsigned char *)&D_80147886 + off),
                   *(int *)((unsigned char *)&D_80147888 + off),
                   rec8);
        }
        rec += 0x18;
        rec8 += 0x18;
        i++;
        off += 0x18;
        src += src[0];
    }
    D_800C8024 = id;
    if (i < 0x40) {
        *(unsigned char *)((unsigned char *)&D_8014788C + i * 0x18) = 0;
    }
    if (D_800C7CF0 >= 2) {
        printf(D_8002371C, i);
    }
    return 1;
}

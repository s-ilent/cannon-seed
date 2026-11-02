/* cc-post: keep-epilogue
 * cc-post: remnant-ori1 $L5 $L7 nop
 * cc-post: swap-regs $20 $21
 * cc-post: addu-commute 2
 * cc-post: delay-sb-out
 *
 * mainmenu_jp func_80077A18 - CD_cachefile: the raw-ISO9660 directory-
 * record parser into the 0x40-entry cache (listing 0x80077A18..0x80077CD0,
 * 0x2bc extent, 0x40 frame, ra+s0..s6). The EIGHTEENTH real-decompiled-C
 * game function and the SIXTH unit of the func_80084924 ISO9660 family.
 * Offline decode cron-20261101-0621; the register web solved at source
 * level cron-202611020013 (11-variant offline ladder); the arm-layout
 * pass + the fixup trio landed cron-202611021158 (probe 175/175 slots
 * exact vs the committed listing under MASPSX_UNIT_FLAGS --addiu-at on).
 *
 * FIXUP MARKERS (all deterministic, marker-scoped, judged by word diff):
 *  - remnant-ori1 $L5 $L7 nop: rule 10 re-inserts the loop-entry guard
 *    retail's cc1 keeps and gcc folds (ori $2,1 / beqz $2,$L7 / nop at
 *    the post-searching-gate join; the labels are gcc-deterministic for
 *    this frozen source - any edit that moves them must re-pin).
 *  - swap-regs $20 $21: gcc's local-alloc hands the anchor/walker pair
 *    the opposite callee-saved regs to retail (probe s4=anchor/s5=walker
 *    vs retail s5=anchor/s4=walker); three source permutations did not
 *    flip it - the exchange is a consistent renaming with the frame
 *    save/restore lines excluded.
 *  - addu-commute 2: the size store's addu (gcc canonicalizes both C
 *    operand orders d-first; retail emitted off-first). Occurrence 2 of
 *    the d==a!=s numeric form (1 = the id-multiply chain, which matches
 *    retail and stays).
 *  - delay-sb-out: gcc packed arm1's sb into its join-j's delay; retail
 *    keeps it inline before the j (arm0's sh-in-delay is retail's OWN
 *    packing and is left alone - sb only).
 *
 * ARM LAYOUT: the slot 0/1 arms are OUT-OF-LINE via the goto form
 * (retail: beqz i,arm0 with the ori v0,1 delay feeding the beq i,v0,arm1
 * whose delay preloads a0=rec8 for the name arm's memcpy; the name arm
 * falls into the dump-gate join). arm0's temp is an anonymous expression
 * (gcc hands it the live-in-at-entry $2); arm1's temps are block-scoped
 * register pins $2/$3 - named locals get $3 first under the live-in $2
 * and the anonymous direct form loses the lh/lb sign extension (the
 * banked int-local law), the pins reproduce retail's exact regs AND
 * forms.
 *
 * The full decode story (identity, stream format, cache table, flow,
 * the closed park laws, the 11-variant web ladder and its negatives)
 * lives in scripts/deferred_func_80077A18.c - kept as the banked ladder
 * history.
 */

extern unsigned char D_80149484[];   /* 0x800-B staging buffer */
extern unsigned char D_80149C84[];   /* buffer bound */
extern unsigned char D_80147884[];   /* cache table, 0x40 records x 0x18 */
extern unsigned char D_8014788C[];   /* cache table +8: next slot's name */
extern unsigned char D_80147885[];   /* cache table +1 (dump arg 2 symbol) */
extern unsigned char D_80147886[];   /* cache table +2 (dump arg 3 symbol) */
extern unsigned char D_80147888[];   /* cache table +4: size word (dump arg 4) */
extern unsigned char D_80147E60[];   /* 0x2C-stride dir descriptor table */
extern int D_800C7CF0;               /* trace level */
extern int D_800C8024;               /* cache guard (the cached dir id) */
extern char D_800236BC[];
extern char D_800236DC[];
extern char D_80023700[];
extern char D_8002371C[];
extern unsigned char D_800236F8[];   /* "." u16 arm constant */
extern unsigned char D_800236FC[];   /* ".." u16 arm constant */
extern unsigned char D_800236FE[];   /* ".." NUL byte arm constant */
extern int func_80077CD4();
extern int func_8007502C();
extern void memcpy_iso9660();
extern int printf();

typedef struct {
    unsigned char b[4];
} W4;
int func_80077A18(int id)
{
    unsigned char *src;
    unsigned char *anchor;
    unsigned char *rec;
    unsigned char *rec8;
    unsigned char *sp;
    W4 ext_w;
    int off;
    int i;
    int t;
    int u;

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
    anchor = D_80147884;
    rec8 = anchor + 8;
    i = 0;
    off = 0;
    rec = anchor;
    while (1) {
        if (src[0] == 0) {
            break;
        }
        ext_w = *(W4 *)(src + 2);
        func_8007502C(*(int *)&ext_w, rec);
        sp = anchor + 4;
        *(W4 *)(off + sp) = *(W4 *)(src + 0xA);
        if (i == 0) {
            goto arm0;
        }
        if (i == 1) {
            goto arm1;
        }
        goto name_arm;
    arm0:
        *(unsigned short *)(anchor + 8) = *(unsigned short *)&D_800236F8;
        goto join;
    arm1:
        {
            register int t2 asm("$2");
            register int u3 asm("$3");
            t2 = *(short *)&D_800236FC;
            u3 = *(signed char *)&D_800236FE;
            *(unsigned short *)(anchor + 0x20) = t2;
            *(unsigned char *)(anchor + 0x22) = u3;
        }
        goto join;
    name_arm:
        memcpy_iso9660(rec8, src + 0x21, src[0x20]);
        rec8[src[0x20]] = 0;
    join:
        if (D_800C7CF0 >= 2) {
            printf(D_80023700, D_80147884[off], D_80147885[off],
                   D_80147886[off], *(int *)(D_80147888 + off), rec8);
        }
        rec += 0x18;
        rec8 += 0x18;
        off += 0x18;
        src += src[0];
        i++;
        if (i >= 0x40) {
            break;
        }
        if (src >= D_80149C84) {
            break;
        }
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

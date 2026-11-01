/* cc-post: keep-epilogue
 * cc-post: remnant-ori1 $L8 $L10 absorb
 *
 * The func_80077678 row (mainmenu_jp, 0x80077678..0x80077824, extent
 * 0x1ac) plus its continuation row func_80084924 (0x80077824..0x80077968,
 * extent 0x148) - CD_newmedia: the LIBCD ISO9660 family's PVD reader +
 * root-directory indexer, landed as real C (runbook phase F step 6, the
 * func_80084924 parent-row split's fifth unit). ONE retail function
 * spanning BOTH yaml rows (the loop body 0x80077824..0x80077914 and the
 * shared exit/epilogue live in the continuation row; the back-edge bnez
 * 0x800778E0 jumps from the continuation row back into this row's loop
 * head .L800777D4). Offline decode cron-20261101-0621; identity from the
 * format strings (D_800235DC/610/640/664/684/698, "sarching dir.." [sic]
 * is retail's own typo).
 *
 * FLOW: stage the ISO9660 PVD (sector 0x10) through func_80077CD4 into
 * the 0x800-B buffer D_80149484; the first call's return value is REUSED
 * as the second call's expected value (gcc keeps it in $s1 and the second
 * gate compares against it, not against a literal); strncmp(&buf[1],
 * D_80023608 ("CD001"), 5) != 0 -> "Disc format error"; the root-dir LBA
 * is read MISALIGNED out of D_80149510 (lwl 3/lwr 0) into a stack-homed
 * int (swl/swr + lw reloads at every use); stage it; "sarching dir.."
 * (gate >= 2); then the repacked-entry loop over the same buffer:
 *   len = src[0] (0 -> done); off = count * 0x2C;
 *   *(int*)(D_80147E8C + off) = *(int*)(src + 2)  (misaligned both sides);
 *   name = D_80147E90 + off;  ord = count + 1;
 *   table[+0] = ord (at-split), table[+4] = src[6] (at-split);
 *   memcpy_iso9660(name, src + 8, len); name[len] = 0;
 *   src += len + (len & 1) + 8 (len re-read from the stream each time -
 *   gcc reloads src[0] three times);
 *   trace dump "\t%08x,%04x,%04x,%s\n" (gate >= 2; the three words load
 *   through the 4-insn at-split, the name pointer spills to 0x10(sp) as
 *   the 5th printf arg);
 *   count = ord; loop back while count < 0x80 && src < D_80149C84.
 * Tail: terminator id 0 at count*0x2C into D_80147E88 (at-split) when
 * count < 0x80; D_800C8024 = 0 (invalidates CD_cachefile's cache guard -
 * the two functions are a writer/consumer pair); "%d dir entries found"
 * (gate >= 2); return 1, failures return 0.
 *
 * Source-shape laws banked this row:
 *  - THE MISALIGNED-ACCESS MECHANISM (the CD_cachefile park's open law,
 *    closed here): the PSX cc1 emits lwl/lwr + swl/swr ONLY for 4-byte
 *    STRUCT COPIES of a char[4]-typed aggregate - plain int derefs
 *    compile ALIGNED (probe: *(int*)&char_array and *(int*)(charptr+2)
 *    both emit lw/sw, memcpy(,4) is NOT inlined). So the root-dir LBA
 *    read is `W4 lba_w; lba_w = *(W4 *)D_80149510;` (lwl/lwr into v0,
 *    swl/swr into the frame home at 0x18(sp), every use an lw reload)
 *    and the table's stream-word copy is `*(W4 *)(off + e8c) =
 *    *(W4 *)(src + 2);` (lwl 5/lwr 2 source, swl 3/swr 0 destination
 *    through the $s4 cursor).
 *  - the E8C store and the name cursor go through PROLOGUE-MATERIALIZED
 *    INT cursors (e8c = (int)&D_80147E8C -> $s4, e90 = e8c + 4 -> $s5,
 *    the +4 derivation literal addiu) - INT, not pointer: gcc 2.6.3
 *    commutes pointer+index sums to pointer-first, int+int sums keep
 *    off-first (retail's addu $2,$16,$20 form); the E84/E88 stores, the
 *    three trace-dump word loads and the terminator store re-materialize
 *    the SYMBOL per access through $at - the aspsx < 2.30 4-insn
 *    at-split, so the unit rides `unit:func_80077678 --addiu-at on` in
 *    tools/maspsx_flags.txt (the family law from func_8007796C).
 *  - the loop is `while (1)` with the two breaks at the body end
 *    (count first, bound second) - the do-while form rotates the len
 *    test into the back-edge, the while(count<0x80) form deletes the
 *    entry guard; retail keeps BOTH a materialized entry guard and a
 *    clean back-edge, which NO source shape produces (11 banked shapes
 *    x pinned flags + -funroll-loops + -O3 for CD_cachefile, plus
 *    do-while/while(1)/while(A&&B)/for/-O1 here) - so the entry probe
 *    (ori $2,1 / beqz $2,$L10 / delay: count = 0) is RE-INSERTED by
 *    cc_post rule 10, marker-gated as `cc-post: remnant-ori1 $L8 $L10
 *    absorb` (dead code: $2 = 1, beqz never fires; the delay-slot init
 *    executes unconditionally either way; anchor mismatch = loud build
 *    failure). The probe is the CD_cachefile park's remnant - the rule
 *    back-ports to that row when it lands.
 *  - the advance reads src[0] ONCE into locals ((adv & 1) + 8 hoisted
 *    through its own int or gcc reassociates); the other two len uses
 *    re-read src[0] inline (gcc reloads: the memcpy len arg, name[len]);
 *  - the multiply fold lands in $s0 (the buffer pointer's register - buf
 *    is dead after src = buf), off is ONE explicit int local;
 *  - the entry table base D_80147E84: +0 u32 ordinal (1-based), +4 u32 id
 *    (src[6], 0-terminated by the tail store), +8 u32 (stream +2), +0xC
 *    char name[0x20] - func_8007796C walks id@+4/name@+0xC;
 *  - retail keeps addiu-sp before jr-ra (keep-epilogue, the family class).
 * Auto name kept for the continuation row (func_80084924 = 0x80077824 in
 * the symbols DB turns inert like the AC04 tail class); the sdk lane owns
 * the renames.
 */

extern unsigned char D_80149484[];   /* 0x800-B staging buffer */
extern unsigned char D_80149C84[];   /* buffer bound */
extern unsigned char D_80149510[];   /* root-dir LBA word, misaligned */
extern unsigned char D_80147E84[];   /* entry table: +0 ordinal */
extern unsigned char D_80147E88[];   /* entry table: +4 id */
extern unsigned char D_80147E8C[];   /* entry table: +8 stream word */
extern unsigned char D_80147E90[];   /* entry table: +0xC name */
extern int D_800C7CF0;               /* trace level */
extern int D_800C8024;               /* CD_cachefile's cache guard */
extern char D_800235DC[];
extern char D_80023608[];
extern char D_80023610[];
extern char D_80023640[];
extern char D_80023664[];
extern char D_80023684[];
extern char D_80023698[];
extern int func_80077CD4();
extern void memcpy_iso9660();
extern int printf();
extern int strncmp();

typedef struct {
    unsigned char b[4];
} W4;

int func_80077678(void)
{
    unsigned char *buf;
    unsigned char *src;
    int e8c;
    int e90;
    char *name;
    W4 lba_w;
    int off;
    int count;
    int ord;
    int id;
    int adv;
    int adv2;
    int ret;

    buf = D_80149484;
    ret = func_80077CD4(1, 0x10, buf);
    if (ret != 1) {
        if (D_800C7CF0 > 0) {
            printf(D_800235DC);
        }
        return 0;
    }
    if (strncmp(buf + 1, D_80023608, 5) != 0) {
        if (D_800C7CF0 > 0) {
            printf(D_80023610);
        }
        return 0;
    }
    lba_w = *(W4 *)D_80149510;
    if (func_80077CD4(1, *(int *)&lba_w, buf) != ret) {
        if (D_800C7CF0 > 0) {
            printf(D_80023640, *(int *)&lba_w);
        }
        return 0;
    }
    if (D_800C7CF0 >= 2) {
        printf(D_80023664);
    }
    src = buf;
    count = 0;
    e8c = (int)D_80147E8C;
    e90 = e8c + 4;
    while (1) {
        if (src[0] == 0) {
            break;
        }
        off = count * 0x2C;
        *(W4 *)(off + e8c) = *(W4 *)(src + 2);
        name = (char *)(off + e90);
        id = src[6];
        ord = count + 1;
        *(int *)(D_80147E84 + off) = ord;
        *(int *)(D_80147E88 + off) = id;
        memcpy_iso9660(name, src + 8, src[0]);
        name[src[0]] = 0;
        adv = src[0];
        adv2 = (adv & 1) + 8;
        src += adv + adv2;
        if (D_800C7CF0 >= 2) {
            printf(D_80023684,
                   *(int *)(D_80147E8C + off),
                   *(int *)(D_80147E84 + off),
                   *(int *)(D_80147E88 + off),
                   name);
        }
        count = ord;
        if (count >= 0x80) {
            break;
        }
        if (src >= D_80149C84) {
            break;
        }
    }
    if (count < 0x80) {
        *(int *)(D_80147E88 + count * 0x2C) = 0;
    }
    D_800C8024 = 0;
    if (D_800C7CF0 >= 2) {
        printf(D_80023698, count);
    }
    return 1;
}

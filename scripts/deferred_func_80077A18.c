/* cc-post: keep-epilogue
 *
 * mainmenu_jp func_80077A18 row UNIT 3 - CD_cachefile: the raw-ISO9660
 * directory-record parser into the 0x40-entry cache (listing
 * 0x80077A18..0x80077CD0, 0x2bc extent, 0x40 frame, ra+s0..s6); offline
 * decode cron-20261101-0621, oracle DOWN (both links 404 at ~42.7h);
 * law-corrected + compile-diffed offline cron-202611012058 (lm_probe_diff
 * vs the committed listing - the baselines on disk are the rolled-back
 * woven-era set, so judge_unit verdicts are unavailable; the listing's
 * hex encodings are the ground truth the probe diffs against).
 *
 * IDENTITY (this window's format-string reads, data_80020000.data.s):
 *   D_800236BC "CD_cachefile: dir not found\n"    - staged-load failure
 *   D_800236DC "CD_cachefile: searching...\n"     - entry
 *   D_80023700 "\t(%02x:%02x:%02x) %8d %s\n"      - per-record dump
 *   D_8002371C "CD_cachefile: %d files found\n"   - exit
 * and the arm constants D_800236F8/FC/FE are the C strings "." and "..":
 * slots 0/1 of the cache are the ISO9660 self/parent entries - they are
 * SYNTHESIZED from the constants, never copied from the stream.
 *
 * STREAM FORMAT (the staged buffer D_80149484..D_80149C84, 0x800 B) =
 * RAW ISO9660 directory records:
 *   +0x00  u8  record length (0 = terminator; the cursor advances by it)
 *   +0x02  u32 extent LBA (misaligned, lwl 5/lwr 2)  -> func_7502C arg
 *   +0x0A  u32 data size (misaligned, lwl 0xD/lwr 0xA) -> rec +4
 *   +0x20  u8  name length
 *   +0x21  char name[name_len] -> memcpy_iso9660 into rec +8, NUL at +8+len
 * (extent@+2 and size@+0xA are the ISO9660 record's own fields; the
 * "%8d" in the dump prints the SIZE.)
 *
 * CACHE TABLE (D_80147884, 0x40 records x 0x18 stride):
 *   +0..+2  three bytes (the dump's %02x x3; written by func_8007502C)
 *   +4      u32 size (from stream +0xA)
 *   +8      name area - "." at slot 0, ".." at slot 1, copies from slot 2
 * (the dump's %s arg = rec + 8; s3/s4/s1 in the asm are three forms of
 * the same index: rec+8 cursor, rec cursor, i*0x18 byte index.)
 *
 * FLOW: id guard on D_800C8024 (== a0 -> return 1); staged load via
 * func_80077CD4(1, *(u32*)(&D_80147E60 + a0*0x2C), &D_80149484); != 1 ->
 * "dir not found" (gate D_800C7CF0 > 0) and return -1; "searching..."
 * (gate >= 2); the parse loop lowers from the "ori 1; beqz never-taken"
 * idiom (gcc's do-while materialization): break on len == 0, break on
 * i >= 0x40, continue only while src < &D_80149C84; arms dispatch on the
 * RECORD INDEX i (i == 0 -> ".", i == 1 -> "..", else the name copy) and
 * gcc folds the i==0/i==1 arms' store addresses to s5+8 / s5+0x20 (the
 * induction-variable materialization); per-record dump gate >= 2 with
 * args (rec[0], rec[1], rec[2], size, rec+8); tail: D_800C8024 = a0;
 * if (i < 0x40) *(u8*)(&D_8014788C + i*0x18) = 0 (the next slot's first
 * name byte zeroed); "%d files found" (gate >= 2); return 1.
 *
 * NOTE: the func_8007502C call sits BEFORE the arms, so slots 0/1 also
 * receive the extent LBA - the synthesized entries are otherwise
 * constants-only.
 *
 * LAWS APPLIED AT THE SOURCE LEVEL (from the closed CD_cachefile park,
 * witnessed by the func_80077678 landing):
 *  - W4 STRUCT-COPY MECHANISM: the extent read homes through a W4 local
 *    (lwl 5/lwr 2 load, swl 0x1B/swr 0x18 frame home, lw reload per use -
 *    the lba_w shape) and the size copy is a direct W4-to-W4 assignment
 *    (lwl 0xD/lwr 0xA source, swl 3/swr 0 destination). Plain int derefs
 *    compile ALIGNED and are WRONG here.
 *  - NO len LOCAL: the head reads src[0] for the == 0 test and the tail
 *    re-reads src[0] for the advance (src += src[0]); a len local would
 *    survive the calls in a callee-saved reg and kill the re-read.
 *  - rec8 derives from rec (rec8 = rec + 8), NOT from &D_8014788C - the
 *    two symbols share %hi, retail materializes the base ONCE (lui s5 +
 *    addiu s5 + addiu s3,s5,8); two symbol operands would emit two
 *    lui/addiu pairs.
 *  - the loop keeps BOTH a materialized entry guard and a clean back-edge
 *    in retail (.L80077AE4: ori $2,1 / beqz $2,.L80077C50 / nop) - no
 *    source shape produces that pair, cc_post rule 10 re-inserts it;
 *    MARKER PENDING the first compile's label numbering (the 77678 row
 *    rode `remnant-ori1 $L8 $L10 absorb`; this row's delay slot is a
 *    plain nop, so the expected variant is `nop`).
 *  - the unit expects `--addiu-at on` (the family law: the four trace-dump
 *    loads re-materialize the D_8014788x symbols per access through $at -
 *    the aspsx < 2.30 4-insn at-split; same class as func_8007796C /
 *    func_80077678).
 *
 * OFFLINE LADDER (cron-202611012058, lm_probe_diff vs the committed
 * listing, MASPSX_UNIT_FLAGS="--addiu-at on" - the flag is CONFIRMED
 * REQUIRED: without it the D_80147E60 table read folds to the 3-insn
 * aspsx>=2.30 form where retail has the 4-insn at-split; the unit flag
 * entry `unit:func_80077A18 --addiu-at on` goes into tools/maspsx_flags.txt
 * AT LANDING together with the yaml flip):
 *  - VERIFIED MATCHING (the web willing): prologue shape (D_800C8024
 *    load before the frame setup, id -> s6, s0..s6 saved, frame 0x40,
 *    the guard beq's delay slot carries the s0 store); the failure path
 *    (gate > 0, printf, j + addiu v0,-1 in the delay); the searching
 *    gate with a zero-init in the branch delay; the 0x2C descriptor
 *    read (the sll/addu/subu/sll multiply chain + the 4-insn at-split);
 *    the extent W4 home (lwl 5/lwr 2 -> swl 0x1B/swr 0x18(sp) -> lw
 *    reload as the call arg); the dump's four per-symbol remats
 *    (encoding-identical: D_80147884/85/86/88 + the off giv each).
 *  - OPEN - THE REGISTER WEB (the ladder's remaining work): retail's
 *    size store recomputes (s5+4)+s1 fresh per iteration (addiu s5,4;
 *    addu s1,v0; swl 3/swr 0) while gcc prefers to strength-reduce
 *    (D_80147884+4+off) into an ADDRESS giv (seed base+4, step 0x18) -
 *    two extra registers, frame 0x48 + s7. v7 (no rec local; the call
 *    arg IS the expression D_80147884 + off) blocked the giv via the
 *    rec8-derived base chain and hit the exact retail store form, but
 *    lost the s4 walker (retail passes a walking-pointer reg seeded
 *    s5-copy; the expr form recomputes base+off per call). v8 (rec
 *    walker restored) re-created the giv. Also inverted: gcc puts the
 *    off=0 init in the searching-gate delay slot and i=0 at the loop
 *    prehead regardless of C order - retail has i=0 in the delay and
 *    off=0 at the prehead. NEXT: init/decl-order experiments, the
 *    two-giv trace (base derived through a walking pointer without the
 *    semantic double-advance), or the arms/store base as a re-derived
 *    symbol form; the tail-NUL and terminator shapes are unverified
 *    past the web (they follow the dump in the listing).
 *  - the remnant marker stays PENDING the first clean compile's label
 *    numbering; this row's delay slot is a plain nop, so the expected
 *    variant is `cc-post: remnant-ori1 <join> <exit> nop` (77678 rode
 *    absorb - its delay carried count = 0).
 *
 * STAGING: yaml row 672 asm -> c + src/func_80077A18.c + judge live +
 * verify 8/8 + ratchets, at the next witnessed window; the
 * memcpy_iso9660 interior rename composes here (7059420f, curated DB
 * per-target sections feed the solo mini-link - 92e12a8a).
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
    unsigned char *rec;
    unsigned char *rec8;
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
    rec = D_80147884;
    rec8 = rec + 8;
    off = 0;
    i = 0;
    while (1) {
        if (src[0] == 0) {
            break;
        }
        ext_w = *(W4 *)(src + 2);
        func_8007502C(*(int *)&ext_w, rec);
        *(W4 *)(D_80147884 + 4 + off) = *(W4 *)(src + 0xA);
        if (i == 0) {
            t = *(unsigned short *)&D_800236F8;  /* "." */
            *(unsigned short *)(D_80147884 + 8) = t;
        } else if (i == 1) {
            t = *(short *)&D_800236FC;  /* ".." */
            u = *(signed char *)&D_800236FE;
            *(unsigned short *)(D_80147884 + 0x20) = t;
            *(unsigned char *)(D_80147884 + 0x22) = u;
        } else {
            memcpy_iso9660(rec8, src + 0x21, src[0x20]);
            rec8[src[0x20]] = 0;
        }
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

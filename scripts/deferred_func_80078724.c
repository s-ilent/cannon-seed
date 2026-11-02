/* cc-post: sdk-aspsx
 * cc-post: cc1-O1
 * cc-post: prologue-param-first
 * cc-post: addiu-imm
 * cc-post: v0-sink
 * cc-post: addr-pin-late
 *
 * Real-decompiled-C game function #23 (draft) - the func_80078724 row
 * (mainmenu_eu, 0x80078724..0x80078948, extent 0x224) lands as the psyq
 * libcd TOC member's .text+0x24 piece (CdGetToc2), identity PROVEN by the
 * sdk_members.py unique TOC placement + sig-db agrees (pinned member row
 * CdGetToc2 = 0x80078724 in config/symbols.curated.txt; mainmenu_jp's
 * twin rows 0x80077da8/0x80077dcc carry the same member).
 *
 * THE -O1 FINDING (this window's toolchain bank): this unit's retail code
 * is an -O1 compile - the loop-carried byte-walk pointer strength-reduces
 * to ONE address register at -O1 but splits into the {min,max}
 * two-register reduced basis at -O2 (probes scripts/iv_probe1.c v1-v3:
 * param-based stores fold at either level; the loop-carried pointer is
 * the discriminator), and the store sequences keep -O1's un-scheduled
 * program order (the -O2 scheduler moves the independent zero store into
 * the FIRST load's delay; retail keeps it in the SECOND's). Delay-slot
 * filling still runs at -O1 (gcc's final pass) and explains every filled
 * slot in the listing. The psyq sdk library bodies carry their own build's
 * flag set; the wrapper #22 (func_80078700) is insensitive (9 insns, no
 * loop) and stays -O2-judged. cc.sh consumes the `cc-post: cc1-O1` marker.
 *
 * Decode (the listing is the only authority): CdGetToc2(1, toc) - the
 * count argument is vestigial (the prologue zeroes a0 before the first
 * call; the toc pointer arrives as the SECOND argument, addu s4,a1,zero,
 * and is the store base throughout). Flow: param[0] = 1 (the dead-ish
 * first store - the byte is re-written 0 before the second command and
 * BCD per track in the loop; the address escapes to the callee so the
 * store survives), handle = func_800751F8(0) (the lock pair's enter half,
 * released with the saved handle at every exit); func_800754C4(0x13, 0,
 * result) = the track-number command - failure prints D_80023754 when
 * D_800C8518 != 0 and returns 0. The result bytes [1]/[2] are the first/
 * last track numbers in BCD: each decodes (b>>4)*10 + (b&0xF) - the
 * pinned locals b1/b2 give the one-load-two-uses shape (srl + andi off
 * the same register); last's final addu rides the verbose-guard bnez
 * delay. D_800C8518 >= 2 prints D_80023728 with (track, last).
 * func_800754C4(0x14, param, result) with param[0] = 0 fills toc[0..2]
 * = {result[1], result[2], 0} (the disc-start entry; each store re-loads
 * its byte - no cross-statement CSE at -O1). The per-track loop runs
 * track = first..last: param[0] = (track/10)*16 + track%10 (the BCD
 * encode, the 0x66666667 magic division), the command re-issued per
 * track (n++ counts attempts BEFORE the failure gate - it rides the
 * beqz delay, matching retail), the entry stores {result[1], b2, 0}
 * with track++ riding the result[2] load's delay, t += 4 riding the
 * back-edge beqz delay; failure takes the shared fail tail. Return =
 * n - 1 (the track count; toc[0] is the extra disc-start entry). The
 * verbose tail (D_800C8518 >= 2 and i >= 0) dumps the entries two bytes
 * at a time through D_80023738 with t += 4 filling the second load's
 * delay and j++ the printf call's. Exit: func_800751F8(handle), return
 * the count (fail path returns 0 after the release).
 */

extern long func_800751F8();
extern int func_800754C4();
extern int printf();
extern int D_800C8518;
extern char D_80023728[];
extern char D_80023738[];
extern char D_80023754[];

long func_80078724(long count, unsigned char *toc)
{
    unsigned char param[8];  /* 0x10(sp) - the command param byte lives at [0] */
    unsigned char result[8]; /* 0x18(sp) - the command result bytes at [1],[2] */
    unsigned char *t;        /* the toc walk pointer */
    unsigned char *rp;       /* the result buffer, pinned for the two early calls */
    unsigned char b1;        /* the first/last BCD bytes, pinned for the decode */
    unsigned char b2;
    long track;              /* first track, then the loop counter */
    long last;               /* last track */
    long n;                  /* the entry counter */
    long handle;             /* the func_800751F8 lock handle */
    long i;                  /* the tail limit, and the return value */
    long j;                  /* the tail print counter */
    long ret;

    param[0] = 1;
    handle = func_800751F8(0);
    rp = result;
    if (func_800754C4(0x13, 0, rp) == 0)
        goto fail;
    b1 = result[1];
    b2 = result[2];
    track = (b1 >> 4) * 10 + (b1 & 0xF);
    last = (b2 >> 4) * 10 + (b2 & 0xF);
    if (D_800C8518 >= 2)
        printf(D_80023728, track, last);
    param[0] = 0;
    if (func_800754C4(0x14, param, rp) == 0)
        goto fail;
    toc[0] = result[1];
    b2 = result[2];
    toc[2] = 0;
    toc[1] = b2;
    n = 1;
    if (last >= track) {
        t = toc + 4;
        do {
            param[0] = (track / 10) * 16 + track % 10;
            ret = func_800754C4(0x14, param, result);
            n++;
            if (ret == 0)
                goto fail;
            t[0] = result[1];
            b2 = result[2];
            track++;
            t[2] = 0;
            t[1] = b2;
            t += 4;
        } while (last >= track);
    }
    i = n - 1;
    if (D_800C8518 >= 2) {
        if (i >= 0) {
            j = 0;
            t = toc;
            while (i >= j) {
                printf(D_80023738, t[0], t[1]);
                t += 4;
                j++;
            }
        }
    }
    func_800751F8(handle);
    return i;
fail:
    if (D_800C8518 != 0)
        printf(D_80023754);
    func_800751F8(handle);
    return 0;
}

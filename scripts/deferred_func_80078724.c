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
 * FLAG-SET REFINEMENT (cron-202611030028, scripts/probe787_flags.sh): the
 * decode block's allocation is NOT plain -O1 — it is -O2 -fno-strength-
 * reduce. Measured on the unit: -O1 = 63/137 (pins v1/a0, hi fused into the
 * destination s-regs, x10 chains in v0, no delay-ride); -O2 plain = 132/137
 * SIZE +12 (the loop's {min,max} strength-reduced basis); -O2 -fno-strength-
 * reduce = 88/136 SIZE -4 with the decode block's retail shape REPRODUCED:
 * pins a0/a1 (the freed argument registers), hi1 in v1 / x10 in v0, hi2 in
 * v0 / x10 in v1 (the v1/v0 role swap), lo into the pins, finals addu
 * s-dest,v-chain,a-pin. The prologue's rule-11 hoist (param copy + consts
 * above the ra save) is also -O2-native (sched1), which is why rule 11 must
 * come OFF at -O2 (its anchor is -O1-shaped, loud-fail otherwise). The loop
 * discriminator the 1358 window measured is the strength-reduction PASS, not
 * the -O level; the loop call block's hoisted arg setup (cmd/param/result
 * above the division) is likewise -O2 sched1 work. RESIDUAL MAP at -O2-fnsr (cron-202611021904, full word-diff; the rule-13
 * misfire is FIXED by the cc1-O1 scoping in cc.sh, 88 -> 87 words): the
 * 87-word diff is FOUR roots plus their branch-offset consequences:
 *   root 1 - the rp/track/t s-reg pair swap: built {rp/t=s0, track=s1},
 *     retail {rp/t=s1, track=s0}; last=s3/n=s2/handle=s5/toc=s4 agree.
 *     DECLARATION ORDER is provably out at -O2-fnsr too (track/last
 *     declared before rp: DIFF 87 unchanged) - no source-shape lever.
 *   root 2 - the lo2 andi destination: built reuses the dead b1 pin a0
 *     and pins the loop's b2 load in a1; retail overwrites the b2 pin a1
 *     itself (early decode) and loads the loop's b2 into v0 with no pin.
 *   root 3 - sched1 placements: built hoists the loop-gate slt INTO the
 *     toc-store block and the n++/track++ above the division cluster;
 *     retail keeps load/store program order (stores, slt, bnez with the
 *     n=1 ori riding its delay; built's ori is a real insn above).
 *   root 4 - RETRACTED (cron-202611021859): the offset-shifted word-diff
 *     misread retail's 0x8007891C move v0,zero (00001021, the fail
 *     path's return-0 materialization) as a nop - the fail tails MATCH.
 *     The SIZE -1 word lives mid-function in the sched1/nop-fill
 *     placements (built folds the n=1 ori into slot positions where
 *     retail keeps a real nop + a real insn).
 *   rule 13 (v0-sink) MISFIRED at -O2-fnsr: gcc's own filler already
 *     sinks the handle (move s5,v0 in the first 754C4 jal's delay,
 *     byte-retail in the raw cc1 stream); the rule then pulled the gate
 *     branch INTO the jal slot (branches are not in its read-set). Now
 *     scoped to cc1-O1 units in cc.sh. Rules 12/14 stay unscoped - the
 *     ori immediate forms and the addr-pin arg positions MATCH retail at
 *     -O2-fnsr. SOURCE-SHAPE LEVERS NOW EXHAUSTED (cron-202611021859):
 *     E2 split-statement decodes (track=/track+=, last=/last+=) 87 -> 92;
 *     E3 operand-order swap on the second decode 87 -> 95 - both dead,
 *     on top of the E1 declaration-order no-op. The structural
 *     alignment (scripts/align787.py, difflib on normalized streams)
 *     confirms the loop/tail SHAPES match - the deltas are exactly the
 *     register-choice and sched1-placement roots. Next window: a narrow
 *     cc_post rule class (s-reg pair swap over the decode/loop block,
 *     scoped + anchored) or gcc 2.6.3 allocator modeling, then land +
 *     judge + verify.
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

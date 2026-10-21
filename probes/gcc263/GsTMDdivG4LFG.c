/* GsTMDdivG4LFG offline probe (window cron-202610211858).
 *
 * The sibling of the queued GsTMDdivTG4LFG 0x304 row: the non-textured
 * divide-G4 member, 0x2C0, FOUR standalone asm sdk rows (mainmenu_jp
 * file 0x4B838 true 0x8006B038, mainmenu_eu 0x4B244, g3_jp 0x37324,
 * g3org_eu 0x341BC) plus TWO data-row-hosted copies (g3_eu inside
 * data_8005E494 at +0x244 of the 0x504 row at file 0x36B24, g3org_jp
 * inside data_8005B8FC at +0x244 of the 0x284 row at file 0x3457C) -
 * the wave is 6 targets, 169 of 176 words byte-identical (the 7
 * differing slots are exactly the relocations: 5 jal + 1 hi/lo pair).
 *
 * KEY QUESTION this probe answers: does OUR cc1 slide the a2 param
 * home out of the entry block the way it does for the T sibling
 * (the 200-of-193 entry-cascade wall)? Retail batches BOTH homes at
 * entry here too (addu s7,a1 / addu fp,a2 in the first four slots).
 * The G DAG differs: pk is a stack parm loaded into s6 via lw at
 * entry, nt homes to fp (not s6), the loop counter is a spilled
 * local (0x60(sp)) not a register, and the beqz delay slot carries
 * the useful p78 spill - a different fill candidate pool.
 *
 * Body map (mainmenu_jp render, true VA 0x8006B038):
 *   s6 = pk (lw 0xC4(sp), the 8th arg), s7 = vt, fp = nt
 *   s5..s2 = v1o..v4o = pk+0x18/0x30/0x48/0x60, s0 = tmd+3,
 *   s1 = tmd+4 (the color pointer, recomputed per iteration),
 *   spills: 0x50 tmd, 0x58 ret, 0x60 counter, 0x68 p78, 0x70 &u44;
 *   locals: 0x40 buf40 (dv's otz out, read as ushort), 0x44 u44
 *   (RotTransPers arg-4 scratch, never read), 0x48 p4C (RTP arg-3
 *   out, the dpq color index).
 *   dv = RotAverageNclipColorDpq3_1 (landed; called by name), args
 *   8-10 are v*o+0x10 here (the T sibling passes v*o+4), arg 14 is
 *   &buf40 (T: &buf40[1]) - different actuals, same 15-arg shape.
 *   sz = func_800667B8 (the 0x18 SZ-fifo reader, ReadSZfifo4 slot),
 *   pk member = func_8006F250, ft table = the D_ hi/lo pair.
 *   The T sibling's UV stores (pk+0xC/0xE) and the four v*o+8 record
 *   stores are ABSENT here - the non-textured primitive carries no
 *   texture words; the color comes from the record itself (tmd+4).
 *   The loop advances the record base by 0x18 (the 0x18-stride
 *   primitive) and s0 rides tmd+3; the counter is the spilled local.
 *
 * SPELLING LAW (this window): our cc1's loop pass runs combine_givs
 * (stock gcc 2.6.3 loop.c), which folds EVERY const-offset DEST_ADDR
 * giv of a biv into the LAST-RECORDED one (the list is prepend-ordered,
 * so the host = the LAST field read in insn order) and the reduction
 * then creates the re-based loop register = biv + host_add. Retail's
 * compiler never re-bases (both dividers' renders read the raw biv
 * form). The dodge is to spell the field reads DIRECTLY off the record
 * base (tmd+0xA..tmd+0x16, no s0 = tmd+3 intermediate) so the FLAG BYTE
 * read (tmd+3, the last statement) becomes the host giv: the reduced
 * register = tmd+3 - exactly retail's s0 - every read lands at retail's
 * exact positive offset (5..0x13), and the biv (tmd itself, now used
 * only for the per-iteration color tmd+4) loses its register and spills
 * to 0x50(sp) as the raw a0 - retail's exact entry spill. The T
 * sibling's committed probe carries the SAME re-base delta (its reads
 * ride tmd+0xC vs retail's tmd+0x10); its K=3 spelling must be fixed
 * the same way before landing.
 */

/*
 * STATUS (window cron-202610211858, five probe iterations): the
 * combine_givs dodge WORKS - the probe's field reads now ride retail's
 * exact base (lhu v0,7(s0) with the s0 = tmd+3 register; slot 32 word
 * 96020007 = retail's word exactly) and the param homes are retail's
 * (addu s7,a1 / addu fp,a2 at slots 4/6). Word count is EQUAL (176 =
 * 176) for the first time. Remaining deltas, all in the allocation
 * order, ~57 words:
 *   1. the color temp (131, 6 refs / LL 33) interleaves into the v*o
 *      block: probe [giv=s0, v4o=s1, v3o=s2, color=s3, v2o=s4, v1o=s5,
 *      pk=s6, vt=s7, nt=fp] vs retail [giv=s0, color=s1, v4o=s2, v3o=s3,
 *      v2o=s4, v1o=s5, pk=s6, vt=s7, nt=fp] - the color must allocate
 *      BEFORE v4o (its pri 15.5/33 = 0.469 vs v4o's 43/96 = 0.448 says
 *      it should - the observed qsort order disagrees; lever = shorten
 *      the color's life or find the exact LL/n_refs the sort saw).
 *   2. the frame: probe 0xA0 vs retail 0xA8 - retail's local area has a
 *      4-byte hole at 0x4C (between p4C and the tmd spill) and its save
 *      area starts at 0x80 (ours 0x78); the pk lw offset (0xBC vs 0xC4)
 *      follows the frame. Candidate: retail's dv or otz is a spilled
 *      local where ours rides regs.
 *   3. the counter/p78 spill-slot order fixed by declaring the counter
 *      before p78 (slot 16 now matches: sw zero,0x60).
 * The v2o/v1o/pk/vt/nt assignments and every loop-body read word MATCH.
 * Next window: steer the color's allocation position (decl-order and
 * life-length levers), fix the frame hole, then the wave is 6 targets
 * (4 standalone flips + 2 data-row splits on the data_80066CF4 pattern)
 * with aliases _dv/_sz/_pk/_ft curated per target.
 * ALSO: the committed GsTMDdivTG4LFG probe carries the SAME re-base
 * delta (its reads ride the host = the last-recorded read, tmd+0xC vs
 * retail's tmd+0x10) - the "loop body matches modulo the entry cascade"
 * claim in its header is STALE; its fix is the same K=0 dodge (read the
 * fields via tmd directly; the T's last-recorded read is *(long *)s0 =
 * tmd+0x10 = exactly retail's base, so the T's re-base becomes
 * INVISIBLE with that spelling) - re-derive its wave after the G wave
 * lands.
 */

typedef struct { char b[8]; } GsTMDdivG4LFG_v8;

extern long RotTransPers(long *a0, long *a1, long *a2, long *a3);
extern void NormalColorDpq(long *a0, long *a1, long c, long *a3);
extern long GsTMDdivG4LFG_dv(long *, long *, long *, char *, char *,
                             char *, long *, long *, long *, long *,
                             long *, long *, long *, long *, long *);
extern void GsTMDdivG4LFG_sz(long *, long *, long *, long *);
extern long GsTMDdivG4LFG_pk(long, char *, long, long *);
extern unsigned char GsTMDdivG4LFG_ft[];

long GsTMDdivG4LFG(tmd, vt, nt, pkin, cnt, shift, otp, pk)
    unsigned char *tmd;
    char *vt;
    char *nt;
    long *pkin;
    unsigned long cnt;
    unsigned long shift;
    long *otp;
    char *pk;
{
    long ret = (long)pkin;
    long *v4o = (long *)(pk + 0x60);
    long *v3o = (long *)(pk + 0x48);
    long *v2o = (long *)(pk + 0x30);
    long *v1o = (long *)(pk + 0x18);
    unsigned long fp = 0;
    long *p78 = (long *)(pk + 0x78);
    long buf40;
    long u44;
    long p4C;
    unsigned long otz;
    unsigned long dv;

    *(long **)(pk + 0xF0) = v1o;
    *(long **)(pk + 0xF4) = v2o;
    *(long **)(pk + 0xF8) = v3o;
    *(long **)(pk + 0xFC) = v4o;

    if (cnt != 0) {
        do {
            *(GsTMDdivG4LFG_v8 *)v1o =
                *(GsTMDdivG4LFG_v8 *)(vt + *(unsigned short *)(tmd + 0xA) * 8);
            *(GsTMDdivG4LFG_v8 *)v2o =
                *(GsTMDdivG4LFG_v8 *)(vt + *(unsigned short *)(tmd + 0xE) * 8);
            *(GsTMDdivG4LFG_v8 *)v3o =
                *(GsTMDdivG4LFG_v8 *)(vt + *(unsigned short *)(tmd + 0x12) * 8);
            *(GsTMDdivG4LFG_v8 *)v4o =
                *(GsTMDdivG4LFG_v8 *)(vt + *(unsigned short *)(tmd + 0x16) * 8);

            if (GsTMDdivG4LFG_dv(v1o, v2o, v3o,
                                 nt + *(unsigned short *)(tmd + 8) * 8,
                                 nt + *(unsigned short *)(tmd + 0xC) * 8,
                                 nt + *(unsigned short *)(tmd + 0x10) * 8,
                                 (long *)((char *)tmd + 4),
                                 (long *)((char *)v1o + 0x10),
                                 (long *)((char *)v2o + 0x10),
                                 (long *)((char *)v3o + 0x10),
                                 (long *)((char *)v1o + 0xC),
                                 (long *)((char *)v2o + 0xC),
                                 (long *)((char *)v3o + 0xC),
                                 &buf40, &u44) > 0) {
                RotTransPers(v4o, (long *)((char *)v4o + 0x10), &p4C, &u44);
                GsTMDdivG4LFG_sz((long *)((char *)v1o + 0x14),
                                 (long *)((char *)v2o + 0x14),
                                 (long *)((char *)v3o + 0x14),
                                 (long *)((char *)v4o + 0x14));
                NormalColorDpq((long *)(nt + *(unsigned short *)(tmd + 0x14) * 8),
                               (long *)((char *)tmd + 4), p4C,
                               (long *)((char *)v4o + 0xC));
                otz = *(unsigned short *)&buf40;
                dv = (otz - otp[2]) >> shift;
                *(long *)(pk + 0x14) = (long)((dv << 2) + otp[1]);
                *(unsigned char *)(pk + 0x13) =
                    (unsigned char)((GsTMDdivG4LFG_ft[0] << 1) | tmd[3]);
                ret = GsTMDdivG4LFG_pk(ret, pk, 0, p78);
            }
            fp++;
            tmd += 0x18;
        } while (fp < cnt);
    }
    return ret;
}

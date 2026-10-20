/* GsTMDdivTG4LFG offline probe (window cron-20261020-1458; re-probed
 * cron-20261020-1613 after the align-1 struct-copy fix).
 *
 * STATUS: 200 of 193 words - the loop body now matches retail shape
 * slot-for-slot modulo the entry cascade, and the entry block is the
 * ONE remaining root cause. Three laws banked this window:
 *
 * 1. ALIGN-1 STRUCT COPY LAW: the four vertex copies are struct
 *    assignments of an alignment-1 type (char b[8] reproduces it; a
 *    4-short struct also emits the same shape). gcc then emits the
 *    retail lwl/lwr + swl/swr quad per copy. A 2xunsigned-long struct
 *    (align 4) or a (long long *) cast gets decomposed to plain
 *    lw/sw pairs - the cast does NOT lower the alignment trust.
 * 2. DECL-ORDER SPILL-SLOT LAW: retail spills p48 to 0x60($sp) and
 *    p40 to 0x68($sp) - p48 first - so the original declared p48
 *    BEFORE p40 (gcc 2.6.3 assigns local spill slots in declaration
 *    order; statement order does not move the slots).
 * 3. SINGLE-EARLY-HOME LAW: our cc1 emits exactly ONE of the two
 *    parameter homes (a1->s6, a2->s7) in the entry block top; the
 *    other defers to the loop-head branch delay slot. Which one is
 *    early follows the first source reference: no alias -> a1's home
 *    early (slot 2 = retail-exact 00a0b021) and a2's late; a2 aliased
 *    via a first-statement local copy (char *nt = nt_;) -> a2's home
 *    early (slot 2 = retail-exact 00c0b821, retail's slot-4 word) and
 *    a1's late. K&R declarations change nothing here. Retail has BOTH
 *    homes in the first four slots (save a1-home, save a2-home) BEFORE
 *    the s5 reload and the 0x3C808080 materialize - reproducing that
 *    batch is the remaining open item; everything downstream (the
 *    s5-vs-s1 packet-base register pick, the extra s0-init spill at
 *    0x70, the 7-word body surplus) follows from it. Next levers: an
 *    entry-block reference to BOTH params that costs zero retail
 *    instructions (CSE-eliminated shape), or finding the source
 *    construct that pins both assign_parms homes unshovable.
 *
 * Retail shape: mainmenu_jp file 0x4E894 (true 0x8006E094), extent 0x304,
 * five-word-relocation layer (4 jal + 1 hi/lo pair) across mainmenu_jp /
 * mainmenu_eu / g3org_jp / g3org_eu / g3_jp - all other 114 words
 * identical (relocation slots 0x1c8 0x1e4 0x1f8 0x214 0x24c 0x250
 * 0x2ac; g3_eu carries NO masked-identical copy - the wave is 5 rows).
 * One source serves all five rows via shared alias symbols.
 *
 * Callee aliases (curated per target):
 *   GsTMDdivTG4LFG_dv - the 0x100 divide-check member (sig-db
 *     RotAverageNclipColorDpq3_1 slot), 15 args (4 reg + 11 stack)
 *   GsTMDdivTG4LFG_sz - the 0x18 SZ-fifo reader (ReadSZfifo4 slot)
 *   GsTMDdivTG4LFG_pk - the packet-walk tail member
 *   GsTMDdivTG4LFG_ft - the flag-priority byte table (the D_ slot)
 * Landed callees called by name: RotTransPers, NormalColorDpq.
 */

typedef struct { char b[8]; } GsTMDdivTG4LFG_v8;

extern long RotTransPers(long *a0, long *a1, long *a2, long *a3);
extern void NormalColorDpq(long *a0, long *a1, long c, long *a3);
extern long GsTMDdivTG4LFG_dv(long *, long *, long *, char *, char *,
                              char *, long *, long *, long *, long *,
                              long *, long *, long *, long *, long *);
extern void GsTMDdivTG4LFG_sz(long *, long *, long *, long *);
extern long GsTMDdivTG4LFG_pk(long, char *, long, long *);
extern unsigned char GsTMDdivTG4LFG_ft[];

long GsTMDdivTG4LFG(tmd, vt, nt_, pkin, cnt, shift, otp, pk)
    unsigned char *tmd;
    char *vt;
    char *nt_;
    long *pkin;
    unsigned long cnt;
    unsigned long shift;
    long *otp;
    char *pk;
{
    char *nt = nt_;
    long ret = (long)pkin;
    long *v1o = (long *)(pk + 0x18);
    long *v2o = (long *)(pk + 0x30);
    long *v3o = (long *)(pk + 0x48);
    long *v4o = (long *)(pk + 0x60);
    long *p78 = (long *)(pk + 0x78);
    long buf40[2];
    long buf48;
    long p4C;
    long *p48;
    long *p40;
    unsigned char *s0;
    unsigned long fp;
    unsigned long otz;
    unsigned long dv;

    buf40[0] = 0x3C808080;
    *(long **)(pk + 0xF0) = v1o;
    *(long **)(pk + 0xF4) = v2o;
    *(long **)(pk + 0xF8) = v3o;
    *(long **)(pk + 0xFC) = v4o;

    if (cnt != 0) {
        p40 = buf40;
        p48 = &buf48;
        s0 = tmd + 0x10;
        fp = 0;
        do {
            *(GsTMDdivTG4LFG_v8 *)(pk + 0x18) =
                *(GsTMDdivTG4LFG_v8 *)(vt + *(unsigned short *)(s0 + 6) * 8);
            *(GsTMDdivTG4LFG_v8 *)(pk + 0x30) =
                *(GsTMDdivTG4LFG_v8 *)(vt + *(unsigned short *)(s0 + 0xA) * 8);
            *(GsTMDdivTG4LFG_v8 *)(pk + 0x48) =
                *(GsTMDdivTG4LFG_v8 *)(vt + *(unsigned short *)(s0 + 0xE) * 8);
            *(GsTMDdivTG4LFG_v8 *)(pk + 0x60) =
                *(GsTMDdivTG4LFG_v8 *)(vt + *(unsigned short *)(s0 + 0x12) * 8);

            if (GsTMDdivTG4LFG_dv(v1o, v2o, v3o,
                                  nt + *(unsigned short *)(s0 + 4) * 8,
                                  nt + *(unsigned short *)(s0 + 8) * 8,
                                  nt + *(unsigned short *)(s0 + 0xC) * 8,
                                  p40, v1o + 4, v2o + 4, v3o + 4,
                                  (long *)((char *)v1o + 0xC),
                                  (long *)((char *)v2o + 0xC),
                                  (long *)((char *)v3o + 0xC),
                                  (long *)&buf40[1], p48) > 0) {
                RotTransPers(v4o, v4o + 4, &p4C, p48);
                GsTMDdivTG4LFG_sz((long *)((char *)v1o + 0x14),
                                  (long *)((char *)v2o + 0x14),
                                  (long *)((char *)v3o + 0x14),
                                  (long *)((char *)v4o + 0x14));
                NormalColorDpq((long *)(nt + *(unsigned short *)(s0 + 0x10) * 8),
                               p40, p4C, (long *)((char *)v4o + 0xC));
                otz = *(unsigned short *)&buf40[1];
                dv = (otz - otp[2]) >> shift;
                *(long *)(pk + 0x14) = (long)((dv << 2) + otp[1]);
                *(unsigned char *)(pk + 0x13) =
                    (unsigned char)((GsTMDdivTG4LFG_ft[0] << 1)
                                    | s0[-0xD]);
                *(unsigned short *)(pk + 0xC) = *(unsigned short *)(s0 - 0xA);
                *(unsigned short *)(pk + 0xE) = *(unsigned short *)(s0 - 6);
                *(long *)((char *)v1o + 8) = *(long *)(s0 - 0xC);
                *(long *)((char *)v2o + 8) = *(long *)(s0 - 8);
                *(long *)((char *)v3o + 8) = *(long *)(s0 - 4);
                *(long *)((char *)v4o + 8) = *(long *)s0;
                ret = GsTMDdivTG4LFG_pk(ret, pk, 0, p78);
            }
            fp++;
            s0 += 0x24;
        } while (fp < cnt);
    }
    return ret;
}

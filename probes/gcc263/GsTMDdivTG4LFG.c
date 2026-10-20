/* GsTMDdivTG4LFG offline probe (window cron-20261020-1458).
 *
 * STATUS: 184 of 193 words shape-exact; the open item is the ENTRY
 * MOVE TIMING for a2 (nt): retail moves BOTH a1->s6 AND a2->s7 in the
 * first four slots (before the s5 reload and the 0x3C808080
 * materialize); the probe moves a1->s6 at entry (3/3 slots exact, frame
 * 0xA0 exact) but defers a2 into s7 until after the entry branch, which
 * shifts the whole allocation cascade (~9 slots). The batch entry move
 * suggests the original body references a2 before the first call in a
 * way the probe draft does not reproduce yet - next lever candidates:
 * K&R parameter declarations (the banked GsSetLightMode entry-copy
 * lever), an earlier normal-table reference in the p40/p48 setup
 * statement order, or a packet-struct-typed pk argument changing the
 * address-escape set. Word census: retail 193 (0x304 = 193 words
 * including the two-lwl/lwr vertex copies), probe 184.
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

typedef struct { unsigned long a, b; } GsTMDdivTG4LFG_v8;

extern long RotTransPers(long *a0, long *a1, long *a2, long *a3);
extern void NormalColorDpq(long *a0, long *a1, long c, long *a3);
extern long GsTMDdivTG4LFG_dv(long *, long *, long *, char *, char *,
                              char *, long *, long *, long *, long *,
                              long *, long *, long *, long *, long *);
extern void GsTMDdivTG4LFG_sz(long *, long *, long *, long *);
extern long GsTMDdivTG4LFG_pk(long, char *, long, long *);
extern unsigned char GsTMDdivTG4LFG_ft[];

long GsTMDdivTG4LFG(unsigned char *tmd, char *vt, char *nt, long *pkin,
                    unsigned long cnt, unsigned long shift, long *otp,
                    char *pk)
{
    long ret = (long)pkin;
    long *v1o = (long *)(pk + 0x18);
    long *v2o = (long *)(pk + 0x30);
    long *v3o = (long *)(pk + 0x48);
    long *v4o = (long *)(pk + 0x60);
    long *p78 = (long *)(pk + 0x78);
    long buf40[2];
    long buf48;
    long p4C;
    long *p40;
    long *p48;
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
            *(GsTMDdivTG4LFG_v8 *)v1o =
                *(GsTMDdivTG4LFG_v8 *)(vt + *(unsigned short *)(s0 + 6) * 8);
            *(GsTMDdivTG4LFG_v8 *)v2o =
                *(GsTMDdivTG4LFG_v8 *)(vt + *(unsigned short *)(s0 + 0xA) * 8);
            *(GsTMDdivTG4LFG_v8 *)v3o =
                *(GsTMDdivTG4LFG_v8 *)(vt + *(unsigned short *)(s0 + 0xE) * 8);
            *(GsTMDdivTG4LFG_v8 *)v4o =
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

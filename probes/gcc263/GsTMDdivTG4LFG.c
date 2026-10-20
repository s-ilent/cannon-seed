/* GsTMDdivTG4LFG offline probe (window cron-20261020-1458; re-probed
 * cron-20261020-1613 after the align-1 struct-copy fix; entry-cascade
 * variant sweep cron-202610201758; ROOT CAUSE FOUND cron-202610201843).
 *
 * ROOT CAUSE (window cron-202610201843, RTL-dump proof - this CORRECTS
 * law 5 below, whose "local-alloc/reload, not scheduling" claim was
 * WRONG): cc1 -da per-pass dumps show reload's output (.greg dump,
 * "Register dispositions" section) has BOTH parm homes as entry insns
 * in retail order - insn 4 a0->a0 (tmd stays, deleted), insn 6 s6<-a1,
 * insn 8 s7<-a2 - i.e. assign_parms emits both copies at entry and
 * reload keeps both there. The deferral is created by SCHED2 (the
 * post-reload scheduler) plus DBR (delay-slot fill):
 *  - gcc 2.6.3 sched.c traverses each block BACKWARD (pick order =
 *    reverse final order; proven by matching the -da .sched2 trace to
 *    the reversed final chain: picks 59, 8, 377, 374, 56, 53, 50, 47,
 *    39, 36, 33, 30, 27, 44, 24, 436..422, 420, 418, 370, 18, 434,
 *    369, 6, 424, 416).
 *  - both homes are IN-BLOCK SINKS (nothing in the entry block reads
 *    s6/s7 or a1/a2; their only anti-dep is save->home, which is a
 *    predecessor edge), so both are ready at T-2, right after the
 *    branch (T-1, priority 0x7fffff51; all other priorities collapsed
 *    to 1 - the latency-1 "no need to move" law in sched.c priority()).
 *  - at T-2 the scheduler swapped to 8 ("now 8 6") and placed it
 *    directly before the beqz; dbr then filled the LOAD-DELAY SLOT
 *    between the cnt reload (lw t0) and beqz t0 with it - a USEFUL
 *    fill. Retail has a LITERAL NOP there (0x8006E108, between lw t0
 *    and beqz): retail's fill pass found no useful candidate, i.e.
 *    retail's sched2 did NOT slide the a2-home to the branch. The
 *    fp-init (addu fp,zero,zero) fills retail's beqz slot NATURALLY
 *    (first insn of the cnt!=0 block, physically the delay slot).
 *  - the ONE open question: why stock sched.c's backward walk slides
 *    the sink-home while retail's compile did not (same DAG shape, so
 *    the difference is the Sony sched patch or a flag). The PSX cc1
 *    ships binaries-only (decompals/old-gcc r0.12); its sched.c diff
 *    is unread, and STOCK sched.c at /tmp/gcc263 (see mirror note)
 *    reproduces OUR behavior, so the patch must be read or inferred.
 *
 * MIRROR NOTE (replaces the "needs a mirror next window" item): stock
 * gcc-2.6.3 source is ONLY at
 *   https://gcc.gnu.org/pub/gcc/old-releases/gcc-2/gcc-2.6.3.tar.bz2
 * (.tar.gz form is gone from ftp.gnu.org and every mirror; old-releases
 * carries the .bz2). Download works from the sandbox. The -da recipe:
 *   mkdir -p build/probe && cd build/probe && \
 *   CC1FLAGS_EXTRA="-da" sh ../../tools/cc.sh -o x.o <probe.c>
 * dumps land in CWD as <input>.<pass> (.rtl/.jump/.cse/.loop/.cse2/
 * .flow/.combine/.sched/.lreg/.greg/.sched2/.jump2/.dbr); the .sched2
 * file carries the FULL backward-scheduler trace (ready lists, picks,
 * hazard swaps) plus final RTL.
 *
 * STATUS: 200 of 193 words - the loop body matches retail shape
 * modulo the entry cascade, and the entry block is the ONE remaining
 * root cause. The window cron-202610201758 sweep ran FOUR more entry
 * variants against the same retail reference (all 200/193, all with
 * exactly ONE param home at entry and the OTHER deferred to the
 * cnt!=0 block head scheduled into the beqz delay slot):
 *
 *   A. both aliases (char *vt = vt_; char *nt = nt_;)  -> a1->s7 @6,
 *      a2->s6 delay
 *   B. decl-swap (nt first, vt second)                 -> a2->s7 @6,
 *      a1->s6 delay  (REG MAP MATCHES RETAIL: vt s6 / nt s7)
 *   C. zero aliases (parms used directly)              -> a1->s6 @2
 *      retail-exact 00a0b021, a2->s7 delay  (KEPT SHAPE - most likely
 *      true source)
 *   D. explicit-register hammer (register char *vt2 asm("$22") = vt;
 *      ...) -> IDENTICAL bytes to C: cc1/reload SINKS even an
 *      asm-bound initializer past the branch; the asm hammer cannot
 *      pin an entry home.
 *
 * Laws banked this window:
 * 4. REVERSE-DECL CALLEE-SAVED MAP (locals): among the pointer
 *    locals, the FIRST-declared alias gets the HIGHEST callee-saved
 *    (s7) plus the entry home; the second gets s6 and defers. The
 *    v*o group allocates descending with declaration order in BOTH
 *    compilers (v1o highest); pk (stack parm) takes the LOWEST
 *    callee-saved in ours (s1) but retail's s5 - the packet-base
 *    pick (s5 vs s1) follows from the home batching, not the source.
 * 5. (SUPERSEDED by the ROOT CAUSE block above - the "not scheduling"
 *    claim and the reload lazy-equivalence theory below are both
 *    WRONG; kept for the record) THE DEFERRAL IS BACKEND PLACEMENT,
 *    NOT SCHEDULING: the deferred
 *    copy is the first instruction of the cnt!=0 block (the beqz
 *    delay slot fill), placed by local-alloc/reload - the scheduler
 *    only filled the slot. Five source shapes cannot move it. The
 *    working theory is reload's lazy parm-register equivalence: a2
 *    lives in the incoming register until its first clobber (the dv
 *    call's arg setup writes a0=v1o/a1=v2o/a2=v3o, killing BOTH a1
 *    and a2 equivalences at the same point), and the asymmetry (a1
 *    homed, a2 deferred) follows the pseudo processing order in
 *    local-alloc/global-alloc. ftp.gnu.org is unreachable from the
 *    sandbox, so gcc-2.6.3 stock source (local-alloc.c block_alloc /
 *    global.c / reload1.c equiv handling) must come from a mirror or
 *    the next-window empirical route: perturb WHERE a2 dies first
 *    (e.g. a C read of a2-derived data placed before the branch) and
 *    watch whether its home moves to entry.
 *
 * Three earlier laws stand: ALIGN-1 STRUCT COPY (char b[8] vertex
 * copies), DECL-ORDER SPILL SLOTS (p48 0x60 before p40 0x68),
 * SINGLE-EARLY-HOME (now refined: which pseudo is early follows the
 * declaration/processing order, and exactly ONE gets it per compile).
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
                                  nt_ + *(unsigned short *)(s0 + 4) * 8,
                                  nt_ + *(unsigned short *)(s0 + 8) * 8,
                                  nt_ + *(unsigned short *)(s0 + 0xC) * 8,
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
                NormalColorDpq((long *)(nt_ + *(unsigned short *)(s0 + 0x10) * 8),
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

/* Real-decompiled-C game function #15 candidate (window 34, cron-20261030-0958).
 *
 * PARKED OFFLINE: oracle DOWN this window (the 2026-10-29 15:21 CDN links
 * 404 at ~09:59Z, expiry 09:53:54Z as window 33 predicted; witness 0/8 after
 * rollback #8), so judge_unit is unavailable (live-only) and nothing here is
 * byte-verified. The decode below is from the COMMITTED ASM ONLY (the retail
 * truth for code+data rows); the landing waits for a witnessed oracle.
 *
 * One g3_eu yaml row, 0x7f0 bytes (func_80052038..func_80052828), twenty-two
 * spimdisasm pieces that are ONE function: the TMD opacket executor - the
 * game's own source-compiled copy of the psyq LIBGS GsSortObject4J class
 * (provenance: sdk_members.txt already reports LIBGS OBJT2=GsSortObject4 and
 * OBJT3=GsSortObject4J claiming 0x800526d4 ambiguous - byte-match inside this
 * row's range; the lib member is near-identical but not the same frame, the
 * LIBSPU precedent). The eight live opcodes are the eight TMD polygon
 * primitive classes (0x20/0x21 .. 0x3C/0x3D, bit1 masked off by `& 0xFD`),
 * and the handler tables are the [a2][mode] grids over the GsTMDfast and
 * GsTMDdiv families the sdk report already places uniquely at 0x80052de4+
 * (LIBGTE).
 *
 * SHAPE (all facts from asm/g3_eu/nonmatchings/func_80052038.s):
 *
 * void func_80052038(long *ctrl, long a1, long a2, long *rec)
 * - frame 0x50; saves s0-s7, fp, ra; a1->s4, a2->s5, a3->s3.
 * - HEAD: v0 = ctrl[0]; if (v0 < 0) -> tail (return, void). Then FIVE
 *   RE-LOADS of ctrl[0], one per field (retail reloads, not CSE):
 *     (ctrl[0]>>3)&3   -> D_80147E24
 *     (ctrl[0]>>5)&1   -> D_80164268
 *     (ctrl[0]>>6)&1   -> D_80147E20
 *     (ctrl[0]>>9)&7   -> a1v -> D_801727D4
 *     (ctrl[0]>>30)&1  -> D_80171E04
 * - a2v = (a1v != 0)  (the beqz delay-slot `ori a2,1` + the 80052104 zeroing
 *   pair); when a1v != 0 the out-record s3 gets {a1v, D_8016AF90, D_8016AFA4}
 *   at [0]/[4]/[8] - a 12-byte descriptor matching the a2*12 stride below.
 * - MODE SELECTOR (80052108..80052168), delay-slot-carrying if-chain:
 *     v1 = 2; if (D_80147E20 == 1) -> L6C;           // beq delay v1=2
 *     v1 = D_80164268; if (v1 != 0) -> L44;
 *     if (GsSetLightMode_lmode == 1) { v1 = 1; goto L6C; }
 *   L44: if (v1 != 1) { v1 = 0; goto L6C; }          // via L68
 *        if (D_80147E24 != 1) { v1 = 0; goto L6C; }  // bne delay v1=0
 *        v1 = 1;                                     // via L60
 *   L6C: s6 = v1 << 2;                               // mode column
 * - PACKET STATE (8005216C): v0 = ctrl[2] (ptr); s0 = v0[4] (0x10, opacket
 *   cursor), s1 = v0[5] (0x14, remaining length), s2 = v0[0], s7 = v0[2];
 *   if (s1 == 0) -> tail; sp[0x20] = a2v * 12 (t0, table row); fp = a2v << 2.
 * - DISPATCH LOOP (800521A0): code = s0[3] & 0xFD; if ((unsigned)(code-0x20)
 *   >= 0x1E) -> 800527DC: printf(D_80021AF0, code, s0) (a1 rides in from the
 *   masked code; delay a2 = s0) then FALLS INTO the loop condition - the
 *   print-and-continue default. Else jtbl_80021B10[code-0x20] (30 entries,
 *   16 live + 14 default-fillers).
 * - CASE BODY LAW: every case loads a handler from its table base
 *   (+ t0 = a2v*12 for the 6-entry [a2][mode] grids, + s6 = mode*4 for the
 *   3-entry [mode] grids, + fp = a2v*4 for the 2-entry [a2] grids), builds
 *   the SEVEN-ARG call (a0 = s0, a1 = s2, a2 = s7, a3 = D_8016AB6C, stack
 *   0x10 = s0[0] len, 0x14 = s5, 0x18 = s4, 0x1C = s3), calls jalr, commits
 *   the return to D_8016AB6C, then s1 -= s0[0] and advances s0 by
 *   len * UNIT. The 0x21-class variant re-orders regs (a2 = D_8016AB6C,
 *   a3 = len, stack 0x10/14/18 = s5/s4/s3).
 * - ADVANCE UNITS (measured): stub 80052594 = <<4 (x16); stub 800525EC =
 *   (<<1 +)<<3 (x24); stub 8005274C = <<5 (x32); j 800527CC delay <<3 ->
 *   27CC: -len, fall 27D0: <<2 (x28); j 800527D0 delay (<<2 +) -> <<2 (x20);
 *   j 800527D0 delay (<<3 +) -> <<2 (x36, cases 0x28/0x35/0x3C); case 0x3D
 *   FALLS THROUGH 27CC->27D0 with (<<1 +)<<2 -len <<2 = x44. Shared-tail
 *   800527EC: bnez s1 -> 800521A0 (the loop back edge); fall = epilogue.
 * - EPILOGUE: keep-epilogue class (no v0 written anywhere).
 *
 * CASE MAP (body -> table(s) -> call form -> advance):
 *   0x20 800521D8: bit2 of s0[2] SET   -> D_80098A98[mode]   stub25EC x24
 *                  bit2 of s0[2] CLEAR -> D_80098998[a2][mode] stub2594 x16
 *   0x21 80052534: D_800989B0[a2] (2)  stub2590->2594 x16, a3=len form
 *   0x24 80052264: D_800989D8[a2][mode] stub25EC x24
 *   0x25 8005261C: D_800989F0[a2] (2)  inline j27CC x28
 *   0x28 800523DC: D_80098A18[a2][mode] inline j27D0(<<3) x36
 *   0x29 80052564: D_80098A30[a2] (2)  inline x16 (sll<<4 direct to 27EC)
 *   0x2C 80052444: D_80098A58[a2][mode] stub274C x32
 *   0x2D 8005271C: D_80098A70[a2] (2)  inline to 27EC (x16 via <<4? re-measure)
 *   0x30 800522A8: bit2 SET   -> D_80098AA4[mode]   stub25EC x24
 *                  bit2 CLEAR -> D_800989B8[a2][mode] inline j27CC x28
 *   0x31 800525BC: D_800989D0[a2] (2)  inline (<<1 +)<<3 x24
 *   0x34 80052378: D_800989F8[a2][mode] inline j27CC x28
 *   0x35 80052670: D_80098A10[a2] (2)  inline j27D0(<<3) x36
 *   0x38 80052488: D_80098A38[a2][mode] stub25EC x24
 *   0x39 800526C8: D_80098A50[a2] (2)  inline j27CC x28
 *   0x3C 800524CC: D_80098A78[a2][mode] inline j27D0(<<3) x36
 *   0x3D 80052774: D_80098A90[a2] (2)  inline fall 27CC->27D0 x44
 *   (table contents from asm/g3_eu/nonmatchings/data/data_8008002C.data.s:
 *    the 6-entry grids mix direct game handlers func_8005xxxx with curated
 *    GsTMDdiv and GsTMDfast names already adopted in symbols.curated.txt.)
 *
 * MATCHING PLAN (next witnessed window):
 * 1. judge_unit needs the row as ONE c unit: the yaml row is already a single
 *    `asm` row 0x7f0 - convert to `c`, write src/func_80052038.c.
 * 2. The switch: `switch (s0[3] & 0xFD)` with 16 cases 0x20..0x3D + default
 *    printf - gcc 2.6.3 lowers to sltiu/jtbl exactly as retail (the 14 dead
 *    table slots get the default label). cc-post: keep-epilogue.
 * 3. The five ctrl[0] reloads: volatile-cast or per-field re-read through a
 *    volatile pointer - retail reloads, plain C CSEs. Probe first: plain
 *    loads (gcc may keep them if the stores to the D_ statics alias).
 *    The D_ writes are extern long stores -> gcc must assume aliasing on
 *    ctrl[0]? ctrl is a long* param - alias analysis may still CSE. Probe
 *    matrix: plain / volatile ctrl / per-field expressions.
 * 4. The tail-merged stubs: identical per-case post-call sequences merge into
 *    80052594/25EC/274C only if the C source's per-case tails are textually
 *    identical apart from the multiplier expression. If gcc refuses a merge,
 *    split the difference with a shared inline helper or accept per-case
 *    code and diff-count.
 * 5. The mode selector's delay-slot carries (v1=2 / v1=0 / v1=1) reproduce as
 *    straight if/else value assignments - window-30 law 3 (no value-selects
 *    in stores) does not bite here; the risk is gcc if-converting the
 *    L44/L60 pair. Probe both if-chains and the ?: form.
 * 6. s0/s1/s2/s7/fp/s6 allocation: register-var pins at the loop head are
 *    likely needed (the func_80048908 idiom) - retail holds the opacket
 *    cursor in s0 across the whole loop with s1 the remaining length.
 *
 * cc-post: keep-epilogue
 */
extern long D_80147E20[];
extern long D_80147E24[];
extern long D_80164268[];
extern long D_801727D4[];
extern long D_80171E04[];
extern long D_8016AF90[];
extern long D_8016AFA4[];
extern long D_8016AB6C[];
extern long GsSetLightMode_lmode[];
extern long D_80098998[];
extern long D_800989B0[];
extern long D_800989B8[];
extern long D_800989D0[];
extern long D_800989D8[];
extern long D_800989F0[];
extern long D_800989F8[];
extern long D_80098A10[];
extern long D_80098A18[];
extern long D_80098A30[];
extern long D_80098A38[];
extern long D_80098A50[];
extern long D_80098A58[];
extern long D_80098A70[];
extern long D_80098A78[];
extern long D_80098A90[];
extern long D_80098A98[];
extern long D_80098AA4[];
extern char D_80021AF0[];
extern int printf();

/* Skeleton of the head + loop scaffold only - the 16 case bodies are the
 * next window's byte-exact work against the live judge. */
void func_80052038(long *ctrl, long a1, long a2, long *rec)
{
    long *pkts;
    long len;
    long mode;
    long a1v;
    long a2v;
    long t0;

    if (*ctrl >= 0) {
        D_80147E24[0] = (*ctrl >> 3) & 3;
        D_80164268[0] = (*ctrl >> 5) & 1;
        D_80147E20[0] = (*ctrl >> 6) & 1;
        a1v = (*ctrl >> 9) & 7;
        D_801727D4[0] = a1v;
        D_80171E04[0] = (*ctrl >> 30) & 1;
        a2v = (a1v != 0);
        if (a2v) {
            rec[0] = a1v;
            rec[1] = D_8016AF90[0];
            rec[2] = D_8016AFA4[0];
        }
        if (D_80147E20[0] == 1) {
            mode = 2;
        } else if (D_80164268[0] != 0) {
            mode = (D_80164268[0] == 1 && D_80147E24[0] == 1);
        } else {
            mode = (GsSetLightMode_lmode[0] == 1);
        }
        pkts = (long *)ctrl[2];
        /* s0 = pkts[4]; s1 = pkts[5]; s2 = pkts[0]; s7 = pkts[2]; */
        t0 = a2v * 12;
        if (pkts[5] == 0) {
            return;
        }
        /* do { switch (pkt[3] & 0xFD) { ... } } while (s1 != 0); */
    }
}

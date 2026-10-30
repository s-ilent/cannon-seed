/* Real-decompiled-C game function #15 candidate (window 34 decode; round-2
 * landing attempt 2026-10-30, cron-20261030-2336 window, witness 8/8 restored
 * 15:45Z on Silent's 11:42 UTC CDN links after the maspsx-patch-location fix).
 *
 * ROUND-3 STATUS (cron-20261030-1806 window): judge SIZE built 1988 vs row
 * 2032 (44 B / 11 insns short; round-2 was 1944/-22, round-1 1932/-25),
 * DIFF 405/497 words (round-2: 436/486). The C below compiles clean and is
 * the resume point - iterate judge_unit, do NOT restart the decode. The
 * staged shape that produced 1988: copy this file to src/func_80052038.c
 * and flip the g3_eu yaml row to [0x32838, c, func_80052038].
 *
 * ROUND-3 FINDINGS (all judge-proven against the live oracle 2026-10-30
 * ~18:20-19:10Z, witness 8/8 on Silent's 11:42Z links; probe files
 * probe_52038_tbl_la.c / probe_52038_tbl_barrier.c + the m-series matrix):
 * - REC-STORE PIPELINED ORDER: retail is lw AF90, lw AFA4, sw a1,0(rec),
 *   sw v0,4(rec), j merge, delay-sw v1,8(rec) - the two loads land BEFORE
 *   any store and the LAST store rides the jump's delay slot. Writing
 *   rec[0]/rec[1]/rec[2] in text order hoists sw0 above the loads; writing
 *   rec[1];rec[2];rec[0] sinks sw0 into the j delay. FIX: pre-load into
 *   locals (r1 = D_8016AF90; r2 = D_8016AFA4;) THEN rec[0]=a1v; rec[1]=r1;
 *   rec[2]=r2 - the r1/r2 locals reproduce retail's store order exactly
 *   (head now byte-exact 0x800520E4..0x800520F0).
 * - T9 TIE: the non-volatile asm tie on t9 (__asm__ ("" : "=r"(t9) :
 *   "0"(t9))) does NOT break the a1v coalescing (still lw $5/srl $5 at
 *   0x800520A8/BC/C0, 3 words) but is harmless; kept in the probe shape.
 * - CASE-BODY TABLE LA-FORM CONFIRMED + THE TWO FORCES: retail's inline
 *   StdFn cases are lui $v0,%hi; addiu $v0,$v0,%lo; addu $v0,$t0,$v0;
 *   addu $v0,$s6,$v0; lw $v0,0($v0) (la IN $v0, addus destructive). The
 *   (char *)D + t0 + s6 form gives the 4-insn at-split; the base-pointer
 *   local tbl = D_xxx forces the 5-insn la-form, but gcc allocates tbl to
 *   $3 and SWAPS the second addu (acc-first instead of retail's s6-first).
 *   PIN IT: register long tbl asm("$2") forces the la into $v0 (round-3
 *   state). REMAINING per no-flag case: the second addu order (built
 *   addu $2,$t0,$2; addu $2,$2,$22 = acc-first; retail addu $v0,$s6,$v0
 *   = s6-first destructive) - ~3 words x8 cases. Pointer-type tree
 *   canonicalization is the mirror mechanism (ptr must be op1); pure-long
 *   sources did not survive the at-refold - the m-series matrix
 *   (m1..m6: source order x barrier placement) is banked in the probe.
 * - FLAG-PATH AT-FORM: retail 0x20/0x30 flag = lui $at,%hi; addiu
 *   $at,$at,%lo; addu $at,$at,$s6; lw $v0,0($at) (4 insns, la completed
 *   BEFORE the index addu). gcc FOLDS %lo into the lw (3 insns) unless
 *   the la is forced to complete: the barrier asm __asm__ ("" : :
 *   "r"(tbl)) between tbl = D_xxx and the indexed load reproduces the
 *   4-insn form (barrier in the round-3 state). gcc 2.6.3 rejects
 *   statement-asm inside expressions (comma-operator form = parse error);
 *   the barrier MUST be statement-position. Remaining flag deltas: the
 *   la rides $v0 (pin) where retail uses $at (its own scratch - not
 *   allocatable from C), and the addu order mirrors.
 * - ALT-FN MAP STILL OPEN: the 8 AltFn cases remain in the fpv at-form;
 *   the retail blocks index by $s6 in at least one case (jalr + addu
 *   $at,$at,$s6) - the fpv-vs-s6 case map must be re-derived from the
 *   committed asm before the AltFn pass (queued round-4 item).
 *
 * ROUND-2 FINDINGS (all judge/probe-proven against the live oracle this
 * window; probe files probe_52038_pin_*.c):
 * - VOLATILE READ-F2 LAW: the five head reads are five SEPARATE loads in
 *   retail; gcc CSEs read-f2 into read-f1's value (no store separates the
 *   statements). read f2 MUST be *(volatile unsigned long *)ctrl - the
 *   volatile kills the CSE without disturbing the scheduler slide; the
 *   other four reads stay plain. This single change reproduces retail's
 *   L0..L4 interleave exactly (load slides between srl(N-1) and andi(N-1)).
 * - CTRL PIN + SPLIT-LIFE LAW: retail reads ALL SIX loads through $a0.
 *   `register long *ctrl asm("$4"); ctrl = ctrlp;` pins the head reads -
 *   BUT the state load `state = (long *)ctrl[2]` sits in a LATER basic
 *   block (after the rec-fill join) and gcc 2.6.3 SPLITS the pinned var's
 *   life per region: head reads got a COPY ($5/$8), only the state load
 *   kept $4 (probe_52038_pin_i/j/k: inline head + state loads => copy;
 *   helper-head or no-state-loads => no copy). FIX: read the state pointer
 *   through the RAW PARAM `state = (long *)ctrlp[2]` - the param pseudo
 *   stays $4 everywhere, the pinned local's life stays single-region, and
 *   ALL loads ride $a0 with NO copy (probe_52038_pin_n: 6/6 loads via $4).
 * - A1V PIN LAW: retail computes a1v as lw $v1,srl $v1,9,andi $a1,v1,7 -
 *   load+shift ride $v1, only the ANDI lands in $a1 ($5). Pin a1v to $5.
 *   OPEN NIT: with the pin, gcc loads DIRECTLY into $5 (lw $5,srl $5,9)
 *   - the t9 temp split coalesces (single-use) and a volatile t9 breaks
 *   the scheduler slide (barrier => early a2v move). 2 insns differ, same
 *   count - resume here.
 * - A2V BRANCH LAW: retail = beqz $a1 with ORI a2,1 in the BRANCH DELAY
 *   SLOT and move a2,zero at the join. The if/else form
 *   (a2v=1+fill / else a2v=0) gives beqz+delay-ori exactly; the preset
 *   form (a2v=0 before the if) emits the move EARLY (wrong); unpinned a2v
 *   emits it early too. OPEN NIT: gcc forwards the known-zero a1v into
 *   the else's a2v=0 => move a2,a1 instead of move a2,zero (1 insn, same
 *   count). The volatile-pin trick breaks the frame; the gcc2 "+r" asm
 *   clobber is unsupported (matching-constraint form added 2 insns).
 * - MODE SHARED-CHAIN LAW: the lmode test is NOT private to the tmp==0
 *   path - retail SHARES the mode=1 (j+delay-ori) and mode=0 blocks across
 *   the tmp==0/lmode!=1 and tmp!=0 paths. The C must write the lmode arm
 *   as an explicit if/else (mode=1/mode=0), NOT `mode = (lmode == 1)`.
 * - CASE-BODY TABLE LAW: retail's StdFn (t0+s6-indexed) tables are FUSED
 *   la-form: lui v0,%hi; addiu v0,v0,%lo; addu v0,$t0,$v0; addu v0,$s6,$v0;
 *   lw v0,0(v0) = 5 insns. The draft's (char *)D + t0 + s6 gives the split
 *   at-form (addu,lui $at,addu $at,lw %lo($at)) = 4 insns - one insn SHORT
 *   per case (x8 StdFn cases = 8 of the 22 missing insns). Banked law
 *   applies: force the la with a base-pointer local
 *   `tbl = D_80098xxx; *(long **)((char *)tbl + t0 + s6)` - the array-
 *   symbol assignment is the fused la, the byte-arithmetic on the LOCAL is
 *   pure addus. OPEN: exact addu operand order (retail: addu v0,$t0,$v0
 *   then addu v0,$s6,$v0) + the AltFn cases index by $s6 in at least one
 *   retail block (jalr + addu $at,$at,$s6) - re-derive the fpv-vs-s6 case
 *   map from the committed asm before the case pass.
 * - ARG-STORE ORDER in the case bodies matches the draft already
 *   (sw $s5,0x14; sw $s4,0x18; sw $s3,0x1c; sw $v0,0x10) and the lead-in
 *   order (lhu v0,(s0); lw t0,0x20(sp); lui/lw a3 = D_8016AB6C; move a1,s2)
 *   matches too - the case pass is ONLY the table form + the stub-merge
 *   distances.
 *
 * ROUND-1 FINDINGS (still standing):
 * - HEAD CONDITION: the 80052074 branch is bltz $v0 -> the epilogue, i.e.
 *   the body runs when ctrl[0] >= 0 - the if (*ctrl >= 0) form is correct.
 * - THE FIVE HEAD RELOADS INTERLEAVE (retail: load(N) slides up between
 *   srl(N-1) and andi(N-1), never crossing a store). Plain C reproduces the
 *   five reloads but NOT the interleave (probe scripts/probe_head_reload.c
 *   variants A/B and probe_head_reload2.c D/E/F all stay sequenced). The
 *   load-hoist needs the SOFTWARE-PIPELINED statement order used below
 *   (each field's load precedes the previous field's store; the scheduler
 *   then interleaves without crossing a store). C89: declarations first,
 *   assignments in pipeline order.
 * - HEAD SHIFTS ARE UNSIGNED (srl not sra): read via
 *   *(unsigned long *)ctrl.
 * - THE HEAD-FIELD TARGETS ARE SCALAR EXTERNS: `extern long D_80147E24;`
 *   + bare-name stores give the retail lui $at/%hi + sw %lo form; the
 *   array-extern form (D_80147E24[0]) makes gcc cache the address in a
 *   call-clobbered reg (la $9) - wrong. Same for D_80164268/D_80147E20/
 *   D_801727D4/D_80171E04/D_8016AB6C/D_8016AF90/D_8016AFA4/
 *   GsSetLightMode_lmode (fused-pair loads for the reads).
 * - PARAM PINS: retail holds a1 -> $20 (s4), a2 -> $21 (s5), rec -> $19
 *   (s3); the register-var pins reproduce the save-slot layout exactly
 *   (0x38/0x3C/0x34) when the initializers run in the order a1, a2, rec.
 * - PIN WARNING: pinning fpv (a2v*4) to $30 makes gcc COALESCE the spilled
 *   t0 (a2v*12) into $fp and emits a dead duplicate sll - WRONG ADDRESSES
 *   in the 6-entry grid cases. fpv must stay UNPINNED; gcc then spills t0
 *   to 0x20(sp) (vars=8, frame 0x50, all ten save slots == retail) and
 *   allocates fp naturally.
 * - CALL TYPES: two typedefs - StdFn 8 args (op, s2, s7, D_8016AB6C, len,
 *   a2, a1, rec) and AltFn 7 args (op, s2, D_8016AB6C, len, a2, a1, rec);
 *   both end in long* - the unprototyped-int tail made gcc warn.
 * - ADVANCE CORRECTIONS over the window-34 case map (asm truth):
 *   0x28 = x20 (sll,addu -> j 27D0 <<2), NOT x36; 0x30-clear = x20, NOT
 *   x28; 0x2D falls INTO the 274C stub = x32 (no inline chain); 0x29 and
 *   0x31 fall through the 2590/25EC merge points (a1 = s2 rides inside
 *   the stub). x16/x24/x32 tail-merge into 80052594/25EC/274C; x20/x28/
 *   x36/x44 stay inline over the shared 27CC/27D0 chain.
 * - gcc lowers `switch (code)` (16 cases 0x20..0x3D, step-4 pattern) to
 *   the exact sltiu/jtbl form with the 14 default-filled dead slots.
 *
 * REMAINING ROUND-3 WORK (re-ranked): (1) the second-addu operand order on
 * the 8 no-flag cases (s6-first destructive vs gcc's acc-first swap) -
 * candidate levers: mid-pointer barrier between the addus (probe m3/m6),
 * source-order variants, or accepting the at-form for these cases too;
 * (2) the AltFn fpv-vs-s6 map re-derivation off the committed asm, then
 * the AltFn table pass; (3) the mode chain (~30-word run: branch-form
 * skeleton proven reproducible in isolation by the goto-form probe v5/v6
 * - goto L_state/L_mode_shared/L_mode_one with f1-vs-tmp register
 * compare - but gcc delay-fills the mode=1/0 arms in the full function;
 * the sltu if-conversion of the round-2 form is byte-closer overall);
 * (4) the a1v 3-word nit + the else a2v forward (move $6,$5 vs $6,$0)
 * + the rec[0] store base ($7 vs $19); (5) the stub-merge distances and
 * the branch-offset cascade (resolves when the above land).
 *
 * cc-post: keep-epilogue
 */
typedef long (*StdFn)(long *, long, long, long, long, long, long, long *);
typedef long (*AltFn)(long *, long, long, long, long, long, long *);

extern long D_80147E20;
extern long D_80147E24;
extern long D_80164268;
extern long D_801727D4;
extern long D_80171E04;
extern long D_8016AF90;
extern long D_8016AFA4;
extern long D_8016AB6C;
extern long GsSetLightMode_lmode;
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

void func_80052038(long *ctrlp, long a1p, long a2p, long *recp)
{
    register long *ctrl asm("$4");
    register unsigned char *s0 asm("$16");
    register long s1 asm("$17");
    register long s2 asm("$18");
    register long *rec asm("$19");
    register long a1 asm("$20");
    register long a2 asm("$21");
    register long s6v asm("$22");
    register long s7 asm("$23");
    long fpv;
    long t0;
    register long tbl asm("$2");
    long mid;
    register long a1v asm("$5");
    long a2v;
    long t9;
    long mode;
    long *state;

    a1 = a1p;
    a2 = a2p;
    rec = recp;
    ctrl = ctrlp;

    if (*ctrl >= 0) {
        long f1;
        long f2;
        long f3;
        long f5;
        f1 = (long)((*(unsigned long *)ctrl >> 3) & 3);
        f2 = (long)((*(volatile unsigned long *)ctrl >> 5) & 1);
        D_80147E24 = f1;
        f3 = (long)((*(unsigned long *)ctrl >> 6) & 1);
        D_80164268 = f2;
        t9 = *(unsigned long *)ctrl >> 9;
        __asm__ ("" : "=r"(t9) : "0"(t9));
        D_80147E20 = f3;
        f5 = (long)((*(unsigned long *)ctrl >> 30) & 1);
        D_801727D4 = t9 & 7;
        a1v = t9 & 7;
        D_80171E04 = f5;
        if (a1v != 0) {
            long r1;
            long r2;
            a2v = 1;
            r1 = D_8016AF90;
            r2 = D_8016AFA4;
            rec[0] = a1v;
            rec[1] = r1;
            rec[2] = r2;
        } else {
            a2v = 0;
        }
        if (D_80147E20 == 1) {
            mode = 2;
        } else {
            long tmp = D_80164268;
            if (tmp != 0) {
                if (tmp == 1 && D_80147E24 == 1) {
                    mode = 1;
                } else {
                    mode = 0;
                }
            } else {
                if (GsSetLightMode_lmode == 1) {
                    mode = 1;
                } else {
                    mode = 0;
                }
            }
        }
        state = (long *)ctrlp[2];
        s0 = (unsigned char *)state[4];
        s1 = state[5];
        s2 = state[0];
        s7 = state[2];
        if (s1 == 0) {
            return;
        }
        s6v = mode << 2;
        t0 = a2v * 12;
        fpv = a2v << 2;
        do {
            unsigned int code = (unsigned int)s0[3] & 0xFD;
            switch (code) {
            case 0x20:
                if (*(unsigned short *)(s0 + 2) & 4) {
                    tbl = D_80098A98;
                __asm__ ("" : : "r"(tbl));
                D_8016AB6C = ((StdFn) * (long *)(s6v + (char *)tbl))(
                        (long *)s0, s2, s7, D_8016AB6C,
                        *(unsigned short *)s0, a2, a1, rec);
                    s1 -= *(unsigned short *)s0;
                    s0 += *(unsigned short *)s0 * 24;
                } else {
                    D_8016AB6C = ((StdFn) * (long *)(s6v + (t0 + (char *)(tbl = D_80098998))))(
                        (long *)s0, s2, s7, D_8016AB6C,
                        *(unsigned short *)s0, a2, a1, rec);
                    s1 -= *(unsigned short *)s0;
                    s0 += *(unsigned short *)s0 * 16;
                }
                break;
            case 0x24:
                D_8016AB6C = ((StdFn) * (long *)(s6v + (t0 + (char *)(tbl = D_800989D8))))(
                    (long *)s0, s2, s7, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 24;
                break;
            case 0x30:
                if (*(unsigned short *)(s0 + 2) & 4) {
                    tbl = D_80098AA4;
                __asm__ ("" : : "r"(tbl));
                D_8016AB6C = ((StdFn) * (long *)(s6v + (char *)tbl))(
                        (long *)s0, s2, s7, D_8016AB6C,
                        *(unsigned short *)s0, a2, a1, rec);
                    s1 -= *(unsigned short *)s0;
                    s0 += *(unsigned short *)s0 * 28;
                } else {
                    D_8016AB6C = ((StdFn) * (long *)(s6v + (t0 + (char *)(tbl = D_800989B8))))(
                        (long *)s0, s2, s7, D_8016AB6C,
                        *(unsigned short *)s0, a2, a1, rec);
                    s1 -= *(unsigned short *)s0;
                    s0 += *(unsigned short *)s0 * 20;
                }
                break;
            case 0x34:
                D_8016AB6C = ((StdFn) * (long *)(s6v + (t0 + (char *)(tbl = D_800989F8))))(
                    (long *)s0, s2, s7, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 28;
                break;
            case 0x28:
                D_8016AB6C = ((StdFn) * (long *)(s6v + (t0 + (char *)(tbl = D_80098A18))))(
                    (long *)s0, s2, s7, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 20;
                break;
            case 0x2C:
                D_8016AB6C = ((StdFn) * (long *)(s6v + (t0 + (char *)(tbl = D_80098A58))))(
                    (long *)s0, s2, s7, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 32;
                break;
            case 0x38:
                D_8016AB6C = ((StdFn) * (long *)(s6v + (t0 + (char *)(tbl = D_80098A38))))(
                    (long *)s0, s2, s7, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 24;
                break;
            case 0x3C:
                D_8016AB6C = ((StdFn) * (long *)(s6v + (t0 + (char *)(tbl = D_80098A78))))(
                    (long *)s0, s2, s7, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 36;
                break;
            case 0x21:
                D_8016AB6C = ((AltFn) * (long **)((char *)D_800989B0 + fpv))(
                    (long *)s0, s2, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 16;
                break;
            case 0x29:
                D_8016AB6C = ((AltFn) * (long **)((char *)D_80098A30 + fpv))(
                    (long *)s0, s2, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 16;
                break;
            case 0x31:
                D_8016AB6C = ((AltFn) * (long **)((char *)D_800989D0 + fpv))(
                    (long *)s0, s2, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 24;
                break;
            case 0x25:
                D_8016AB6C = ((AltFn) * (long **)((char *)D_800989F0 + fpv))(
                    (long *)s0, s2, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 28;
                break;
            case 0x35:
                D_8016AB6C = ((AltFn) * (long **)((char *)D_80098A10 + fpv))(
                    (long *)s0, s2, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 36;
                break;
            case 0x39:
                D_8016AB6C = ((AltFn) * (long **)((char *)D_80098A50 + fpv))(
                    (long *)s0, s2, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 28;
                break;
            case 0x2D:
                D_8016AB6C = ((AltFn) * (long **)((char *)D_80098A70 + fpv))(
                    (long *)s0, s2, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 32;
                break;
            case 0x3D:
                D_8016AB6C = ((AltFn) * (long **)((char *)D_80098A90 + fpv))(
                    (long *)s0, s2, D_8016AB6C,
                    *(unsigned short *)s0, a2, a1, rec);
                s1 -= *(unsigned short *)s0;
                s0 += *(unsigned short *)s0 * 44;
                break;
            default:
                printf(D_80021AF0, code, s0);
                break;
            }
        } while (s1 != 0);
    }
}

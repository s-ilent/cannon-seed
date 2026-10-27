# block-move unit decode - judge-loop state (cron-202610260919)

The movstrsi landing recipe (cron-202610260649) executed to the first judge
diffs; the tree splits were reverted (ratchet-gated), the decode artifacts
are staged here. Everything below is oracle-proven or judge-observed.

## TRUE UNIT EXTENTS (recipe correction)

The recipe said "split at yaml 0xB660 (VA 0x8002AE60)" - that is the 0649
window's body chunk, NOT the entry. Both boots' units are the SAME source
function whose real entry is the jal'd prologue and whose tail is the
matching epilogue:

- slps_00270: VA 0x8002ADA0..0x8002B464 (0x6c4), yaml/file 0xB5A0..0xBC64.
  Entry func_8002ADA0 (0x40 prologue, jal'd from 0x8002A7C4), epilogue
  func_8002B444 (restores ra/s4/s3/s2/s1/s0, frame 0x28).
- sces_00269: VA 0x8002ABC8..0x8002B28C (0x6c4), yaml/file 0xB3C8..0xBA8C.
  Entry func_8002ABC8 (0x40 prologue, jal'd from 0x8002A5EC), epilogue
  func_8002B26C.

All 33 interior chunks accounted byte-exact between entry and epilogue in
both boots (chunk sizes sum to 0x6c4 exactly). NO external branch enters
either unit's interior; the only outside refs are the two entry jals plus
sces head branches to interior labels func_8002ADA0/func_8002AF10 (both
already in config/symbols.sces_00269.txt - prelude-resolvable).

## DECODE (same C serves both boots, per-target symbols)

Memory-card save unit, o32 8 args: path(s4), code(s2), str(a2->strcpy),
rec(s3, 0x30 record), src5(s0, stack 0x38), src6(stack 0x3C),
src7(stack 0x40), size(stack 0x44). See the two .c files for the full
body: signed-div sector math (three separate /0x2000 expressions), 0xff
byte-loop fill of the work buffer, 'SC'+code header (one pointer var +
two distinct per-byte symbols), strcpy, 0x30 straight-line record copy,
(short)code==0x13 if/else with THREE 0x80 movstrsi block-moves per arm
(both arms re-bind assignment 1 src5->hdr+0x80 - that is why gcc expands
it twice, no CSE), 0x200 block-move copy back into the work buffer, then
open/close/write/read verify tail (returns 2/0/1/-3).

Symbol map: slps D_8006974C/D_801150F8/F9/FA/FB/D_80115158/D_801151F8/
D_80115278 <-> sces D_800693F4/D_80114678/79/7A/7B/D_801146D8/D_80114778/
D_801147F8. sces has NO gp_value -> no gp rewrite; slps does.

## LANDED-BLOCKERS SOLVED THIS WINDOW (bank these)

1. src/ is ratchet-gated: placeholder tokens (func_XXXXXXXX/D_XXXXXXXX)
   are counted PER OCCURRENCE in src/ and include/ - an unmatched unit's
   src cannot land (652/60 vs 644/0). Files stage HERE until the loop
   closes; the memclr build-inert precedent only worked because those
   units' names were already real.
2. slps stager rewrites bare-symbol operands to %gp_rel when the symbol
   is missing from the gp_info table (tools/gp_flags.py info reads ONLY
   config/symbols.slps_00270.txt). The unit's eight data symbols must be
   added to the curated zone of config/symbols.slps_00270.txt with
   `absolute:true` (D_8006974C is within gp range but retail loads it
   lui/addiu - the _spu_inTransfer precedent). Verified: with the entries
   added, the judge mini-links and diffs bytes.
3. The two yaml splits + giant-.s head/tail surgery were rehearsed
   (exact line splits: slps 5374..5971 unit lines out of
   func_800272F8.s, tail file asm/nonmatchings/func_8002B464.s; sces
   5183..5780 out of func_80027340.s, tail asm/sces_00269/
   func_8002B28C.s) and reverted clean.

## JUDGE LOOP STATE (first diffs, slps)

First compile: LINK-FAIL fixed by (2); then a real byte diff of 136+
words starting in the prologue: OURS interleaves the arg binds into the
save sequence (lw a0,0x44(sp) lands where retail still has sw s3,0x1c),
retail keeps ALL SIX saves (ra,s4,s3,s2,s1,s0) ahead of every bind
(s4=a0, s3=a3, lw v1,0x44(sp), s2=a1, lw s0,0x38(sp)). Iteration matrix
queued: statement order around t=size+0x200 (the size load must NOT
hoist into the save window - try computing total after the header
stores, or redeclaring the param order), then the fill-loop form
(sltiu bound, per-iteration base materialization), then per-arm
block-move layout, then the open/close tail scheduling.

## JUDGE LOOP PROGRESS (cron-202610261034)

The splits + symbols + srcs were wired IN-TREE this window (extract clean:
head/tail .s + yamls only; the three-file clobber lesson did NOT fire for
these rows; no unit .s was generated since the srcs existed) and the judge
mini-links cleanly with the curated entries - blocker 2's fix re-verified.
Tree then REVERTED to aaa23ad3 (landing requires a converged loop; only the
curated D_ entries were kept - they are durable across regens and inert
without the split). Variant snapshots live in variants/.

v0 FIRST-JUDGE FACTS (slps_00270):
- SIZE EXACT: built 1732 = retail 0x6c4. SIX diff regions only:
  0x004..0x010 + 0x014..0x018 (prologue bind order), 0x01C..0x15C (divs +
  fill + stores + strcpy + S30 + dispatch head), 0x5CC..0x5D4 (-1 register
  s2 vs s1), 0x5D8..0x6BC (open/close tail scheduling), 0x6C0..0x6C4
  (epilogue final word nop vs addiu sp,0x28).
- THE MIDDLE IS BYTE-EXACT: 0x15C..0x5CC (1132 bytes) - all THREE 0x80
  movstrsi block-moves, the unaligned+aligned dispatch, the 0x30 S30
  straight-line copy, the (short)code==0x13 branch - the decode's core law
  verified end to end.

LAWS BANKED (each oracle-observed):
1. MODULO: `t % 0x2000 != 0` compiles to `andi v0, v1, 0x1fff` + beq - gcc
   2.6.3's zero-test shortcut. Retail instead runs a FULL SECOND branchy
   division. FALSIFIED forms: `t != total` (V3), inline `t != t/0x2000*
   0x2000` (V4), copy-var `u = t; t != u/0x2000*0x2000` (V5a) - ALL merge
   into ONE div (CSE/coalesce) and shrink 4 bytes. Retail's div2 shape:
   `addu v0,v1` BEFORE bgez (branch reads the copy's register, delay slot
   nop) + `addiu v0,v0,0x1fff` + sra + sll + `beq v1,v0` - the div operand
   is a DISTINCT pseudo holding a copy of t, compared against t itself.
   OPEN: which C form blocks the CSE (the real compile kept both divs).
2. PROLOGUE: gcc 2.6.3 emits LAZY saves for the current C (each s-reg
   saved immediately before its bind, interleaved, ra/s1 last); retail is
   BLOCK saves (ra,s4,s3,s2,s1,s0) then binds s4,s3,[v1=size],s2,[s0=src5].
   The str shuffle `addu a1,a2` rides strcpy's DELAY SLOT in retail
   (B670) but gcc hoists it into the entry batch for our C. OPEN.
3. FILL LOOP: built = pointer walk (hoisted base, base+0x1FF end cursor);
   retail = per-iteration lui/addiu base materialization + sltiu bound +
   the 'S' constant (0x53) riding the loop bnez delay slot. Symbol-index
   alone did NOT prevent the hoist. OPEN.
4. -1 REGISTER: ours materializes -1 into s2 at the fd==-1 test; retail
   reuses s1 (hdr's home) after hdr's liveness ends. Likely self-resolves
   with the prologue law. OPEN.
5. TAIL: open/close scheduling region + the epilogue's final delay-slot
   word (cc_post rules 4/5 territory). OPEN.

Register assignment CONFIRMED IDENTICAL both sides (path=s4, code=s2,
src5=s0, rec=s3, size=t via v1) - only emission order and shapes differ.

## JUDGE LOOP PROGRESS (cron-202610261304): THE DIV2 LAW CLOSES

Window shape: rehydrate OK; HEAD 7623cd2 was 400 behind -> reset to 9f2c59fa;
worklog_digest exit 1 (the rollback restored an ancient worklog snapshot, 134
windows missing) -> RESTORE NOTE appended verbatim, digest exit 0. Disc-return
#31: links still valid (expiry ~09:53 UTC), both CHDs re-downloaded in
foreground, sha256 gates pass, per-sector extracts, witness 8/8 STRICT,
verify 8/8 GREEN before any wiring.

THE KEYSTONE (NEXT WINDOW (b) of cron-202610261034) IS SOLVED. The retail
div2's full second division survives iff its operand is a DIFFERENT pseudo
from div1's, i.e. the source's test divides the RAW size PARAM, not t:

    total = t / 0x2000 * 0x2000;
    if (t != size / 0x2000 * 0x2000)      /* div2 on size (P), LHS t (T) */
        total += 0x2000;

Mechanism (gcc 2.6.3 source-level, expmed.c ~2865): the signed TRUNC div by
power-of-2 branchy path (BRANCH_COST < 3) is
[copy_to_mode_reg(op0); bgez copy; addiu copy,0x1fff; sra] with a REG_EQUAL
(div op0 op1) note on the quotient sra. CSE eliminates the second division
iff its note canonicalizes to div1's (same operand pseudo via copy
equivalences). The mips delay-slot trick (CSE rewrites the branch+correction
reads to the operand's canonical register, then the copy rides the bgez
delay slot) explains div1's retail shape; div2 keeps the before-copy shape
(copy precedes the branch, nop slot, correction reads the copy) when the
rewrite does not fire - observed for the size-operand form.

Screen results (scripts/bm_unit_decode/div2_screen.py, cc.sh pipeline):
- e1 (V4 repro) / e2 rem-var / e3 two quotient vars / e4 total-copy /
  e5 body-rediv: ALL merge into ONE div (4-byte-class shrink) - the 1034
  falsifications reproduce.
- V6 `if (size != size / 0x2000 * 0x2000)` (both sides size): the second
  division SURVIVES (div2's note (div P c) != div1's (div T c)) but BOTH
  divisions take the delay-slot shape - div2's copy rides its own bgez slot,
  WRONG vs retail (div2 must be the before-copy form).
- W1 `if (t != size / 0x2000 * 0x2000)` (LHS t, div2 on size): RETAIL SHAPE
  EXACT for the div2 region - div1 = delay-slot form (T live across, copy in
  slot, correction reads the operand), div2 = before-copy form (move v0,P;
  bgez v0; nop; addiu v0,v0,0x1fff; sra; sll; beq v1,v0 with t as LHS).
  The winning form is committed as variants/v6_w1_size_div.c.
- W3 (u = size copy; same test through u): shape-identical to W1 -
  the copy variable is unnecessary; W1 is the minimal form.

JUDGE v1 FACTS (wired split + W1 src, judge_unit slps_00270):
- The wired tree compiles and mini-links CLEAN once the unit's eight data
  symbols are appended (session-local) to the GENERATED table with
  absolute:true - wire_split.py now does that step (curated file stays the
  durable source; gp_flags.py reads only config/symbols.slps_00270.txt).
- SIZE built 1752 vs retail 1732 (+5 insns). First diffs open at the
  prologue bind interleave (LAW 2: ours interleaves saves/binds, retail
  keeps all six saves ahead of every bind) and cascade; 419/433 words.
- Div1's correction folds differently: ours `addiu v0,P,0x21ff` (t+bias
  re-derived from the size register), retail `addiu v0,T,0x1fff` (reads t's
  register) - the (mem sp+0x44) quantity-invalidation timing decides; expect
  it to follow the prologue-order fix.
- The div2 region itself: shape-exact. The +20 bytes live in the fill-loop
  shape (ours countdown `li 0x1ff/.../bgez`, retail up-counter sltiu form,
  LAW 3) and the tail scheduling (LAW 5).
- Tree REVERTED per commit-only-on-green (RULES 4.1): yaml + giant asm +
  generated table restored, tail .s and src/ removed. The wiring is now ONE
  command: `python3 scripts/bm_unit_decode/wire_split.py
  scripts/bm_unit_decode/variants/v6_w1_size_div.c`.

NEXT WINDOW: the judge loop continues on the W1 base - (a) prologue
block-save form (LAW 2; the 1034 iteration matrix + the correction-folding
observation above), (b) fill loop (LAW 3), (c) tail + epilogue (LAW 5) and
the -1 register (LAW 4, likely self-resolves), then the sces twin
func_8002ABC8 (expect only scheduler deltas). Landing = split + srcs +
converged loop; the ratchet gate (652/60) keeps the split out of the tree
until convergence.

## JUDGE LOOP PROGRESS (cron-202610261419): THE FILL-LOOP LAW CLOSES

Window shape: rehydrate OK; HEAD was behind (rollback-era clone) -> reset to
87a9e62e; worklog_digest exit 1 (135 windows missing: the ancient worklog
snapshot plus the other agents' landed TASKS records) -> RESTORE NOTE
appended verbatim per SOP, re-run exit 0. Disc-return #32: links still valid
(expire ~09:53 UTC), both CHDs foreground-downloaded + sha256-gated,
per-sector extracts, witness 8/8 STRICT, verify 8/8 GREEN before any wiring.

THE ITEM (NEXT WINDOW (b) of cron-202610261304): the fill-loop law (LAW 3)
hunted through three screened forms + one wired judge run.

LAW 3 CLOSES ON THE COUNTER'S TYPE. The retail fill loop (up-counter,
per-iteration base materialization, sltiu bound, the 0xff constant and the
'S' 0x53 header constant riding the loop's delay slots) is reproduced when
the fill counter is UNSIGNED:

    unsigned int i;   /* not int */

    for (i = 0; i < 0x200; i++)
        D_8006974C[i] = 0xFF;

v7 (W1 + unsigned i) head screen: `move v1,zero / lui at,%hi / addu at,at,v1 /
sb a3,0(at) / addiu v1,v1,1 / sltiu v0,v1,0x200 / bnez v0 / li v0,0x53` - the
signed `int i` compile instead strength-reduced the loop into the countdown
pointer walk (li v1,0x1ff ... bgez with the pointer decrement in the bgez
slot), the pre-v7 diff. The `i != 0x200` bound form (v8) emits bne-against-
0x200 with a nop slot (wrong shape); moving the div block after the fill
loop (v9) degrades the prologue further (size into t0, div1 before-copy
form) - both falsified.

JUDGE v2 (wired v7, judge_unit slps_00270): SIZE built 1752 vs retail 1732
(+5 insns, unchanged - both loop forms are 8 insns; the +20 bytes live in
the tail scheduling LAW 5 and LAW 2's cascade), first diffs still open at
the prologue interleave. The fill-loop SHAPE is now retail's; the remaining
diff regions are LAW 2 (prologue block saves + the size-load register) and
LAW 5 (tail + epilogue).

LAW 2 REFINED (v10 falsification): the t-based test form (`t != t/0x2000*
0x2000`) MERGES the second division again even on the v7 base (one chain,
the 4-byte class shrink) - the div2 operand must stay the RAW size param
(W1), and the prologue's size-load register (ours a3/t0 scratch vs retail
v1) is downstream of the pseudo graph that W1's double size read creates.
Note the retail div2 copy reads v1 (t's register) while W1's reads the size
scratch - the convergence path likely runs through statement-order and
reload-timing levers (e.g. `int t; t = size; t += 0x200;` making the first
size read a plain copy into t's home), not through the test's operand.

Tree REVERTED per commit-only-on-green. Variants v7/v8/v9/v10 snapshotted in
variants/. Wiring remains ONE command: wire_split.py <candidate.c>.

NEXT WINDOW: (a) LAW 2 hunt - block-save prologue forms (the scheduler
interleave follows the pseudo graph; candidates: the `t = size; t += 0x200;`
split, a first-statement order that binds s-regs in retail's order);
(b) LAW 5 tail + epilogue scheduling (the +20 bytes); (c) then the sces twin
func_8002ABC8 (expect only scheduler deltas). Landing = split + srcs +
converged loop (ratchet-gated until the loop closes).

## JUDGE LOOP PROGRESS (cron-202610261649): THE CORRECTION-FOLDING LAW CLOSES; THE DIV2 OPERAND PARADOX IS NOW EXACT

Window shape: rehydrate OK; rollback had reset HEAD to 7623cd2 and eaten the
worklog restore note too -> reset to ee26f762, RESTORE NOTE re-appended
(136 windows), digest exit 0. Disc-return #33: disk/ empty again, links still
valid (expire ~09:53 UTC, ~1h left), CHDs foreground-downloaded + gated,
per-sector extracts, witness 8/8 STRICT, verify 8/8 GREEN before any wiring.

THE ITEM (NEXT WINDOW of cron-202610261419): LAW 2 (prologue block saves +
size-load register) via the `t = size; t += 0x200;` split candidate, plus a
systematic falsification sweep of the div2 operand classes.

THE CORRECTION-FOLDING LAW CLOSES (v11). The 1304 prediction ("our div1
correction folds 0x21ff from the size register vs retail's 0x1fff from t's
register; expect it to follow the prologue-order fix") is REFIRMED-REVISED:
it follows the T-SPLIT, not the prologue. `int t; t = size; t += 0x200;`
loads size directly into t's home v1 (`lw v1,0x44(sp)` first insn) and the
div1 correction becomes `addiu v0,v1,0x1fff` FROM V1 - retail's exact fold.
Cost: one extra insn (the size scratch copy `move a3,v1` that div2's
size-operand read now needs) - judge v3 wired v11: SIZE 1756 vs 1732, DIFF
427/433, prologue still interleaved (now with the lw hoisted to insn 1).

THE FALSIFICATION MATRIX (all on the v7 unsigned-i base, head-screened):
- v12 `u = t` copy BEFORE div1, test both sides u: MERGED (one chain).
- v14 `u = t` copy AFTER div1, test both sides u: MERGED.
- v15 t eliminated, both divs + LHS on the raw `(size + 0x200)` expression:
  MERGED (the expression CSEs to one temp; div2 shares div1's quotient).
- v16 `size += 0x200` in place, both divs on the updated param: MERGED.
- v18 div1 + LHS on the `(size + 0x200)` expression, div2 on RAW size:
  SURVIVES - but the shape is W1's (div2 copy reads the param scratch a3,
  div1 correction folds 0x21ff from a3). No gain over W1.
- (v10, last window: t-based test on the v7 base: MERGED.)

THE OPERAND LAW (strengthened): the second division survives IFF its
operand is the RAW SIZE PARAM (its own pseudo, distinct from the t
expression's temp). EVERY t-valued class merges: plain variable (W1 base),
copy variable before or after div1 (v12/v14), inline expression (v15),
in-place `size += 0x200` (v16).

THE PARADOX (now exact, for the next window): retail's div2 copy reads V1 -
T's register - while every surviving screened form's copy reads the PARAM
SCRATCH (a3/t0). No screened C form can read v1 there: the param-operand
class always materializes the param in its own scratch, and every t-valued
operand merges. The reconciliation must come from gcc 2.6.3's actual
mechanics, not more screening. NEXT WINDOW LEAD (mechanized): read the
LOCAL gcc-2.6.3-psx source and answer three questions exactly:
  Q1 cse.c: does a REG=REG copy insn create a quantity equivalence that
     canonicalizes a later div's REG_EQUAL note (v12/v14 say behaviorally
     yes - find the code path)?
  Q2 expmed.c expand_divmod: what decides copy-before-branch vs
     copy-in-delay-slot for the branchy signed path, and what op0 RTL goes
     into the REG_EQUAL note (the original operand or the temp)?
  Q3 what RTL does `param += const` expand to (in-place on the param's
     pseudo, or a fresh pseudo)?
Then re-derive the retail form from the answers and screen it.

LAW 5 (tail + epilogue, the +20 bytes) untouched this window - the head
consumed it. Tree REVERTED per commit-only-on-green; variants v11-v18
snapshotted; suite 85/85; ratchets 644/0.

## JUDGE LOOP PROGRESS (cron-202610261804): THE DIV2 PARADOX IS REDUCED TO ONE CSE BEHAVIORAL PARAMETER

Window shape: oracle DOWN (rollback ate the discs + baselines are the Oct-10
woven-era set, witness 0/8; Silent's links EXPIRED ~09:53 UTC) -> offline
window by design. worklog_digest.py is GONE (local-only tool, not in git -
rollback ate it; flagged to Silent). Reconstructed the retail head from the
REPO ITSELF: asm/nonmatchings/func_8002ADA0.s (the pre-carve giant row) is
git-tracked retail disassembly - NO baseline needed to pin the head.

THE RETAIL HEAD IS NOW FULLY PINNED (B5A0..B60C, all three divisions):
- t-split CONFIRMED in retail: lw v1,0x44(sp) (size into t's home) ...
  addiu v1,v1,0x200 IN PLACE. v11's shape is retail's.
- div1 TIGHT: bgez v1 / [delay: addu v0,v1] / addiu v0,v1,0x1fff (correction
  reads t's home) / sra v0,13 / sll a0,v0,13. v11 already reproduces this.
- div2 LOOSE: addu v0,v1 (THE PARADOX COPY - reads T'S HOME, value = t, NOT
  raw size!) / bgez v0 (branch on the COPY) / nop / addiu v0,v0,0x1fff
  (correction reads the COPY, unstacked 0x1fff) / sra v0,13 / sll v0,v0,13.
- test: beq v1,v0 - LHS = t ITSELF, RHS = div2's product.
- div3 (total/0x2000, the sector byte): loose, delay slot FILLED with the
  strcpy-dst addiu, correction from the copy. A DIFFERENT operand value
  (total), so no merge with div1/div2 - consistent.
- SEMANTICS FIX: retail's test is T-BASED (t != t/0x2000*0x2000 class), not
  size-based. Proof: t = size+0x200; size is DEAD after the in-place addiu
  (no copy of raw size exists before it); div2's copy reads v1 = t. The
  0x1E00 counterexample separates the two tests. W1/v11's C
  (t != size/0x2000*0x2000) is the WRONG SOURCE SEMANTICS.

THE MECHANISM (closed by -da RTL dumps on the local cc1, v19):
- Expansion (pre-CSE) emits EVERY branchy signed division as the LOOSE
  form: [W = op0; bgez W; addiu W,W,0x1fff; sra W] with REG_EQUAL note
  (div:SI op0 8192) on the sra. Two divisions = two independent sequences.
- The TIGHT form is CSE's WORK, not the expansion: cse canonicalizes the
  branch's compare operand and the correction's input through the
  copy-equivalences (W's qty = op0's qty -> rewire to op0's home), then
  dbr-schedule sinks the now-branch-independent copy into the delay slot.
- THE MERGE: div2's note (div u_pseudo 8192) folds through the u->t copy
  equivalence to (div t_pseudo 8192) = div1's recorded qty -> the whole
  div2 sequence dies, the test's RHS becomes div1's product (beq v1,a0).
  v19's .cse dump shows this exactly (4 sra -> 3 sra across cse-main).
- -fcse-skip-blocks governs whether the taken-path table crosses the
  division's own join (bgez target): ON = note fold completes = merge;
  OFF = fresh table at the join = note fold fails = div2 SURVIVES.

THE FALSIFICATION MATRIX EXTENDED (all offline screens, no oracle):
- v19 (u = t after div1; test t != u/0x2000*0x2000): default O2 MERGED;
  -fno-cse-follow-jumps MERGED; -O1 div2 survives TIGHT (both divs tight,
  u-copy eliminated); -fno-cse-skip-blocks div2 survives TIGHT (branch
  REWIRED to v1); both flags off div2 survives TIGHT. The u->t chain is
  canonicalized IN EVERY CONFIG - the copy never survives as the branch's
  operand.
- v20 (t-split + test LHS and div2 both on the (size+0x200) expression):
  default MERGED (plus the 0x21ff stacked-correction artifact);
  -fno-cse-skip-blocks div2 survives LOOSE but the operand RECOMPUTES
  (addiu v0,a3,512 from the force-mem param home) and the correction
  STACKS (addiu v0,a3,8703) - the fresh join table cannot fold the
  expression to v1's qty.
- v21 (t-split + LHS = t, div2 operand = the (size+0x200) expression):
  default MERGED; -fno-cse-skip-blocks div2 survives LOOSE, branch on the
  materialization, but operand = recompute-from-a3 + 0x21ff + the delay
  slot filled with the taken-path sra (5-insn shape). NOT retail.

THE WALL (the exact remaining divergence): the local cc1 canonicalizes
div2's branch/correction operands through copy-chains UNCONDITIONALLY
(same-block chain u->t recorded anywhere visible -> rewire). RETAIL's
compile left div2's branch ON THE COPY (loose) with an UNSTACKED
correction reading the copy. Under every (source, flags) combination
tested, the local compiler either merges div2 or rewires it tight. Retail
did neither. The copy survives in retail => its uses were never rewired =>
the copy-equivalence was never in cse's table at div2's insns => either
(a) the retail cc1's cse.c lacks/weakens the compare-canonicalization
through copies (patch-level difference - but the local cc1 IS "2.6.3 [AL
1.1, MM 40] Sony Playstation" from decompals/old-gcc 0.12, presumably the
retail family), (b) a flag we haven't found disables it, or (c) retail's
copy was created post-CSE (reload/regmove) from a pseudo whose CSE-time
qty was unconnected to t. gcc-2.6.3 SOURCE IS NOT LOCAL (tools-local has
binaries only; the aaca343d "local gcc source" lead was wrong) - ftp.gnu.org
timed out, mirrors 404'd; the -da dumps substitute for most of it.

NEXT WINDOW LEADS (mechanized):
1. Diff the -da dump CHAIN (rtl/jump/cse/loop/cse2/flow/combine/lreg/greg/
   sched/sched2/dbr) for v21-no-skip-blocks: find WHICH pass rewrites the
   correction's input (the 0x21ff stack) and whether cse2/loop change the
   div2 region. The .dbr dump explains the delay-slot sra trick.
2. Test -O1 with selective O2 flags re-enabled (-fexpensive-optimizations,
   -fschedule-insns) hunting a config where div2's branch keeps its own
   register: the -O1 result (both tight) + skip-blocks-off (loose but
   recompute) bracket the retail shape from two sides.
3. Fetch gcc-2.6.3 source via a working mirror (kernel.org, ibiblio,
   uk.gnu.org) or the decompals/old-gcc repo if it carries patches; read
   cse.c's compare canonicalization (fold_rtx on SET_SRC/COMPARE) and
   check for a psx-fork diff against vanilla 2.6.3.
4. THE C-FORM DECISION: the t-based test is RETAIL'S SEMANTICS - when the
   loop closes, the landed C must use it (v19-class), NOT W1's size-based
   test. The landing gate stays: converged loop or nothing.
5. Disc-return #34: witness 0/8, links expired - request fresh links (the
   discs ARE missing AND needed: verify, judge, and every baseline
   consumer are gated).

Variants v19_mixed_u.c / v20_expr_test.c / v21_expr_on_t.c snapshotted in
variants/. Tree untouched (screens compile to build/judge only). Suite +
ratchets not run this window (offline research only) - nothing
build-adjacent touched.

## JUDGE LOOP PROGRESS (cron-202610261919): THE DIV2 REWIRE IS ALL CSE, AND THE SOURCE IS FINALLY LOCAL

Window shape: oracle DOWN (rollback left the Oct-10 woven-era baselines in
place - they match the PRE-FLIP oracle, witness 0/8; Silent's links EXPIRED
~09:53 UTC) -> offline window. worklog_digest exit 1 (138 windows missing -
the rollback restored the ancient worklog snapshot) -> RESTORE NOTE appended,
digest exit 0 (the digest tool itself is now rollback-proof: a0f77df2 put it
IN-repo, so every reset --hard restores it - the cron-202610261804 "flagged
for Silent" item is RESOLVED). HEAD was behind (7623cd2 -> aa3c98a4: the two
intervening windows closed the correction-folding law on the t-split and
reduced the div2 paradox to one cse parameter) -> reset forward, tree clean.

ITEM (2) DONE - THE FLAG BRACKET (scripts/bm_unit_decode/flag_bracket.py,
new tool): v21 across 13 regimes. THE MERGE IS GOVERNED BY EXACTLY ONE FLAG:
-fcse-skip-blocks (ON: default-O2, O1+skip, O1+exp+skip, O1+all-O2 -> test
becomes `beq v1,a0`, div2 gone). OFF: div2 survives in EVERY other config
INCLUDING plain -O1 - as the a3-RECOMPUTE class (operand addiu v0,a3,512,
stacked correction addiu v0,a3,8703). -fexpensive-optimizations,
-fschedule-insns/-insns2, -fthread-jumps, -fcse-follow-jumps,
-fstrength-reduce, -fcaller-saves: ZERO effect on the div2 region. NO flag
regime produces the retail loose-copy shape. (The v20 falsification "at
-O1" in the 1804 record was really a no-skip-survival - re-read the -da
evidence below.)

THE NEVER-SCREENED FORMS (v4/v20 at no-skip, first time): v4-inline
(`t != t/0x2000*0x2000`, op0 = t's pseudo) at -fno-cse-skip-blocks ->
div2 REGISTER-COUNT-RETAIL but TIGHT (bgez v1 / move v0,v1 in the delay
slot / addiu v0,v1,0x1fff reading the source) - the canonicalized form.
v20 at no-skip -> BOTH corrections as the stacked recompute (a3+0x21ff)
while the branches stay on the fresh operand - the expression-qty form.
LAW: the canonicalization target = the qty of the div2 operand pseudo:
reg-link qty -> tight (v4/v19-class); expression qty -> recompute
(v20/v21-class). Retail = NO canonicalization at all (branch + correction
on the copy, nop slot).

ITEM (1) PARTIAL - THE -DA CHAIN (v4, no-skip; pass order rtl -> jump ->
cse -> flow -> combine -> loop -> cse2 -> jump2 -> lreg -> greg -> sched
-> dbr -> sched2): EXPANSION EMITS THE RETAIL DIV2 SHAPE EXACTLY -
insn 45 (set (reg 89) (reg/v 79)) copy, jump 47 (ge (reg 89)) branch on
the copy, insn 49 (plus (reg 89) 8191) correction on the copy (the copy
PRECEDES the branch = the loose form). THE REWRITE IS ALL CSE: at .cse
the branch reads (reg/v 79) and div1's correction is FOLDED to
(plus size 8703) (8191 count 3->2, 8703 0->1). COUNTS IDENTICAL ACROSS
ALL TEN LATER PASSES - flow/combine/loop/cse2/jump2/lreg/greg/sched
NEVER touch the region; the delay-slot copy sink = dbr's work. There is
no post-CSE escape hatch in the local cc1.

ITEM (3) DONE - THE SOURCE IS LOCAL: gcc-2.6.3.tar.bz2 fetched from
https://gcc.gnu.org/pub/gcc/old-releases/gcc-2/gcc-2.6.3.tar.bz2 (the
404s were the missing gcc-2/ level; ftp.gnu.org and every /gnu/gcc/
mirror prune 2.6.3, but gcc.gnu.org's old-releases/gcc-2/ still has it),
extracted at tools-src/gcc-2.6.3-src/gcc-2.6.3/ (untracked). THE RULE
(cse.c canon_reg, line 2456): fold_rtx on a pseudo REG operand returns
qty_first_reg[reg_qty[regno]] - THE FIRST REGISTER OF THE QUANTITY -
UNCONDITIONALLY (hard regs exempt). The copy (set reg89 reg79) links
reg89 to t's qty via insert_regs -> make_regs_eqv (the folded src's
class contains a REG -> merge, line ~1017). qty_first_reg = t's pseudo
-> the div2 rewrite is INEVITABLE in vanilla 2.6.3 once the operand's
defining SET is a reg-to-reg copy whose src has a live qty. For retail's
div2 to stay on the copy, the operand's SET must NOT have merged into a
reg-linked qty: the only vanilla paths are (a) the folded src was NOT a
plain REG (an expression class with no REG element -> make_new_qty for
the dest -> qty_first_reg = the copy ITSELF), or (b) the src's qty was
invalid with no REG in its class. The v21-class recompute IS path (a):
branch stays LOOSE (reads the recompute's result reg = "the copy") but
the correction still folds through the expression to a3+8703. RETAIL
THEREFORE REQUIRES BOTH: an OPAQUE operand SET (no expression in the
class -> the correction stays +0x1fff on the copy) AND no cheaper
register source to re-derive from (no size register - which the REAL
block-save prologue provides: size loads straight into v1 from 0x44(sp),
so the only re-derivation is a mem-based expr, costlier than the copy).
THE WALL IS NOW A C-FORM HUNT, NOT A FLAG HUNT: find the C that makes
the div2 operand's SET opaque-or-unlinked while keeping the t-split.

NEXT WINDOW:
1. -da chain on v21-no-skip (the banked lead, still open): does the div2
   SET merge with t's qty or make a fresh qty; at which insn does the
   recompute-entering rewrite happen; does the class of (plus size 512)
   hold a REG at div2's SET (it must NOT, for the fresh-qty path).
2. Read cse_insn's correction-fold + use_related_value to pin why v21's
   correction folds to (plus a3 8703) while v4's stays (plus 79 8191).
3. Design + screen the C-form candidate from the qty-boundary rule
   (operand SET opaque / unlinked; t-split kept; t-based test kept).
4. Disc-return #35 when fresh links arrive - the judge loop is the only
   path to convergence; the flag regime CANNOT close it (proven above).

Tree untouched (screens + dumps live in build/judge/). flag_bracket.py
committed (full-head mode is authoritative; the window classifier is
advisory only - div1's sll can sink into div2's delay slot at -O1 and
break the window anchor). Variants unchanged (v0-v21). Suite + ratchets
not run this window (offline research only, nothing build-adjacent).

## JUDGE LOOP PROGRESS (cron-20261026-1349): THE JOIN-BOUNDARY LAW CLOSES - THE FIRST LOOSE+UNSTACKED DIV2 SURVIVOR IS SCREENED

Window shape: oracle DOWN (witness 0/8, disk/ empty, Silent's links expired
~09:53 UTC; disc-return #35 still pending) -> offline window by design.
worklog_digest exit 1 AGAIN (a fresh rollback restored the ancient worklog
snapshot AND ate the 1235 restore note) -> RESTORE NOTE appended, exit 0.
HEAD was behind (7623cd2 -> c00c90a5, the 1919 landing) -> reset forward.
The vanilla gcc-2.6.3 source (1919's extraction) was also rolled back
(it lived in /tmp) -> re-fetched from gcc.gnu.org old-releases, now kept at
tools-src/gcc-2.6.3-src/gcc-2.6.3/ under /home/z (rollback-resistant).

ITEM (1) DONE - THE -DA CHAIN ON v21-no-skip (scripts/bm_unit_decode/
da_chain_div2.py, new tool; every pass rtl->jump->cse->loop->cse2->flow->
combine->sched->lreg->greg->sched2->jump2->dbr): THE DIV2 SET MAKES A FRESH
UNLINKED QTY, AND THE RECOMPUTE-ENTERING REWRITE IS CSE'S CORRECTION FOLD.
The .cse dump prints the block cut: "Processing block 2..36" ends at
div1's join label; the div2 region (45 materialization, 47 copy, 49 branch,
51 correction) lives in the NEXT block 37..52 - the t-split's addiu and
t's qty are in the DEAD previous block. At block start new_basic_block()
(cse.c:760) flushes the table AND resets reg_qty to self (= INVALID:
REGNO_QTY_VALID_P(N) = reg_qty[N] != N, cse.c:485). Expansion's insns:
45 (set 88 (plus 78 512)) - the expression materialization; 47 (set 90 88)
- the loose copy; 49 (ge 90) branch on the copy; 51 (plus 90 8191)
correction on the copy; the sra's REG_EQUAL note carries (div 88 8192).
AT .cSE: 45's dest flips 88->90 and 47 becomes (set 88 90) (make_regs_eqv's
first-reg liveness rule: the copy dest outlives the block via the sra at
insn 53, so it wins canonical form); the branch STAYS on 90 (fresh qty's
first reg - NO link to t/79 exists in this block); the correction FOLDS to
(plus 78 8703) - the class of 90's qty holds the expression (plus 78 512)
and fold_rtx's PLUS associativity + use_related_value re-derive it from
size's home a3 (cheaper: kills the dependence on 90's addiu). flow deletes
the dead flipped copy; cse2/combine/sched/lreg/greg/sched2 NEVER touch the
region (counts identical); dbr only fills delay slots. THE RECOMPUTE IS
BORN AT CSE, insn 51, via the expression entry created INSIDE the fresh
block at insn 45.

ITEM (2) DONE - THE v21-vs-v4 CORRECTION QUESTION CLOSES ON TABLE
REACHABILITY: use_related_value (cse.c:1760) can only fold through
expressions PRESENT in the CURRENT block's table. v21's operand-expression
entry is created post-join (insn 45, same block as the correction) ->
reachable -> the 8703 stack fires. v4's t-expression entry ((plus 78 512)
at t's creation) lived pre-join -> died at the boundary -> use_related_value
finds NOTHING -> the correction stays (plus 79 8191) unstacked on the
canonicalized reg. canon_reg (cse.c:2456) rewrites a pseudo operand to
qty_first_reg UNLESS the qty is invalid; insert_regs (cse.c:1001) gives a
folded-src REG with an invalid qty a FRESH qty (this is how a plain copy of
t REVIVES t's qty in the fresh block -> v4/v19-class tight), while an
EXPRESSION set makes an unlinked fresh qty (v21-class loose).

ITEM (3) DONE - THE C-FORM CANDIDATE EXISTS AND SURVIVES: v22
(variants/v22_u_prejoin.c = v7 base + the t-split + u = t BEFORE div1 +
test `t != u/0x2000*0x2000`), the NEVER-SCREENED v12-class corner at
-fno-cse-skip-blocks. SCREEN RESULT (no-skip): div1 tight-unstacked
(bgez v1 / [delay: move a3,v1] / addiu v0,v1,0x1fff), div2 = move v0,a3 /
bgez v0 / nop / addiu v0,v0,0x1fff / sra / sll - BRANCH ON THE COPY,
CORRECTION UNSTACKED ON THE COPY, test beq v1,v0 - THE RETAIL SHAPE, FIRST
FORM EVER TO SHOW IT. Mechanism: u = t is a reg-copy in the PRE-join block;
the join kills its link; in the fresh block the div2 copy (set 90 u) makes
a fresh qty from u's INVALID reg (no t-revival - nothing reads 79 there),
first_reg = 90 (u's last use is the copy itself; 90 outlives via the sra),
and the qty's class holds NO expression -> no fold. AT DEFAULT FLAGS v22
MERGES (beq v1,a0) - the regime dependence is real: RETAIL'S COMPILE =
skip-blocks-OFF EFFECTIVE REGIME + the u-severance form (the PSX cc1
driver/fork plausibly builds with the flag off; flag_bracket's 13-regime
matrix showed ON = merge in every other respect).

REMAINING DELTAS (judge-loop material, NOT screen-material): (a) div2's
copy reads a3 (the u-copy sunk into div1's delay slot by dbr) where retail
reads v1 DIRECTLY - both remaining deltas resolve if u's pseudo coalesces
into t's hard reg (then the u-copy vanishes, div1's own W copy takes the
delay slot exactly as retail's addu v0,v1, and div2's copy reads v1);
coalescing is a local-alloc/reload outcome driven by pressure - the REAL
prologue (LAW 2 context) is the testbed, screens cannot weigh it;
(b) one stray dead copy (div1's canonicalization leftover, move v0,v1
before the branch) - expected to follow the same coalescing; (c) LAW 2
(prologue interleave) and LAW 5 (tail + epilogue, the +20 bytes) untouched.
THE LANDING C MUST USE: the t-split + u-severance + the t-based test +
unsigned i (NOT W1's size-based test - retail semantics are t-based, and
the div2 operand is the JOIN-SEVERED copy, not the raw param).

NEXT WINDOW: (1) judge v22 the moment the oracle returns (disc-return #35:
the judge loop is the ONLY arbiter of the coalescing deltas; SIZE/DIFF +
the head 30 vs retail); (2) if the judge keeps the a3-vs-v1 delta, screen
one-use-coalescing nudges (u's def as the function's FIRST statement,
renaming pressure) - still C-only, no flags; (3) LAW 5 tail hunt continues
offline (the +20 bytes sit in the tail law + the epilogue); (4) when fresh
links arrive: witness 8/8 -> verify 8/8 GREEN -> judge v22 wired via
wire_split.py (ratchet-gated, commit-only-on-green).

Variants v22_u_prejoin.c snapshotted; da_chain_div2.py lands (dump-chain
window tool); tree untouched (screens + dumps in build/judge/ only). Suite
+ ratchets not run (offline research only, nothing build-adjacent).

## LAW 5 PROGRESS (cron-202610262304): THE EPILOGUE CONVENTION IS PER-PROVENANCE - THE RULE-1 K>=4 GENERALIZATION IS PROVEN BYTE-INERT AND SAFE, AND THE V22 TAIL DELTAS ARE ENUMERATED

Window shape: the 1235 sandbox tool outage ENDED (probe first, per the
blocked-window protocol). HEAD was behind (7623cd2 -> 657449e2: the
cron-20261026-1349 join-boundary landing was already on origin/main) ->
reset forward, tree clean. worklog_digest exit 1 (a fresh rollback restored
the ancient snapshot AND ate the 1235 capture files restore_digest/
restore_header_202610261235.txt) -> RESTORE NOTE appended verbatim from a
fresh capture, exit 0 (140 windows; the gate is green for the first time
since the rollback streak began). Oracle DOWN (witness 0/8, disk/ empty,
Silent's links expired ~09:53 UTC; disc-return #35 re-requested) -> offline
window: the 1349 NEXT-WINDOW item (3), the LAW 5 tail hunt.

THE EPILOGUE CONVENTION IS PER-PROVENANCE, NOT PER-SHAPE (new tool
rule1_corpus_scan.py): census every `lw $ra,N($sp)` epilogue window in every
landed asm row (5219 windows corpus-wide) by reload count k and frame-
release position. Game-code rows put the release in the BRANCH DELAY SLOT
at EVERY k - 622 swapped windows at k>=4, up to k=9 (e.g. func_80022AFC
rows); SDK/ASPSX rows keep GCC order at every k - 567 gcc-order windows at
k>=4 (the LIBGT/0x8004xxxx-0x8006xxxx regions). The unit's shared epilogue
thunk func_8002B444 (pinned in the giant row: lw ra/s4/s3/s2/s1/s0, jr ra,
addiu sp,sp,0x28 IN the branch slot, no trailing nop) is the k=6 SWAPPED
form - the form rule 1 exists to reproduce, currently out of its k<=3 reach.

THE C-TREE AUDIT (new tool epilogue_audit.py): compile ALL 240 src units
offline through cc.sh and census the PRE-cc_post maspsx epilogue windows.
Result: k=0 x92, k=1 x10, k=2 x2, k=9 x1 - EXACTLY ONE unit produces a
k>=4 epilogue, SsSeqCalledTbyT (k=9, gcc order, LIBSND SSCALL member,
c-row in all eight targets, no asm row - oracle-gated), and its source
ALREADY carries `cc-post: sdk-aspsx` (which implies keep-epilogue, so rule
1 is disabled for it entirely). Every other C epilogue sits at k<=3 inside
rule 1's current reach. The name-based census's two apparent C-tagged
gcc-order k>=4 counterexamples (func_8004DB08 g3_eu, trapIntrDMA
func_80068248 mainmenu_eu - both LIBETC INTR members) resolve as
ASM-provenance in those targets (their yaml c entries are different, larger
sdk extents elsewhere): the same symbol is c in one build and asm-sdk in
another, and the asm rows carry the gcc-order retail bytes.

THE LANDING RECIPE (build-affecting, so verify 8/8-gated; provably
byte-inert until the unit's split lands): (1) generalize rule 1's swap to
[lw $ra][lw $rX]{k>=2}[addu $sp][j $ra](nop)? -> [lws][j $ra][addu $sp]
with the trailing nop absorbed - the k=1 base case keeps its own nop after
the ra reload (its retail form is [lw ra][nop][j][addu], distinct from the
k>=2 no-nop form); (2) NO marker work needed - the lone k>=4 C unit is
already sdk-aspsx-exempt; (3) the generalization changes nothing on today's
tree and activates only for func_8002ADA0's game-code k=6 thunk.

THE V22 TAIL MAP (tail_screen.py lands; NOTE its end-aligned diff is noisy
when the block ORDER differs - read it next to a raw objdump of the built
unit): the deltas vs the retail tail enumerate as - (a) the epilogue-thunk
convention itself (fixed by the recipe above; retail k=6 swapped, ours
gcc-order + trailing nop); (b) the -1/0x200 register pair: retail holds -1
in s1 from the prologue era and materializes 0x200 ONCE into s2
(`ori s2,zero,0x200` right after write's delay slot) for BOTH the write and
read compares; ours materializes -1 into s2 LATE (at the first fd test),
saves write's ret into s1 (`move s1,v0`) and value-propagates it into
read's compare (`beq v0,s1` - the compiler knows s1 == 0x200 there); the C
is already the right SHAPE (direct compares, no result variables), so this
is register-assignment/coalescing class - the REAL prologue's pressure is
the testbed, judge material; (c) D_8006974C's address: retail re-derives
`lui a1/%hi + addiu a1/%lo` at EACH of write and read, ours caches it in
s3 once (`lui s3/addiu s3/move a1,s3`) - same class as (b); (d) the -3 err
path: retail shares ONE 0xC block (func_8002B438: jal close/addu a0,s0/
addiu v0,-3) targeted by BOTH `bne v0,s2` sites, ours inlines a close+
return site per failure with flipped branch polarity (beq-to-ok instead of
bne-to-err) - cross-jump/layout outcome; (e) return-2: retail emits
`j func_8002B444 / ori v0,2` from mid-body, ours falls through into the
inline epilogue after `li v0,2` - same layout class as (d).

NEXT WINDOW: (1) disc-return #35 -> witness 8/8 -> verify 8/8 GREEN ->
land the rule-1 k>=4 generalization (the recipe above) -> judge v22 wired
via wire_split.py (ratchet-gated, commit-only-on-green; the judge is the
only arbiter for deltas (b)-(e)); (2) if the judge keeps the (b)/(c)
register deltas, screen one-use/renaming/redeclaration nudges; (3) LAW 2
block-save hunt continues offline; (4) the sces twin func_8002ABC8 after
the slps unit closes.

Tree untouched (three tools land under scripts/bm_unit_decode/ only:
rule1_corpus_scan.py, epilogue_audit.py, tail_screen.py; screens compile
into build/judge/ only). Suite 85/85 OK; ratchets not run (nothing
build-adjacent moved). Restore note re-appended (third attempt; the 1235
capture files were rollback-eaten, a fresh capture was used).

## LAW 2 CLOSES ON SCHEDULE-INSNS2 + THE TAIL-NUDGE FALSIFICATION MATRIX (cron-20261027 window)

Window shape: oracle still DOWN (witness 0/8, the woven-era baselines match
the PRE-FLIP oracle; disc-return #35 still pending) -> offline window.
Executed the 2304 NEXT-WINDOW items (2) and (3): the one-use/renaming/
redeclaration nudge screens for the v22 tail deltas, plus the LAW 2
prologue hunt. New tool: head_tail_matrix.py (variant + cc1 flags ->
total insns + prologue 16 + tail 42 read-out).

LAW 2 (PROLOGUE SAVE-BLOCK) CLOSES ON -fno-schedule-insns2: our default
compile interleaves saves and binds (lw v1,size hoisted BEFORE any save;
ra saved 12th, s1 last) - that interleaving is schedule-insns2's work.
Under -fno-schedule-insns2 the prologue becomes retail's exact save-block:
addiu sp / sw ra FIRST / sw s4,s3,s2,s1,s0 descending / THEN the binds
(s4<-a0, s2<-a1, a1<-a2, s3<-a3, lw v1,size, lw s0). Sizes: default 432,
no-skip 440, no-sched2 436, no-skip+no-sched2 442 (retail 433) - the two
flag laws are INDEPENDENT (skip-blocks governs the div2 head, sched2
governs the prologue save-block; the tail deltas survive all four regimes).

RESIDUAL PROLOGUE DELTAS (judge material): (i) bind order - retail binds
s3<-a3 and lw v1,size BEFORE s2<-a1; ours binds s2<-a1 first; (ii) ours
hoists move a1,a2 (str) into the prologue while retail binds str->a1 AT
THE STRCPY CALL SITE (delay slot addu a1,a2,zero) - a2 safely carries str
to strcpy in retail because NO call precedes strcpy; (iii) ours pads the
size-load interlock with a nop under no-sched2 while retail fills it with
the s2/s0 binds - the bind-order lever is upstream of scheduling.

TAIL-NUDGE FALSIFICATION MATRIX (all screened vs retail through
tail_screen/head_tail_matrix; sizes AND the discriminating registers are
INVARIANT): v23_decl_fd_first (renaming class: fd declared first),
v24_read_cmp_flip (one-use class: 0x200 != read(...) source-order flip),
v25_buf_redecl (redeclaration class: &D_8006974C[0] at read's site) -
each 432 default / 436 no-sched2 exactly like v22, -1 stays in s2, write's
ret stays saved into s1 with the const in v0, s3 keeps the address cache.
CONCLUSION: the (b)/(c) register deltas are NOT C-reachable by the three
nudge classes - they are allocator-cascade outcomes (real-prologue
pressure is the testbed); the judge remains the only arbiter.

REGIME FALSIFICATION (tail vs the div2 law's retail regime): v22 at
-fno-cse-skip-blocks does NOT realign the tail (440 insns, 60/60 tail
mismatch) - the skip-blocks law and the tail deltas are orthogonal; retail
cannot be both skip-blocks-off (div2 survives, +4) and 433 total unless
the judge finds compensating deltas in (b)-(e) + the epilogue recipe.
NEXT WINDOW (unchanged priorities, refined): (1) disc-return #35 ->
witness 8/8 -> verify 8/8 GREEN -> land the rule-1 k>=4 generalization ->
judge v22 under BOTH the default and the no-sched2 prologue regimes
(ratchet-gated, commit-only-on-green); (2) if the judge keeps (b)/(c),
the next lever class is the middle's pseudo pressure (the byte-exact
middle constrains every experiment - do NOT perturb it); (3) the sces
twin func_8002ABC8 after the slps unit closes.

Tree untouched (head_tail_matrix.py + v23/v24/v25 land under
scripts/bm_unit_decode/ only; screens compile into build/judge/ only).
Suite + ratchets not perturbed (offline research only, nothing
build-adjacent).

## THE GLOBAL-ALLOC CASCADE MECHANIZES THE REGISTER DELTAS (cron-20261027-0134 window)

Window shape: 79th rollback (HEAD -> 7623cd2, worklog stripped again -> RESTORE
NOTE re-appended, Task ID cron-20261026-1735-restore, exit 0; helper scripts
also eaten and re-created). Oracle still DOWN (witness 0/8, disc-return #35
pending) -> offline window: the queued "middle's pseudo pressure" lever
research, executed as a -da/reload mechanization of the str->a1 hoist and the
-1 register choice. New tool: str_chain.py (compiles with -da, finds the
strcpy call + str's pseudo in the expansion dump, tracks it across all passes
and prints global-alloc's own commentary).

STR'S PSEUDO (judge delta (ii), mechanized): str = pseudo 73, a textbook
move-chain - insn 8 (set 73 <- a2) [entry bind, a2 dead after] and insn 133
(set a1 <- 73) [the strcpy arg setup, 73 dead after]. The greg dump states
"73 preferences: 5 6" (set_preference in global.c records BOTH move
endpoints) and "73 conflicts: ... 2 4 7 29" - NEITHER endpoint hard reg is
conflicted, so global-alloc picks from {5,6}: ours = 5 (a1), making the
entry bind the surviving copy (move a1,a2 in the prologue) and the call
setup a deleted no-op. Retail's a2 outcome needs hard reg 5 excluded at
73's allocation turn (45th of 48) - an earlier allocno holding/conflicting
a1 in retail's RTL - i.e. the allocation ORDER/CASCADE, not the C.

THE -1 REGISTER (judge delta (b), mechanized to the pass-0 REUSE rule):
-1 = pseudo 155, (set (reg:SI 155) (const_int -1)) with REG_EQUIV const,
tail-only live range. Post-reload it lands in s2 (18) although s1 (17) is
free and unconflicted ("155 conflicts: 71 82 155 162 163 2 4 5 6 29").
global.c find_reg runs TWO passes: pass 0 considers ONLY already-allocated
regs (never allocates a fresh one) minus regs_someone_prefers; pass 1
(only if pass 0 fails) scans in REG_ALLOC_ORDER/ascending. s2 was
allocated EARLIER (code's pseudo - disjoint live range, so shareable);
s1's holder (hdr's pseudo, 72/74/71 region) is allocated AFTER 155. So
pass 0 reuses s2 -> -1 shares the dead code's register. Retail's -1 in s1
implies the same rule under a different allocation ORDER (s2 not yet
allocated at -1's turn -> pass 0 empty -> pass 1 ascending -> s1).

CONCLUSION (strengthens the 1620 falsification): the str hoist, the -1/0x200
pair and (by the same rule) the s3 address cache are global-alloc cascade
outcomes - the pseudo SET + allocation ORDER from the byte-exact middle is
the input, not any local C form. The three C nudge classes are exhausted;
the judge (and only the judge) can weigh whether retail's cascade can be
reached from the same C, or whether the v22 shape IS the same-C optimum.
find_reg's two-pass semantics (reuse-first, never-fresh-in-pass-0,
someone-prefers exclusion) + set_preference's move-endpoint recording are
BANKED as the allocator's decision procedure for all future tail judging.

NEXT WINDOW (unchanged priorities): (1) disc-return #35 -> witness 8/8 ->
verify 8/8 GREEN -> land the rule-1 k>=4 generalization -> judge v22 under
both prologue regimes; (2) the sces twin func_8002ABC8 after the slps unit
closes; (3) if still offline: the allocation-ORDER input (allocno_order's
sort keys vs the middle's ref counts) is the next mechanization target.

Tree untouched (str_chain.py lands under scripts/bm_unit_decode/ only;
dumps compile into build/judge/ only). Offline research only, nothing
build-adjacent.

## THE ALLOCATION-ORDER INPUT CLOSES: ORDER 48/48 EXACT, DISPOSITIONS 45/48 REPLAYED (cron-20261026-1849 window)

Window shape: 80th rollback (HEAD -> 7623cd2 again; worklog stripped to the
cron-20261014-2112 tail -> RESTORE NOTE re-appended, Task ID
cron-20261026-1849-restore, exit 0; helper scripts re-eaten and re-created).
Discs still missing (disk/ empty, woven-era baselines, witness 0/8, links
expired, disc-return #35 still pending) -> offline window: the queued item,
the allocation-ORDER input (allocno_order's sort keys vs the middle's ref
counts), executed to a full mechanization on the vanilla 2.6.3 source +
-fda dumps. New tool: alloc_order.py (compiles a variant with -da, parses
.lreg's dump_flow_info + .greg, recomputes the order, replays find_reg).
Reference output banked at alloc_order_v22_out.txt (v22_u_prejoin, default
flags). The vanilla source re-mirrored at tools-local/gcc-2.6.3-src/gcc-2.6.3
(tarball sha256 71f67384...c140 re-verified; the tree is UNTRACKED and
rollback-vulnerable - re-fetch recipe stays in TASKS.md 2026-10-25 2058).

THE ORDER IS A DUMP READ-OUT: global.c dump_conflicts prints ";; N regs to
allocate:" listing allocno_reg[allocno_order[i]] IN ALLOCATION ORDER (merges
as +K, multi-reg sizes as (M)) - the .greg dump states the attempt sequence
directly, no re-derivation needed for future tail judging.

THE KEYS ARE A SECOND DUMP READ-OUT: allocno_compare = pri =
trunc((double)(floor_log2(n_refs) * n_refs) / live_length * 10000 * size),
sort DESCENDING, ties by ascending allocno (allocno index = ascending head-
pseudo order; qsort therefore deterministic). global-alloc consumes the
reg_n_refs / reg_live_length values set by flow_analysis and mutated only by
local-alloc's copy opts - and toplev.c:3111 calls dump_flow_info AGAIN for
the .lreg dump AFTER local_alloc and BEFORE global_alloc with NOTHING in
between, so .lreg's "Register N used X times across Y insns" lines ARE the
exact pri inputs. Aggregation (global.c 383-423): pseudo -> allocno iff
n_refs != 0, not local-alloc-assigned, live_length != -1; merges sum n_refs,
take max live_length; size = PSEUDO_REGNO_SIZE (SImode = 1); LL 0 -> -1
before sorting. MEASURED: computed order == dump order 48/48 EXACT for
v22_u_prejoin (the .flow dump's counts are the pre-combine view - the .lreg
one is the global-alloc view; use .lreg).

FIND_REG REPLAY (45/48 dispositions): used1 = fixed_reg_set when
calls_crossed == 0 / call_used_reg_set when > 0 (CRITICAL: the -1 pseudo
crosses 6 calls, so every call-clobbered GR is excluded for it - this, not
pass 0, is what walks the ascending scan to the first free call-saved reg)
+ static hard conflicts + DYNAMIC adds from earlier-allocated conflicting
allocnos (find_reg:1186-1190, after the dump is printed); pass 0 = reuse
only (regs_used_so_far = local-alloc regs + every earlier GLOBAL allocation,
find_reg:1179 - the pool grows turn by turn), pass 1 = plain ascending scan
(no REG_ALLOC_ORDER on mips); then the pruned-preferences override MOVES the
pick to an own-preferred reg when the pass pick is outside the set.

THE TWO CRITICAL ROWS REPRODUCE EXACTLY:
  * pseudo 155 (const -1, cc=6): pass 1 ascending -> 16 (dyn-conflicted by
    82), 17 (dyn-conflicted by 163, allocated the turn before) -> 18 = s2.
    The 1735 pass-0-reuse reading of the -1-in-s2 is SUPERSEDED: 18 was NOT
    in the reuse pool at 155's turn (entry pool = {2,3,5} only, no earlier
    allocno held 18); the actual rule chain is calls_crossed=6 ->
    used1=call_used_reg_set -> pass-1 ascending. The cascade conclusion is
    unchanged - 82->s0 (turn 7) and 163->s1 (turn 41) are higher-priority
    allocnos, i.e. order outcomes - and retail's -1 in s1 = the same rule
    under a retail order where 17 is still free at -1's turn.
  * pseudo 73 (str, cc=0): pass 0 = reuse pool - conflicts{2,4,7,29+dyn} ->
    candidates {5,18,19,20} ascending -> 5 = a1 (5 is in the ENTRY pool via
    a local-alloc-assigned pseudo and is also 73's own preference, so no
    override needed). Retail's a2 = the same pass-0 rule under a retail
    pool/conflict state where 5 is unavailable at str's turn (turn 45 of 48).

THE 3 RESIDUAL MISSES (turns 3/20/23) ARE COPY-PREF-DRIVEN: someone-prefers
(prune_preferences) IS modeled - rebuilt from the PRINTED (already-pruned)
preferences of conflicting lower-priority allocnos, reverse-priority scan,
size rule - and it alone fixes turn 37 (95: someone-prefers evicts the pass-0
pick, pass 1 ascends to 7 = the dump's answer). The dump never carries
hard_reg_copy_preferences, so someone-prefers rebuilt from printed prefs is a
conservative subset; the 3 misses are exactly the rows where a lower-priority
conflicting allocno's COPY-pref displaces the pass-0 pick. caller-saves and
the local-alloc kick-out do not fire in this unit.

CONCLUSION (closes the queued input-side item): the allocation order and 45
of 48 dispositions are now a PURE FUNCTION of dump-readable inputs
(n_refs, live_length, size, calls_crossed from .lreg; conflicts/prefs from
.greg) - the byte-exact middle pins the pseudo set, the keys pin the order,
the order + find_reg's rules pin the cascade. The C-reachable space was
already exhausted (1620 nudges falsified, 1735 cascade conclusion); this
window mechanizes the cascade's INPUT side end to end. The judge remains the
only arbiter of whether retail's cascade is reachable from the same C; when
it returns, its (b)/(c) deltas are PREDICTED: -1 in s2 unless retail's order
frees s1 at -1's turn, str -> a1 via pass-0 unless retail's pool lacks 5.

NEXT WINDOW (unchanged priorities): (1) disc-return #35 -> witness 8/8 ->
verify 8/8 GREEN -> land the rule-1 k>=4 generalization -> judge v22 under
both prologue regimes (the replay above predicts the deltas the judge will
see); (2) the sces twin func_8002ABC8 after the slps unit closes; (3) if
still offline: derive copy_prefs from the .lreg RTL (mark_reg/expand_
preferences semantics) to close the last 3 dispositions, or start the sces
twin prep. Tree untouched beyond scripts/bm_unit_decode (dumps compile into
build/judge/ only). Offline research only, nothing build-adjacent.

## THE PASS-0 POOL SEED CLOSES THE REPLAY: 48/48, AND THE COPY-PREF ITEM CLOSES AS UNNECESSARY (cron-20261026-2004 window)

Window shape: 81st rollback (worklog stripped -> RESTORE NOTE re-appended
verbatim, Task ID cron-20261026-2004-restore, exit 0; append_restore_note.py
and fetch_gcc263_src.py re-created; gcc-2.6.3-src re-mirrored, tarball
sha256 re-verified). HEAD advanced 7623cd2 -> 886a4de5 (a3088375 confirmed
ancestor; the 1735/1849 alloc-lane landings present). Oracle still DOWN
(disk/ empty, woven-era baselines, witness 0/8, links expired, disc-return
#35 pending) -> offline window: the queued copy-prefs item.

THE DISCOVERY (the queued item's premise was wrong, in a productive way):
global.c 331-359 initializes regs_used_so_far to
    call_used_regs | regs_ever_live | local-alloc renumberings
("we consider registers that do not have to be saved over calls as if they
were already used since there is no cost in using them") - the 1849 model
seeded the pass-0 pool with {local-alloc regs} ONLY, under-producing it by
the entire call-clobbered class. regs_ever_live is read off the .lreg RTL
(pre-prologue: mips emits the save block in machine_dependent reorg, AFTER
global-alloc, so the dump RTL is the exact ever-live view global-alloc saw)
= {2,3,4,5,6,7,31} - a SUBSET of call_used here. True seed =
call_used | local = {0..15,24..29,31} | {2,3,5} = 23 regs, not 3.

THE THREE RESIDUAL MISSES RESOLVE AS PLAIN PASS-0 PICKS under the true
seed: turn 3 (121) -> 6, turn 20 (81) -> 4, turn 23 (108) -> 8 - each the
ascending-first call-used reg outside used1 (their hard conflicts
{2,3,4,5,29}+dyn block 2-5, the conflict-free call-used scan starts at
6/4/8 respectively). NO someone change, NO copy-prefs. The 1849
"copy-pref-driven" reading is FALSIFIED.

THE COPY-PREFS ITEM CLOSES WITHOUT A TOOL: set_preference sets copy, prefs
AND full together in both branches (plain-REG src sets the copy bit; every
one-side-hard/one-side-global SET sets prefs+full); prune_preferences
prunes all three with ONE mask -> copy is a SUBSET of the printed
hard_reg_preferences; find_reg's copy-pref override reaches only the
ascending-first class-related free reg, which the prefs override reaches
too -> the printed-prefs override subsumes the copy-pref override's pick.
(full == prefs for SImode spans, so someone-prefers is exactly rebuildable
from the printed prefs modulo the matrix asymmetry - global.c 110:
"conflicts is not symmetric; a conflict between allocno's i and j is
recorded either in element i,j or in element j,i" - the dump prints the OR
of both directions, the rebuild over-approximates the C loop's
CONFLICTP(allocno, j) row test, and the 48/48 replay shows the
over-approximation never bites in this unit.)

MECHANISM UPGRADES + SURVIVORS: t2 (106->7) upgrades pass1+pref ->
pass0+pref (6 was a pass-0 candidate all along; the prefs override still
moves the pick to 7 = printed prefs). The 155->18 pass-1 reading SURVIVES:
at t42 the pool's call-saved members are {16,17} (global allocations t7 /
t41 - ever_live has NO call-saved regs pre-prologue) and both are
dyn-blocked -> pass-0 fails -> pass-1 ascending -> 18. 73->5 pass-0
SURVIVES (5 = local pool entry + own pref). mips.h tables banked:
FIXED_REGISTERS GR = {0,1,26,27,28,29} ($at IS fixed),
CALL_USED_REGISTERS GR = {0..15,24..29,31}.

LANDED: alloc_order.py pool-seed upgrade (parse_lreg_everlive off the .lreg
RTL, CALL_USED_FULL, merge-member exclusion from the local set) +
re-banked alloc_order_v22_out.txt at 48/48. Tree untouched beyond
scripts/bm_unit_decode (dumps compile into build/judge/ only); ratchets
644/0 = baseline, suite 85/85 OK.

NEXT WINDOW: (1) disc-return #35 -> witness 8/8 -> verify 8/8 GREEN ->
land the rule-1 k>=4 generalization -> judge v22 under both prologue
regimes (ratchet-gated, commit-only-on-green; the replay predicts the
deltas at 48/48 - the judge's (b)/(c) deltas remain ORDER outcomes, now
with the full pool model); (2) the sces twin func_8002ABC8 after the slps
unit closes; (3) if still offline: start the sces twin prep - the
alloc-side offline queue is now EMPTY (order AND dispositions both 48/48;
no remaining alloc-side item).

## THE SCES TWIN PREP: THE POOL MODEL GENERALIZES 50/50 AND LAW 2 CONFIRMS ON THE TWIN (cron-20261026-2004 window)

* alloc_order.py on func_8002ABC8.c: 50 allocnos, order EXACT, dispositions
  50/50 ON THE FIRST RUN - zero re-tuning; the corrected pool model
  (call_used | ever_live | local seed) generalizes across the boots.
  Critical rows identical: str = pseudo 73 -> 5 pass-0 (SAME pseudo number
  as slps); 72 -> 18, 74 -> 19, 71 -> 20. The twin's const -1 = pseudo 152
  (slps: 155), SAME pri 1612 (5 refs, LL 62), SAME disposition 18 = s2.
* head_tail_matrix on the twin: default 433 insns (= retail 433! slps
  default = 432), no-sched2 436 - the same +3 over retail as slps
  no-sched2. The default compile hits the retail TOTAL while interleaving
  the prologue (schedule2 shape); no-sched2 hits the retail SHAPE while
  +3 (the size-load interlock nop + bind order) - the same tension as
  slps, judge material unchanged in kind.
* LAW 2 GENERALIZES: the retail sces prologue (committed asm/sces_00269/
  nonmatchings/func_80027340.s:5185-5199) is the no-sched2 save-block
  EXACTLY: addiu sp,-0x28 / sw ra 0x24 / sw s4,s3,s2,s1,s0 0x20..0x10
  descending / binds after (s4<-a0, s3<-a3, lw v1,0x44(sp), s2<-a1,
  lw s0,0x38(sp)). The twin's bind-order delta (i) (s3<-a3 + size load
  before s2<-a1) and interlock (iii) (our no-sched2 nop at index 12)
  reproduce slps's residual delta sheet exactly.
* LANDED: alloc_order_twin_out.txt + twin_head_tail_default.txt +
  twin_head_tail_nosched2.txt (all under scripts/bm_unit_decode/). Suite
  85/85; ratchets untouched (nothing build-adjacent).
* NEXT WINDOW: on disc return, judge the twin under BOTH prologue regimes
  like slps (the 50/50 replay pre-predicts its cascade; expected deltas:
  bind order, the str->a1 hoist at the callsite, the size-load interlock
  - the same three).

## THE LIVE JUDGE VERDICTS (cron-20261027-0748 window - the discs returned)

* Phase A witness 8/8 STRICT first shot (Silent's 2026-10-27 06:29 links);
  Phase B verify 8/8 GREEN + suite 85/85 + ratchets 644/0 on HEAD
  (7224aee4, which already carries the Phase C rule-1 n-load patch - the
  runbook's Phase C acceptance is satisfied by that verify).
* HARNESS BUG FOUND + FIXED en route: wire_split_twin.py wrote the twin's
  yaml rows at VA low bits (0xABC8/0xB28C) instead of the +0x800 file
  offsets its own docstring records (0xB3C8/0xBA8C) - the judge then
  mini-linked the unit 0x800 low and sliced retail mid-previous-function
  (432/432 total mismatch, first word jal). Byte test on the returned
  baseline pinned the retail prologue addiu sp,-0x28 at file 0xB3C8 =
  VA 0x8002ABC8; the giant's own address comments (B3C8 8002ABC8) agree.
  Fixed in-script; the dry-run rehearsal validated the giant CUT (line
  based) but nobody had ever run the judge, so the offset defect was
  invisible until the oracle came back.
* LIVE VERDICTS (judge_unit, sha1-gated on the returned baselines):
  - slps func_8002ADA0 (v22_u_prejoin.c): default 426/431 words, built
    1724 vs row 1732 (-8); no-sched2 381/433, built 1736 (+4). First
    diffs: default diverges at +4 (save-order); no-sched2 diverges at
    +0x20 - the save-block MATCHES retail under no-sched2 (Law 2 live).
  - sces func_8002ABC8 (func_8002ABC8.c): default 144/432 words, built
    1728 vs row 1732 (-4); no-sched2 416/433, built 1740 (+8). First
    diffs: default diverges at +4; no-sched2 diverges at +0x20 (Law 2
    live on the twin too).
* READING: neither regime closes either unit - the pre-registered deltas
  (b)-(e) (the -1/0x200 pair, the D_8006974C/D_800693F4 cache, the shared
  -3 err block, the return-2 j-thunk layout) are REAL and live-only
  confirmed. NEW SIGNAL: the twin candidate is 2/3 exact under the
  DEFAULT regime (144/432) vs slps's 426/431 - the twin decode is much
  closer to retail than the slps v22 candidate; the slps unit's remaining
  work is the bigger lift.
* Both probes reverted per runbook after judging; tree back to HEAD +
  the wire-script fix.

## THE TWIN MUTATION MATRIX OPENS (cron-20261027-1018 window - judge loop live, ~2s/iteration)

* Phase A re-run: the sandbox rollback ate disk/+baselines/ again; the
  06:29 links STILL LIVE ~4h later - disc_return.sh second production
  run, witness 8/8 STRICT again.
* New harness scripts/bm_unit_decode/judge_fulldiff.py (run with the
  venv python - capstone lives there, NOT in system python): full
  word-by-word diff of build/judge/<unit>.bin vs the retail slice with
  both sides disassembled, run-grouped with anchors. The twin's 144
  diff words = TWO clusters: run 1 (84 words, 0x8002ABCC..0x8002AD20)
  and run 2 (60 words, 0x8002B194..0x8002B284).
* RUN 1 DECODED: (a) the prologue save/bind permutation (schedule2
  interleaves; retail keeps saves ahead of binds) - allocator outcome;
  (b) the size param reload targets a0 (built) vs v1 (retail), and the
  t-chain runs v1 = v1 + 0x200 in retail (lw v1,0x44(sp) DIRECTLY);
  (c) THE FILL LOOP FORM: built = countdown (ori v1,0x1ff; bgez; -1
  stride), retail = UPWARD (move v1,zero; sltiu v0,v1,0x200; bnez) -
  gcc 2.6.3 REVERSED our int-induction loop.
* MUTATION V-unsigned-i (mechanistic, CONFIRMED): `unsigned i` blocks
  the loop reversal (i >= 0 is a tautology) and the built reproduces
  the retail sltiu-bound upward form. Judge count equal (144/432, the
  cascade relocates), but the retail-correct shape STAYS in the staged
  candidate func_8002ABC8.c. The candidate's own law 4 ("sltiu bound")
  is now actually reproduced by its source.
* MUTATION V-minus1-fill (D[i] = -1): NEGATIVE - gcc constant-folds to
  the identical 0xff store; no shared -1 pseudo is born.
* RUN 2 DECODED (the return-2 path, delta (e) live): retail = addiu
  s1,-1; beq s0,s1,create; [fall-through] jal close (a0 <- s0 in the
  delay slot); j 0x8002b26c (the shared k=6 epilogue thunk) with
  ori v0,2 in the j DELAY SLOT. Built = addiu s2,-1; bne s0,s2 (branch
  INVERTED, return-2 laid out later); the create path falls through.
  Retail's -1 in s1 vs ours in s2 (delta (b), live-confirmed).
* NEXT: the two remaining levers are both gcc arrangement/allocator
  outcomes - (1) coerce the fd==-1 guard's block order so close+return-2
  falls through to the j-thunk (source-side try: invert the guard to
  `if (fd != -1) { close(fd); return 2; }`); (2) the prologue/size-load
  register choices via declaration/ref-order mutations. The fulldiff
  harness makes every iteration readable; the judge is the arbiter.

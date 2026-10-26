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

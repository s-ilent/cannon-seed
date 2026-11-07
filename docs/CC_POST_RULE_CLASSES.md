# The cc_post rule-class survey — the func_8007736C residue

Authored: window cron-202611070331 (2026-11-06/07). Status: DESIGN — no rule
implemented, no source shape retried. This is the "rule-class survey before
any implementation" item from the cron-202611062231/cron-202611062346 queues.

## 1. Provenance and standing

The func_8007736C (mainmenu_jp) probe ladder closed its source-side work at
judge DIFF 122/186, SIZE 756 vs retail 744 (probe c3, window
cron-202611062001; ladder state parked in scripts/deferred_func_8007736C.c).
Nine source shapes were probed across three windows (2001 / 2116 / 2231):
three landed (the carried-c component loop, the sep2 per-iteration opaque
def, the c3 form itself), six refuted (the -1 non-pin shape c4, the walk
i-home c5a/c5b, the K&R import order kr1, the asm-input import order c6,
the walk-head anchor c7 and its opaque variant c7b). Window cron-202611062231
decomposed the full 122 map and attributed EVERY class to a cc_post
mechanism — the source-shape surface is exhausted. This survey specifies the
four rule classes to marker-interface level so implementation windows can
proceed one rule at a time without re-deriving the evidence.

Evidence artifacts (all in-repo):
- probes/gcc263/func_8007736C_probe_{c3,c4,c5,c6,c7,c7b,kr1}.c — each header
  carries the verdict and the banked law text.
- scripts/deferred_func_8007736C.c — the parked draft, header items (7)/(8).
- docs/TASKS.md sections cron-202611062001 / 2116 / 2231 / 2346.
- tools/cc_post.py (rules 1-18; the header carries the byte-verified
  rationale for each), tools/cc.sh (the marker grep block), and the per-rule
  test convention tests/test_cc_post_rule17.py / tests/test_cc_post_rule18.py.
- The AF70 decision brief (window cron-20261101-0507, in docs/TASKS.md) —
  option B banked the reg-field class at concept level; section 6 here
  promotes it to an interface spec.

## 2. Constraints every new rule must satisfy (from the shipped machinery)

1. **Marker opt-in, never default-on.** cc_post rules fire only on units
   whose C source carries `cc-post: <rule> [args...]` comments; tools/cc.sh
   greps them and forwards args. cc_post never runs on the asm split path.
   Any rule that DELETES instructions or rewrites register/displacement
   fields must stay marker-gated forever — there is no corpus-wide audit
   that can prove such a transform safe everywhere.
2. **Loud failure.** A marked rule that finds no matching site exits 3
   (never a silent pass). A bare rule17 marker without args loud-fails in
   cc.sh itself. New rules inherit both behaviours.
3. **Count checks.** Where a pattern could match more than once, the marker
   carries the expected count (the `cc-post: lt0-scc <count>` precedent,
   default 1).
4. **Per-rule unit test.** tests/test_cc_post_ruleNN.py is the convention
   (rule17: 208 lines, rule18: 160); every new rule ships with one.
5. **Measurement is live-only.** Judge verdicts come from the judge pipeline
   (staging = the yaml func_8007736C row asm->c + the probe copy +
   tools/judge_unit.py) against TRUE baselines only; staging reverts per
   run. baseline_audit runs BEFORE any scan/review on a rolled-back sandbox
   (the cron-202611062346 lesson: the unit's first scan ran against woven-era
   bytes and burned a cycle).
6. **maspsx hazards bound the source side.** Memory clobbers are a maspsx
   hazard (asm volatile("" ::: "memory") ate the $L9 label into a
   '# DEBUG: skipped' line, probe c7 header) — when a source-side fix would
   need a clobber, the fix is tool-side. This is exactly why class B below
   cannot be fixed in C.
7. **Ratchets equal the tree; suite 157/157; structured commits; never
   --no-verify.**

Rule numbers below are CANDIDATE numbers (next free after 18); assignment
happens at implementation. Order of presentation = the 2231 map's class
order, not the build order (section 7 gives the build order).

## 3. Class A — the s6/-1 hoist class (~12 words, the biggest class)

**Retail shape** (probe c4 header; the 2231 map): the sentinel compare is
materialized FRESH at the site — `addiu $v0,$zero,-1` immediately before
`beq $a0,$v0` — and $s6 is never saved; the frame has no s6 slot.

**Built shape** (c3's carried-c regalloc): the -1 constant is hoisted out of
the outer loop into a callee-saved home — `addiu $22,$zero,-1` before the
outer loop, `beq $4,$22` at the test, and an `sw $s6/... /lw $s6` pair in
the prologue/epilogue.

**Why the cascade is one class** (the 2231 map): the prologue s6 word, the
ra-slot +4 shift (s6 took a slot, pushing the ra save one word), the hoisted
addiu at [37], the [61]-[62] register fields, and every displacement-only
diff ([50][66][74][80][89][93][102][108]) die together when the hoist dies.
~12 words total.

**The banked source laws** (probe c4, three refutation directions):
- The sep2 lever needs the opaque def on a CONDITIONAL path that does not
  dominate the loop latch. The sep2 def works because it sits on the head-
  test fall-through arm; a def+barrier in the tail dominates the latch, so
  loop.c hoists it regardless of the barrier, and the "0" tie then drags
  the compare onto the hoisted register.
- The barrier inherits the hoisted input's register via the "0" tie — the
  barrier cannot hold a different home.
- def-before-call + use-after forces a callee-saved home (the call clobbers
  $2/$3), and the -1 has no nested-loop use, so the sep2 per-iteration trick
  has no purchase.
Retail's shape is therefore UNREACHABLE at the source level for this
regalloc web; it must be a post-pass.

**Proposed mechanism (candidate rule 19, "site-fresh-const")**:
marker `cc-post: site-fresh-const <imm> <built-reg>`; transform, all
shape-verified, loud-fail on any mismatch:
1. Locate the hoisted def `addiu $<built-reg>,$zero,<imm>` sitting in the
   outer preheader region (the marker pins the function; the rule pins the
   def by its unique shape + the single compare use).
2. Locate the single compare `beq $a0,$<built-reg>` that consumes it.
3. Insert `addiu $2,$zero,<imm>` immediately before the compare; retarget
   the compare's register field to `$2`.
4. Delete the hoisted def.
5. Delete the `sw $<built-reg>,N($sp)` / `lw $<built-reg>,N($sp)` pair.
6. **Frame renumber** (the new machinery): every slot displacement ABOVE the
   deleted slot shifts -4; the frame-size addiu in prologue and epilogue
   shrinks by 4; the ra slot returns to retail's offset. The rule verifies
   the deleted slot is the TOPMOST used slot before renumbering and
   loud-fails otherwise (a middle-slot delete would need a gap-preserving
   remap — out of scope, reject).
7. Liveness guard for the inserted `$2` def: the rule verifies no `$2` use
   appears between the inserted def and the compare, and that the compare's
   block does not read `$2` on entry (gcc reserves $2/$3 as caller-saved
   scratch; at this site the previous `$2` def is the merged load whose use
   is the same compare region's OTHER branch — the judge verdict is the
   real gate; the textual check is the fast-fail).
Safety argument: steps 1-5 move nothing that crosses a call or a label
boundary other than deleting a dead-after-retarget def; step 6 is pure
renumbering of explicit sp offsets. The judge verdict (live-only) plus the
unit test plus the exact-size check (744 restored) gate the landing.

**Yield / risk**: ~12 words including the entire displacement cascade — the
highest-value rule in the survey. Risk: the frame renumber is the first
displacement-touching machinery in cc_post; the mitigation is the topmost-
slot-only restriction and the loud-fail.

## 4. Class B — the volatile-load andi (+1 word, at [54])

**Retail shape**: the volatile copy-exit re-load's result feeds the merged
`beqz` directly — no andi.

**Built shape**: `andi $2,$2,0x00ff` at the merge after volatile load D.

**The banked source laws** (probe c7 header):
- gcc 2.6.3 volatile reads bypass the zero-extend tracking; non-volatile
  reads do not get the andi — but a plain non-volatile read gets
  CSE-ELIMINATED entirely (load D vanishes; retail's re-load is real).
  No C-source spelling yields both the real re-load AND no andi.
- `asm volatile("" ::: "memory")` kills the andi but breaks maspsx's
  delay-slot handling ($L9 eaten into a '# DEBUG: skipped' line) — the
  memory-clobber hazard (section 2.6). The fix CANNOT ride the source.

**Proposed mechanism (candidate rule 20, "vol-extend")**: marker
`cc-post: vol-extend <count>`; transform: delete `andi $2,$2,0x00ff` at the
marker-attested merge site, shape-verified — the andi's dest must feed the
following `beqz`, the src must be the preceding `lbu`'s dest. Never
default-on: `andi $r,$r,0x00ff` is a genuine zero-extend elsewhere in the
corpus.

**Yield / risk**: 1 word. Lowest risk in the survey; the only subtlety is
that the deletion must not strand the load's delay-slot bookkeeping (the
lbu is not a load-delay-class insn on this toolchain, verified by rule18's
precedent of counted single-insn deletes).

## 5. Class C — the prologue import order ([5]-[8], 4 words)

**Retail shape**: the prologue imports out/$s5 FIRST (the `sw $s5,0x44` /
`addu $s5,$a0` pair precedes the pathv import).

**Built shape**: the init copies emit pathv/$s3 first in every variant ever
built.

**The banked source laws** (probes kr1 + c6): ALL THREE import-order
candidates are refuted — (1) declaration order (the c3 form), (2) the K&R
register-param form (kr1), (3) the early asm-input use (c6: judged
127/186, +5 WORSE — the input-only asm did not reorder the init copies, the
barrier displaced the guard loads into the import block and reshuffled the
spill batch, an sw $16 even landed in a beq delay slot). The init order is
not first-use-driven in gcc 2.6.3.

**Proposed mechanism (candidate rule 21, "import-order")**: a rule15-family
extension. _rule15_on_run already parses the prologue run
[frame][saves][import run][jal][delay] and reorders it (imports interleaved
with their saves, ra last, leftover save sunk into the jal delay); the
extension adds an EXPLICIT ORDER argument:
marker `cc-post: import-order <reg>,<reg>[,...]` — reorder ONLY the
import-copy run to the listed register order; everything else (saves, ra
placement, leftovers, delay fill) stays as the built order or the rule15
form, per the unit's other markers. Independence argument: import copies
read only incoming-arg/zero registers and write only the frame or their own
callee-saved home — a pure reorder of mutually independent insns (the same
argument rule15 documents). Count-checked: the listed set must equal the
run's register set exactly, loud-fail otherwise.

STATUS (window cron-202611070716, 5915e484): SHIPPED, with one refinement
the fresh judge artifacts forced — the built form interleaves each import's
save with its copy (the c3 source shape), so the transform moves each
listed register's (save, copy) ITEMS to the listed-order front, then the
remaining pure saves in their built order (reordering only the copies
cannot fix a sw word). Region parse starts after the frame insn (the guard
loads precede it); independence guard: no copy reads any copy's dest.
Live judge at rule19+rule21: SIZE 748, DIFF 145/186, the prologue
[0]-[67] fully retail-matched.

**Yield / risk**: 4 words. Low risk — the smallest delta on existing
machinery in the survey.

## 6. Class D — the walk cluster ([115][120]-[124]+)

Three sub-features, all attributed, none source-reachable:

**(d1) the walk i-home.** Retail homes the walk's counter i in $s2 (level's
dead register); gcc hands it $s4 (sep's dead register) in every shape —
function-scope implicit, function-scope explicit, block-scope after the pins
(c5a), block-scope first (c5b): four shapes, all identical. The i-home is
INSENSITIVE to declaration scope and order; retail's s2 is unreachable by
source steering. This is the cc_post REG-FIELD class — the same family the
AF70 decision brief (cron-20261101-0507) banked as option B.

**(d2) the off-init / i-init positions.** Built emits the off-init early at
[115]; retail has it in-block at [124], and retail's i-init sits in the
skip-branch delay slot at [115]. Instruction POSITIONS, not fields.

**(d3) the walk-head anchor route.** Retail materializes the shared anchor
into $v0 (`lui $v0,0x8014` / `addiu $v0,$v0,0x788c`), derives
`rec = addiu $s0,$v0,-8`, and copies `name = move $s3,$v0`. c7 (transparent
anchor) coalesced the anchor into name's own s3 (lui $s3 direct); c7b (the
"=r"/"0" opaque barrier) blocks VALUE propagation but not REGISTER
coalescing — the anchor->name copy became a no-op. Three shapes refuted;
the real move copy is a post-pass product.

**Proposed mechanism (candidate rule 22, "reg-field" + a position mover)**:
- reg-field: marker `cc-post: reg-field <old> <new> <site>[,<site>...]`
  where each site is `label:insn-index` into the built .s. The rule rewrites
  the register field ONLY at the listed sites, each verified against the
  expected insn shape recorded at survey/wordmap time; loud-fail on any
  mismatch. The explicit site list substitutes for liveness analysis (the
  textual .s cannot prove s2 dead — but the banked decode says s2 is level's
  DEAD register, its live range closed before the walk); the judge verdict
  is the semantic gate.
- position mover: the (d2) feature wants init insns MOVED across a branch —
  a distinct, higher-risk transform (moves can cross live ranges). It ships
  only after reg-field proves the site-list machinery, and only with its
  own marker + shape verification + judge gate.
The site lists come from the wordmap of the CURRENT judge artifacts
(build/judge/func_8007736C.{r,mas}.s). NOTE: the 2231 wordmap tool was
scripts-repo-external and did not survive the sandbox rollbacks — the
re-derivation recipe is: arm the oracle disc-free (the 8-build rehearsal
flow), stage the probe, run judge_unit, then word_diff -G0 between the .r
and .mas slices for the index map. Regenerate the map at implementation
time, never trust a stale one.

**Yield / risk**: the walk cluster's remaining words (the map's
[115][120]-[124]+ group). Highest machinery cost in the survey — hence LAST
in the build order despite landing mid-list in the map.

## 7. Recommended implementation order and per-rule gates

**Order: A -> C -> B -> D.** (STATUS 2026-11-07: A shipped as rule 19,
window cron-202611070601, 8d7014da; C shipped as rule 21, window
cron-202611070716, 5915e484; B shipped as rule 20, window
cron-202611070146 - judged live at SIZE 744 = retail for the first time,
DIFF 144/186 with the andi gone; only D open.)
- A first: the largest class (~12 words) AND its displacement cascade die
  together; one rule class removes the biggest block and the frame returns
  to retail's layout, which also un-shadows every later word map (later
  rules see the post-A indices).
- C second: 4 words on the smallest delta (the rule15 parser already
  tokenizes the run).
- B third: 1 word, trivial transform, but strictly site-gated.
- D last: the site-list machinery is the heaviest and (d2) is a genuinely
  new transform class; by then A-C have re-shaped the map and the site
  list must be re-derived against the post-A/B/C tree.

Per-rule acceptance gates (all mandatory):
1. Unit test tests/test_cc_post_ruleNN.py green (suite stays 157/157).
2. The marker absent => byte-identical output (the rule cannot perturb
   unmarked units — assert in the test).
3. Judge verdict on func_8007736C measured live (oracle armed disc-free,
   witness 8/8 STRICT, baseline_audit 8/8 MATCH first); staging reverted.
4. verify 8/8 GREEN on the final tree; ratchets recomputed to equal the
   tree; no --no-verify.
5. The probe ladder's parked best (c3, 122/186) remains the source of
   record until the rules land — the rules apply to the STAGED probe row,
   and the landing decision is a separate, owner-visible step.

## 8. Non-goals and ownership notes

- No source-shape retrials: the surface is exhausted (nine shapes, three
  landed, six refuted, all banked with laws). New source ideas are out of
  scope for this row.
- No default-on activation for any rule in this survey.
- func_8006AF70 stays OWNER-GATED: this survey's reg-field class shares the
  option-B mechanism the AF70 brief banked, but AF70's landing call remains
  Silent's; nothing here changes that.
- The mainmenu_jp sdk-lane items (the WithMode twin, the scan refresh, the
  census realignment) are lane-owned and untouched by this survey.

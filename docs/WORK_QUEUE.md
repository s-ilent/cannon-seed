# Current work queue

**Reconciled 2026-11-22** using the **latest** November 21 entry in
[TASKS.md](TASKS.md) (cron-202611211415, close-out at `a13c6f92`) and the
subsequent source-only CI/toolchain commits. This file, **not the October
"## Queued" section at the top of TASKS.md**, is the task entry point.
Use [STATUS.md](STATUS.md) for verification confidence and
[RESEARCH_LOG_INDEX.md](RESEARCH_LOG_INDEX.md) to find older experiments.

**Always start by refreshing evidence:** record HEAD, the relevant yaml
rows/source files, existing branch/PR work, and current
`python3 tools/audit_c_names.py --cross --adjudicate` output. The
numbers below are the last historical snapshot, not a promise about a
newer tree.

## Source-only measurement before selecting a research region

Run `python3 tools/coverage_report.py --strict --json --rows` and use
`origin_unattributed_asm_bytes` to identify **candidate** non-SDK areas,
not confirmed game functions. Inspect any large span's containing YAML
and actual assembly, then use SDK archive evidence and call/data flow
to establish genuine game ownership. The reporting semantics are in
[COVERAGE.md](COVERAGE.md). `make coverage` prints a compact summary.

**Semantic audit discipline:** adding `config/coverage_reviews.json` entries
requires a per-row source review and rationale. A file without detected
inline asm is merely a *candidate for semantic review*, not automatic
semantic-C progress. Shared code repeated in different targets contributes
multiple **target instances** to byte totals.

## Ready: bounded read-only research

### R1 — Game-code recovery atlas (independent research track)

**Twenty-five bounded runs completed (2026-11-22):**
[G3 render preparation](research/G3_RENDER_PREP_ATLAS_20261122.md)
identifies staging/submission;
[HUD/font queue and outer frame loop](research/G3_HUD_QUEUE_FRAME_LOOP_20261122.md)
recovers Psy-Q GsOT, ten-entry font queue and game frame;
[mode sequence atlas](research/G3_MODE_SEQUENCE_ATLAS_20261122.md)
enumerates eight game-state callbacks and submodes;
[FOBJ sprite-path atlas](research/G3_FOBJ_SPRITE_PATH_20261122.md)
proves a 100×6-byte 2D sprite command queue, 12-way display-state
dispatcher and GsSortSprite OT submission; the
[3D TMD polygon-path atlas](research/G3_TMD_GEOMETRY_TO_OT_20261122.md)
proves **descriptor creation → GsLinkObject4 → 0x6C-byte
3D scene records → GsSortObject4J-like dispatcher → GsTMDfast*
polygon packet insertion → GsDrawOt** in JP, with EU corroboration; and the
[communication buffer schema](research/G3_COMM_BUFFER_SCHEMA_20261122.md)
now proves `D_80166360` is a **per-frame immediate-mode 0x18-byte request
pool** (literal "Communication Buffer" string evidence) with a bump
allocator, 756-record capacity gate, laser (`mylaser.c`) and object-spawn
producer systems, the corrected dispatch consumption rule and the 0x6C
record field map. The [laser producer pool](research/G3_LASER_POOL_20261122.md)
proves the persistent 32×0x84 pool, allocator/back-reference, three-mode
fallthrough, origin-relative endpoint and final emission after release.

The [gunner and target pool atlas](research/G3_GUNNER_TARGET_POOL_20261122.md)
resolves the four laser wrapper callers to 4×0x8C player records, the
124×0xAC collision-participating object array, 74/100/124 allocator bounds,
trigger cadence and hit-mask writes. Release does not clear the owner
back-reference on the inspected path; external lifecycle is still open.
The [damage and score atlas](research/G3_HIT_DAMAGE_SCORE_20261122.md)
proves four-gunner arbitration, rotating hit priority, fractional
and whole-stage durability, packed-decimal score awards and a
representative non-collidable death transition.
The [fragment effects atlas](research/G3_FRAGMENT_EFFECTS_20261122.md)
resolves 8003D9FC to a specialized type-0x38 constructor, with 10-byte
fragment records, two launch policies, motion and boundary conversion.
The [mission scripting atlas](research/G3_MISSION_SCRIPTING_20261122.md)
recovers section/environment timelines, primary/secondary encounter lists,
object descriptor layouts, general constructors and dual-clock scripts.
The [retail dispatch atlas](research/G3_RETAIL_DISPATCH_TABLES_20261122.md)
verifies both tracked private original EXE blobs against committed SHA-1
oracles, resolves all 256 dispatch slots, 18 opcode entries, both damage
jump tables, and records the SsGetNck attribution conflict.
The [mission inventory](research/G3_MISSION_INVENTORY_20261122.md)
counts 857 authored mode-zero events, 730 descriptors, 23 config IDs,
and decodes 177 field-qualified dual-clock script streams in both regions.
The [movement atlas](research/G3_MOVEMENT_SEGMENTS_20261122.md)
resolves 24-byte records, six destination modes and 261 paths/553 segments.
The [type-1D controller](research/G3_TYPE1D_CONTROLLER_20261122.md)
resolves config 66 to 7B and active type 1C.
The [formation and model atlas](research/G3_TYPE1D_FORMATIONS_20261122.md)
resolves all 74 events in six waves, the one-record heading initializer,
conditional fixed-point movement and the 307-row TMD resource table, with
resource 9F mapped to archive index 57.

The [stream clock and vehicle pose atlas](research/G3_STREAM_CLOCK_POSE_20261122.md)
resolves the 0x50-byte STR metadata copy, absolute mission time as twice the
custom metadata clock, and moving origin/rotation/displacement writers.

The [proximity and shared health atlas](research/G3_PROXIMITY_HEALTH_20261122.md) resolves 80035348, shared 10000-unit health, collision angles, difficulty multipliers, damage counter, alarm and death gate.

The [object census and composite candidates](research/G3_OBJECT_CENSUS_COMPOSITES_20261122.md) maps all 29 nondefault slots, finds 35/10/5 child allocations in types 80/88/89, and resolves direct damage caller 8003AC2C.

The [Doldva rotating reactor atlas](research/G3_DOLDVA_REACTOR_20261122.md) identifies type 80 through KUUBO_DIED/DOL_SUCS, recovers cylindrical geometry, rotation, hit aggregation/five stages and exclusive tick-3888 success gate.

The [SPARKBIT final objective atlas](research/G3_SPARKBIT_FINAL_OBJECTIVE_20261122.md) resolves type 89, five independent targets, specialized countdown script, rotation acceleration, success and timeout result gates.

The [player count and scaling atlas](research/G3_PLAYER_COUNT_SCALING_20261122.md) resolves D_800AC164, four local slots versus 1..6 effective-count override, independent difficulty row, and 692–857 encounter eligibility.

The [gameinfo/playrec atlas](research/G3_GAMEINFO_PLAYREC_20261122.md) recovers named settings API, difficulty mapping, count override setter/default, and replay infrastructure. DRAGOON startup passes zero to separate object-mode selector.

The [alternate-mode and placeholder atlas](research/G3_ALTERNATE_MODE_PLACEHOLDERS_20261122.md) resolves the invalid nonzero static schedule alias and six inert type98 records, distinguishes active short config views, and identifies nested 74/100/124 object pool prefix boundaries.

The [resource archive atlas](research/G3_RESOURCE_ARCHIVES_20261122.md) resolves flat offset lookup, TIM upload/free, TMD in-place mapping, region-specific texture indices, and four-target common loader shapes.

**Next specific R1 question:** build a four-target shared-function atlas, starting with well-bounded game-owned leaves and resource loaders; identify safe matching C candidates and reproducible build witnesses. Resource resolver consumers and actual STR/TMD validation remain separate. STR extraction remains blocked on container startup; both CHDs are now project inputs. Recover TMD archive loader/offset format separately.
Mode-nonzero aliased data and type 98 remain open. The render arrays are proven
frame-local staging; do not convert builders before a producer-side
landing decision.
**Owner/SDK provenance gate:** EU `src/func_80052038.c` is an
already retail-matched C row (historical claim), but functions as
a Psy-Q **`GsSortObject4J`-like** TMD dispatcher. Investigate
archive/member evidence separately; **do not rename or change its
C row/coverage ownership unilaterally**. Packet-workbuffer allocation
bounds, sprite resource `0x707`, and current retail oracle remain open.

**Target:** `g3_jp` first; `g3_eu` for comparison.

**Why:** Current C coverage includes abundant SDK members and wrappers,
while the meaningful main-game code remains poorly classified. A
game-specific map gives the next matching campaign high-value targets
rather than another pass over identical glue functions.

**One-run scope:** choose exactly one coherent contiguous game-code
region or function family **not already settled** in TASKS.md, and:

1. Establish row/ROM/VA extent with `config/splat.g3_jp.yaml`, asm
   labels, any nearby data pointers, call targets and candidate function
   entry/exit boundaries.
2. Check ownership: SDK member/window evidence
   (`config/sdk_anchors.txt`, `tools/sdk_members.py` outputs) vs
   game-owned code; report ambiguities.
3. Cross-check EU offsets/call graph when possible; distinguish exact
   byte twins, address-shifted siblings, and inferred analogues.
4. Explain **gameplay or state responsibility** in terms of observable
   writes/reads/dispatch; avoid invented names and interpretative leaps.
5. Produce an evidence table (address/extent, backing path, xrefs,
   verified vs inferred) and rank one or two feasible future semantic-C
   conversion candidates. Record a negative result when evidence rules out
   a candidate.

**Deliverable:** a short source-linked investigation, appended to a
*focused* durable subsystem document or a standalone research note;
cross-link from [RESEARCH_LOG_INDEX.md](RESEARCH_LOG_INDEX.md). No source
changes unless the full oracle is available and a separate landing
decision was made.

**Done for a run:** at least one NEW conclusion or clearly demonstrated
negative/blocked finding, with source/offset evidence and the next
specific question. Do not reopen a previously measured region merely to
repeat its summary.

### R2 — Cross-target source reuse and semantic-quality classification

**Target:** a bounded sample of current `src/` C rows and their actual
target yaml consumers.

**Question:** Which C rows reconstruct behavior, and which are
assembly-preserved, register-pinned, special-rule hybrids or thin wrappers?
What game structures are still opaque?

**Method:** classify no more than 10–20 functions in one pass; use the
per-target `coverage_report.py --json --rows` output to verify which YAML
rows actually compile each source, rather than deducing ownership from
the filename. Extend `config/coverage_reviews.json` only after examining
the **entire** row, and record a narrow evidence-backed tier. Keep binary-match evidence separate from C
semantic quality. Include samples from `g3_jp` where possible.

**Deliverable:** a small reusable evidence-backed classification table,
with links to source/yaml rows, not an unverified global percentage.

### R3 — Read-only status of the retained naming exceptions

**Target:** the last recorded 13 cross-target shared-name cases,
mainmenu_jp's 20 reserved name/placement rows, and the known parked
memclr/INTR and `func_800629A0`/`func_80036CFC` exceptions.

**Method:** rerun the census/adjudicator and check live YAML ownership,
definitions, curated names and C references. Report changed membership,
owner conflicts, and exact affected targets. **Do not rename, repartition
or automatically "fix" intentional shared-name mismatches.**

**Deliverable:** a decision brief with options for shared canonical name
vs region-local alias, with proposed collision policy and complete impact
surface. This can be worked on without the retail baseline.

## Ready only with full retail oracle

### L1 — Guarded toolchain roll-out verification

After pulling commit `2d5e0673` or later, on a host with the legally
provisioned baseline and exact historical tools:

```sh
# Guarded compiler rebuild/attestation on an existing checkout:
sh tools/patch_cc1_263.sh
sh tools/rehydrate.sh
python3 tools/toolchain_preflight.py
sh tools/witness_check.sh
for target in slps_00270 sces_00269 mainmenu_jp mainmenu_eu \
              g3_jp g3_eu g3org_jp g3org_eu; do
    make clean
    make verify TARGET="$target" || exit 1
done
```

If the guarded compiler source build is absent, run
`sh tools/build_cc1_263.sh` before the patch script. A clean
`make verify` must **never** fall back to a prebuilt unguarded compiler.
Save exact command/output hashes and record success or the first precise
failure (environment vs source vs oracle).

**Acceptance:** witnessed baseline 8/8 and full-image 8/8 matching
at the **same HEAD**, with the preflight passing; source-only green CI
is not acceptable substitute evidence.

### L2 — Candidate gameplay C conversions

Only after R1/R2 establish boundaries, owners and source hypotheses:
make one bounded C conversion on a dedicated branch, then
`make clean verify TARGET=<target>`. If shared headers, common
translation units or shared source resolution changed, verify **all
eight** executables before merge. A unit-level judge or a good
partial-diff score is not a substitute for image SHA-1.

## Owner-gated or parked; do not schedule as self-directed landings

| Subject | Current rule / unblock condition |
| --- | --- |
| 13 cross-target shared names | Owner chooses naming convention after R3 decision brief |
| mainmenu_jp 20 tool-fair rows | Reserved naming lane; obtain lane handoff/owner direction |
| `func_8006AF70` / `SsSetTickMode` | Owner choice for round-7 4-word mismatch, see DISC_RETURN_RUNBOOK phase C |
| `setIntr` / `GsSetDrawBuffOffset` / 43 size-wrong units | Previously parked, investigate only a **new** mechanism or explicit assigned scope |
| SDK memclr/OMF def-base cases | Require member/ownership evidence; not generic rename or asm-to-C work |
| Tracked extracted retail files and Git-history rewrite | Owner has deferred remediation; preserve history, do not force-push |

## Run protocol for scheduled research

- **One bounded, substantive investigation per execution.** Do not
  default to repeated sweeps, status recaps, mass edits or speculative
  "matching" work.
- **Reconcile first.** Check HEAD, current branches/PRs, focused docs
  and the relevant previous TASKS.md entries. Retire completed work;
  don't restage old tasks based on stale top-of-file queue text.
- **Always provide evidence.** State target, addresses, byte extents,
  source paths, method, verified facts, inferences, negative results
  and unresolved requirements.
- **No-oracle mode:** read-only static research and documentation.
  Do not modify C, assembly, YAML or oracles merely to show activity.
- **Oracle mode:** require a baseline witness, guarded toolchain
  preflight and per-target full-image hashes before any match claim.
- **Progress is not a claim.** `tools/progress.py` is a heuristic
  function-instance census, not a percentage of recovered gameplay.
- **Finish with an exact next step** and mark any decision blocked on
  owner input as **owner-gated**.

New research evidence should live in focused documents where
possible, indexed from [RESEARCH_LOG_INDEX.md](RESEARCH_LOG_INDEX.md).
Keep [TASKS.md](TASKS.md) as historical source, not as an ever-growing
new task queue.

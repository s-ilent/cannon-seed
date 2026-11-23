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

**Eleven bounded runs completed (2026-11-22/23):**
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
record field map; and the [producer records atlas](research/G3_PRODUCER_RECORDS_20261122.md)
decodes both producer pools — `D_8016B014` (124 × 0xAC objects, two scan
bounds, 256-way type dispatch `D_8008A2F4`, three creation paths, complete
field map) and `D_80163944` (32 × 0x84 lasers, `lsr_mode` lifecycle) — plus
the `D_800ABBE4` 0x14-row model table schema, the `func_80024910`
offset-directory resolver and the `\\DRAGOON\\TMD.DAT;1` loader family,
recording the negative result that the table setter and loaders are
**unreached** in the static g3_jp image — a negative pass 8 then **closed at
byte level on both twins**: every word of the witnessed retail executables
scanned, zero `jal`/`j`/literal/lui-pair references reach the block, all
branch hits branch-internal (the block is branch-closed), leaving only
runtime-computed control flow; pass 8 also decoded the four gameplay handler
bodies (types 0x18/0x19/0x1C/0x1D), extending the object field map into
`+0x34..+0x54`/`+0x6C..+0x84`, mechanizing the `+0x30` resource selector,
and banking the definition-chain step, the 0x31 type morph, the laser-contact
resource link via `+0x2A`, the camera-anchor triple and the EU model table
`D_800AC428`.

**Next specific R1 question:** the PCSX-Redux trace per RUNTIME.md — pass 11
(atlas §16) closed the request→render-surface chain end to end: the consumer
constructors decode per case (case 0/4 camera-relative words minus the
D_8016AC18/1C/20 anchor, case 1/5 absolute halfword coordinates, case 3/7
halfwords through the `func_800326A8` transform, case 0xE the laser
constructor with id+8 and the forced type-3 word), the shared builders
`func_8002E4B8` (world) / `func_8002E770` (projected, which hard-rejects
kind 7 — dead end-to-end), and the two resource lookups
`func_8002F368` (world/TMD; head = `lw(D_800ABBE4)`, 0x14-byte rows) and
`func_8002F3D4` (projected/sprite; head = `lw(D_800ABBEC)`, 0x34-byte rows).
Since both tables image-initialize to 0 and the game renders, the tables
MUST be populated at run time — the sharp PCSX-Redux question is now "what
writes the two table head pointers at runtime"; optionally `func_800326A8`
to label the case-3/7 coordinate space. The render arrays are
proven frame-local staging; do not convert builders before a producer-side
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

**Passes 1–5 delivered 2026-11-23:**
[the classification sample](research/G3_R2_SOURCE_REUSE_CLASSIFICATION_20261123.md) —
pass 1: 16 shared C rows (x5–x8 instances) fully read and tiered: 7
semantic_c, 9 asm_preserved (the whole sampled GTE math family), 0
hybrid; the three sampled unknown-name rows are GTE compose-rotation
members, not game logic. Pass 2: the origin-unattributed C frame —
10 more rows registered (the g3_jp 0x1CC hand-asm subdivision four-up =
game-owned rendering; SetVertex0-2/ReadSZfifo3/4 = SDK members in an
evidence gap; func_800642A0 g3_eu = the first live hybrid, a real
decompiled SPU-init driver). Pass 3: the g3_eu/mainmenu_eu
unattributed-C singletons — 13 rows fully read and placed against their
live YAML rows: 11 semantic_c (the palette-fade wrapper family with
per-target callee deltas, CD host-command glue, init-driver constant
wrappers, slot-clear trio, fixed-slot stores) + 2 hybrid (the
identity-proven SVM init func_80067690, register pins $5/$4/$2; the
_SN_write write-all loop, `total` pinned to $18), 0 asm_preserved.
Pass 4 (same window): the mainmenu_eu 8-byte mini family — 8 rows of
one empty void function each, the empty body IS the retail two-instruction
return; registered semantic_c (func_80030990 is an R3 Class-B shared
name — classification only).
Pass 5 (same window): the wave/fifo INSTANCE registration — all 30
pending target instances of pass 2's classifications registered at the
four lane-free targets (g3_eu 9, mainmenu_eu 6, g3org_jp 9, g3org_eu
6): the 0x1CC subdivision wave (16 of its 20 instances; every body
byte-identical to g3_jp func_8005A13C modulo the row name, re-verified
mechanically) and the LIBGTE fifo family (19 instances across the five
targets that carry the members); placements double-checked against the
live report and the target YAMLs; mainmenu_jp's instances lane-owned
and untouched. Registry now 90 entries (34 semantic_c / 5 hybrid /
51 asm_preserved, 22,092 reviewed bytes); g3_eu reviewed bytes
3,620 → 5,552, mainmenu_eu 2,340 → 4,224. **mainmenu_eu's
unattributed-C frame is fully reviewed AND registered (4,224 of
4,224); g3_eu's only unreviewed unattributed-C rows are the two gated
ones (func_80052038 owner gate, func_8006AC04 runbook-gated partial);
the g3org singleton populations (g3org_eu 164 bytes / 4 rows, g3org_jp
244 bytes / 9 rows) are the last unregistered non-lane frames. The
remaining R2 value is the boot-target C rows (check the do-NOT-grab
lanes first), the g3org singleton passes, then the asm-row
wrapper-boundary sampling — which overlaps R1; coordinate there
instead of duplicating.**

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

**Delivered 2026-11-22:**
[the decision brief](research/R3_SHARED_NAME_DECISION_BRIEF_20261122.md) —
the 13 cross-target names decompose into travelling definition names
(Class A, 15 by-construction mismatches) and the mainmenu pair-family
(Class B, 16 rows + the `func_80030990` sces asm third holder); four options
with costs, a four-rule collision policy, unchanged parked/laned
exceptions. **Awaiting the owner's ratification; no renames made.**
Membership re-checks stay cheap:
`python3 tools/audit_c_names.py --cross --adjudicate`.

<details><summary>Original task text (retired)</summary>

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

</details>

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

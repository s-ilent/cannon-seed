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

**Twenty bounded runs completed (2026-11-22..26):** the pass-20 note [G3 main flow decode](research/G3_MAIN_FLOW_DECODE_20261126.md) decodes main (0x800224C0..0x80022788) instruction by instruction and lands the module's top-level schedule: 49 call sites in five phases (boot / attract / service setup / game loop / teardown+reboot), the attract tier is the frame function func_8002FC68's own private frame engine (probe + service chain + the func_8002FDB8 loop: state word D_8016AEB0, the video-prep pair func_8005E6C4/func_8005E740, music driver 1 func_8002FF48 whose return 1 is the primary exit, OT clear, VSync(4), GsSwapDispBuff, func_8002AC04, GsDrawOt), the vsync clock is registered only AFTER attract returns (VSyncCallback(0x8002370C) = a mid-entry of the sound orchestrator func_800236F8, the D_800ABE4C countdown + D_800AC5AC mode-counter machinery), the game loop is the master dispatcher func_80042C6C (loops while D_800AC4F4 != 1, the 8-way mode dispatch per iteration = the per-scene tier), and the teardown tail ends in LoadExec("cdrom:\\MAINMENU.EXE;1", 0x801FFF00, 0) - the module-swap reboot back to the launcher, which is why the crt0 continuation has only data words after jal main (main is the terminal call); the boot pilot loader func_8002278C (the second code-in-data function) decodes as the pilot/data setup: getter(3)==1 gates the pilot chain, getter(4) = the name string strcmp'd against "FRANK"/"REIKO"/"JOHNSON"/"SHARK" writing bit masks 1/2/4/8 to *(0x800AB284), "GHOST" diverts to the ramp chain, the default path runs the binding layer func_80026D6C and builds "\\DRAGOON\\%s%d.DAT;1" via func_8004803C + loads via func_80024954 with the "card load err(%d) name = %s\n" report; the pass-19 0x8BE divergence constant is confirmed in situ at 0x8002FCB4 as the a0=0 variant's s1; gp = 0x800AB26C fixed from the crt0 lui/addiu pair; the pass-19 note [G3 music-lane EU twins](research/G3_MUSIC_LANE_EU_TWINS_20261126.md) closes pass-18's scheduler/driver-2 question - g3_eu carries the same two entry-less shapes: the EU scheduler twin func_800299D4 and driver-2 twin func_8002FC48 (verified by normalized word alignment plus full hand reads) hold ZERO static references of any form in g3_eu (real-name census over 586 files, .word sweep, raw hi/lo scan all empty), so the pair is machine-total unreferenced in BOTH retail images and stays dead-variant unless a runtime trace fires it; the EU caller census otherwise mirrors pass 18's JP counts 1:1 (tick 2 <- 3 callers, binding <- 4 jals + main's data word 0x0C009B5A, driver 1 <- the frame function's jal, frame function <- main's data word 0x0C00BE3E, snapshot 2, evaluator 40 internal), the initializer is the EU scene-reset twin's fallthrough tail (byte-read), the pass banks two census traps (the .s comment word column is byte-reversed so the caller census's code-enc path is inert - census by the REAL carve names; EU glabel func_8002FFB8 is a render-function branch-join, NOT JP's driver 2: same VA, different entity) and records the lane's first code-side JP/EU divergence (EU frame branch pack s1=0x8BC vs JP 0x8BE); tools/audit_eu_twins.py lands the normalized-alignment twin finder; the pass-18 note [G3 music-lane callers](research/G3_MUSIC_LANE_CALLERS_20261125.md) corrects pass-17's empty census with the intra-row lesson (splat rows are carve units - chunk-to-chunk calls inside one row file are real references) plus the un-split main living in two data rows, anchors tick 1/tick 2/initializer/driver 1/the dispatcher to main end to end, leaves exactly the scheduler + driver 2 unreferenced (machine-total), and lands tools/audit_caller_census.py; the pass-17 note [G3 music-lane dispatch](research/G3_MUSIC_LANE_DISPATCH_20261125.md) decodes the four-lane music engine end to end (per-lane records at D_80165242 stride 0x44, the dispatcher's 2/4/8/default map, the four handlers' shadow writes, the tick skeleton, the request evaluator's classes and budget, the two ramps, the binding layer's tag-to-mode map 0x12->2/0x23->4/0x41->1/0x53->8); the pass-16 note [G3 sound boot chain](research/G3_SOUND_BOOT_CHAIN_20261125.md) closes pass-15's tone-table writer question — the full sound init at 0x80029C24 loads fload3("\SE.VH;1") (the 0x8620-byte 63-program VAB header), parks an inlined copy in the below-image resident region at 0x80016604 (0x80016600 = the vab id, 0x8001EC24 = the SPU body address; all three survive module swaps), opens it with SsVabOpenHead, streams the \SE.VB;1 body via snd_fload3_TransBody, and the SsUtGetVagAtr loop (progs 0..0x3D) fills the tone array D_800CFF84..0x800D0744 whose record bytes +4/+5 are psyq's VagAtr.center/.shift — exactly the executor's noteByte/fineByte; the voice cache D_800D0744 is executor-write-only and keyoff-read-only (strict census, the loose-sweep "consumers" exposed as byte-column false positives); the boot-chain caller census: slps/sces/mainmenu_eu run the full init, the g3-family modules re-attach only (SsVabFakeHead/FakeBody over the resident state) and the re-attach's own SsUtGetVagAtr loop re-fills all 62 records from the FakeHead-registered resident header — the crt0 bss-zero wipes the array per module load and the re-attach repairs it before any script runs, so the module-swap sound model closes with no open remainder (a same-window correction to the note's first reading); the pass-15 note [G3 script note-on semantics](research/G3_SCRIPT_NOTE_ON_20261125.md) decodes the handler executor func_80029FC0 end to end — every script command is a psyq SsUtKeyOn VAB note-on (prog = handler id, volumes = per-program multiplier x global L/R scalers, tone bytes from the runtime table D_800CFF88), the callee identity proven on four legs (sig-db 27/27 row alignment + LIBSND.H prototypes + the keyon/set-VVol error strings + the single-caller census), 10 direct-fire sites with hardcoded progs mapped; the pass-14 note [G3 script absent-command resolution + EU pin](research/G3_SCRIPT_ABSENT_COMMANDS_20261125.md) closes both pass-13 open questions (no second consumer anywhere — cursor/stream/labels/tables swept; no table patcher; absent commands advance the stream and consume the once-latch; the counter clock + latch lifecycle + mode-handler vector decoded; the complete EU twin machinery pinned and the EU corpus machine-compared — the 3 mode-1 variant scripts are the only JP/EU divergence: JP absent band vs EU present payloads over identical gates); the pass-13 note [G3 script stream corpus](research/G3_SCRIPT_STREAM_CORPUS_20261124.md) decodes the {frame-gate, payload} two-channel format and the whole mapped corpus; the pass-12 note [G3 script interpreter + 4-lane rank](research/G3_SCRIPT_INTERP_LANE_RANK_20261124.md) decodes the two remaining unnamed slot-4 stage helpers, the 46-command script table and the script stream base; the earlier eleven:
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

**Next specific R1 questions:** (a) who sets D_800AC4F4 = 1 - the dispatcher exit / reboot-to-launcher trigger (the vsync-clock family func_8002334C/384/C8/D8 and the *(gp) = 0x800AB26C word the vsync machinery reads are the suspects); (b) the getter func_80025944 id map (0x11/2/3/4/5/0xA/0xF) including the stateful slot-2 wrinkle pass 20 recorded; (c) the EU corroboration of main's schedule in one pass (the pass-19 band map already carries the jal twins); (d) the stride-12 work base - what s2 points at in func_80026718's caller frame and who consumes the tick calls' sp+0x10/sp+0x12 stack-buffer outputs; (e) the scheduler + driver 2 runtime question is now two-image machine-total (pass 19) - only a PCSX-Redux trace per RUNTIME.md could revive either entry; (f) the standing pass-11 runtime question, whose static half is closed: the PCSX-Redux trace per RUNTIME.md — pass 11
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

**Passes 6–7 delivered 2026-11-24 (window cron-20261124-0609):**
pass 6 — the g3org singleton populations: 13 instances over 12 shared
files fully read and registered (8 semantic_c: the empty-void pair +
three palette-fade wrappers per target, callees func_800416D0 /
func_80041AB0; 5 asm_preserved bare hand-asm units at g3org_jp); both
g3org unattributed-C frames close exactly (g3org_eu 2,048 of 2,048;
g3org_jp 2,176 of 2,176). Pass 7 (same window) — the boot-target C
rows: the do-NOT-grab check held (sces's five rows are the fifo
family, not the parked setIntr family; slps's rows are fifo + a
matched live c row), one full read (slps func_80024F00, the boot
targets' first review, hybrid: volatile hand-asm nop + the real C
store boot_flag_0 = 0) plus ten mechanical fifo instance
registrations; sces closes at 92 of 92, slps at 108 of 108. Registry
now 114 entries (42 semantic_c / 6 hybrid / 66 asm_preserved,
22,700 reviewed bytes); fifo registered at 29 of its 30 live
instances (mainmenu_jp's ReadSZfifo4 lane-owned). **The unattributed-C
classification frame is exhausted at every lane-free target: closed at
g3_jp (pass 2), mainmenu_eu (pass 5), g3org_eu/g3org_jp (pass 6),
sces_00269/slps_00270 (pass 7); the only unreviewed unattributed-C
rows left campaign-wide are mainmenu_jp's lane-owned frame and g3_eu's
two gated rows (func_80052038 SDK-ownership gate, func_8006AC04's
44-byte runbook Phase D tail). The lane's remaining value is the
asm-row wrapper-boundary sampling — which overlaps R1; coordinate
there instead of duplicating.**

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

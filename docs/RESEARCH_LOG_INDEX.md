# Research log index

The original [TASKS.md](TASKS.md) is retained **verbatim** as the
16,366-line historical laboratory notebook (through 2026-11-21). Its
`## Queued` section was assembled in October and contains **completed,
superseded or owner-gated tasks**; it is **not the current queue**.
Use [STATUS.md](STATUS.md) for the current evidence-qualified picture
and [WORK_QUEUE.md](WORK_QUEUE.md) for new work.

The notebook is valuable as a record of successful experiments,
failed hypotheses, reversals, reproducible byte-match checks and
toolchain incidents. Keep it accessible rather than rewriting or
silently deleting apparent duplicates.

## New game-specific static investigations

- [G3 JP/EU graphics preparation and display-submit atlas (2026-11-22)](research/G3_RENDER_PREP_ATLAS_20261122.md): measured 299-instruction cross-region skeleton over two complete function bodies; buffer-indexed ordering-table clearing, VSync/swap/draw submission, and a non-game formatting false positive. **Static only**; no new retail or runtime witness.
- [G3 HUD font queue and main frame loop (2026-11-22)](research/G3_HUD_QUEUE_FRAME_LOOP_20261122.md): resolves the 20-byte OT record to `GsOT`, reconstructs bounded 10-entry `{text,x,y}` queue and 64-glyph sprites, identifies both first draw callees and traces the JP/EU outer frame loop and mode dispatch. **Static only**.
- [G3 main-mode sequence controller (2026-11-22)](research/G3_MODE_SEQUENCE_ATLAS_20261122.md): enumerates the full JP/EU 8-slot dispatch (7 distinct handlers), identifies named start/main/restart states and nested jump tables, and traces timer/record state transitions. **Static only**; mode-specific OT packet producer remains unproven.
- [G3 FOBJ sprite queue and slave-system dispatch (2026-11-22)](research/G3_FOBJ_SPRITE_PATH_20261122.md): verifies a separate 100-entry/6-byte sprite command queue (JP/EU), 12-way display-state producers, 36-byte GsSPRITE lookup/staging and direct `GsSortSprite` OT edge; distinguishes HUD from later scene geometry. **Static only**.
- [G3 TMD scene geometry to OT (2026-11-22)](research/G3_TMD_GEOMETRY_TO_OT_20261122.md): maps game descriptor traversal, GsLinkObject4, 0x6C world scene records, linked TMD dispatch through named Psy-Q callbacks, 20-byte GPU polygon packets, OT links and GsDrawOt; separates 0x7C projected sprites. **Static only**; EU existing matching C dispatcher is an unadjudicated SDK ownership candidate.
- [G3 communication buffer schema (2026-11-22)](research/G3_COMM_BUFFER_SCHEMA_20261122.md): proves `D_80166360` is the literal "Communication Buffer" (source error string) — a per-frame 0x18-byte request pool with bump allocator `func_8003EE70`, 756-record capacity gate, laser (`mylaser.c` evidence) and object-spawn producer systems, the corrected 15-way dispatch consumption rule (0xE/!bit4 → world, bit4 → projected) and the 0x6C record field map; render arrays are immediate-mode staging rebuilt every frame. **Static only**.

- [G3 laser producer pool (2026-11-22)](research/G3_LASER_POOL_20261122.md): proves a 32×0x84 persistent laser pool, first-free allocation and caller back-reference, same-call mode fallthrough, origin-relative endpoint calculation and final submission on slot release; all 430 compared instruction shapes agree across JP/EU. **Static only**.

- [G3 gunner and target object pools (2026-11-22)](research/G3_GUNNER_TARGET_POOL_20261122.md): traces all four laser wrapper callers to a distinct 4×0x8C gunner array, recovers trigger cadence, proves the 124×0xAC collision participant/allocator pool with 74/100/124 prefix bounds, and maps per-pass hit notification; 590 JP/EU instruction shapes agree. **Static only**.

- [G3 hit arbitration, damage and score (2026-11-22)](research/G3_HIT_DAMAGE_SCORE_20261122.md): proves hard-coded four-gunner arbitration, rotating hit priority, fractional durability and signed terminal threshold, packed-decimal score awards, and a representative non-collidable death transition. 348/348 JP/EU normalized instructions, 320 exact. **Static only**; damage jump-table class mapping pending.

## Fast navigation

```sh
# List dated historical research windows without opening the whole file:
rg -n '^## 2026-' docs/TASKS.md | tail -60

# Find one exact function, problem class or tool:
rg -n -i 'func_8006AF70|SsSetTickMode' docs/TASKS.md
rg -n -i 'carve-name|--adjudicate|name==VMA' docs/TASKS.md
rg -n -i 'SpuVmDamperOn|VM_DON|memclr' docs/TASKS.md
rg -n -i 'ORACLE DOWN|guarded-cc1|rehydrate' docs/TASKS.md

# Look at a bounded section (use the actual line numbers from rg):
sed -n '16354,16365p' docs/TASKS.md
```

## Where the reliable starting evidence lives

| Topic | Primary references | State/reading guidance |
| --- | --- | --- |
| **Most recent work** | TASKS.md, November 21 final window (`cron-202611211415`), [last recorded section](TASKS.md) | Six VM_DON C-row repaints and final non-lane name sweep, `a13c6f92`; 8/8 historical oracle reported |
| Region/executable maps and provenance | [RECON.md](RECON.md), [LOADMAP.md](LOADMAP.md) | Measure with current configs and committed SHA-1 witnesses; legacy prose may describe prior carve |
| The actual compiler/assembler pipeline | [TOOLCHAIN.md](TOOLCHAIN.md), [CI.md](CI.md), tools/toolchain_preflight.py | Current effective guarded compiler **overrides stock-cc1 descriptions**; source-only CI does not assert retail match |
| Carve-name repair and exception classes | TASKS.md November 18–21, tools/audit_c_names.py, config/sdk_anchors.txt, config/symbols.curated.txt | 75 historical mismatches were **not** 75 unattended rename opportunities; see [WORK_QUEUE.md](WORK_QUEUE.md) |
| Cross-region identity and matching | tools/pair_report.py, tools/near_twin_census.py, docs/MATCHING.md | Requires live witnessed baselines/build ELFs; identity percentages do not prove function ownership |
| SDK member ownership, archives, relocations | tools/sdk_members.py, tools/omf_pubsyms.py, tools/sdk_anchors.py | Distinguish real Psy-Q members, veneers, game code and library member tails |
| Main-menu continuation web | [FABRIC.md](FABRIC.md) | Addresses and frame/continuation assumptions already investigated; read before another flattening or naive C conversion |
| Read-only game-code boundaries | [GRID.md](GRID.md), [G3 render path](research/G3_RENDER_PREP_ATLAS_20261122.md), [HUD + frame loop](research/G3_HUD_QUEUE_FRAME_LOOP_20261122.md), tools/invariant_census.py, tools/xref_census.py | Preparation/submission incoming callers, typed OT record and two HUD callees now resolved; next is game-mode dispatch table and gameplay ownership |
| Unit-code diff and postprocessing | [CC_POST_RULE_CLASSES.md](CC_POST_RULE_CLASSES.md), tools/wordmap.py, tools/cc_post.py | Many speculative register/allocation fixes already tested; no fresh attempt without a new hypothesis |
| Disc recovery and parked oracle work | [DISC_RETURN_RUNBOOK.md](DISC_RETURN_RUNBOOK.md) | **Landing ladder mostly closed**, Phase C remains owner-gated; don't restart retired Phase D/E/F/H |
| Runtime evidence | [RUNTIME.md](RUNTIME.md) | Optional observed execution only, not full program coverage or proof of match |

## Recent chronology / supersession map

- **October 15–24:** initial Psy-Q windows, symbol adoptions and scan
  campaign. The opening TASKS.md `## Queued` section still describes
  parts of this campaign, including partial 5/8 scan status that later
  entries explicitly superseded.
- **Late October–early November:** sector-frame extraction correction,
  deep linker/assembler research, maspsx patch classes and large
  SDK-linked member campaign. Match claims were repeatedly corrected
  when baseline provenance or compiler fallbacks changed.
- **November 6–9:** the seven `SsVabOpenHeadWithMode` targets and
  name-respelling/zero-edit/shared-merge campaigns. Recent entries
  explicitly mark ZEROEDIT, SHAREDMERGE, RESPELL, RIDER and SELF
  queues **complete**. Do not relaunch them from older subheadings.
- **November 17–18:** carve-name discrepancy investigations and
  scoped cleanup; the clean-extract carrier-list issue closed.
- **November 21, first windows:** `tools/audit_c_names.py`
  `--adjudicate` tool landed; the original name mismatch counts were
  divided into shared, SDK-parked, own-name-holder and real carve cases.
  Six C-row VM_DON renames were prepared, temporarily blocked while
  the witnessed oracle was unavailable.
- **November 21, final window:** oracle recovered from preserved CHD
  inputs; six VM_DON copies landed; g3_eu and mainmenu_eu non-lane stale
  C families repaired; last log reports **8/8 full-image matching
  at `a13c6f92`** and explicitly parks remaining cases.
- **November 22 documentation review:** [STATUS.md](STATUS.md) and
  [WORK_QUEUE.md](WORK_QUEUE.md) become the current entry points.
  Separately, CI and toolchain integrity were improved in
  `dfd10e79` and `2d5e0673` but the retail 8/8 gate has **not
  been independently rerun on those newer commits**.

## Writing future research

Prefer a focused file for new subsystem evidence, with:
target/ROM/VA, original file or yaml rows, exact cross-region mapping,
verified/inferred/refuted labels, a concise conclusion, and the next
specific research question. Cross-link it here and update
[WORK_QUEUE.md](WORK_QUEUE.md) when a task closes.

Do not grow the two-million-character TASKS.md just to narrate
every compiler experiment or duplicate an older checkpoint. Existing
historical contents remain available for citation and provenance.

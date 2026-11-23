# G3 R2 pass 1 — the shared-SDK C-row classification sample

**R2 pass 1 — 2026-11-23.** Bounded **read-only source review** per
[WORK_QUEUE.md](../WORK_QUEUE.md) R2: 16 shared C rows sampled from the
per-target `coverage_report.py --json --rows` output, each row's entire
source file read this window, each row's ownership cross-checked against
the live YAML-derived JSON (row kind, VRAM, extent, SDK-evidence bytes),
never from the filename. Registry entries added at the **g3_jp instances
only** — the semantic-recovery primary target — keeping the pass inside
the 10–20-function bound; the other target instances stay unreviewed and
are counted separately by the report. No source, YAML, asm or oracle
change. This note is a qualitative classification record, **not** a
retail SHA-1 witness and not a gameplay-recovery percentage.

## Method

1. `python3 tools/coverage_report.py --json --rows` over all eight
   targets; candidate rows drawn from the **largest shared unreviewed
   C-row names** (≥2 targets carrying the name as a live `c` row,
   ranked by summed bytes), with the boot targets and `g3_jp` both
   represented; already-registered names excluded.
2. For every sampled row the **entire** `src/<name>.c` was read and the
   tier judged on the full body: `semantic_c` (intelligible C, no inline
   asm), `hybrid` (meaningful C mixed with pinned asm), `asm_preserved`
   (algorithm lives in handwritten extended asm; not semantic C) —
   tiers per [COVERAGE.md](../COVERAGE.md).
3. `config/coverage_reviews.json` extended only after the full read, one
   narrow per-row evidence string each; suite re-run 299/299 after the
   extension; `--strict` report accepts all entries.

## The sample

16 functions, all carried by one shared `src/<name>.c`; instance counts
from the live JSON (kind `c` rows per target); g3_jp row extents
SDK-evidenced in full in every case.

| Row (g3_jp VA) | Tier | Targets carrying the row | g3_jp extent | Evidence (full read) |
| --- | --- | --- | --- | --- |
| [SsSeqCalledTbyT](../../../src/SsSeqCalledTbyT.c) 0x8006BF8C | semantic_c | 8 | 0x274 | Sequencer tick dispatcher over the 0xAC-stride track table: guard re-entry, slotbits scan, nested cresc/decresc/tempo arms inside the play arm, raw-arg stop arm. |
| [SsSetSerialVol](../../../src/SsSetSerialVol.c) 0x8006BD58 | semantic_c | 8 | 0x160 | Builds the 0x28 `SpuSetCommonAttr` record (mask 0xC0/0xC00, `vl*0x7FFF/0x7F` clamp-scale) and forwards it. |
| [GsGetTimInfo](../../../src/GsGetTimInfo.c) 0x8004F624 | semantic_c | 8 | 0xE4 | TIM header walker: bit-3 image-present leg, CLUT round-down-to-4, separate pixel/CLUT walkers. |
| [GsSetLightMode](../../../src/GsSetLightMode.c) 0x8005DDE8 | semantic_c | 6 | 0x8C | Mode 0..3 goto-chain onto the shared static, printf error leg. |
| [GsClearOt](../../../src/GsClearOt.c) 0x8005DD90 | semantic_c | 8 | 0x58 | OT struct writer (top/bottom/tail, `4 << width` byte span) + one forwarded clear call. |
| [GsMapModelingData](../../../src/GsMapModelingData.c) 0x8004F5AC | semantic_c | 6 | 0x78 | TMD relocation walker: flag/count reads, three-field `+=` base loop, addend spelled through the fixed base. |
| [_SsUtBuildADSR](../../../src/_SsUtBuildADSR.c) 0x8006E620 | semantic_c | 8 | 0x8C | Packs the halfword ADSR record into the two SPU attribute words (signed flags, shift-then-mask rates). |
| [ScaleMatrixL](../../../src/ScaleMatrixL.c) 0x80049B80 | asm_preserved | 8 | 0x124 | Left-scaling LIBGTE member; entire product pipeline one volatile asm block, wrapper only `m[4]=last; return`. |
| [ScaleMatrix](../../../src/ScaleMatrix.c) 0x8004A1B0 | asm_preserved | 8 | 0x124 | Right-scaling twin; same all-asm block shape (five unrolled multu blocks, delay-slot store). |
| [OuterProduct12](../../../src/OuterProduct12.c) 0x80051B18 | asm_preserved | 8 | 0x58 | Cop2 control save/install, GTE op as `.word`, swc2 stores; unreachable from plain C. |
| [ApplyMatrixSV](../../../src/ApplyMatrixSV.c) 0x8004A130 | asm_preserved | 8 | 0x5C | Five ctc2 rotation loads, mvmva `.word`, mfc2/sh stores through the register-var return. |
| [RotTransPers4](../../../src/RotTransPers4.c) 0x80052210 | asm_preserved | 8 | 0x80 | rtpt over three vertices + rtps on the fourth, stacked-arg SXY stores, combined FLAG, SZ3>>2 return. |
| [RotAverageNclipColorDpq3_1](../../../src/RotAverageNclipColorDpq3_1.c) 0x8005DA08 | asm_preserved | 6 | 0x100 | Three single rtps, per-vertex IR0 restore before each NCDS, nclip/avsz3 `.word` spellings, retail branch words pinned. |
| [func_800492F8](../../../src/func_800492F8.c) 0x800498E0 | asm_preserved | 8 | 0x110 | GTE rotation-matrix composer: SetRotMatrix head + three strided MVMVA passes, whole body one asm block. Auto name kept (prototype unattested). |
| [func_8005E4E8](../../../src/func_8005E4E8.c) 0x80049FD4 | asm_preserved | 6 | 0x10C | Compose-rotation, in-place form: stages from and commits at (a1), three MVMVA passes, one asm block. |
| [func_8005E3DC](../../../src/func_8005E3DC.c) 0x80049EC8 | asm_preserved | 5 | 0x10C | Byte-identical twin of func_8005E4E8 except commit destination ((a0)) and return staging; one asm block. |

Registry delta: `g3_jp` reviewed rows 5 → 21 (4→11 semantic_c,
1→10 asm_preserved); reviewed bytes 528 → 4,180 of 12,640 g3_jp C bytes.
All-target reviewed-byte totals are unchanged because only g3_jp
instances were registered.

## Findings

1. **The sample's tier split is 7 semantic_c : 9 asm_preserved : 0
   hybrid.** The semantic tier is exactly the LIBGS/LIBSND
   wrapper-and-walk class (TIM walking, OT clearing, TMD relocation,
   ADSR packing, serial-volume attribute building, light-mode setting,
   sequencer ticking). No sampled row mixes meaningful C with pinned
   asm; the split is clean, which supports treating the landed C corpus
   as two disjoint landing classes.
2. **The GTE math family is asm_preserved by toolchain necessity, not by
   an ownership gap.** Every cop2/GTE command in the sample is emitted as
   its exact retail `.word` (GNU as has no GTE mnemonics) or via lwc2/
   swc2/ctc2/mfc2 moves inside one volatile block; plain-C decomposition
   additionally loses retail's load scheduling (documented in the
   RotTransPers4 header). These rows are at their landing ceiling; the
   honest expectation is that the whole LIBGTE math cluster stays
   asm-backed.
3. **The three unknown-name rows sampled are GTE compose-rotation
   members, not game logic** — func_800492F8 (0x110 composer),
   func_8005E4E8/func_8005E3DC (the 0x10C in-place/copy twins). They sit
   adjacent to the landed SetRotMatrix/ApplyMatrix family and behave as
   SDK-like math. They are naming candidates for the curated namespace,
   but naming is **not** exercised here (the R3 shared-name lane and the
   curated-file rules govern renames; this pass renamed nothing).
4. **Reuse shape: no target-divergent copies in the sample.** Every
   sampled source is one shared file across x5–x8 target instances
   (x8 for ten of the sixteen), and the JSON shows each instance fully
   SDK-evidenced at its g3_jp placement. Region divergence in this
   sample is confined to per-target data aliases (documented in each
   header), not to body drift.
5. **What remains opaque:** none of the 16 sampled rows touch game-owned
   state (no comm-buffer, object-pool, laser or mode-dispatch references
   appear anywhere in them), reinforcing the STATUS.md statement that
   the recovered C tier so far concentrates in SDK plumbing while the
   game proper stays assembly-backed. The rows that would answer the
   "which C rows reconstruct behavior" question for **game** code live
   in the origin-unattributed C share (1.60% of unattributed mapped
   bytes) — that population is the natural next R2 sampling frame.

## Next R2 step

One bounded follow-up pass over the **origin-unattributed C rows**
(`origin_unattributed_c_bytes` per target from the same JSON): classify
whether the currently landed unattributed C is game-side behavior or
SDK-adjacent glue, extending the registry only where a full row read
supports the tier. The hybrid tier also remains unsampled after this
pass (the two registered hybrid entries predate it).

## Pass 2 (same window) — the origin-unattributed C rows

The follow-up frame executed immediately: the unattributed C population
is small and structured (g3_jp 12 rows / 2,088 bytes; sces_00269 5 rows /
92 bytes; slps_00270 6 rows / 108 bytes; g3_eu 22 rows / 7,360 bytes are
the extremes), and ten more rows were fully read and registered —
9 g3_jp instances + the one g3_eu hybrid:

| Row (instance VA) | Tier | Extent | Evidence (full read) |
| --- | --- | --- | --- |
| [func_8005A13C](../../../src/func_8005A13C.c) g3_jp 0x8005A13C | asm_preserved | 0x1CC | Recursive triangle-subdivision driver, front half: one file-scope `__asm__` string of verbatim retail hand-asm bytes (depth cull, screen X/Y bands, midpoint splitter). |
| func_8005A92C / func_8005B42C / func_8005BD4C g3_jp | asm_preserved | 0x1CC ×3 | The x20 byte-identical wave's other g3_jp members; same hand-asm unit, differing only in the `.globl` row name. |
| [SetVertex0](../../../src/SetVertex0.c) / [SetVertex1](../../../src/SetVertex1.c) / [SetVertex2](../../../src/SetVertex2.c) g3_jp 0x8004E980/90/A0 | asm_preserved | 0x10 each | LIBGTE fifo members: two lwc2 cop2 loads each; cop2 unreachable from plain C. |
| [ReadSZfifo3](../../../src/ReadSZfifo3.c) / [ReadSZfifo4](../../../src/ReadSZfifo4.c) g3_jp 0x80052290/A4 | asm_preserved | 0x14/0x18 | LIBGTE fifo members: swc2 stores of the SZ lanes; whole body inline asm. |
| [func_800642A0](../../../src/func_800642A0.c) g3_eu 0x800642A0 | **hybrid** | 0x548 | The game-side SPU reset/init driver (`_spu_init` family): real decompiled C (nine x3 timeout spins, SPUSTAT wait, 24-voice sweep, convergent finish) with exactly one zero-byte memory-clobber barrier asm; registered hybrid because semantic_c forbids inline asm while the substance is C. |

Registry delta: g3_jp reviewed rows 21 → 30 (19 asm_preserved), reviewed
bytes 4,180 → 6,112 of 12,640 C bytes; g3_eu gains its first hybrid
(1,352 bytes). Suite 299/299 after the extension; `--strict` accepts all
entries.

### Pass-2 findings

1. **The unattributed C tier is NOT SDK-adjacent glue — it is mostly
   game-side code preserved as hand asm.** The recurring 0x1CC four-up
   per target (the x20 byte-identical wave over mainmenu_eu / g3_jp /
   g3_eu / g3org_jp / g3org_eu) is a frustum-honoring recursive triangle
   subdivision driver feeding a display-list builder: game-owned
   rendering, landed verbatim as a file-scope asm string because gcc
   emits no cfc2 and the chunks are hand-scheduled. Its recursive tail
   sits in a **mis-typed data row** (`data_8005A308` per the source
   header) — a known yaml-hygiene item, not re-measured here.
2. **Some unattributed rows are plain SDK members without committed
   anchor evidence.** SetVertex0-2 / ReadSZfifo3/4 are LIBGTE fifo
   helpers; their "unattributed" label reflects the committed archive
   census, not unknown origin. This is the concrete demonstration of the
   COVERAGE.md rule that UNATTRIBUTED must not be read as "game".
3. **The hybrid tier is live and first proven on game-side C**:
   func_800642A0 is a real decompiled game function (SPU init) whose
   only asm is a zero-byte barrier; the tier boundary (semantic_c
   refuses inline asm) puts it in hybrid despite its C substance —
   the schema works as designed.
4. **Origin share correction:** of g3_jp's 2,088 (0x828) unattributed C
   bytes, 0x730 (the 0x1CC four-up) are game-side and 0x5C are
   evidence-gap SDK members (SetVertex0-2 + ReadSZfifo3/4); the remaining
   0x9C are the three already-reviewed palette rows. g3_jp's
   unattributed C population is now **fully reviewed** — zero unreviewed
   rows remain in the frame.

### Next R2 step (updated)

The remaining unattributed-C mass sits at **g3_eu (22 rows / 7,360
bytes)** and **mainmenu_eu (20 rows / 4,224 bytes)** — mostly the 0x1CC
wave plus EU singleton rows (func_80052038 owner-gated, func_800642A0
now reviewed). A bounded pass 3 would classify the g3_eu/mainmenu_eu
singletons not covered by the wave and the owner gates. After that, the
R2 lane's remaining value is sampling the **asm** rows' C-wrapper
boundaries, which overlaps R1's ownership work — coordinate there
instead of duplicating.

## Pass 3 (2026-11-23, later window) — the g3_eu/mainmenu_eu unattributed-C singletons

Bounded **read-only source review** per the frame above: 13 rows, every
row's entire source file read, every placement verified against its live
target YAML row (never the filename), registry entries added at the
sampled instances only. Excluded from the frame: the 0x1CC wave members
(pass 2's game-owned classification, instance registration pending), the
owner gate `func_80052038`, the fifo family (ReadSZfifo3/4, SetVertex0-2
— classified at the g3_jp instances in pass 2), and the rows already
registered before this pass (g3_eu func_80047804 semantic_c, MulMatrix
asm_preserved, func_800642A0 hybrid; mainmenu_eu func_80034ACC /
func_80034804 semantic_c, func_8002A9F8 hybrid). No source, YAML, asm or
oracle change.

| Row (instance VA) | Tier | Extent | Evidence (full read) |
| --- | --- | --- | --- |
| [func_80067690](../../../src/func_80067690.c) g3_eu 0x80067690 | **hybrid** | 0x438 | The libsnd SVM (VMANAGER) init, member identity proven (psyq row-stream kind-0x30 walk + def-row offset math, header note); real decompiled C (zero sweeps 0xC0/0x18/0x10, register-ternary 0x18 voice cap, per-voice 0x34-stride record init by DLABEL indexing, SPU voice-register run through `*D_800AB874`) with register-asm locals ($5/$4/$2 pins), two zero-byte barriers and one materializer. Single caller func_8006AC04 (`ori a0,0x18` delay slot). `_svm_damper` rename claim owner-gated (omf_pubsyms pin) — no rename exercised. |
| [func_80048908](../../../src/func_80048908.c) g3_eu 0x80048908 | **hybrid** | 0xc0 | Write-all host loop over the LIBSN `_SN_write` member: unsigned 0x8000 chunk guard, accumulate/bail −1, stop on short write, len==0 shares the return-total tail; one register-asm var pins `total` to $18 (the banked _SN_write idiom), rest plain C. |
| [func_8004682C](../../../src/func_8004682C.c) g3_eu 0x8004682C | semantic_c | 0xdc | Four thin void wrappers over the palette-fade/UV helper func_8004427C (`x*4+0x100`/`0x14`, `0x17`, two constant-pair calls); plain C, no asm; shaping laws read off the landed retail assembly. |
| [func_80062840](../../../src/func_80062840.c) g3_eu 0x80062840 | semantic_c | 0x94 | CD host-command glue: command 0xE with a one-byte stack arg, optional `flags&0x100` arm registering `data_ready_callback` + func_80063364 through the CD callback pair, shared 0x1B continuation. |
| [func_8006B648](../../../src/func_8006B648.c) g3_eu 0x8006B648 | semantic_c | 0x78 | Three functions: range-guarded slot clear (`idx>=3` → 0, else zero the halfword at `*D_800ABA5C + idx*16`, return 1) + two delay-slot constant wrappers feeding func_800653AC (1, 0). |
| [func_8006AD50](../../../src/func_8006AD50.c) g3_eu 0x8006AD50 | semantic_c | 0x40 | Two one-call wrappers feeding func_8006AC04 with constants 0/1 materialized in the jal delay slot; game-authored glue (both jal'd from func_80028140). |
| [func_80046660](../../../src/func_80046660.c) g3_eu 0x80046660 | semantic_c | 0x30 | The 0x4B palette-fade wrapper, word stream identical to mainmenu_eu's func_8005AC68 with only the callee delta (func_8004427C vs func_80058884). |
| [func_8004E29C](../../../src/func_8004E29C.c) g3_eu 0x8004E29C | semantic_c | 0x20 | Non-leaf wrapper forwarding to the target-curated local LIBGTE SetGeomScreen copy; a0 passthrough is the whole marshalling; game-authored (caller func_80022B5C). |
| [func_8005E16C](../../../src/func_8005E16C.c) g3_eu 0x8005E16C | semantic_c | 0x10 | Fixed-slot long store committing the argument into D_80171EA0; reached from func_80022B5C. |
| [func_8005E244](../../../src/func_8005E244.c) g3_eu 0x8005E244 | semantic_c | 0x10 | Fixed-slot long store into D_8016AB6C; reached from func_8002A2CC and func_80022B5C. |
| [func_8005AE34](../../../src/func_8005AE34.c) mainmenu_eu 0x8005AE34 | semantic_c | 0x3c | Palette-fade wrapper family member — the g3_eu func_8004682C first wrapper's word stream verbatim (`x*4+0x100` fold, `0x14` third arg) with callee func_80058884. |
| [func_8005AC68](../../../src/func_8005AC68.c) mainmenu_eu 0x8005AC68 | semantic_c | 0x30 | Palette-fade wrapper carrying the family's **fifth constant 0x4B** (not in the landed g3_eu row); the same twelve-word body also sits at g3org_jp (src/func_80043E94.c) — one C shape, three targets, callee extern is the only per-target delta. |
| [func_8005AE70](../../../src/func_8005AE70.c) mainmenu_eu 0x8005AE70 | semantic_c | 0x30 | Palette-fade wrapper, the g3_eu second-wrapper shape verbatim (`0x17` third arg) with callee func_80058884. Same NAME as g3_eu's separate 0x1CC wave row at the same VA 0x3B670 — a shared-name case owned by the R3 lane; classification only, no rename. |

Registry delta: 39 → 52 entries; g3_eu reviewed rows 3 → 13 (9
semantic_c / 3 hybrid / 1 asm_preserved), reviewed bytes 1,684 → 3,620
of 18,340; mainmenu_eu reviewed rows 3 → 6 (5 semantic_c / 1 hybrid),
reviewed bytes 2,120 → 2,276 of 14,156. All-target reviewed rows now 26
semantic_c / 5 hybrid / 21 asm_preserved (14,396 bytes). Suite 299/299
after the extension; `--strict` accepts all entries.

### Pass-3 findings

1. **The EU singleton population is ordinary game-side C, not one more
   SDK cluster.** 11 of 13 rows are semantic_c with zero inline asm —
   the palette-fade wrapper family (constants 0x14/0x17/0x4B across
   g3_eu/mainmenu_eu/g3org_jp, callee extern the only per-target
   delta), CD host-command glue, the init-driver constant wrappers, the
   slot-clear trio and two fixed-slot stores. The strongest multi-target
   one-src class yet seen in the C tier: func_8005AC68's twelve-word
   body is byte-identical across three targets.
2. **The hybrid pair is register-pinned decompiled C, heavier than pass
   2's single-barrier precedent.** func_80067690 pins three registers
   ($5/$4/$2) with two zero-byte barriers and one materializer; the SVM
   identity is *proven*, not inferred — the game's own cc1 2.6.3-PSX
   build of the libsnd VMANAGER init. func_80048908 pins `total` to $18.
   Both sit at their landing ceiling short of a compiler-flag exception;
   neither is a semantic-C candidate.
3. **A same-name different-row case is documented, not "fixed".**
   mainmenu_eu's func_8005AE70 (0x30 wrapper) and g3_eu's func_8005AE70
   (0x1CC wave member, per-target override source `src/g3_eu/`
   func_8005AE70.c) live at the same VA 0x3B670 in their respective
   images. Shared-name ownership belongs to the R3 lane; this pass
   registered the classification and renamed nothing.
4. **Frame accounting closes exactly.** g3_eu's 7,316 unattributed row
   bytes = 1,936 this pass + 1,352 func_800642A0 (reviewed) + 64
   func_80047804 (reviewed) + 1,840 wave + 2,032 owner gate + 92 fifo
   family. mainmenu_eu's 4,224 = 156 this pass + 2,120 pre-registered
   big three + 1,840 wave + 44 fifo + 64 eight-byte mini family. The
   only unreviewed EU unattributed-C left is therefore the wave
   instances, the owner gate, the fifo instance registrations, and
   mainmenu_eu's eight 8-byte mini rows (64 bytes).

### Next R2 step (after pass 3)

**Pass 4 (tiny, closes the EU frame):** the mainmenu_eu 8-byte mini
family (func_8002E3C0/func_8002E3C8/func_8002FF04/func_80030978/
func_80030980/func_80030988/func_80030990/func_800309C8 — 8 rows,
64 bytes) plus instance-level registration of the already-classified
wave/fifo rows if instance byte-credit is wanted. func_80030990 is an
R3 Class-B shared name — classification only there. After that the EU
unattributed-C frame is fully reviewed and the R2 lane's remaining
value is the asm-row wrapper-boundary sampling, which overlaps R1's
ownership work — coordinate there instead of duplicating.

## Pass 4 (same window) — the mainmenu_eu 8-byte mini family

The frame above executed immediately: all eight rows fully read, every
placement verified against `config/splat.mainmenu_eu.yaml`
(0xCE10/0xCE18/0xE5C4/0xEF08/0xEF10/0xEF18/0xEF20/0xEF58, each 0x8).
Each source is **one empty void function** — the retail row is exactly
the two-instruction return, so the empty body IS the full behavior; all
eight registered `semantic_c` with per-row placement evidence.
func_80030990 additionally shares its name with sces_00269's 0xcc
sdk-tagged **asm** row (the R3 Class-B family) — classification only,
no rename, no yaml change.

Registry delta: 52 → 60 entries (34 semantic_c / 5 hybrid /
21 asm_preserved, 14,460 reviewed bytes); mainmenu_eu reviewed bytes
2,276 → 2,340 (semantic_c 1,940), of 14,156. Suite 299/299; `--strict`
accepts all entries.

### The EU unattributed-C frame after pass 4 — accounting

Every g3_eu/mainmenu_eu unattributed-C **singleton** is now reviewed:

- **g3_eu** (7,316 row bytes): 3,620 reviewed across this doc (pass 3 +
  pre-existing func_80047804/MulMatrix/func_800642A0); the only
  unreviewed remainder is 1,840 wave instances (classified game-owned
  in pass 2 at the g3_jp instances; per-instance registration pending) +
  2,032 owner-gated func_80052038 + 92 fifo instances (classified SDK
  in pass 2; per-instance registration pending).
- **mainmenu_eu** (4,224 row bytes): 2,340 reviewed; the only
  unreviewed remainder is 1,840 wave instances + 44 fifo instances,
  both already classified in pass 2.

The EU unattributed-C frame is therefore **fully reviewed at the
singleton level** — zero unknown-content rows remain; what is left is
instance-level bookkeeping of already-classified families and the
owner gate.

### Next R2 step (after pass 4)

1. Optional bookkeeping pass: register the wave/fifo **instance**
   entries (g3_eu/mainmenu_eu) to convert the pass-2 classification
   into instance byte-credit — mechanical, no new reads.
2. The last untouched unattributed-C frame is the boot targets
   (sces_00269 ~5 rows / ~92 bytes; slps_00270 ~5 rows / ~108 bytes
   beyond its registered row) — **check the do-NOT-grab lanes first**
   (slps boot copies = scan lane; the sces setIntr family is parked)
   before sampling.
3. Then the asm-row wrapper-boundary sampling, which overlaps R1's
   ownership work — coordinate there instead of duplicating.


## Pass 5 (same window) — the wave/fifo instance registration

The pass-4 next-step item 1 executed: the 15 pending target instances of
the two pass-2 classifications are registered — the 0x1CC hand-asm
subdivision wave (4 instances per target) and the LIBGTE fifo family
(SetVertex0-2 + ReadSZfifo3/4 at g3_eu; ReadSZfifo3/4 only at
mainmenu_eu, which does not carry the SetVertex trio as live `c` rows —
its 44 fifo bytes are exactly the ReadSZfifo pair). Bounded **mechanical
bookkeeping, no new source reads**: the classification evidence was
banked by pass 2's full reads at the g3_jp instances; this pass
re-verified the two mechanical facts per instance and registered them.

1. **Wave identity re-verified mechanically.** All eight EU wave-member
   bodies are byte-identical to the pass-2-reviewed g3_jp func_8005A13C
   modulo each file's own row name (normalize the name, whitespace-
   collapsed compare) — including the two per-target override sources
   (`src/g3_eu/func_8005AE70.c`, `src/mainmenu_eu/func_8006F34C.c`),
   which are the same unit at 7,081 bytes each.
2. **Placement verified twice.** Every instance checked against the
   live YAML-derived `coverage_report.py --json --rows` output AND
   directly against `config/splat.g3_eu.yaml` /
   `config/splat.mainmenu_eu.yaml` (row present as a live `c` row; VRAM
   and extent per the report). Tier `asm_preserved` carried from pass 2.
   No source, YAML, asm or oracle change.

| Instances | Tier | Placement (live YAML) | Basis |
| --- | --- | --- | --- |
| g3_eu func_80059B80 / func_8005A370 / func_8005AE70 / func_8005B790 | asm_preserved | 0x80059b80 / 0x8005a370 / 0x8005ae70 / 0x8005b790, 0x1cc each | pass-2 wave classification; body ≡ g3_jp func_8005A13C modulo row name |
| g3_eu SetVertex0 / SetVertex1 / SetVertex2 | asm_preserved | 0x8004e2bc / 0x8004e2cc / 0x8004e2dc, 0x10 each | pass-2 fifo classification (LIBGTE, lwc2 cop2 loads) |
| g3_eu ReadSZfifo3 / ReadSZfifo4 | asm_preserved | 0x80051bf4 (0x14) / 0x80051c08 (0x18) | pass-2 fifo classification (LIBGTE, swc2 SZ stores) |
| mainmenu_eu func_8006E05C / func_8006E84C / func_8006F34C / func_8006FC6C | asm_preserved | 0x8006e05c / 0x8006e84c / 0x8006f34c / 0x8006fc6c, 0x1cc each | pass-2 wave classification; body ≡ g3_jp func_8005A13C modulo row name |
| mainmenu_eu ReadSZfifo3 / ReadSZfifo4 | asm_preserved | 0x800660d0 (0x14) / 0x800660e4 (0x18) | pass-2 fifo classification (LIBGTE, swc2 SZ stores) |

Registry delta: 60 → 75 entries (34 semantic_c / 5 hybrid /
36 asm_preserved); all-target reviewed bytes 14,460 → 18,276 (+1,932
g3_eu, +1,884 mainmenu_eu); g3_eu reviewed rows 13 → 22 (bytes 3,620 →
5,552), mainmenu_eu reviewed rows 14 → 20 (bytes 2,340 → 4,224). Suite
299/299 after the extension; `--strict` accepts all entries.

### The EU unattributed-C frame after pass 5 — accounting

- **mainmenu_eu is CLOSED at the instance level.** All 4,224
  unattributed-C bytes now sit on reviewed rows (2,340 singletons +
  1,884 wave/fifo instances); zero unreviewed unattributed-C rows
  remain in the target.
- **g3_eu holds exactly two unreviewed unattributed-C rows, both gated
  outside R2.** The live frame reconciles exactly: 7,360 unattributed
  bytes = 5,284 on reviewed rows (5,552 reviewed of which 268 are
  anchor-covered) + 2,032 owner-gated func_80052038 (the SDK-ownership
  gate, do-NOT-grab) + 44 unattributed of func_8006AC04's 0x14c row
  (the disc-return runbook's Phase D landing target, runbook-gated).
- The wave is now registered at 12 of its 20 instances (g3_jp 4,
  g3_eu 4, mainmenu_eu 4); g3org_jp/g3org_eu (8 instances) remain a
  future mechanical pass of this same motion, and mainmenu_jp's
  instances are lane-owned — untouched here.

### Next R2 step (after pass 5)

1. The boot-target unattributed-C rows (sces_00269 ~5 rows / ~92 bytes;
   slps_00270 ~5 rows / ~108 bytes beyond its registered row) are the
   last untouched C frame — **check the do-NOT-grab lanes first**
   (slps boot copies = scan lane; the sces setIntr family is parked)
   before sampling.
2. The g3org_jp/g3org_eu wave/fifo instance registration (8 + pair
   instances) — the same mechanical motion as this pass, whenever the
   lane is next opened.
3. Then the asm-row wrapper-boundary sampling, which overlaps R1's
   ownership work — coordinate there instead of duplicating.

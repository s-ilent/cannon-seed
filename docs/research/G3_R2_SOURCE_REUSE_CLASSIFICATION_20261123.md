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


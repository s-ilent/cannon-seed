# G3 R1 pass 12 — the MAIN_SEQUENCE script interpreter and the 4-lane rank step

**R1 pass 12 — 2026-11-24 (window cron-20261124-1409).** Bounded **JP-first
read-only static analysis** per [WORK_QUEUE.md](../WORK_QUEUE.md) R1 and
the next-target record in
[G3_MODE_SEQUENCE_ATLAS_20261122.md](G3_MODE_SEQUENCE_ATLAS_20261122.md)
("trace one of the sustained `MAIN_SEQUENCE` helpers — start with
`func_80044F60` and `func_80044B7C`"). Source-only: no retail SHA-1
comparison, no runtime capture, no C conversion, no rename, no YAML or
oracle change. All claims below are read off the tracked tree
(`asm/g3_jp/nonmatchings/*.s`, `asm/g3_eu/nonmatchings/*.s`,
`config/splat.*.yaml`, the extracted data `.s` views).

## The carve context

Both targets are **interior sub-blocks of one giant walk row**:
`config/splat.g3_jp.yaml` `[0x2534C, asm, func_80044B4C] # 0x1eac`
(VA 0x80044B4C..0x800466F8). The nonmatching file's per-block labels are
carve points, not function boundaries — the two "functions" the atlas
names are contiguous instruction ranges inside it:

- **func_80044B7C**: real body 0x80044B7C..0x80044D2C (0x1B0 bytes; the
  flow enters at the 0x24 head block and returns only in the last block's
  `jr $ra` at func_80044D08's tail). `func_80044D2C` starts the next
  real unit.
- **func_80044F60**: real body 0x80044F60..0x80045044 (0xE4 bytes; the
  returns sit in the shared epilogue block func_80045044).

## func_80044F60 — the per-frame script command interpreter (0xE4)

Verified from `asm/g3_jp/nonmatchings/func_80044B4C.s` (glabels
func_80044F60/func_80044FE4/func_80045034/func_8004503C/func_80045044):

1. **Gate**: `*D_800AC3C4 & 0x20` must be set, else immediate return.
   All of D_800AC3C4/D_800AC384/D_800AC58C/D_800AC17C are bare
   link-time addresses ≥ 0x800AC000 — **runtime RAM beyond the mapped
   image** (see the runtime-RAM law below).
2. **Cursor**: `s0 = *D_800ABE14` — the committed script pointer (also
   runtime RAM). Read opcode halfword `t0`; `s0 += 2`.
3. **Terminator**: opcode −1 → return **without committing** the cursor
   (the epilogue restores s0 from the stack; the store to D_800ABE14 at
   func_8004503C happens only on the dispatch path).
4. **Wait-gate**: if the signed halfword operand 1 read from the stream
   satisfies `*D_800AC384 < operand` → return **without committing**
   (the operand is re-read next frame — a frame-count wait opcode).
5. **Mode-gate**: if the signed mode `*D_800ABF9C` != operand 1 → the
   general dispatch; if mode matches **and** opcode ∈ {0xC, 0xD, 0xE,
   0xF} → return without commit (a mode-gated opcode class).
6. **Dispatch**: opcode < 0 → `func_800450F4(op, arg1, arg2, arg3)` (the
   long form: three more inline halfword args, sign-extended); opcode ≥ 0
   → `func_80045088(op)` (short form). Both executors re-test the 0x20
   gate; the short form additionally fires only when the once-latch
   `*D_800AC58C` is clear and sets it — the long form has no latch.
7. **Commit**: only the dispatch path stores `s0` back to D_800ABE14.

## The executor chain — command table and handlers

Verified from `asm/g3_jp/nonmatchings/func_8002A2DC.s` (walk row
`[0xAADC, asm, func_8002A2DC] # 0x9910`) and
`asm/g3_jp/nonmatchings/func_800280A4.s` (walk row
`[0x88A4, asm, func_800280A4] # 0x2220`):

- Both executors funnel into **func_8002FA9C** (real body
  0x8002FA9C..0x8002FB18): it walks the **command table D_800772F4**
  (mapped static data — inside `data_80071790`, yaml
  `[0x51F90, data, data_80071790] # 0xbe30`, at blob offset +0x5B64) of
  {opcode, handler-id} halfword pairs terminated by the −1/−1 sentinel,
  and on match calls **func_80029FC0(handler_id)**. Unknown opcode →
  return −1, no call.
- **func_80029FC0**: handler id < 0 → immediate return (func_8002A180
  is a bare epilogue; negative ids are no-ops). Non-negative: reads the
  per-handler multiplier `a1 = lh(D_80076CEC + id*2)` — **D_80076CEC**
  is mapped static data in the same blob at +0x555C, 64 halfwords,
  neutral value 0x7F — then scales it by `*D_800ABB54` and by
  `*D_800ABB5C` (both mapped, inside `data_80080048`), each product
  divided by 0x7F with the gcc `break` zero-check plumbing and printf
  error paths (fixed string source `t1 = 0x80016600`, string identity
  inferred). Reading 0x7F as the unity multiplier, the table values are
  per-handler **rate scales** (0x5A ≈ ×0.71, 0xB1 ≈ ×1.39, 0x9D ≈
  ×1.24, 0x2D ≈ ×0.35, 0x78 = ×1.2 — interpretation marked inferred;
  the arithmetic chain itself is verified).
- The dispatcher's command sites include **three `SsSetSerialVol`
  wrappers** (func_8002A23C / func_8002A26C / func_8002A29C — the libsnd
  serial-A/B/C volume members): the script system drives sequencer
  sound commands, tying it to the LIBSND tier registered in R2 passes
  1–2.

### The command table D_800772F4 — full decode (verified bytes)

46 records + sentinel, decoded from
`asm/g3_jp/nonmatchings/data/data_80071790.data.s`. The authoritative
machine-decoded pairing (opcode → handler id, order-preserving):

```
01→00 03→01 04→02 00→03 02→04 05→05 39→06 3A→07 3B→08 3C→09
0A→0D 06→0E 09→17 23→18 08→1A 22→1B 07→1C 11→1D 0B→1E 0C→1F
0D→20 0E→21 0F→22 12→23 13→24 14→25 15→26 16→27 17→28 18→29
19→2A 1A→2B 1B→2C 1C→2D 1D→2E 10→2F 25→30 3E→31 40→32 3D→33
3F→34 41→35 42→36 43→37 44→38 45→39        FFFF FFFF (sentinel)
```

Handler ids occupy 0x00..0x39; opcodes 0x0C..0x0F (the interpreter's
mode-gated class) map to handlers 0x1F..0x22.

## The script stream and its reset

- **Reset** func_80044A90 (in `asm/g3_jp/nonmatchings/func_80033C44.s`,
  the game main module walk row): zeroes the wait counter D_800AC384
  and D_800ABEAC, then sets BOTH the committed cursor D_800ABE14 and a
  second pointer D_800AC3B4 to **D_800ABA08** — the **script stream
  base**, mapped static data inside `data_80080048` (yaml
  `[0x80048, data, data_80080048] # 0x2bfb8`) at blob offset +0x2B9C0.
- func_80044A90 sits immediately beside the producer-pool wipe
  func_80044A6C/func_80044A78 (store-zero loop over D_8016B014, 124
  records × 0xAC) — the same pool the producer-records atlas decoded —
  grouping the mode-reset helpers together.
- The stream content itself (the retail sequence scripts, halfword
  opcodes + inline args from D_800ABA08) is **not decoded here** — it
  is the natural next read now that the opcode semantics are known.

## func_80044B7C — the 4-lane metric rank step (0x1B0)

Verified from `asm/g3_jp/nonmatchings/func_80044B4C.s` (glabels
func_80044B7C..func_80044D08):

1. **Inputs**: the live-lane bitmask `*D_800AC17C` (runtime RAM), the
   4-lane state table D_801474FC (runtime RAM, **stride 0x8C**, lane
   metric word at +0x34), the staging table D_80144714 (runtime RAM,
   4 records × 8 bytes).
2. **Registration loop** (4 iterations, bit v1 = 1<<lane): live lane →
   staging record = {word = lane+0x34 metric, half = lane index}; dead
   lane → record zeroed.
3. **Sort**: a full 4-pass exchange sort of the four staging records
   **descending by metric word** (swap when record[i] < record[i+1]),
   using the 8-byte stack temp; the compare/swap loop structure and the
   0x8 stride are verified instruction-level.
4. **Rank**: walking the sorted records, each lane's rank (1 = highest
   metric; ties share the previous rank — the rank counter only
   advances on a strictly smaller metric) is stored into
   **D_80144794[lane_index]** = {word = metric, half = rank} (indexed
   by the record's lane halfword, not sorted position).
5. **Writeback** (4 iterations): for each lane, the metric word is
   stored to the 0x10-stride output record D_80170394[lane]+4, the rank
   is tested against the SAME live bitmask at the rank's bit position
   (`*D_800AC17C >> rank & 1`): set → rank stored to both
   D_80170394[lane]+8 and the lane record's +0x38 field
   (D_801474FC[lane]+0x38); clear → 0 stored. Then `jr $ra`.

Reading: a per-frame **podium/rank computation across four lanes**
(scores or another per-lane metric, ranked descending, gated by a
live-lane mask whose bit positions coincide with the ranks). "Lane"
interpretation (player/cannon-seat/channel) is marked inferred — the
mechanics are verified.

## The caller: the slot-4 MAIN_SEQUENCE callback

Both targets are called from **func_80042A20** (`func_80033C44.s`,
0x80042A88 / 0x80042AB8) — the slot-4 callback the mode atlas already
profiles. The stage order verified here, extending the atlas record:
`D_800ABEDC &= ~0x10`; mode-select `func_80040460` / `func_80024730`
via signed `*D_800ABF9C`; `D_800AC29C = 1`; then **func_8003E268 →
func_80044F60 → func_80044D2C → func_800451B4 → (D_800AC1DC = 1) →
func_8003F198 → func_8003E784 → func_80044B7C** → … The interpreter is
the second stage, the rank step a later one; both sit inside the
sustained (non-mode-advancing) active-processing slot exactly as the
atlas concluded.

## EU twins

- EU walk row: `[0x24FB4, asm, func_800447B4] # 0x1eac` — same extent
  as the JP row (byte-twin row, different cut points: EU's sub-blocks
  differ in shape, e.g. an `intr_start_aux3` label the JP row lacks).
- EU interpreter: **func_80044BC8** (gate `*D_800ACC14 & 0x20`, cursor
  `*D_800AC664` — the EU aliases of D_800AC3C4/D_800ABE14; identical
  prologue/operand flow).
- EU rank head: **func_800447C4** (the walk row's second sub-block,
  0x20 — same `ori t0,3` / `ori v1,1` arming pair).
- EU command table: **D_80077B34** (inside the EU blob at
  `data_80071FD0`'s region), consumed by EU **func_8002F72C** — the
  func_8002FA9C twin, same walk-record compare structure. The table's
  retail content **byte-matches** the JP 46-record decode above.

## Runtime-RAM law (the pass's structural finding)

Every mutable script/rank state word touched by these functions — gate
D_800AC3C4, cursor D_800ABE14, wait counter D_800AC384, mode
D_800ABF9C, latch D_800AC58C, second pointer D_800AC3B4, bitmask
D_800AC17C, lane table D_801474FC, staging D_80144714, rank staging
D_80144794, rank output D_80170394 — is a **bare link-time address into
the region beyond the mapped yaml rows** (≥ 0x800AC000, plus the
0x8014xxxx/0x8017xxxx extended-RAM region): runtime RAM, zero-init at
boot, populated by the game. Only three backing objects are mapped
static data: the command table D_800772F4, the multiplier table
D_80076CEC (both in `data_80071790`), and the script stream
D_800ABA08 (in `data_80080048`). A C conversion of either target would
therefore need declarations for the runtime-RAM symbols — the same
class of work the landed SPU/comm-buffer conversions already carry.

## Evidence table (verified vs inferred)

| Claim | Level | Backing |
| --- | --- | --- |
| Interpreter gate/cursor/wait/mode/dispatch/commit flow | verified | asm/g3_jp/nonmatchings/func_80044B4C.s glabels func_80044F60..func_80045044 |
| Command table 46 records + sentinel, full pairing | verified | data_80071790.data.s dlabel D_800772F4 |
| Lookup walk + handler call | verified | func_8002A2DC.s glabel func_8002FA9C |
| Negative handler id = no-op return | verified | func_800280A4.s glabel func_8002A180 |
| Multiplier table + ×rate ÷0x7F chain | verified | func_80029FC0 head/body |
| Rate-scale reading of the multiplier values | inferred | values + arithmetic; no runtime sample |
| Rank: registration/sort/rank/writeback mechanics | verified | func_80044B4C.s glabels func_80044B7C..func_80044D08 |
| "Lane" = player/seat/channel semantics | inferred | mechanics only |
| Script stream base + reset chain | verified | func_80033C44.s func_80044A90 |
| Producer-pool wipe adjacency | verified | func_80044A6C/A78 vs the pass-7 atlas |
| EU twins (row, interpreter, rank head, table, lookup) | verified | asm/g3_eu yaml row + the four glabels/dlabels cited |

## Conversion-candidate ranking (L2-protocol, no landing exercised)

1. **func_80044F60 (0xE4)** — small, self-contained, game-owned, plain
   control flow, no cop2; the only complications are the runtime-RAM
   extern declarations and the shared epilogue block inside the walk
   row. Feasible **after a carve split** of the walk row (interior
   conversion is exactly what the render-prep atlas warns against
   scheduling in isolation) — split-first, then convert.
2. **func_80044B7C (0x1B0)** — same class; the four-pass exchange sort
   and rank indexing are plain C shapes. Same split precondition.
Both are ranked **below** any runbook-gated landing and are NOT
scheduled here; this pass only records feasibility.

## Next R1 question

Decode the **script stream** itself from D_800ABA08 using the verified
opcode semantics (46 commands, the wait/mode classes, the −1
terminator): segment it into the retail sequence scripts, map each
script to its trigger mode via the 0xC..0xF class and the mode operand,
and label the 46 handlers through the multiplier values and the
SsSetSerialVol sites. This converts the interpreter decode into a
"what plays when" sequence atlas — the direct continuation of the
mode-sequence and producer-records passes.

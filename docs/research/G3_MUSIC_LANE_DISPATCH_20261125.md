# G3 R1 pass 17 — the music lane: the dispatcher, the four mode handlers, the tick, and the note2pitch table

**R1 pass 17 — 2026-11-25 (window cron-20261125-1409).** Bounded **JP-first
read-only static decode** continuing
[G3_SOUND_BOOT_CHAIN_20261125.md](G3_SOUND_BOOT_CHAIN_20261125.md)'s next
question (1): the music-lane state the giant chunk writes — the per-lane
records at `D_80165242` (stride 0x44), the dispatcher `func_80029840` and
its four mode handlers `func_80029200`/`func_800292E8`/`func_800293C4`/
`func_800293FC`, the mirror family `D_800CFF00`/`CFF04`/`CFF14`/`CFF24`,
and the note2pitch table `D_800AB048` — the pass-12 "separate mixer lane"
made concrete. Source-only: no retail SHA-1 comparison, no runtime
capture, no C conversion, **no rename** (the two sdk-recorded pitch
helpers keep their func_ names; sdk-curation governs adoption), no YAML
or oracle change. Zero prior-pass corrections. One open remainder
recorded honestly (the tick entries' own caller).

## The two address families

Everything below splits into two strided arrays, both verified
instruction-level:

**A. The per-lane runtime records** — extended RAM, **stride 0x44**, four
lanes (0..3). The lane-0 mode word `D_80165242`; lanes 1..3 materialize
as `D_80165286`/`D_801652CA`/`D_8016530E` (the literal `%hi/%lo` forms in
func_800279CC's four-lane read — the machine check for both the stride
and the lane count). Every `lane*0x44` byte offset in the campaign's
music functions computes as `((lane<<4)+lane)<<2` — lane·17·4. Record
fields touched (relative to the mode word, all runtime RAM inside the
crt0 zero range `[0x800ABA8C, 0x80171F04)`):

| offset | field | writer |
| --- | --- | --- |
| −0x3E (`D_80165204`) | halfword, init 1, the mode-1 fade counter (inc 0→2) | func_80026B64 / func_800272C8 |
| −0x3C (`D_80165206`) | halfword, init 0 | func_80026B64 |
| −0x26 (`D_8016521C`) | halfword, init 1 | func_80026B64 |
| −0x24 (`D_8016521E`) | halfword, init 0 | func_80026B64 |
| −0x1C (`D_80165226`) | halfword, init 0; copied to lane 3 by the steal path | func_80026B64 / func_8002704C |
| −0x0A (`D_80165238`) | halfword at +0x14: the "current pair" selector (0 = pending pair) | — |
| −0x08..−0x02 (`D_8016523A..40`) | mode-8 handler's four shadow halves (rec +4..+7) | func_80029200 |
| **+0x00 (the mode word)** | the lane mode: 0 idle / 1 / 2 / 4 / 8 / 0x100 invalid | the binding layer's tag loop |
| +0x44·lane (mode-4 write) | `D_80165224 + lane·0x44`: mode-4's rec+4 copy | func_800292E8 |

**B. The in-image mirror family** — all ≥ 0x800AC000, runtime RAM beyond
the mapped rows (the pass-12 runtime-RAM law; inside the crt0 zero
range), all `lane*4` slots:

| block | slots | content |
| --- | --- | --- |
| `D_800CFEE4..EF0` | 4 words | the per-lane record POINTERS the dispatcher dereferences |
| `D_800CFEF4..CFF00` | 4 words | the slot GUARD words (init 1, tick re-arms 1, func_800279CC syncs with the live modes, read ≠ 0 before binding) |
| `D_800CFF04..CFF10` | 4 words | the mode mirrors, written by both tick entries |
| `D_800CFF14..CFF20` | 4 words | the per-frame REQUEST masks (the dispatcher's return), read by func_8002945C |
| `D_800CFF24..CFF30` | 4 words | the MASK words (block list), written by the binding layer as the request-word copy, read by func_8002945C classes 1–3 |
| `D_800CFE14..24` | 4 words | the saved music-mode words (work-struct field 0x11) |
| `D_800CFE94`/`D_800CFEBC` | 2 bases | the record pool: trigger bytes +0/+1, sub-records at +2/+0xA/+0x12/+0x1A |

## func_80029840 — the lane dispatcher (0xA4 with chunks)

Verified from `asm/g3_jp/nonmatchings/func_800280A4.s` (glabels
func_80029840..func_800298E4):

1. `a0` = the lane (sign-extended halfword); `a0 = *(D_800CFEE4 + lane*4)`
   — the bound record pointer; `mode = lhu(D_80165242 + lane*0x44)`.
2. Dispatch: mode **2** → `func_800293FC`; **4** → `func_800292E8`;
   **8** → `func_80029200`; anything else → `func_800293C4`.
3. The handler's return value rides back as the function result — the
   per-frame REQUEST mask (see the tick).

## The four mode handlers

All four read the bound record's parameter bytes and compute a request
mask; the byte-mask shape is common to three of them:
`mask = (((rec[2] ^ 0xFF) & 0xF9) << 8) | ((rec[3] ^ 0xFF) & 0xFF)` — an
inverted-bit request map over record bytes +2/+3 — with the tail test
`mask & 0x800`: set → return 0x800 alone (the override clamp), clear →
return the full mask.

- **func_800293FC (mode 2, 0x48+0x18)** — the position/pan pair:
  signed bytes rec+4 → `D_800AC594`, rec+5 → `D_800AC596` (the same words
  the ramp func_80029738 consumes and func_80029984 thresholds at −0xA).
  Return = the 2-bit flag pair built from rec+3 bits 2/3 (`0x40`/`0x20`
  shapes: bit2 clear → `0x40`; bit3 clear → `| 0x20`) — not the common
  byte mask.
- **func_800292E8 (mode 4, 0xD4+0x8)** — copies rec+4..+7 to the shadow
  halves `D_800ABDCC/CE/D0/D2` and rec+4 to the lane record +0
  (`D_80165224 + lane*0x44`); returns the common mask ORed with the
  "≥ 0x80" sign bits of the shadow pairs (rec+5 → `0x40`, rec+6 →
  `0x80`, rec+7 → `0x04`), then the 0x800 clamp.
- **func_80029200 (mode 8, 0x100+0x8)** — copies rec+4..+7 to
  `D_800ABDA4/A6/A8/AA` AND to the lane record −0x08..−0x02
  (`D_8016523A..40 + lane*0x44`); returns the common mask with the 0x800
  clamp (no sign bits).
- **func_800293C4 (default, 0x30+0x8)** — no shadow writes at all; just
  the common mask from rec+2/+3 with the 0x800 clamp. Idle lanes' modes
  (0) and the invalid mode 0x100 both land here, so an unbound lane
  still publishes a (zero-parameter) request mask every frame.

## The record type tags → the mode write (the binding layer's slot loop)

The binding layer (entry `0x80026D6C`, called from the not-yet-split
main data region via the raw word `0x0C009B5B` at 0x80022A04 in
`data_80022800.data.s` — the same data-row call form pass 16 used for
the sound re-attach) walks the four slots with `t0 = D_800CFF24`,
`a0 = D_80165242`, `a2 = D_800CFEE4` (func_80026F50's prologue):

- Slot bit NOT set in the binding bitmask `t1` → `sh zero → mode word`
  (the lane stops) and skip.
- Slot bit set → read the bound record's **byte +1 = the type tag**
  (func_80026F84) and map it, all branch-delay verified:
  **0x12 → mode 2, 0x23 → mode 4, 0x41 → mode 1, 0x53 → mode 8,
  anything else → 0x100** (the invalid mode). Then
  `D_800CFF24[slot*4] = D_800CFF14[slot*4]` — the mask word snapshots
  the last request word.
- The tag check `record[1] == 0x12` also exists as the standalone
  predicate func_800298E4 (0x30) — **zero references in g3_jp** (name,
  `jal`/`j` encodings 0x0C00A639/0x0800A639, data words): dead.
- The guard words gate the bindings: each of the six pointer writes
  (`D_800CFEE4 ← D_800CFE94+0` / `← D_800CFEBC+2`; `D_800CFEE8 ←
  D_800CFEBC+0` / `← D_800CFEBC+0xA`; `D_800CFEEC ← D_800CFEBC+0x12`;
  `D_800CFEF0 ← D_800CFEBC+0x1A`) reads its slot's guard word
  (`D_800CFEF4`/`EF8`/`EFC`/`CFF00`) first and binds only when ≠ 0;
  the pool-side trigger bytes (base+0 ≠ 0 with base+1 == 0x80 for the
  CFE94 path; base+0 == 0 and the target byte == 0 for the CFEBC
  paths) select which sub-record binds. The binding bitmask `t1`
  (bits 1/2/4/8 per slot) accumulates through the walk and feeds the
  mode writes above; the tail clears `gp+0xA8` when the walk started
  clean and returns `t1`.

## The tick — func_800276B8 and the 4-arg entry func_800270E8

Both sit in the caller walk row `[0x32FC, asm, func_80022AFC] # 0x4f44`
(VA 0x80022AFC..0x80027A40) and share the same skeleton (verified
instruction-level):

1. Mirror the mode: `D_800CFF04[lane*4] = lhu(mode word)` (both entries).
2. Mode 0 → return −1 (func_8002768C/func_800279A4 epilogues).
3. `mask = func_80029840(lane)`; `D_800CFF14[lane*4] = mask` — the
   request word the evaluators consume this frame.
4. **func_800276B8 path** (a1 gates the entry: a1 == 0 returns the
   accumulator `lw 0x868($gp)`): mode 2 → the ramp func_80029738;
   otherwise resolve the frame's requests in priority order —
   `func_8002945C(0x1000, class, lane)` → on failure 0x4000 → 0x8000 →
   0x2000, each success ORing a status bit (1/2/8/4) and stopping;
   mode 8 with no request satisfied → the ramp func_800295E0, mode 8
   with a satisfied request → the request chain (rec+0x14 word ≠ 0 →
   request `0x5`, then `0xA0`, `0x40`, `0x8`, `0x20`, `0x10`, `0x1`
   through func_8002945C class 1, status bits 0x10/0x20/0x40
   accumulated).
5. **func_800270E8 path** (a3 = the class argument): a3 == 1 →
   mode 2 → request `0x20`; mode ≠ 2 → request `0x800`, then the
   mode-8 chain (`0x40`/`0x8`); a3 ≠ 1 → mode 1 → the fade-counter
   path (request `0xA`/`0xC` picked by the record −0x26 halfword,
   counter `D_80165204 + lane*0x44` incremented 0→2 per accepted
   request) / mode 4+ shapes at func_800273B0+.
6. **The tail** (both paths): re-arm all four guard words
   (`D_800CFEF4..CFF00` ← 1, the four-store downward loop
   func_80027984), accumulate the result into `gp+0x868`.
7. **The lane-3 steal** (func_8002704C, entered when `gp+0xA8` == 1 and
   lane 0's mode == 8): lane 3's mode word ← 8, its pointer slot
   ← `D_800CFE94` (the pool base), five record halfwords copied from
   lane 0 (+0x22/+0x24/+0x28/+0x2C/+0x30), `D_80165304` (lane 3's
   +0x14) ← 0, mask word ← request word. `gp+0xA8` is set/cleared by
   func_800299BC/func_800299CC — func_800299BC is called from main's
   data region (the raw word `0x0C00A66F` at 0x800227B8 in
   `data_80022878.data.s`).
8. **The caller census (the open remainder):** neither tick entry has a
   caller in g3_jp — no `jal`/`j` by name, no encoded words
   (`0x0C019C3A`/`0x08019C3A`/`0x0C019DAE`/`0x08019DAE`), no raw
   pointer words in any data row, and the complete j/jal-word decode of
   both main-region data rows (`data_80022800`, `data_80022878`)
   contains no tick target. The driver is recorded as unidentified in
   this pass (a not-yet-carved region, a pointer table not yet mapped,
   or an interrupt-context caller are the candidate shapes; the
   initializer func_80026B64 and the scheduler func_800299D8 carry the
   same census result).

## func_8002945C — the request evaluator (0x1AC with chunks)

`func_8002945C(mask, class, lane)` — the ONLY funnel through which the
game tests the lanes' per-frame request words (six in-file call sites +
the tick chains):

1. `req = lhu(D_800CFF14 + lane*4)`; `mode = lhu(mode word)`; mode 0 →
   return 0.
2. class 0 → plain `req & mask` test. class 1 → additionally
   `(mask & CFF24[lane*4])` blocks. classes 2/3 → the same block check
   plus `D_800ABAE4 = 2` / `= 4` on commit.
3. **The budget:** when a class 1–3 request is mask-blocked, the global
   `D_800ABAE4` is decremented; when it reaches 0 the request force-
   commits and the budget resets to 2 (func_80029598).
4. Return 1 = the request's bit(s) were present in this frame's mask
   (and not blocked); the callers turn that into their state
   transitions.
5. `D_800ABAE4` (and `D_800ABADC`, `D_800ABB4C`) are zeroed by the
   scene-reset path func_80026AD0 (the same function that re-inits the
   0x1E/0x2D pan defaults).

## The two volume ramps

- **func_800295E0 (0x154 with chunks, mode-8 pair):** reads the lane
  record +0x14 word (`D_80165238 + lane*0x44`); nonzero → the CURRENT
  pair `D_800ABDAA−0x7F`/`D_800ABDA8−0x7F`, zero → the pending pair
  `D_800ABDA6−0x7F`/`D_800ABDA4−0x7F` (signed deltas from unity 0x7F).
  Big deltas (|d| outside ±0x20) pick a step — first delta: < −0x20 →
  1, ≥ 0x21 → 2; second: < −0x20 → 8, ≥ 0x21 → 4 — gated by the
  per-lane counter `D_80076CAC[lane*4]` (in-image mapped data at blob
  +0x551C, four zero words at boot, verified): the step fires every
  OTHER tick while the delta stays big (counter 0 → fire+1, next tick
  1→2, tail func_80029708/func_80029814 resets at 2).
- **func_80029738 (0x108 with chunks, mode-2 pair):** the same shape on
  `D_800AC596−0x7F`/`D_800AC594−0x7F` with the tighter band ±0x10 and
  counter `D_80076CBC[lane*4]` (blob +0x552C, four zero words).
- The sibling playlist tables sit between the counters and pass 15's
  multiplier table: `D_80076CCC` = {0x8, 0x1, 0x4, 0x2, 0x10, 0x80, 0x1,
  0x100} and `D_80076CDC` = {0x4, 0x2, 0x8, 0x1, 0x1000, 0x4000,
  0x1000, 0x4000} (8 request-mask halfwords each, verified bytes) —
  consumed by the scheduler func_800299D8.

## The scheduler func_800299D8 (the playlist walker)

Called with (gate, arg): gate 0 zeroes `gp+0xAA/AC/AE`; otherwise the
tick counter `gp+0xAA` increments (< 0x2710), then one slot round:
for each lane whose mode == 1 (the tag-0x41 mode), with `gp+0xAE` not
parked at −1, pull `lhu(D_80076CCC + cursor*2)` or
`lhu(D_80076CDC + cursor*2)` (the pool picked by the `s4` argument)
and fire it through func_80029B8C; the accepted responses drive the
`gp+0xAE` wait state (−1 parked, ~15 ticks between entries). The
scheduler and its callee func_80029B8C carry the same no-caller census
as the ticks. The music-mode save/restore pair func_8002658C/func_800265E4
persists `D_800CFE14[lane*4]` (four words) through work-struct field
0x11 (func_80025C1C/func_80025AD8) — called from main's data rows at
0x800224E0/0x80022704.

## The initializer func_80026B64 (0x208)

The per-lane boot (four iterations, `s2 += 0x44`): zero
`D_800CFF14[lane*4]` and `D_800CFF24[lane*4]`; run the per-lane helper
chain func_80027C28(0,0,lane), func_80027B04(0x1E−s6, 0x1E−s5, lane, 0;
stack 3), func_80027B04(0x1E, 0x1E, lane, 1; stack 5),
func_80027B04(0x2D, 0x2D, lane, 2; stack 7), func_80027B8C(0x2C0, 0x400,
lane), func_80027E04(0x7F, lane), func_80027E80(0x1E, lane),
func_80027FB0(0x2D, 0x2D, lane), func_80027EC0(0x1E, 0x1E, lane),
func_80027D84(0, lane), and the eight mixer-channel calls
func_80028144(±0x64, lane, ch 0..7); set the record halves
(`D_80165204`/`D_8016521C` ← 1, `D_80165206`/`D_8016521E`/
`D_80165226` ← 0), zero the mode word, arm the guard word to 1.
No caller found in g3_jp (same census as the ticks).

## The note2pitch table D_800AB048

Mapped static data inside `data_80080048` (blob +0x2B000), verified
bytes: **193 halfwords, 0x800AB048..0x800AB1CA** — a 2^(n/192) pitch-rate
table: entry 0 = **0x1000** (the SPU unity pitch 1.0), the last entry =
**0x2000** (exactly 2.0 — one octave), sentinel 0x0000; 192 entries =
12 semitones × 16 fine fractions (the first row 0x1000/0x100E/0x101D/
0x102C/0x103B/0x104A/0x1059/0x1068/0x1078/0x1087/0x1096/0x10A5/0x10B5/
0x10C4/0x10D4/0x10E3).

Its only consumers are the two libsnd VMANAGER members
**func_8006605C** ("note2pitch", 0xBC) and **func_80066118**
("note2pitch2", 0x100) — already recorded `adoptable` in
`config/sdk_members.txt` (sig-db no-hit), yaml rows marked `sdk` — and
**both are unreferenced in g3_jp** (no `jal`/`j` by name, no encoded
words `0x0C019917`/`0x08019917`/`0x0C019846`/`0x08019846`, no pointer
words in any data row): dead SDK members this build linked but never
called. Their math, verified instruction-level:

- `delta = note + 0x3C − center` (the 60 = the MIDI-C5 offset;
  func_8006605C's center/fine come from `D_80170374/0x80170375`, the
  note from `D_80170366` — all extended-RAM bytes; func_80066118's come
  from a per-voice record: `lw(D_8016AC60)` base, index
  `(lbu(D_80170370) + lbu(D_8017036B)*16) << 5` — stride 0x20, bytes
  +4 center / +5 fine, the fine argument carries a +7 round-before-
  shift and a ≥ 0x10 → +1 semitone carry).
- `index = (delta % 12) * 16 + (fine >> 3)` (the fine clamped ≤ 0xF);
  `rate = lhu(D_800AB048 + index*2) << (delta/12 − 5)` (sllv for
  positive, srav for negative) — the classic note→SPU-pitch
  transposition, built around octave 5.
- **The game's own note-on path never touches the table:** the script
  executor's SsUtKeyOn call passes `center − 0x18`/`shift` (pass 16's
  tone identity) into the library, which serves pitch internally; the
  table and its two helpers are the library's own unused machinery in
  this build.

## The EU twins

The same machinery exists in g3_eu: the caller-row twin
`asm/g3_eu/nonmatchings/func_80022B5C.s` (98 `D_80165xxx` refs) and the
sound-row twin `asm/g3_eu/nonmatchings/func_800280A0.s` (128 refs). The
EU lane records sit at a different base — the EU mode word is
**D_8016532C** (18 refs; JP's D_80165242 has its own 18 in the JP
sound row) with the shadow family `D_8016535A..6E` — same shapes,
different carve offsets. Recorded as the twin check; the EU numbers
were not re-derived field by field (JP-first discipline).

## Evidence table (verified vs inferred)

| Claim | Level | Backing |
| --- | --- | --- |
| Dispatcher dispatch map 2/4/8/default | verified | func_80029840..func_800298E4 chunks (bne chain + jal targets) |
| Pointer table stride 4, mode stride 0x44, 4 lanes | verified | lane·17·4 form ×18 sites; the four literal mode words D_80165242/86/CA/0E in func_800279CC |
| The four handlers' shadow writes + common mask shape | verified | func_80029200/292E8/293C4/293FC bodies (xori/andi/sll/or chains, 0x800 clamp ×3) |
| Tag→mode map 0x12→2, 0x23→4, 0x41→1, 0x53→8, else 0x100 | verified | func_80026F6C..func_80026FD8 (all delay slots read) |
| Mirror family layout CFEF4..CFF30 | verified | the tick/binding/evaluator materializations (each block cited above) |
| Tick skeleton (mirror, dispatch, request store, priority chain, tail re-arm) | verified | func_800276B8/func_800270E8 chunks |
| Tick caller | **open** | name + encoded-word + data-word census all empty |
| Request evaluator classes + budget | verified | func_8002945C..func_800295D8 |
| Ramp bands, steps, half-rate counters | verified | func_800295E0/func_80029738 + the mapped counter tables (4 zero words each) |
| Playlist tables 8 halfwords ×2 | verified | data_80071790.data.s dlabels D_80076CCC/CDC |
| Binding-layer call from main's data region | verified | raw word 0x0C009B5B at 0x80022A04 (data_80022800.data.s) |
| gp+0xA8 steal flag + the lane-3 steal | verified | func_800299BC/CC, func_8002704C, the raw word 0x0C00A66F at 0x800227B8 |
| note2pitch = 193 halfwords, 0x1000 → 0x2000, sentinel 0 | verified | data_80080048.data.s dlabel D_800AB048 (full byte dump) |
| note2pitch/note2pitch2 dead in g3_jp | verified | name + encoded-word + pointer census empty; sdk_members rows already adoptable |
| The pitch math (index, octave shift, carry) | verified | func_8006605C/func_80066118 bodies (0x2AAAAAAB division idiom, sllv/srav shift) |
| Music-mode persistence via work field 0x11 | verified | func_8002658C/func_800265E4 + main's data-row calls 0x800224E0/0x80022704 |
| "Request mask" semantics of the handler returns | inferred | the return values land in CFF14 and are AND-tested by every evaluator; no runtime sample |
| The lane/record byte semantics (pan, position) | inferred | the shapes and the 0x7F-unity deltas; no audio sample |

## What this closes (the pass-12 "separate mixer lane" made concrete)

The script system (pass 12–16) and the music lane are two independent
consumers of the same libsnd tier: the script executor fires note-ons
directly (SsUtKeyOn with the tone-array center/shift), while the music
lane maintains four per-lane records whose bound sequences publish a
per-frame REQUEST MASK through the dispatcher; the game's request
evaluators (func_8002945C) turn mask bits into state transitions, the
two ramps glide the shadow volumes toward the records' target bytes at
half rate, and the playlist scheduler walks the mapped request-mask
tables through the same evaluator. The pass-12 remark that the
SsSetSerialVol trio "belongs to a different consumer" resolves to this
lane: the mode-2 handler's pair (`D_800AC594/AC596`) and the ramp
outputs are the music lane's own volume/position state, entirely
separate from the executor's per-program volume chain
(`D_800ABB54/B5C`).

## Next R1 question

(1) The tick/initializer/scheduler caller hunt: the three entry points
carry a complete empty census in g3_jp — the driver is the natural next
read (the candidates: the VSync/IntrCallback registration chain, the
uncarved data-region call sites beyond the two rows decoded here, or a
function-pointer table not yet mapped). (2) The record pool's byte
protocol: the trigger bytes (`+0/+1 == 0x80`) and the sub-record
parameter bytes (+2..+7) come from the pool fills — trace who writes
`D_800CFE94`/`D_800CFEBC`'s pool and what the eight bytes of each
sub-record mean per tag (the tag→mode map above then reads as four
sequence classes). (3) When disc links return: Phase A/B per the
runbook (the ladder stays closed); the fresh-set request rides every
report.

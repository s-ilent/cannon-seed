# G3 R1 pass 14 — the absent-command resolution sweep and the EU script pin

**R1 pass 14 — 2026-11-25 (window cron-20261124-2209).** Bounded **JP-first
read-only static decode** continuing
[G3_SCRIPT_STREAM_CORPUS_20261124.md](G3_SCRIPT_STREAM_CORPUS_20261124.md):
the pass-13 note left two open questions — the absent-command mechanism
(second table / third reader / inert) and the ticker payload role — plus
the EU pinning follow-up. This pass executes the full-image reference
sweep, decodes the shared counter's clock, and pins the complete EU twin
machinery and corpus. Source-only: no retail SHA-1 comparison, no
runtime capture, no C conversion, no rename, no YAML or oracle change.
One pass-13 reading (the selector indexing formula) is corrected here.

## Method — the full-image reference census

Every reference in the g3_jp tree (`asm/g3_jp/**/*.s`, `src/g3_jp/*.c`)
to all 38 script-system symbols — both cursors, the shared counter, the
reset-zeroed word, the stream base, both pointer tables, all 26 script
content labels (4 region A + 8 region B + 14 stub bank), the executor
state words, and both tables — was extracted and classified
(definition / store / load / address-materialization), plus a second
range-wide sweep over 0x8008AF00..0x8008B200 and 0x800ABA00..0x800AC000
that catches references through any other symbol in the script-adjacent
windows. Sweep scripts: `scripts/r1_pass14_sweep.py`,
`scripts/r1_pass14_sweep2.py`, `scripts/r1_pass14_eu_corpus.py` (all
read-only).

## The three pass-13 hypotheses resolve

### 1. "A second command table exists at runtime" — CLOSED (no patcher)

A store sweep across the whole code tree finds **zero** `sw`/`sh`/`sb`
into the 0x80076000..0x80078000 window (command table D_800772F4 +
multiplier table D_80076CEC). The 46-record table is immutable in the
image; nothing can grow or retarget it at run time through any static
reference.

### 2. "The payloads are consumed by a third reader" — CLOSED (no reader)

- **Ticker cursor D_800AC3B4**: exactly 3 stores (ticker
  func_80042BF0, reset func_80044A90, selector func_80044AC0) and
  1 load (the ticker's own re-read). No other reference exists.
- **Interpreter cursor D_800ABE14**: exactly 3 stores (reset,
  selector, the interpreter's commit block func_8004503C) and 1 load
  (func_80044F60). No other reference exists.
- **Stream content 0x800ABA08..0x800ABA5C**: the only code reference
  in the whole image is the reset's address materialization
  (lui/addiu of the base). Not a single load or store.
- **All 26 script content labels**: referenced only by the two pointer
  tables' `.word` entries and their dlabels — zero code references.
- **The outside-state cluster is real but script-blind**: the shared
  counter D_800AC384 is additionally read by the clock
  (func_800233C8, below) and by func_80044514; D_800ABEAC is read by
  func_80023384; the metric sum D_800ABFB4 is read by func_80022BBC.
  All three are decoded below — none consumes script content.

### 3. "They are inert in retail" — REFINED (position-consuming no-ops)

The interpreter's dispatch paths are pinned instruction-level
(`asm/g3_jp/nonmatchings/func_80044B4C.s`):

- Short form: func_80044F60 → `jal func_80045088` (func_80045034),
  falls into **func_8004503C** → `sw s0 → D_800ABE14`.
- Long form: func_80044FE4 → `jal func_800450F4`, then
  `j func_8004503C` → the same store.

The commit is **unconditional on the dispatch path** — the executor's
return value (−1 on a table miss) is ignored. An absent command
therefore **advances the stream**: the pair (and any long-form inline
args) is consumed, and the next pair becomes the interpreter's cursor.
What does NOT happen: no handler runs (the table walk returns −1),
nothing reads the committed payload again.

**The once-latch side effect.** func_80045088 tests the latch
D_800AC58C and — if clear — sets it to 1 **before** calling the table
walk func_8002FA9C. A short absent command therefore consumes the
frame's single short-command slot exactly as a present one would. The
latch is cleared by func_800450C4 (gate-retest + `sh zero`), called
every frame from the main dispatcher **func_80042C90** (the chain
func_80022E24 → func_80024718 → func_80044294 → func_800444B0 →
func_80044514 → func_8004515C → **func_800450C4** → jalr through the
mode-handler vector D_8008AF1C indexed by `(D_800AC5AC & 7)*4`). The
vector table decodes as {func_800246B0, func_800246D0, func_80042E10,
func_800429B8, **func_80042A20** (the slot-4 MAIN_SEQUENCE callback,
matching the atlas), func_80043828, func_80042E08, func_80042E08}.

Nine game sites fire script commands directly through the gate-retest
wrapper func_80045054 (all feeding the same latch + table walk):
func_8003A128, func_8003AC24, func_8003C1DC, func_8003C2C4,
func_8003CA9C, the mode-0x1F/0xF block func_80042BD8 (fires short
command 0x6 then joins the ticker flow), func_800431EC, func_800433CC,
and func_800319F0. The long form (func_800450F4) re-tests the gate but
never touches the latch, as pass 12 recorded.

## The shared counter's clock (the missing writer)

Pass 12/13 verified both channels *reading* the counter
D_800AC384 but not who advances it. The writer is a three-block chain
in `asm/g3_jp/nonmatchings/func_80022AFC.s`, ticked per frame by the
mode-state driver func_80022FE4 (`jal func_8002334C`):

- **func_8002334C**: gate — `lh D_800AC494` zero → no write; then
  `lw 0x0($gp)` compared against 1.
- **func_80023384**: if `lhu D_800AC16C < 0x2711` (10001) AND
  `lh D_800ABFC4 == 0` → `counter = lhu(D_800AC16C) − lhu(D_800ABEAC)`
  (the timer minus the selector's stored start offset); otherwise →
  **func_800233C8**.
- **func_800233C8** (also the direct target of both gate jumps):
  `counter = lhu(D_800AC384) + 2`, stored by **func_800233D8**
  (`sh → D_800AC384`).

So the timeline clock runs **+2 per tick while the game timer
D_800AC16C is ≥ 10001 or the flag D_800ABFC4 is set**, and inside the
10001-timer window (with D_800ABFC4 clear) the counter is
**re-derived every tick as timer − start-offset** — the script
timeline is slaved to the game timer in that window, and the selector's
D_800ABEAC store is the script's start offset inside it. This also
explains the ticker's commit test shape (`gate < counter`): both
channels compare against a counter that moves 2 units per tick.

## The outside-state consumers, classified

- **func_80044514** (0x100, func_80033C44.s): a **state-snapshot
  copier** — loads a long list of mode-state halfwords (D_800ABFEC,
  D_800ABCC0, D_800ABE74, D_800ABFA4, D_800AC16C, **the counter
  D_800AC384**, D_800ABF94, D_800AC394, D_800AC17C, D_800AC5A4,
  D_800AC06C, D_800ABFC4, D_800ABE24, D_800AC08C, …) and stores each
  into a parallel shadow word (D_800AC32C = 4 first, then D_800AC044,
  D_800AC3BC, D_800AC3EC, D_800ABD8C, …). It is the per-frame save of
  the live state block into the shadow block that func_80042C90's
  chain runs just before the latch clear. No script content.
- **func_80022BBC** (func_80022AFC.s): the **results/rank display
  formatter** — reads the metric sum D_800ABFB4 (written by the
  pass-13 metric collector func_80044D2C), scales it ×10
  (`(sum*2+sum)<<1`), and builds a stack record feeding the
  func_80025944 / func_80025C1C / func_8002615C display pipeline.
  Consumes the metric VALUE, not script content.

## The selector indexing — pass-13 correction

The pass-13 formula `D_8008B1A8[(a0+v1)*4 + a1]` was a misreading. The
verified instruction sequence (func_80044AC0, func_80033C44.s
0x80044AC0..0x80044B34) computes:

```
v0 = (lh(D_800AC1D4) * 3) << 4      // mode * 48 bytes
v1 = lh(D_800ABE94) << 2            // slot * 4 bytes
interp cursor = lw(D_8008B1A8 + mode*48 + slot*4)
ticker cursor = lw(D_8008AF9C + slot*4)
```

So the interp table is **mode-major, 12 entries per mode group**
(mode word D_800AC1D4; the 24 entries = 2 groups), slot word
D_800ABE94 bounds-checked to 1..8 **after** the cursor stores (the
invalid-slot bail `beqz a1` / `slti a1,9` branches to 0x80044B44 —
the tail-merged `jr $ra` of the adjacent sdk C row func_80044B38, the
g3_jp second SpuVmDamperOn leaf whose compiled shape
ori/sh/jr/nop places its `jr` at row+0xC; placement proven by the 8/8
verify). The ticker table has no mode dimension. This matches the EU
selector func_80044728 instruction-for-instruction (EU mode word
D_800ACA24, slot word D_800AC6E4).

## The EU pin — complete alias map and corpus comparison

EU aliases pinned this pass (all verified instruction-level in
`asm/g3_eu/nonmatchings/func_800338AC.s` / `func_800447B4.s`):

| role | JP | EU |
| --- | --- | --- |
| script stream base | D_800ABA08 | D_800AC24C |
| ticker cursor | D_800AC3B4 | D_800ACC04 |
| interpreter cursor | D_800ABE14 | D_800AC664 |
| shared counter | D_800AC384 | D_800ACBD4 |
| reset (zeroes counter + start-offset word, sets both cursors) | func_80044A90 | func_800446F8 |
| start-offset word | D_800ABEAC | D_800AC6FC |
| selector (mode*48 + slot*4 table walk) | func_80044AC0 | func_80044728 |
| selector mode word | D_800AC1D4 | D_800ACA24 |
| selector slot word | D_800ABE94 | D_800AC6E4 |
| selector timer source | D_800AC16C | D_800AC9BC |
| ticker (blind both-halfword commit) | func_80042BF0 | func_80042858 |
| interpreter (pass 12) | func_80044F60 | func_80044BC8 |
| interpreter gate | D_800AC3C4 | D_800ACC14 |
| interpreter mode-gate word | D_800ABF9C | D_800AC7EC |
| short executor (latch set before walk) | func_80045088 | func_80044CF0 |
| once-latch | D_800AC58C | D_800ACDDC |
| latch clear (per frame) | func_800450C4 | func_80044D2C |
| table walk | func_8002FA9C | func_8002F72C |
| command table (byte-identical, pass 12) | D_800772F4 | D_80077B34 |
| ticker pointer table (12) | D_8008AF9C | D_8008B7B4 |
| interpreter pointer table (24, mode-major) | D_8008B1A8 | D_8008B9C0 |

**Table structure**: both tables are slot-for-slot structural twins.
Ticker table: slots 0/9/10/11 → the 4 region-A scripts, slots 1..8 →
8 one-shot stubs. Interp table: 2 mode groups × 12; in each group,
slots 4/5 (the two long-form volume-ramp scripts) and slots 8..11
(the ladder pair + stubs) carry the group's scripts; the group-1
variants replace exactly the slots where JP and EU differ (below).

**Corpus comparison** (machine-decoded halfword streams, all 26
labels + 15 EU labels; `scripts/r1_pass14_eu_corpus.py`):

- **Region A: 4/4 byte-twins** (the ticker timelines (1,F3)(0x227,F4)
  (0x2FE,F5) END etc.).
- **Region B: 5/8 byte-twins** — D_8008B00C↔D_8008B824 (the
  7-event long-0x800A ramp), D_8008B054↔D_8008B86C (the 7-event
  long-0x800A ramp over frames 2..0x66), D_8008B09C↔D_8008B8B4 (the
  13-step table-hit ladder 0x12..0x1D/0x10), D_8008B0D4↔D_8008B8EC
  (the 4-event (2,0xB)(0x60,0x11)(0xD0,0xE)(0xE6,0xF)), and
  D_8008B0E8↔D_8008B900 (the 19-event announce sequence).
- **The 3 mode-1 variant scripts are where JP and EU diverge** —
  and the divergence is exactly the absent band:
  - JP D_8008B144 (mode-1 twin of the 0x12..0x1D ladder, same frame
    gates) carries payloads **0x28..0x34 — all absent from the
    table**; EU D_8008B95C carries **0x12..0x1D/0x10 — all present**
    (identical content to its mode-0 ladder).
  - JP D_8008B17C carries **0x26/0x27/0x37/0x38 — all absent**; EU
    D_8008B994 carries **0xB/0x11/0xE/0xF — all present** (the
    mode-0 script's payload set over the same gates, with the last
    gate 0xE6 → 0xFD).
  - JP D_8008B190 carries **0x26/0x35/0x36/0x37/0x38 — all absent**;
    EU D_8008B9A8 carries **0xB/0xC/0xD/0xE/0xF — all present** over
    JP's exact frame gates (2/0xAC/0xD3/0x10A/0x137).
- **Stub bank: 14/14 byte-twins** — the bare-terminator stubs, the
  (1, 0xF6/0xF7/0xF8/0xF9/0xFA/0xFB) one-shots, and the 3-pair
  (0,0)(0,0)(0x3C,0) stub, all identical.

The absent-band region-B payloads therefore exist **only in the JP
data**: EU fills the same mode-1 variant slots with present payloads
(mirroring its mode-0 content), JP fills them with the absent band.
The ticker band 0xF3..0xFF is region-invariant (byte-twin), consistent
with the ticker never dispatching anything.

## Resolution statement

Both pass-13 open questions are now closed at the static-image level:

1. **Absent commands have no mechanism anywhere in the image.** No
   second table exists (no patcher), no third reader exists (the
   reference census is exhaustive over both cursors, the stream
   content, all script labels, and both tables), and no runtime patch
   reaches the command table. Their only effects are **stream
   advancement** (unconditional commit) and the short-form latch
   consumption.
2. **The ticker's committed payloads have no reader.** The ticker is a
   pure timeline tracker; its cursor is re-pointed by reset/selector
   and never read by anything else.

What remains open is *intent*, not mechanism, and the EU comparison
now constrains it: the absent-band payloads sit in the **mode-1
variant scripts only, in JP only, over frame gates that EU fills with
present payloads**. Two readings stay recorded without a mechanism
being invented: (a) the JP mode-1 scripts are deliberately silent
timelines — the absent payloads occupy dispatch slots so the timeline
advances on the same gates while playing nothing, the JP-specific
companion of EU's present-payload variants; or (b) the JP payload
halfwords are stale annotations from a build where the 0x26..0x38 band
dispatched. The verified facts that discriminate: the band is
structured (twin ladders over identical gates), JP-only, and
mode-1-only; the machinery is region- and mode-invariant.

## Evidence table (verified vs inferred)

| Claim | Level | Backing |
| --- | --- | --- |
| No stores into the table region (no patcher) | verified | full-tree store sweep, 0 hits in 0x80076000..0x80078000 |
| Both cursors + stream content have no second consumer | verified | the 38-symbol census + the range-wide sweep 2 |
| Commit unconditional on the dispatch path | verified | func_8004503C store after both executor forms |
| Latch set before the walk; cleared per frame by func_800450C4 | verified | func_80045088 / func_80042C90 chains |
| 9 direct command-firing sites via func_80045054 | verified | jal census |
| Counter clock func_8002334C/384/C8/D8 (+2 / timer−start) | verified | func_80022AFC.s bodies + the func_80022FE4 jal |
| func_80044514 = state snapshot; func_80022BBC = metric formatter | verified | both bodies |
| Selector indexing mode*48 + slot*4 (pass-13 correction) | verified | func_80044AC0 instruction sequence |
| Selector bail tail-merges into the func_80044B38 leaf's jr | verified (coherence + 8/8 verify placement) | branch target 0x80044B44 + the compiled leaf shape |
| Mode-handler vector D_8008AF1C (8 slots, slot 4 = func_80042A20) | verified | data_80080048.data.s dlabel |
| EU alias map (18 aliases) | verified | both EU walk-row files, instruction-level |
| EU tables slot-for-slot structural twins | verified | dlabel dump + slot-wise class compare |
| Region A 4/4 + stubs 14/14 + region B 5/8 byte-twins | verified | machine halfword-stream compare |
| Mode-1 absent-band payloads are JP-only | verified | the 3-script diff |
| The two intent readings (silent timeline vs stale annotations) | open | the discriminating facts are recorded; no mechanism assumed |

## Next R1 question

~~The script subsystem is now decoded end to end — interpreter, ticker,
selector, corpus, clock, latch, tables, EU twins — with the absent-band
*intent* the only open item, and it is data-curation-shaped rather than
mechanism-shaped. The natural next reads, in value order: (1) label the
46 handlers sound-semantics-by-multiplier (the D_80076CEC values + the
three SsSetSerialVol wrappers func_8002A23C/26C/29C give each command's
volume/rate meaning — the "what plays when" atlas), which also answers
whether the EU present-payload variants and JP absent-band variants
occupy semantically parallel slots; (2) the EU-side direct command
firers (the EU aliases of the 9 func_80045054 callers) to confirm the
latch arbitration is region-invariant; (3) the two conversion candidates
(func_80044F60 0xE4, func_80044B7C 0x1B0) remain recorded-with-
precondition (walk-row split first) — NOT scheduled without the split
decision.~~

**(1) Done in [G3_SCRIPT_NOTE_ON_20261125.md](G3_SCRIPT_NOTE_ON_20261125.md)**
(pass 15, same window): every script command is a psyq SsUtKeyOn VAB
note-on (prog = handler id; volumes = per-program multiplier × global
L/R scalers; tone bytes from the runtime table D_800CFF88); the
SsSetSerialVol wrappers belong to a separate consumer (open). The
remaining reads: the runtime tone-table writers, the EU direct-fire
twins, and the walk-row split decision.

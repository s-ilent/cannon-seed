# R1 pass 18 — the music-lane caller census: every tick consumer, the
# initializer, driver 1 and the master dispatcher anchored to main;
# the pass-17 empty census corrected

Date: 2026-11-25/26 (window cron-20261125-2209, job 540513's fifteenth
fire). Scope: g3_jp only (JP-first discipline; the EU twins are not
re-derived). Docs-only: zero source, YAML, asm or oracle change. Zero
prior-pass content corrections except the census itself, whose
correction IS this pass.

## The headline correction

Pass 17 recorded "a complete empty caller census" for the tick
entries func_800276B8/func_800270E8, the initializer func_80026B64
and the scheduler func_800299D8. The census was correct within its
method, and the method had two gaps:

1. **The intra-row grep gap.** The name-based sweep treated every
   reference inside a row file as the row's own definition (the
   "owner file" shortcut). Splat rows are carve units, not functions:
   one row file holds dozens of functions and chunks, and chunk-to-
   chunk calls inside one file are real references. All four music
   entries are chunk members of such rows, and every one of their
   callers was sitting inside the "owner" files.
2. **The un-split main.** g3_jp's main body is carved as two DATA
   rows (`data_80022878.data.s`, true VA 0x80022288..0x80022800, and
   `data_80022800.data.s`, true 0x80022800..0x80022AFC) whose .word
   values ARE the call map. Pass 16/17 decoded "both main data rows"
   word by word but never re-derived the j/jal targets against the
   music-lane entries; the .word 0x0C00BF1A (= jal func_8002FC68) at
   true VA 0x80022594 is the single reference that anchors the whole
   frame side.

With both gaps closed (machine sweep over all 586 .s files of the
module for name, %hi/%lo, raw lui/addiu/ori pairs, .word pointers,
encoded j/jal words and halfword pairs — the yaml tiles the whole
0x800..0x8C800 image with 721 rows, zero gaps, so the sweep is
total), the corrected census is:

| entry | pass 17 said | corrected |
| --- | --- | --- |
| func_800276B8 (tick 1) | no caller | **1 caller**: jal at 0x800267EC (func_80026718) |
| func_800270E8 (tick 2) | no caller | **3 callers**: 0x800238C4 (func_800236F8), 0x8002FF70 (driver 1), 0x8002FFD8 (driver 2) |
| func_80026B64 (initializer) | no caller | **fallthrough tail** of the scene reset func_80026A80 (+ its own per-lane loop back at 0x80026D3C) |
| func_8002FF48 (driver 1) | (not yet carved as a question) | **1 caller**: jal at 0x8002FE44 (func_8002FC68, the frame function) |
| func_8002FC68 (frame function) | — | **1 caller**: .word 0x0C00BF1A at true VA 0x80022594 = main |
| func_800299D8 (scheduler) | no caller | **still zero** — no name/%hi/%lo/pointer/encoded reference anywhere in the image |
| func_8002FFB8 (driver 2) | — | **still zero** — same result, machine-complete |

The scheduler and driver 2 are the only two entries that stay
entry-less, and the sweep that says so is total (every byte of the
image is carved; every static address form was checked). They are
recorded as genuinely unreferenced in g3_jp — dead variants or
runtime-pointer entries, with the honest note that no runtime
evidence exists either way in a static image.

## The anchored chains

### The master dispatcher (the frame engine)

`.word 0x0C010B1B` at true VA **0x800226F4** in data_80022878.data.s
= **main calls the dispatcher body at 0x80042C6C**. The dispatcher
(func_80042C64's body, chunk func_80042C90, span 0x80042C64..
0x80042D84; the `jr $ra; nop` at its head is the compiler's merged
return tail reached by the three branches from the interpreter chunk
func_80042BF0 above it — not the function entry):

1. prologue; `jal func_80044108`; `sh -1` into D_800ABEDC;
   `s0 = &D_8008AF1C`.
2. The loop body (func_80042C90): seven fixed steps —
   func_80022E24, func_80024718, func_80044294, func_800444B0,
   func_80044514 (pass 14's state-snapshot copier), func_8004515C,
   func_800450C4 (pass 14's once-latch clearer) — then
   **`jalr D_8008AF1C[(lhu(D_800AC5AC) & 7) * 4]`**: the 8-slot mode
   dispatch through the in-image vector (slot 0 func_800246B0,
   1 func_800246D0, 2 func_80042E10, 3 func_800429B8, 4
   func_80042A20, 5 func_80043828, 6/7 func_80042E08; the .word
   table at D_8008AF1C in data_80080048.data.s, verified).
3. The fixed tail — func_8004450C, func_800450EC, func_80042D4C (the
   0x100 bit-poker on the D_800AC18C cursor), func_80024720,
   func_80024728 — then **`jal func_80022FE4`** (0x80042D18): the
   scene update runs once per loop iteration, NOT inside a mode
   handler (this corrects the natural first reading that ties it to
   slot 4).
4. Loop while `lh(D_800AC4F4) != 1`; exit through func_8002AD24.

### The scene update → the tick consumers

**func_80022FE4** (head 0x80022FE4, span ..0x800232D0; the counter-
clock region of pass 14) calls **func_8002343C** (jal at 0x80023270,
chunk func_80023268). **func_8002343C** (span 0x8002343C..0x800236F8)
is the tick-consumer orchestrator:

- `jal func_80026718` at **0x80023510** — the tick-1 consumer.
- `j` at **0x800234CC**, `beqz` at **0x80023590**, `j` at
  **0x80023664** and **0x80023674** — tail-entries into
  **func_800236F8**, the tick-2 consumer function (span
  0x800236F8..0x80023D78), whose body mixes the tick-2 call
  (0x800238C4, delay `a3 = s5`), mode-word compares against
  D_800AC5AC (values 2/5), playlist-table halfword reads from the
  D_80071790 row at a dynamic offset, and **direct script-executor
  fires `jal func_80029FC0` with `a0 = 0xA`** (0x80023978 and
  0x80023870 — prog 0x0A, one of pass 15's direct-only programs, on
  the quiet-path branch).

### The tick-1 consumer (the stride-12 record writer)

**func_80026718** (span 0x80026718..0x80026A80): per-lane loop with
s0 = lane over a caller-provided work base s2:

- `addu a0, s0; ori a1, 1; jal func_800276B8; ori a2, 2` at
  0x800267EC..F0 — tick 1 with (lane, 1, 2).
- `(s0 * 3) << 2 = lane * 12` stride records off s2:
  `sw v0, 0x10(rec)` stores the tick-1 return (the per-lane request
  mask) into record+0x10; `lw v1, 0x6C(s2); or v0; sw 0x6C(s2)`
  ORs the mask into a base+0x6C accumulator word; a conditional path
  (`lw v1, 0x10(rec)` vs s4; `lw v0, 0xC(rec)`; `lw 0(s2); or; sw`)
  ORs the record's stored mask into base+0.
- Then `sra s0, 16` (undoing the branch-delay `sll s0, s1, 16` fixup)
  and `jal func_800279CC` — pass 17's four-lane snapshot function —
  whose return lands in `sw v0, 0x8(rec)` (record+0x8).

The stride-12 record layout (+0x8 snapshot, +0xC unknown halfword
test, +0x10 tick mask, base+0/+0x6C OR-accumulators) is machine-read
from the body; the work base's absolute identity (what s2 points at)
is not derived in this pass — recorded as the open remainder.

### The tick-2 consumers in the frame function (drivers 1 and 2)

**func_8002FC68** (the frame function, span 0x8002FC68..0x8002FF48,
entered by main at true VA 0x80022594): takes a0 (mode-ish arg, two
constant-pack branches a1=4/s5=1/s1=0x8BE vs a1=2/s5=2/s1=0xA4E),
runs the render loop (the chunks func_8002FECC with `VSync(4)`,
GsSwapDispBuff, func_8002AC04, GsDrawOt), and calls **driver 1**:

- `jal func_8002FF48` at **0x8002FE44** (chunk func_8002FDB8).

**Driver 1 = func_8002FF48** (own prologue, span 0x8002FF48..0x8002FF68
+ its loop chunks): `jal func_80026D6C` (the binding layer), then
s0 = lane 0, s1 = -1 (the sentinel), a0 = sp+0x10, and the loop head
func_8002FF68: `addiu a1, sp, 0x12; addu a2, s0; jal func_800270E8;
ori a3, 2` — tick 2 per lane with class 2 and two stack-buffer
outputs (a0 = sp+0x10, a1 = sp+0x12 — note the ODD halfword address
+0x12, a byte/halfword buffer, not a word). Dispatch on the return:
== -1 → lane++; (ret & 0xFE) == 0 → lane++ and loop (`slti s0, 4` +
`bnez` back at func_8002FF94); else return 1 via the func_8002FFA4
epilogue; exhausted loop returns 0.

**Driver 2 = func_8002FFB8** (0x8002FFB8..0x8003002C): the same
prologue + binding-layer + 4-lane tick-2 loop shape, minus the -1
sentinel, plus early exits on return 4 and 8 to the shared epilogue
func_8003002C. **Zero references of any static form** — recorded as
the second genuinely-unreferenced entry (alongside the scheduler).

### The initializer chain (pass 17's second open, closed)

main (`jal` at true VA **0x800224F4**) calls **func_80024224** (span
0x80024224..0x800242DC), which calls **func_80023DCC** (`jal` at
0x8002423C, span 0x80023DCC..0x80024224), which calls the scene
reset **func_80026A80** (`jal` at 0x80023DE8). func_80026A80's body
(pass 17's "scene-reset path func_80026AD0" is a chunk of it) runs
the reset steps — func_800715BC/func_80071684, ChangeClearPAD(0), the
D_800ABADC/D_800ABAE4/D_800ABB4C clears, GsSetOrign(0x1F4, 0x1F4),
the func_80027EC0(0x1E,0x1E)/func_80027FB0(0x2D,0x2D) pan defaults —
then **falls through** (its tail `s1=0; s4=0x2D; s3=0x2D; s2=0` are
real instructions, no jr) into **func_80026B64, the initializer**,
whose chunk is the per-lane loop body (the `bnez` at 0x80026D3C is
its own loop-back to the chunk head). Pass 17's "initializer has no
caller" is thereby resolved: the initializer IS the tail of the
scene-reset function, reached by fallthrough.

### The boot anchor (the crt0 continuation is code-in-data)

The g3_jp entry (exe.json pc0 = 0x80047EF0, matching pass 16's crt0)
zeroes .bss [0x800ABA8C, 0x80171F04), ends `addiu $v0, $zero, 0x4` +
nop — and **falls through into the "data" row data_80047F1C.data.s**
(true VA 0x80047F1C..0x80047FAC), whose words are the crt0
continuation: a table-driven SP setup (a0 = 0x80047F9C + 4 from the
crt0 tail's v0; `lw` the SP0 entry; `or sp, v0, 0x80000000`), stack/
heap arithmetic against the word at 0x800920D4, `jal func_8004B494`
(0x80047F7C), and **`jal 0x800224C0` = MAIN** (0x80047F90, the word
0x0C008930). This closes the boot-side anchor: entry → bss zero →
SP table → libc setup → main, all inside the carved surface once the
data rows are read as code.

## Method lessons banked (the reason pass 17 went blind)

1. **Intra-row references are real references.** Any caller census
   that maps "owner file = definition" across splat rows is wrong
   for chunk-rich rows; the glabel-line itself is the only
   definition-site marker.
2. **Census output must be saved whole before triage.** The first
   corrected run's decisive word-enc line was already in hand but
   scrolled away under head/tail filters; the file-then-grep
   discipline found it in one step.
3. **Un-split functions live in data rows.** The main-region rows
   are code carved as .word values; a caller census that only reads
   asm rows misses main entirely. Decoding every .word as an
   instruction (op 2/3 → j/jal target) turns a data row into a call
   map.
4. **Row names are woven-era spellings; VAs in .s comments are true
   space.** `data_80022878.data.s` spans TRUE 0x80022288..0x80022800
   (its name is the woven-era address). Never infer a row's span
   from its name; read the comment columns.

## Evidence table (verified vs inferred)

| Claim | Level | Backing |
| --- | --- | --- |
| tick 1's single caller at 0x800267EC | verified | func_80022AFC.s:5354 (`jal func_800276B8`), inside func_80026718 |
| tick 2's three callers | verified | 0x800238C4 (func_800236F8), 0x8002FF70 + 0x8002FFD8 (drivers), all `jal` |
| initializer = scene-reset fallthrough tail | verified | func_80026AD0 chunk tail ends `addu s2, zero, zero` (no jr); internal loop-back 0x80026D3C |
| driver 1 called from the frame function | verified | func_8002A2DC.s:8148 (`jal func_8002FF48` at 0x8002FE44) |
| frame function called by main | verified | data_80022878.data.s:215 (`.word 0x0C00BF1A`, true VA 0x80022594) |
| dispatcher called by main | verified | data_80022878.data.s:303 (`.word 0x0C010B1B`, true VA 0x800226F4) |
| scene reset chain main → func_80024224 → func_80023DCC → func_80026A80 | verified | jal sites 0x800224F4 (.word), 0x8002423C, 0x80023DE8 |
| the 8-slot vector D_8008AF1C contents | verified | data_80080048.data.s:15561..15570 (.word table, slots 0..7) |
| dispatcher loop: `jalr D_8008AF1C[(D_800AC5AC & 7) * 4]` | verified | func_80033C44.s 0x80042CC8..0x80042CE8 (andi 7, sll 2, lw, jalr) |
| dispatcher exit `D_800AC4F4 == 1` | verified | 0x80042D20..0x80042D2C (`bne v1, 1, func_80042C90`) |
| scene update runs per loop iteration (not in slot 4) | verified | the `jal func_80022FE4` sits in the loop body after the jalr |
| driver 1's arg/buffer shape (a0 sp+0x10, a1 sp+0x12, a2 lane, a3=2) | verified | 0x8002FF48..0x8002FF7C chunks |
| driver 1's return protocol (-1 skip, &0xFE continue, 0/1 exits) | verified | func_8002FF68/FF94/FFA4 |
| tick-1 consumer stride-12 records (+0x8/+0xC/+0x10, base+0/+0x6C) | verified | func_80026718/func_80026848 bodies |
| func_800236F8 mixes tick-2 + playlist reads + executor prog-0x0A fires | verified | 0x800237F8..0x800238C4 chunks (jal func_80029FC0 a0=0xA at 0x80023978) |
| scheduler func_800299D8 unreferenced | verified (machine-total) | sweep over 586 files, all address forms, zero yaml gaps |
| driver 2 func_8002FFB8 unreferenced | verified (machine-total) | same sweep |
| main's own sequencing (call order, per-frame vs per-scene) | inferred | the .word call map order only; no flow decode of main's branches |
| the stride-12 work base s2's absolute identity | open | not derived in this pass |

## Next R1 questions

1. **The scheduler and driver 2** stay unreferenced: decide dead-
   variant vs runtime-pointer with the EU twins (does g3_eu carry
   the same two entry-less shapes? If EU wires one of them, the JP
   counterpart's reader is a live question again).
2. **Main's flow decode** (the ~55-call .word map in true-VA order):
   which of main's callees are per-frame, per-scene, or boot-only —
   this turns the census into the module's top-level schedule.
3. **The stride-12 work base** (what s2 points at in
   func_80026718's caller) and the a0/sp+0x10 stack-buffer outputs
   of the tick calls: who consumes the records downstream.
4. When disc links return: Phase A/B per the runbook (the ladder
   stays closed — judge-prep/audit per the standing surface); the
   fresh-set request rides every report.

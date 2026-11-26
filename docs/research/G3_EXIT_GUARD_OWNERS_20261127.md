# R1 pass 22 — the exit-guard words owned: the button-bit word's
# identity, the gp+0xA grace countdown, the D_800AC164 step counter,
# and the STAR_MODE7 gate pair + length source

Date: 2026-11-27 (window cron-20261126-2209, job 540513's eighteenth
fire). Scope: g3_jp only, JP-first discipline. Docs + curated-symbol
bank only; zero source, YAML, asm or oracle change; zero renames (the
six curated names are INERT scan-time inputs per the c32d807d
convention).

## The question this pass closes

Pass 21's open list (a)-(c): the button-bit word behind
func_80023584's 0x10 mask (the pad lane stays lane-owned and
untouched), the mode-5/gp+0xA and D_800AC164 guard owners, and the
D_800ABF9C / D_800ABFC4 gate pair plus D_800AC294's writer (the
STAR_MODE7 length source). Every guard word of both exit machines
(pass 21's machine A and machine B) now has a complete in-image
owner census.

## 1. The button-bit word *(s1) — identity pinned, pad lane untouched

The pointer is NOT the pad hardware buffer. In the registered-vsync
row the loop prologue (the func_800237A4 block, 0x800237C8..0x800237D0)
builds `fp = D_8014772C` and `s1 = fp` — **s1 is the base of a bss
slot-state array at 0x8014772C** (an auto symbol; the address is
runtime RAM, far above the payload end 0x800AC000). The per-slot
stride is two bytes: func_80023884's loop tail advances
`addiu s0, s0, 0x2` and writes the parallel slot word
`D_801474E4[s0] = -1`, and the dispatcher row reads the same array
indexed (`lh D_8014772C[v0]` at 0x80044330, read-only there).

The full static census of the array base is four sites:

- **reads**: func_80023584's `lw 0(s1)` / `andi 0x10` (the mode-2
  exit request bit — pass 21's writer site 1), the sibling tail
  func_80023554's `lw 0(s1)` / `andi 0x1` (the counter-request bit
  that decrements s0 and fires executor command 0x36), the loop body's
  `lh 0(s1)` at 0x80023844 (bnez = the slot already holds a value),
  and the dispatcher row's indexed read at 0x80044330.
- **writes** (both in the vsync mode machine itself):
  0x80023880 `sh 3, 0(s1)` — the delay slot of the jump that follows
  the executor call func_80029FC0(0xA) (the machine's own
  acknowledge store: the slot takes the value 3 after the script
  command fires), and func_80023884 `sh zero, 0(s1)` — the clear
  path that also parks -1 into D_801474E4[s0].

Reading: bit 0x10 of a slot halfword is the mode-2 exit request bit
the mode machine sets/tests on its own state array; bit 0x1 is the
sibling's scripted-counter request bit. The actual pad getters
(func_80045B9C/func_80045C10) and the D_800AC17C button bitfield are
separate surfaces and stay lane-owned.

## 2. gp+0xA (0x800AB276) — the vsync grace countdown

The gp is fixed at 0x800AB26C (pass 20), so gp+0xA is the halfword at
**0x800AB276** (inside the giant data row data_80080048; static bytes
0x0000, and it has no dlabel — gp-relative addressing only). The
complete census is four sites, all in the registered-vsync row:

- **re-arm (writer)**: func_8002377C's tail 0x800237A0
  `sh 0x32, 0xA(gp)` — reached on EVERY vsync tick whose mode word
  D_800AC5AC is neither 2 nor 0x32 (50); the mode-2 and mode-0x32
  branches skip the store.
- **decrement (writer)**: func_80023910 0x80023924 — the
  non-exit fallthrough of the mode machine: if the halfword is > 0
  it is decremented and stored back; <= 0 it is left at 0.
- **readers**: the mode-5 arm in func_800238C4 (0x80023900 — the
  `beqz` that fires func_80023D14's exit store only when the
  countdown is fully decayed) and func_80023910's own guard read.

Semantics: the countdown is a per-vsync grace window kept alive at 50
ticks in every mode except 2 and 0x32; the mode-5 / tick-2-return-4
exit arm (pass 21's writer site 2) can only fire after the grace
window has decayed to 0, which requires the mode transitions to have
stopped re-arming it (the mode word must have settled into 2 or 0x32
long enough for the decrementer to run it to zero). The initial
value is the static 0x0000.

## 3. D_800AC164 — the mode-4 step counter (the counter-expiry arm)

The complete census: 58 references, six stores, five owner sites.

- **arm**: func_80022F24 (the scene-reset/render-setup tail,
  0x80022FD0) stores **getter(9)'s return** — the flow calls the
  getter func_80025944(9), skips on -1, requires mode
  D_800AC5AC == 4, requires `sltiu a0-1, 6` (the value must be
  1..6), then `sh a0 → D_800AC164`. This is a new getter id for the
  pass-20 map: **id 9 = the mode-4 step-count source** (id 8 was
  already seen in the vsync prologue func_8002375C).
- **clear**: func_80042F18 (the " WAIT_STEP0" state handler,
  D_80021384) stores 0 inside its state-reset pack (alongside
  D_800AC17C=0, D_800AC02C=0x1D0, D_800ABE7C=0, D_800AC494=0,
  D_800AC404=0, gp+0x78C=0, D_800ABE94=1, ...), and func_800447A8
  stores 0 in its own ~15-word state-reset pack.
- **increment**: func_80043730 bumps BOTH the record counter
  `0x44(a0)` and D_800AC164 by 1 per call (the paired per-call step
  bump).
- **decrement**: func_800239F4 (0x80023A80) stores `a1-1` when the
  slot's D_800ABF6C[s0] == 0 — the per-tick decay.
- **exit arm**: func_800239F4's `beqz D_800AC164 → func_80023D24`
  (pass 21's writer site 3: the exit store plus script command 0x35),
  guarded by the tick-2 return match AND `lh D_800AC02C >= 0`.

Reading: D_800AC164 is the WAIT_STEP-style step counter — armed from
getter(9) at mode 4, bumped per step call, decayed per vsync tick,
and the counter-expiry exit fires only at 0 with the wait word
non-negative.

## 4. D_800ABF9C — the attract timeline variant selector

Sole writer: **func_80030838** (0x80030838..0x8003097C, the frame
region row), a two-variant timeline initializer selected by a0's low
halfword:

- **variant A (a0 == 0)**: D_800ABF9C = 0, D_800ABFFC = 1,
  D_800AC3AC = 0x12A9, D_800AC3A4 = 0xB32, and the checkpoint pack
  D_800AC22C / AC234 / AC24C / AC254 / AC25C / AC264 / AC26C / AC27C /
  AC284 = **50 / 95 / 140 / 185 / 230 / 275 / 320 / 365 / 410**
  (step 45), with the fallthrough tail storing D_800ABE34 = 490.
- **variant B (a0 != 0)**: D_800ABF9C = 1, D_800ABFFC = 3,
  D_800AC3AC = 0x1471, D_800AC3A4 = 0xC44, checkpoints
  **55 / 104 / 154 / 203 / 253 / 302 / 352 / 401 / 451**, and
  D_800ABE34 = 420.

The ONLY caller in the whole static image is **main itself** — the
raw jal-encoded word 0x0C00C20E at VA 0x800224EC inside main's
code-in-data body (pass 20's map), with the delay slot
0x00002021 = `addu a0, zero, zero` (a0 = 0), immediately before
main's jal to the pass-18 scene-reset chain at 0x800224F4. So main
boots the attract timeline in variant A, **variant B is
static-dead**, and D_800ABF9C is a constant-0 switch for its ~40
readers (the frame-region timeline code in func_8002A2DC.s, the
dispatcher row, func_80044B4C.s, func_800280A4.s) — the same shape as
pass 19's machine-total dead twins. The static dlabel bytes agree
(four zero halfwords at 0x800ABF9C).

## 5. D_800ABFC4 — the attract outcome selector

Five writer sites, all dispatcher-row attract state handlers, each
paired with a script-selector call func_80022DE0(<label>):

- **1 = VICTORY**: func_80041B98 and func_80041C08 both call
  func_80022DE0(D_80021208 = "VICTORY_INIT") and store 1
  (func_80041B98's pack: D_800ABE74=1, D_800ABE94=9, D_800AC43C=2;
  func_80041C08's pack: D_800ABFEC=0x302, D_800AC494=0, ...).
- **2 = DEFEAT / DEAD_END**: func_80042054 calls
  func_80022DE0(D_80021268 = "DEFEAT_INIT") and stores 2 (pack:
  D_800ABFEC=0x302, D_800AC2B4=-1, D_800AC494=0, D_800ABFAC=0x38);
  func_800423C0 calls func_80022DE0(D_800212B0 = "DEAD_END") and
  stores 2 (pack: D_800AC2B4=-1, D_800ABE94=0xB); and func_80041AEC
  stores 2 with no visible script call in its own block (pack:
  D_800AC2B4=-1, D_800AC01C=0, D_800ABE7C=0x2C, D_800ABE94=0xA).
- **gate effect**: in the exit gate func_80043EEC, outcome 2 selects
  the HIGHER STAR_MODE7 exit threshold; any other value the lower —
  the defeat/dead-end sequences run longer before the attract exit.

## 6. D_800AC294 — the STAR_MODE7 length mirror (the length source)

Sole writer: **func_80022EC8** (0x80022EC8..0x80022F24, the
registered-vsync row):

1. `a0 = &D_800AC294; jal func_8002B20C` — func_8002B20C is one
   load-and-store: `*a0 = *(D_800ABB74 + 8)` — the word is OVERWRITTEN
   from the +0x8 field of the record whose pointer sits in
   **D_800ABB74**, the StGetNext out-record pointer (the retry loop
   func_8002AE78 passes &D_800ABB74 to StGetNext; func_8002AEA0
   compares rec+8 against a requested length — the LIBSPU stream
   record machinery).
2. `D_800AC294 <<= 1` — then the word is doubled.

So D_800AC294 is re-derived each service tick as
`stream_record->field_8 * 2`, NOT an accumulator. The service entry
is func_80022E24's call func_8002ADA0(D_8016AEA8, D_800ABA9C, 2)
returning != -1 (pass 20's attract service chain). The reader is the
exit gate's four compares (below).

## 7. The gate — pass 21 errata and the corrected tier map

The gate in func_80043EEC has **FOUR** threshold sites, not three:

- the three `j func_80043F80` tails pass 21 counted: 0x16F8 (5880)
  at 0x80043F34, 0xC78 (**3192** — pass 21's "3200" is a decimal
  slip) at 0x80043F44, 0x1E76 (7798) at 0x80043F6C;
- PLUS the fallthrough tail **func_80043F70** (0x80043F7C:
  `slti 0x141E` = **5150**), which pass 21 missed — the
  D_800ABF9C!=0 / D_800ABFC4!=2 combination.

Semantics confirmed: `slti v0, D_800AC294, thr` then
`beqz v0 → func_80043FAC` — the exit trio
(D_800AC5AC=1 / D_800ABE94=0 / D_800AC4F4=1) fires immediately when
**D_800AC294 >= threshold**; below the threshold the D_800ABE7C
countdown (func_80043F80) ticks down once per call and expiry (sign
bit set) reaches the same trio.

The effective tier map with variant A always live
(D_800ABF9C == 0): **outcome 2 → 5880, outcome != 2 → 3192**. The
higher pair (0x1E76/0x141E) is reachable only under variant B —
static-dead. The gate's structure is intact for a variant that no
retail path ever selects.

## 8. Adjacent census facts (recorded, not named)

- **D_800ABE7C** = the attract state timer: ~50 re-arm sites across
  the dispatcher-row state handlers (per-state values: 0x2C at
  func_80041AEC, 0 at the func_80042F18 / func_800447A8 packs), the
  shared countdown func_80043F80 expires. A lane-wide word — left for
  the attract-machine owner to name.
- **D_800AC02C** = the WAIT_STEP wait word: armed 0x1D0 (464) twice
  in func_80042F18's pack, cleared at 0x800432B8, other setters at
  0x80042E88 / 0x80043370 / 0x800435D8; the func_800239F4 guard
  requires it >= 0.
- The variant pack's companions D_800ABFFC (1 vs 3), D_800ABE34
  (490 vs 420), D_800AC3AC (0x12A9 vs 0x1471), D_800AC3A4 (0xB32 vs
  0xC44) and the checkpoint array D_800AC22C..D_800AC284 ride the
  same func_80030838 selection.

## The curated bank (inert, scan-time input)

Six names bank under `// target: g3_jp` in
config/symbols.curated.txt (the c32d807d convention: names are
scan-time symbols-file input only; no yaml/asm row moves until a lane
runs a scan):

- `attract_variant = 0x800ABF9C`
- `attract_outcome = 0x800ABFC4`
- `attract_stream_len2 = 0x800AC294`
- `attract_step_cnt = 0x800AC164`
- `vsync_grace_cnt = 0x800AB276`
- `st_next_rec = 0x800ABB74`

None of the six addresses carries a name in any other target's
namespace (verified against symbols.curated.txt / symbols.g3_eu.txt /
symbols.g3_jp.txt), none is an sdk-member placement (sdk_members /
sdk_anchors / sdk_windows / sdk_symbols all clean), and none touches
the R3 shared-name brief's classes (the six are g3_jp-unique game
data words; the cross-target shared names and the parked trios are
untouched).

## What this closes and what it opens

Closed: pass 21's open (a) (the button-bit word's identity — the
bss slot-state array, pad lane untouched), (b) (the gp+0xA grace
countdown and the D_800AC164 step counter owners), and (c) (the gate
pair's writers and D_800AC294's writer chain), with two pass-21
errata (the fourth threshold tier; 0xC78 = 3192).

Open: (a) the getter func_80025944 id map — now with ids 8/9 observed
in situ (the pass-20 ids 0x11/2/3/4/5/0xA/0xF plus the new pair); (b)
the EU corroboration of passes 20+21+22 in one walk; (c) the stride-12
work base (unchanged); (d) the attract state timer D_800ABE7C's
per-state value map (the ~50 re-arm sites) for the attract-machine
owner; (e) when disc links return, runbook Phase A/B; fresh-set
request rides every report.

# R1 pass 26 — the EU corroboration of the exit machines: the exit
# flag, all four writers, the store trio and five of the six guard
# words are instruction-identical twins; the fourth gate threshold
# diverges by 6 in a static-dead tier

Date: 2026-11-27 (window cron-20261127-0609, job 540513's nineteenth
fire — same window as pass 25). Scope: g3_eu as the comparison image
for passes 21+22 (JP-first discipline maintained). Docs only; zero
source, YAML, asm or oracle change; zero renames; zero curated banks.

## The question this pass closes

Passes 25's refreshed next-question (a): the EU corroboration of pass
21 (the exit-flag census: four writers, two machines, write-once) and
pass 22 (the guard words' owners). Every site below is an
instruction-level read in both regions' rows; the JP side is not
re-derived.

**Verdict: the exit machines are two-image. The exit flag
(D_800AC4F4 → EU D_800ACD44, +0x850), its four writer sites, the
store trio behind writer 4, the dispatcher's reader, and five of the
six pass-22 guard words all land as instruction-identical twins at
measured band shifts. One genuine constant divergence surfaces: the
gate's fourth (fallthrough, variant-B-only) threshold is EU 0x1418
vs JP 0x141E — the lane's second code-side constant divergence, in a
tier that is static-dead in both regions. The bss slot-state arrays
are per-region data (EU base D_80148058, +0x92C), not shared
addresses.**

## The exit flag and its reader

- **EU exit flag = D_800ACD44** (JP D_800AC4F4 +0x850 — the same band
  as the store trio's companions below).
- The dispatcher's reader: EU row func_800338AC.s reads
  `lh D_800ACD44` at **0x8004298C**, `ori v0, 1`, `bne v1, v0 →
  func_800428F8` (the EU dispatcher loop head), else `jal func_8002AD14`
  (the close-out twin, JP func_8002AD24 −0x10) — the same line
  numbers as JP's row (pass 21's pinned reader).

## The four writers, both machines

Machine A — the vsync-side mode machinery (EU row func_80022B5C.s,
+0x60 band; the whole machine is line-identical to JP's
func_80022AFC.s):

| writer | JP (pass 21) | EU twin | note |
|---|---|---|---|
| 1. the mode-2 button exit | func_8002366C `sh v0` @ 0x80023674 | `sh` @ **0x800236D0** | guard chain (lw *(s1) / andi 0x10 / mode switch) reads on the same lines |
| 2. the mode-5/grace arm | func_80023D14 tail `sh v0` @ 0x80023D18 | func_80023D74 tail `sh` @ **0x80023D78** | |
| 3. the counter expiry + script 0x35 | func_80023D24: ori 1, sh, `jal func_80029FC0` delay `ori a0, 0x35` | **func_80023D84**: ori 1, `sh D_800ACD44` @ 0x80023D8C, `jal func_80029FB0` (the executor twin, −0x10) delay `ori a0, 0x35`, `j` to the join twin | instruction-identical including the delay slot and the following `sh v0, 0x4A(gp)` |

Machine B — the dispatcher-row attract timer (EU row func_800338AC.s,
−0x398 band):

| writer | JP | EU twin | note |
|---|---|---|---|
| 4. the store trio | func_80043FAC: `sh D_800AC5AC=1 / sh D_800ABE94=0 / sh D_800AC4F4=1` | **func_80043C14**: `sh D_800ACDFC=1 / sh D_800AC6E4=0 / sh D_800ACD44=1` @ 0x80043C18/C20/C28 | instruction-identical, followed by the shared epilogue twin func_80043C2C (= JP func_80043FC4); the countdown twin before it is func_80043BE8 (= JP func_80043F80) |

The pass-21 census shape therefore holds verbatim in EU: four writer
sites, two machines, every store = 1 (writer 4's companions stored
first), and the same single reader. The write-once-per-load reading
is two-image.

## The pass-22 guard words — EU addresses (measured, not extrapolated)

| word | JP | EU | band | verification |
|---|---|---|---|---|
| vsync_grace_cnt (gp+0xA) | 0x800AB276 | **0x800ABABA** | rides gp (+0x844) | three sites on JP's exact lines: re-arm `sh 0x32, 0xA(gp)` @ 0x80023800, reader `lh` @ 0x80023960, decrement `sh` @ 0x80023984 |
| attract_step_cnt | D_800AC164 | **D_800AC9B4** | +0x850 | arm `sh a0` @ **0x80023030** (the func_80022F24-twin store, JP 0x80022FD0, same line 386-387) + two readers on JP's lines |
| attract_variant | D_800ABF9C | **D_800AC7EC** | +0x850 | the two variant stores inside EU func_800304A0 (the pass-25 timeline-init twin): variant A `sh zero` @ 0x800304B0, variant B `sh v0` @ 0x8003054C — and EU main calls it with a0=0 (pass 25's site), so variant B is static-dead in EU too |
| attract_outcome | D_800ABFC4 | **D_800AC814** | +0x850 | readers @ 0x80022BDC / 0x800233D0, JP's lines |
| attract_stream_len2 | D_800AC294 | **D_800ACAE4** | +0x850 | the gate's `lw` compares @ 0x80043B94 / 0x80043BA8 |
| st_next_rec | D_800ABB74 | **D_800AC3B8** | **+0x844 (the exception)** | the StGetNext retry loop twin (EU func_8002AE68, JP func_8002AE78 −0x10) passes `&D_800AC3B8`; the +0x850 prediction misses by 0xC — exactly why every twin is read, not extrapolated |

Companions: the mode word D_800AC5AC → EU **D_800ACDFC** (+0x850) and
D_800ABE94 → EU **D_800AC6E4** (+0x850), both from the store trio;
the button bitfield D_800AC17C → EU **D_800AC9CC** (+0x850, the row's
next-function word).

## The gate — three constants identical, the fourth diverges

EU gate func_80043B54 (= JP func_80043EEC −0x398) verified head to
tail:

- `lui a0, 0x8002146C` ("STAR_MODE7", EU string at 0x8002146C; JP
  0x8002148C — the string table shifts −0x20 here) → `jal func_80022E40`
  (the script-selector twin, JP func_80022DE0 +0x60) → the gate reads
  lh D_800AC7EC (the variant twin) first, as pass 22 describes.
- The three shared thresholds are byte-identical constants on JP's
  exact lines: **0x16F8** @ 0x80043BA0, **0xC78** @ 0x80043BB0,
  **0x1E76** @ 0x80043BD4.
- **The fourth (fallthrough, variant-B-only) tier diverges: EU
  `slti v0, v0, 0x1418` (5144) @ 0x80043BE4 vs JP `slti 0x141E`
  (5150)** — the lane's second code-side constant divergence (after
  pass 19's frame-pack 0x8BE vs 0x8BC). It sits in the tier pass 22
  proved static-dead in JP (variant B unreachable); EU's variant
  selector is likewise constant-0 (pass 25's a0=0 call), so the tier
  is static-dead in BOTH regions and the divergence is a compiler-era
  artifact of the variant-B build, not a behavior difference.

## The bss slot-state arrays are per-region data

The pass-22 button-bit reading (s1 = fp = the bss slot-state array
base, written only by the vsync mode machine) is two-image with
measured EU bases — but the arrays are NOT shared addresses:

- JP: s6 = D_801474FC, fp/s1 = **D_8014772C** (the pass-22 array).
- EU: s6 = **D_80147E28**, fp/s1 = **D_80148058** — both **+0x92C**,
  on the same instruction lines (lui/addiu pairs at JP 0x800237B0/C8 =
  EU 0x80023810/28).

The +0x92C bss shift is its own band (runtime RAM laid out per
region); pass 22's four-site census of the array base reads on the
same lines in EU (the loop prologue build, the parallel-array park
D_801474E4 → EU D_80147E10's family, the dispatcher row's indexed
read — the EU dispatcher's indexed read of the array sits at JP's
line with the EU base).

## Evidence table (verified vs inferred)

| Claim | Level | Backing |
|---|---|---|
| EU exit flag = D_800ACD44, reader pinned | verified | dispatcher-row lh/bne/jal read at JP's lines |
| four writers, instruction-identical twins | verified | per-site reads incl. writer 3's executor call and delay slot |
| store trio + mode word + E94 twins at +0x850 | verified | EU func_80043C14 body |
| five guard words at +0x850, st_next_rec at +0x844 | verified | each word's writer/reader sites read in EU rows |
| grace countdown = EU gp+0xA = 0x800ABABA | verified | three same-line sites |
| gate constants 0x16F8/0xC78/0x1E76 identical, fourth tier 0x1418 vs 0x141E | verified | slti sites on both sides |
| variant B static-dead in EU | verified | EU main's a0=0 call (pass 25) + the EU variant stores |
| bss arrays per-region (+0x92C) | verified | prologue lui/addiu pairs |
| the 0x1418/0x141E divergence's cause (compiler era vs deliberate tweak) | open | static-dead tier, no behavioral surface |

## What this closes and what it opens

Closed: pass 25's refreshed next-question (a) — the exit machines and
five of the six guard words are two-image; the second code-side
constant divergence is on the record; the bss band is measured.

Open: (a) the EU corroboration of passes 23+24 (the gameinfo family's
EU addresses — do EU's accessors carry the gameinfo.c strings? do the
73-slot tables match?) — the natural pass 27; (b) the stride-12 work
base (unchanged); (c) D_800ABE7C's per-state value map (unchanged,
attract-machine owner); (d) when disc links return, runbook Phase
A/B; the fresh-set request rides every report.

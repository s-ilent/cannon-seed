# R1 pass 29 — the stride-12 work base resolved: the poll table is
# D_800CFE24 (derived in-body, not caller-provided), and the tick stack
# buffers are the mixer hand-off consumed by tick 2 itself and the
# orchestrator's per-channel arrays

Date: 2026-11-27 (window cron-20261127-1409, job 540513's twentieth
fire). Scope: g3_jp static decode, docs only; zero source, YAML, asm
or oracle change; zero renames; zero curated banks (the work-base
data-word bank is left as a follow-up lane item, the pass-27
convention).

## The question this pass closes

Pass 18's open #3, carried unchanged through passes 19/23/24/25/26/27
and WORK_QUEUE's Next list: **the stride-12 work base — what s2 points
at in func_80026718's caller frame — and who consumes the tick calls'
sp+0x10/sp+0x12 stack-buffer outputs.**

**Verdict: both halves close at the byte level. (1) s2 is NOT
caller-provided — func_80026718 derives it in-body from the literal
D_800CFE24 (lui/addiu at 0x80026734/38); the call site passes nothing
(jal at 0x80023510, nop delay slot, a0 computed in-body from the loop
counter). D_800CFE24 is the 4-lane music request-poll table, and the
request-flag PRODUCERS (func_80026638/func_80026690) plus the
gp+0x8C accessor pair (func_80026A0C/func_80026A18) hold ZERO
references of any static form in the retail image — jal/j/data words
all empty — so the request half of the poll is statically dead and
tick 1 fires only through the binding-mask half. (2) The sp+0x10/sp+0x12
buffers are the per-lane two-halfword mixer hand-off: tick 2's mode
handlers WRITE them, tick 2 reads them back against the GsSetOrign
full-scale words, and the orchestrator persists them into the
per-channel arrays D_8016AFF4/D_8016B004/D_801474E4 and feeds the
apply call func_80027C28. The drivers themselves never read their own
buffers — pure return-value dispatch.**

## Part 1 — the work base: D_800CFE24, the request-poll table

### The erratum first

Pass 18's note says "per-lane loop with s0 = lane over a
caller-provided work base s2". The caller-provides half is WRONG:
the only call site (jal at 0x80023510, chunk func_800234D4 of
func_80022AFC.s) has a NOP delay slot and arms no argument; s2 is set
inside func_80026718's own prologue (`lui s2, %hi(D_800CFE24);
addiu s2, s2, %lo(D_800CFE24)` at 0x80026734/38) and a0 (the lane) is
computed in-body at 0x800267E4 (`addu a0, s0` from the s1 loop
counter). Recorded as an erratum to the pass-18 note, not a
re-reading.

### The table map (every address row-private to func_80022AFC.s)

D_800CFE24 is the base of a 4-lane, 12-byte-stride request-poll table;
the WHOLE band (base .. +0x6C) is referenced by no file other than
func_80022AFC.s (D_800CFE24/28/90 tree-wide grep = that one row). The
layout as machine-read from the poller body:

| offset | role | evidence |
|---|---|---|
| +0x0 | fresh-mask OR accumulator | or/sw at 0x80026838-44; read by the post-loop gates |
| +0x4 (= D_800CFE28) | the ACTIVE-LANE BINDING MASK | anded with 1<<lane at 0x800267A0; it IS the binding layer's output word (func_80026D6C result stored at 0x8002677C, cleared 0 at 0x80026748) |
| +8(+12L) | per-lane snapshot (init -1; func_800279CC result) | sw s4 at 0x800267D4; sw v0 at 0x8002686C |
| +0xC(+12L) | per-lane REQUEST flag | producers func_80026638 (set 1, a0 = lane or -1 = all lanes) / func_80026690 (clear 0) |
| +0x10(+12L) | per-lane tick-1 mask cell (init 0) | sw zero 0x800267DC; sw v0 0x80026804 |
| +0x38 | mirror of +0x0 | sw at 0x8002699C |
| +0x3C..+0x64 | history copy: slots 5..8 hold [snapshot(L), request(L+1), mask(L+1)] | func_800269A0 loop: rec+8/+C/+10 -> rec+0x3C/0x40/0x44 = 12(L+5)+0/4/8 |
| +0x6C | second OR accumulator (all stored masks) | or/sw at 0x80026808-14 |

### The poller flow

Entry gate: v0 = *(gp+0x88) (D_800AB2F4). Nonzero ->
func_80026770: jal func_80026D6C (the binding layer), result ->
D_800CFE28, base+0 = 0, D_800CFE90 = 0. Zero -> clears D_800CFE28 =
0. Then the per-lane loop (s3 = 1<<lane, s4 = -1 sentinel):

- `(1<<lane) & D_800CFE28` set -> tick path (the lane is in the
  current binding).
- else request flag +0xC(+12L) nonzero -> tick path.
- else snapshot = -1, mask cell = 0 (lane idle).

Tick path: `jal func_800276B8(lane, 1, 2)` (tick 1, single caller
census 1) -> mask stored at +0x10(+12L) AND or'd into +0x6C; the
fresh mask is or'd into base+0 only when the stored cell != -1 and
the lane's request flag is 0; then `jal func_800279CC(lane)` (the
snapshot, 2 callers) -> +8(+12L).

Post-loop consume gates (all jal func_80026A24 = the CLEAR: base+0 &=
~mask, then per-lane +0x10(+12L) &= ~mask): (base+0 & 3) == 3 ->
clear 3; == 0xC -> clear 0xC; == 0x30 -> clear 0x30; any 0x30 bit ->
clear 0xF; bit 0x1 -> clear 0x30. Then the mirror write (+0 -> +0x38)
and the history copy.

Cross-links: base+0 bit 0x10 with *(gp+0x90) == 1 fires script
command 0x37 (0x80026960); bit 0x20 with *(gp+0x90) == 1 fires 0x35
(0x8002698C) — the same executor commands pass 22's exit machines
arm. base+0 is OR'd into gp+0x8C (D_800AB2F8) every poll
(0x80026930-40).

### The producers and the gp+0x8C pair are STATIC-DEAD (two-image)

The caller census (tools/audit_caller_census.py over 586 g3_jp row
files): func_80026638 = 0 symrefs, func_80026690 = 0 symrefs,
func_80026A0C = 0 symrefs, func_80026A18 = 0 symrefs. The raw-word
leg over the DE-FRAMED retail payload (the carve IS the runtime
image: the migrated yaml's VAs = runtime VAs; the framing
reconciliation is tools/deframe.py's job): jal word 0x0C00998E, j word
0x0800998E and the data word 0x80026638 (and the same trio for
0x80026690/0x80026A0C/0x80026A18) — zero hits each in g3_jp. Controls
all hit exactly as censused (poller 1, driver 1 = 1, tick 2 = 3, tick
1 = 1, the clear gates = 5), so the sweep is sound. Cross-module
numeric coincidences (g3org_jp data words 0x80026A0C/18/24, three
0x080099A4 j-words in sces_00269) are the same-VA-different-entity
pattern — separate executables with their own VA spaces, not
references. The EU twins confirm two-image: EU poller control
0x800266F4 jalx1 (mirrors JP), the EU twins 0x80026614/0x8002666C/
0x800269E8/0x800269F4 all zero refs in g3_eu.

**Consequence: no static code path ever SETS a lane request or reads
gp+0x8C in either retail image.** The request half of the poll OR is
statically dead — tick 1 fires only when the lane is in the binding
mask (the func_80026D6C result); the request flags are bss-zero
forever; the gp+0x8C accumulator and the +0x38/+0x3C..+0x64 mirror
and history band are written every poll and read by nothing static.
The -1 = all-lanes variant of the setters suggests an entry that
never existed in retail (debug or a cut feature); recorded, not
speculated further.

### The caller chain (the gameinfo cross-link)

The poller's single caller (chunk func_800234D4) requires ALL of:
*(gp+0) == 1 (the mode word), `jal func_80025944` with a0 = 8 —
**get_game_info(8) == 1** (getter id 8 = the 0x80010B28.. halfword
array, the pass-23/27 map) — and func_800233E8() != -1 (the
sign-extended-halfword sentinel test). The music poller is thus
gated by the gameinfo flag array's cell 8: the gameinfo family and
the music lane meet here.

## Part 2 — the sp+0x10/sp+0x12 stack buffers: the mixer hand-off

### Three tick-2 call sites, one shape

| caller | site | frame | args |
|---|---|---|---|
| driver 1 func_8002FF48 | 0x8002FF70 | 0x28 | a0 = sp+0x10, a1 = sp+0x12, a2 = lane, a3 = 2 |
| driver 2 func_8002FFB8 | 0x8002FFD8 | 0x20 | same shape |
| the orchestrator func_800236F8 | 0x800238C4 | 0x28 | a0 = sp+0x10 (armed 0x80023838/0x800238B8), a1 = sp+0x12 (0x80023840/BC), a2 = s2, a3 = s5 |

### The drivers never read their own buffers

Driver 1's loop (func_8002FF68/90/94/A4) dispatches ONLY on the
return value: ret == -1 -> lane++; (ret & 0xFE) == 0 -> lane++ and
loop (slti s0, 4); else return 1 via func_8002FFA4; exhausted -> 0.
The epilogue restores ra/s1/s0 and nothing else. Driver 2
(func_8002FFD0/30018/3001C/3002C): same return-value-only dispatch
plus the 4/8 early exits. Zero loads from 0x10(sp)/0x12(sp) in either
driver. The buffer bytes are tick 2's scratch, not the drivers'.

### The consumers are inside tick 2 (func_800270E8, span
0x800270E8..0x800276B8)

s5 = a0, s6 = a1 (0x80027110/14). The per-lane mode halfword
D_80165242[lane] (the pass-17 lane records) selects the handler at
0x80027430-0x8002748C: mode 2 -> func_80029028, 4 -> func_800289D8,
8 -> func_800286A4, else func_80028D3C — each called with (a0 = s5,
a1 = s6, lane). **The handlers WRITE the two halfwords through the
pointers**: the mode-2 handler computes from D_800AC596 x
D_800ABAEC / D_800ABAFC (a signed divide-by with break guards) and
stores `sh t1, 0(t5)` at 0x800291E8 and `sh t0, 0(a1)` at 0x800291F0
(the odd sp+0x12 byte address is a HALFWORD pointer, as pass 18
suspected).

Tick 2 then READS them back: `lh v0, 0(s5)` at 0x800275D8 compared
(|v| via the bgez/negu pair) against D_800ABAEC, and `lh v0, 0(s6)`
at 0x800275F8 against D_800ABAF4 — equality feeds the andi s0, 0xFD
clear; the mismatch paths run func_8002945C calls (the ramp/step
function, 40 internal refs) and build the return mask. **D_800ABAEC/
D_800ABAF4 are the GsSetOrign words** (`sh a0/sh a1` at 0x80027A64/
0x80027A6C in the real GsSetOrign = pass 25's 0x80027A60) — the
scene reset's GsSetOrign(0x1F4, 0x1F4) sets the mixer's full-scale
pair; the same cells serve the GTE origin and the music full-scale.

### The orchestrator's persistence + apply (the real downstream)

The orchestrator (func_800236F8, the registered VSyncCallback) reads
the buffers back in chunk func_80023AD4 (the *(gp+0) == 0 path) at
0x80023AE4/0x80023AE8: `lhu v1, 0x12(sp)` -> **D_8016AFF4[lane]**;
`lhu v0, 0x10(sp)` negated -> **D_8016B004[lane]**; then
`jal func_800279CC` -> **D_801474E4[lane]** (pass 22's parallel
array). The alternate path (chunk func_80023B30, *(gp+0) != 0)
re-loads the persisted pair, negates the first back
(a0 = -D_8016B004[lane]), writes the pair into its OWN sp+0x10/
sp+0x12 (0x80023B54/58) and calls **func_80027C28(a0, a1)** — the
apply step (3 call sites: 0x80023B68, 0x80023DA4, and 0x80026B90 =
the initializer's tail region).

**The buffer lifecycle closes end to end: mode handler writes the
lane's two halfwords -> tick 2 validates them against the
GsSetOrign full-scale pair and folds the result into the return
mask -> the orchestrator persists them into the per-channel arrays
(D_8016AFF4 / D_8016B004 / D_801474E4) -> the next tick's alternate
path re-feeds the persisted pair to func_80027C28, the apply call.**
Nothing downstream of the orchestrator touches the stack buffers;
the drivers' frames are pure scratch.

## Evidence table (verified vs inferred)

| Claim | Level | Backing |
|---|---|---|
| s2 = D_800CFE24, derived in-body | verified | lui/addiu at 0x80026734/38; call site nop delay |
| the table map (+0/+4/+8/+0xC/+0x10/+0x38/history/+0x6C) | verified | per-instruction reads of the poller chunks |
| base+4 = the binding mask (func_80026D6C output) | verified | sw v0 at 0x8002677C, the 1<<lane and at 0x800267A0 |
| func_80026A24 = the combined-request clear | verified | nor/and/sw body + per-lane loop |
| producers + gp+0x8C pair unreferenced | verified | caller census 0 + de-framed payload raw-word sweep 0 (controls hit) |
| two-image unreferenced status | verified | EU twins swept in g3_eu, zero refs, EU control jalx1 |
| drivers never read their buffers | verified | full chunk reads of func_8002FF48/2FFB8 families |
| handlers write the buffers | verified | sh t1, 0(t5) / sh t0, 0(a1) at 0x800291E8/F0 |
| read-back vs the GsSetOrign words | verified | lh + |v| compares at 0x800275D8/F8; GsSetOrign sh at 0x80027A64/6C |
| orchestrator persistence + func_80027C28 apply | verified | chunk func_80023AD4/23B30 reads; 3 apply call sites |
| what the two halfwords mean (volume/pan candidates) | open | values computed and persisted, semantics un-named |
| func_80026D6C's binding-mask composition | open | the tag-to-mode map is pass 17's; the mask bit-per-lane layout is new |
| why the producers are dead | open | recorded, not speculated |

## What this closes and what it opens

Closed: pass 18's open #3 — the stride-12 work base is D_800CFE24
(the 4-lane request-poll table, row-private), the pass-18
"caller-provided" reading is an erratum, and the tick stack buffers'
consumers are tick 2's handlers/read-back plus the orchestrator's
persistence and apply chain. The music poller's static-dead request
half is two-image.

Opens: (a) the two halfwords' semantics (the volume/pan candidates)
and the func_80027C28 apply-step decode; (b) the binding-mask
composition inside func_80026D6C (which tag combinations set which
lane bits); (c) the EU walk of this family per the JP-first
discipline (the twin addresses are banked in the pass-19 table,
−0x24 band); (d) when disc links return, runbook Phase A/B; the
fresh-set request rides every report.

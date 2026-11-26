# R1 pass 19 — the EU twin check: g3_eu carries the same two
# entry-less shapes; the scheduler and music driver 2 are
# machine-total unreferenced in BOTH retail images

Date: 2026-11-26 (window cron-20261126-0609, job 540513's sixteenth
fire). Scope: g3_eu as the comparison image for pass 18's g3_jp music-
lane caller census (JP-first discipline maintained: the JP side is
pass 18's machine-total and is not re-derived). Docs + one read-only
tool (`tools/audit_eu_twins.py`); zero source, YAML, asm or oracle
change.

## The question this pass closes

Pass 18 left the scheduler `func_800299D8` (the playlist walker) and
music tick driver 2 `func_8002FFB8` as g3_jp's only two genuinely
unreferenced music-lane entries — dead variants or runtime-pointer
entries, no static evidence either way — and posed the EU check: does
g3_eu carry the same two entry-less shapes? If EU wires one of them,
the JP counterpart's reader becomes a live question again.

**Verdict: EU carries both shapes, and neither is referenced — the
pair is machine-total unreferenced in both retail images.** The
dead-variant reading now has two-image machine evidence; only a
runtime-pointer sighting (PCSX-Redux trace) could still revive either
entry, and it would have to do so in a form both regions share.

## Method (and the two census traps it exposed)

1. **Twin location.** `tools/audit_eu_twins.py` aligns normalized
   instruction words between the vram-sorted g3_jp and g3_eu streams:
   j/jal targets, branch offsets and lui/addiu/ori immediates may
   shift between regions, all other fields must match. Thirteen of the
   twenty-two probes matched contiguously at 0.64–0.94; the rest MISS
   on EU carve seams (the EU image interleaves other functions between
   JP-adjacent chunks — the frame region runs at a different band than
   the sound rows), and those were read BY HAND in the EU rows.
2. **The caller census.** `tools/audit_caller_census.py --module g3_eu`
   with the REAL EU carve names. Two traps surfaced here and are
   banked:
   - The census's `code-enc` path can never match: the .s comment word
     column stores the instruction bytes in little-endian byte order
     (`F98B000C` for `jal` = word `0x0C008BF9`), while the tool compares
     the logical big-endian encoding. Every working hit in this pass
     came from NAME symrefs (jal/j/branch mnemonics spell the target's
     glabel) or `.word` operands (which DO carry the logical value).
     Synthetic census names (e.g. `eu_driver1=0x8002FBD8`) therefore
     see only the `.word` layer; re-running with the real glabel names
     is mandatory for a complete count.
   - Same VA ≠ same entity across regions. EU's glabel
     `func_8002FFB8` — the very address JP's driver 2 occupies — is a
     BRANCH-JOIN label inside EU's render/HUD function
     (0x8002FE7C..0x8003001C), reached by two internal branches
     (0x8002FF64 `beqz`, 0x8002FF90 `bne`). A naive cross-region
     name/VA match would have "wired" JP's dead driver 2 through a
     label that is not even a function head. The music-lane EU census
     table below separates the two entities explicitly.
3. **Completeness for the two decisive addresses.** Beyond the name
   census, a raw hi/lo scan (%hi/%lo-form lui/addiu-ori materializations
   of 0x800299D4 and 0x8002FC48 across all 586 EU files) returned zero
   hits, so no runtime-pointer table entry in static data exists
   either.
4. **Fallthrough identity.** The initializer has no EU twin by
   reference because it needs none: the EU scene-reset twin
   (0x80026A5C) is body-identical to JP's (same reset steps, same
   `s1=0 / s4=0x2D / s3=0x2D / s2=0` tail, no `jr`), falling through
   into the same per-lane initializer loop body (the EU clear targets
   are the mirror family D_800D0764/D_800D0774, the JP ones
   D_800CFF14/D_800CFF24 — a +0x850 EU shift of the below-image mirror
   base; the scheduler's record word moves +0x12C (EU D_8016536E vs JP
   D_80165242), while pass 17's mode word moves +0xEA (EU D_8016532C)
   — the EU record family does not shift as one block).

## The EU twin map (verified)

Three EU row files carry the whole lane, at three different shift
bands; the deltas confirm the regions do NOT shift uniformly:

| JP entry | EU twin | delta | EU row | identity evidence |
| --- | --- | --- | --- | --- |
| func_8002343C (tick-consumer orchestrator) | 0x8002349C | +0x60 | func_80022B5C.s | align 0.812 (64 insns) |
| func_800236F8 (tick-2 consumer fn) | 0x80023758 | +0x60 | func_80022B5C.s | align 0.844 |
| func_80023DCC (main chain step 2) | 0x80023E2C | +0x60 | func_80022B5C.s | align 0.641 (64 insns; EU body diverges in immediate class) |
| func_80026718 (tick-1 consumer) | 0x800266F4 | −0x24 | func_80022B5C.s | align 0.875 |
| func_80026A80 (scene reset head) | 0x80026A5C | −0x24 | func_80022B5C.s | align 0.772 + hand byte-read of the whole head incl. tail |
| func_80026B64 (initializer) | fallthrough of 0x80026A5C's tail | — | func_80022B5C.s | hand byte-read: same no-jr tail, same loop body |
| func_80026D6C (binding layer) | 0x80026D68 | −4 | func_80022B5C.s | EU carve glabel + 4 jal callers (below) |
| func_800270E8 (tick 2) | 0x800270E4 | −4 | func_80022B5C.s | align 0.844 |
| func_800276B8 (tick 1) | 0x800276B4 | −4 | func_80022B5C.s | align 0.860 |
| func_800279CC (4-lane snapshot) | 0x800279C8 | −4 | func_80022B5C.s | align 0.781 |
| func_8002945C (request evaluator) | 0x80029458 | −4 | func_800280A0.s | align 0.859 |
| func_800295E0 (mode-8 ramp) | 0x800295DC | −4 | func_800280A0.s | align 0.844 |
| func_80029840 (lane dispatcher) | 0x8002983C | −4 | func_800280A0.s | align 0.828 |
| **func_800299D8 (scheduler)** | **0x800299D4** | −4 | func_800280A0.s | align 0.906 + head hand-read (byte-twin prologue/counters, EU reads D_8016536E) |
| func_8002FC68 (frame function) | 0x8002F8F8 | −0x370 | func_8002A2CC.s | 0.900 on the 20-insn head + full hand read (prologue, mode-branch packs, render loop, `jal` driver 1) |
| func_8002FF48 (music driver 1) | 0x8002FBD8 | −0x370 | func_8002A2CC.s | full hand read: same sentinel shape (s1=−1), `jal` binding, `jal` tick 2 ×4-lane loop |
| **func_8002FFB8 (music driver 2)** | **0x8002FC48** | −0x370 | func_8002A2CC.s | full hand read: same −1 immediate check + ret 4/8 early exits, `jal` binding, `jal` tick 2 |
| func_8003002C (driver-2 shared epilogue) | 0x8002FCBC | −0x370 | func_8002A2CC.s | 3 branch targets from driver 2's dispatch |
| func_80022FE4 / func_80024224 / func_8002704C / func_80029738 / func_80042C6C | not re-derived | — | — | carve-seam MISS; not needed for the verdict (JP-first discipline continues) |

The JP/EU band structure: the sound row (evaluator/ramps/dispatcher/
scheduler) and the tick/snapshot/binding tier sit at −4; the tick
consumers/orchestrator/scene-reset tier at +0x60 or −0x24; the frame
region (frame function + both drivers + shared epilogue) at −0x370.

## The EU caller census (machine-total, 586 files)

`tools/audit_caller_census.py --module g3_eu` with the real EU carve
names; every count below is non-definition symrefs + `.word` operands:

| EU twin | refs | the references |
| --- | --- | --- |
| 0x8002349C orchestrator | 1 | jal 0x800232D0 (scene-update region — JP: 1 at 0x80023270) |
| 0x80023758 tick-2 consumer | 4 | j ×3 + beqz ×1 (0x8002352C/0x800235F0/0x800236C4/0x800236D4 — JP: 4 at 0x800234CC/0x80023590/0x80023664/0x80023674) |
| 0x800266F4 tick-1 consumer | 1 | jal 0x80023570 (JP: 1 at 0x80023510) |
| 0x80026A5C scene reset | 1 | jal 0x80023E48 (JP: 1 at 0x80023DE8) |
| 0x80026D68 binding | 4 + 1 word | jals 0x80023804 (tick-2 consumer), 0x8002674C (tick-1 consumer), 0x8002FBE4 (driver 1 prologue), 0x8002FC50 (driver 2 prologue) + main data-row `.word 0x0C009B5A` at 0x80022A64 (JP: 4 jals + `.word 0x0C009B5B` at 0x80022A04) |
| 0x800270E4 tick 2 | 3 | jals 0x80023924 (consumer), 0x8002FC00 (driver 1 loop), 0x8002FC68 (driver 2 loop) — JP: exactly 3 (0x800238C4/0x8002FF70/0x8002FFD8) |
| 0x800276B4 tick 1 | 1 | jal 0x800267C8 (tick-1 consumer — JP: 1 at 0x800267EC) |
| 0x800279C8 snapshot | 2 | jals 0x80023B70, 0x80026828 (JP: 2 at 0x80023B10/0x8002684C) |
| 0x80029458 evaluator | 40 | the tick/evaluator machinery's internal funnel (JP: heavily referenced, same shape) |
| 0x800295DC mode-8 ramp | 1 | jal 0x80027884 (tick region) |
| 0x8002983C dispatcher | 2 | jals 0x80027174, 0x8002774C (the two ticks — JP: the same two) |
| 0x8002F8F8 frame function | 1 word | main data-row `.word 0x0C00BE3E` at 0x800225F8 (JP: `.word 0x0C00BF1A` at 0x80022594) |
| 0x8002FBD8 driver 1 | 1 | jal 0x8002FAD8 (inside the EU frame function — JP: 1 at 0x8002FE44) |
| **0x800299D4 scheduler** | **0** | **zero of any static form** (JP: 0, machine-total) |
| **0x8002FC48 driver 2** | **0** | **zero of any static form** (JP: 0, machine-total); raw hi/lo scan also zero |

The wired chains are a 1:1 structural mirror of pass 18's JP census —
same caller counts, same call sites modulo the per-band shifts, same
main data-row anchoring (EU main = data_80022800.data.s /
data_80022A18.data.s, the twins of JP's data_80022878/data_80022800).
The two entry-less shapes are the same two entries.

## The one real JP/EU divergence found in the lane

The EU frame function's mode-1 branch pack carries `s1 = 0x8BC` where
JP carries `s1 = 0x8BE` (the `a1=4 / s5=1` branch; the `a1=2 / s5=2`
branch's 0xA4E is identical). First code-side constant divergence the
music-lane decode has produced; the s1 value feeds the render-loop
geometry pack — not chased further in this pass (recorded as the
pass-20 candidate alongside the script corpus's known mode-1 variant
divergence from pass 14).

## Evidence table (verified vs inferred)

| Claim | Level | Backing |
| --- | --- | --- |
| EU scheduler twin 0x800299D4 exists, body = JP scheduler | verified | align 0.906 over 64 insns + head hand-read (identical prologue, gp+0xAA/0xAE/0xAC counters, 0x2710/0x28 clamps; EU record base D_8016536E) |
| EU driver-2 twin 0x8002FC48 exists, body = JP driver 2 | verified | full hand read: −1 check, ret 4/8 exits, 4-lane tick-2 loop, binding prologue (and the JP "minus the −1 sentinel" wording of pass 18 is corrected: JP driver 2 HAS the −1 immediate check; the s1 REGISTER sentinel is driver 1's alone — both regions identical here) |
| EU driver-1 twin 0x8002FBD8, called by the EU frame function | verified | jal at 0x8002FAD8 + full hand read |
| EU frame function 0x8002F8F8 wired by EU main | verified | data-row `.word 0x0C00BE3E` at 0x800225F8 |
| EU binding 0x80026D68 wired by EU main + both drivers + 2 consumers | verified | 4 jals + data-row `.word 0x0C009B5A` at 0x80022A64 |
| EU tick 2 has exactly 3 callers | verified | 3 jals, sites listed above |
| EU scheduler + EU driver 2 unreferenced | verified (machine-total) | name census over 586 files + `.word` sweep + raw hi/lo scan, all zero |
| the initializer is EU's scene-reset fallthrough | verified | hand byte-read of the EU tail (no `jr`) + identical loop body |
| EU `func_8002FFB8` is NOT the driver-2 twin | verified | EU row read: branch-join inside 0x8002FE7C..0x8003001C, 2 internal branch targets |
| JP/EU frame-branch constant 0x8BE vs 0x8BC | verified | JP 0x8002FC9C vs EU 0x8002F92C `ori $s1` |
| the census `code-enc` path is inert (byte-reversed comment words) | verified | F98B000C vs 0x0C008BF9 on the live jal lines; all real hits were name/`.word` |
| scheduler/driver-2 are dead variants vs runtime-pointer entries | open (strengthened) | two-image machine-total absence; runtime trace is the only decider |

## Next R1 questions

1. **Main's flow decode** (pass 18's next #2, unchanged): the ~55-call
   `.word` map in true-VA order — per-frame vs per-scene vs boot-only.
2. **The stride-12 work base** (pass 18's next #3, unchanged): what s2
   points at in func_80026718's caller frame; who consumes the
   a0/sp+0x10 stack-buffer outputs downstream.
3. **The scheduler/driver-2 runtime question is now a two-image
   question**: if a PCSX-Redux trace ever fires either entry, it must
   do so through a runtime-computed pointer in BOTH regions' shapes
   (or expose the regions' divergence); otherwise they stay recorded
   dead variants with two-image static evidence.
4. **The 0x8BE/0x8BC frame-branch constant** (new): what the two bytes
   feed in the render-loop geometry pack.
5. When disc links return: Phase A/B per the runbook (the ladder stays
   closed — judge-prep/audit per the standing surface); the fresh-set
   request rides every report.

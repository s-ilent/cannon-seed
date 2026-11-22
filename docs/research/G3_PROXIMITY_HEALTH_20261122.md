# G3 proximity response, shared health and failure sequence

R1 pass 18, 2026-11-22. Input research head 756cab108e54b0d5609baecc5bb39fd1074d418f. Extends [hit arbitration](G3_HIT_DAMAGE_SCORE_20261122.md), [type-1D controller](G3_TYPE1D_CONTROLLER_20261122.md), [formation inventory](G3_TYPE1D_FORMATIONS_20261122.md), [stream clock/pose](G3_STREAM_CLOCK_POSE_20261122.md).
Inspected unchanged original EXE blobs JP 7b5ad2b5035634abd6873c86c90f486f6a99dffd / EU e9cfc4ee2bb3a4b474567d371037cfcd6c56cbb7 (SHA-1 independently verified in pass 15). Direct raw word decode; no original assets extracted, no matching build/runtime witness.

## Shared health

Both initialization paths set D_800AC2B4 and D_800AC394 to 10000 (8004483C..80044858, 800449C8..800449DC). The first is the actual shared vehicle health, the second tracks it with smoothing. This is separate from the four gunner records discussed in the hit/score atlas.

JP 80035348..80035418 (EU 80034FB0..80035080) accepts object pointer. Exact logic, with signed halfword loads and low-halfword stores:
- if health >= 0 and D_800ABFC4 == 0:
  - signed multiplier = *(s16 *)(80089F3C + 14 * D_800ABDFC + 2 * D_800AC164)
  - signed base damage = *(s16 *)(*(u32 *)(obj+0x60) + 0x12)
  - increment D_800AC09C (16-bit damage-event counter) and subtract multiplier * base damage from health.
- independently, if D_800ABF84 == 1 and resulting signed health <= 0, force health to 1. This is a verified nonlethal override; source/UI name not yet established.
- No health saturation to zero in the ordinary path. It is possible to hit exactly zero, and the initial gate is >=0, not >0. Negative health blocks further ordinary damage. The state gate suppresses ordinary damage even for a successful proximity result.
- No gunner index is passed to this function.

The multiplier table starts JP 80089F3C, EU 8008A754. Eight consecutive rows of seven signed halfwords sampled and all 56 values match:
row 0=2, 1=4, 2=6, 3=8, 4=10, 5=13, 6=15, 7=20, each repeated across all seven columns. The indexing still uses D_800AC164, even though these observed columns are equal. No bounds check in this routine. Eight rows observed, not a proven UI option count. 800441E4 copies seven adjacent settings halfwords from JP 8008AF3C, values [3,1,1,0,1,0,0], into separate globals; the third initializes D_800ABDFC to 1 at 8004424C. May be overridden by persisted settings. Do not claim the exact user-facing difficulty name yet.

Active config 0x7B (JP 80089A74) +0x12 is 25; initial config 0x66 (800AB970) +0x12 is 0. Earlier pass established type1D constructor swaps the config pointer to 0x7B. Conditional damage per qualifying active fighter contact: [50,100,150,200,250,325,375,500], i.e. [0.5,1,1.5,2,2.5,3.25,3.75,5]% of initial health. At initialization row 1, 74 contacts would deduct 7400, if all spawned and hit and no external state/health changes. This is a hypothetical maximum loss from these 74 authored entries under that row, not an observed hit rate or session outcome.

## Proximity collision arbitration

Two wrappers:
- JP 800351D0..800352A0 calls 80035068 with two output angles, applies modular halfword ranges, then calls 80034EC0 and checks signed halfword after +0x4000 is nonnegative, calls 80035348 at 8003527C, returns -1. Otherwise 0.
- JP 800352A0..80035348 calls 80034EC0 first, applies the same modular angle ranges, calls 80035348 at 80035324, returns -1 or 0.
- Exact both range checks are (u16)(angle + bound) < 2*bound; second output bound 0x1555 always, first output bound 0x16C1 in mode zero or 0x1A4F otherwise. Equivalent approx +/-30 degrees for second, +/-32 or +/-37 degrees for first assuming existing 16-bit full-turn convention. Half-open range; exclusions matter. First wrapper has extra heading test. Do not identify geometric axes without the two angle producers fully mapped.
- Direct JP JAL callers of first: 80030AFC, 80034038, 80037414, 800385C0, 800389AC, 8003A110, 8003DF9C, 8003E16C. Second: 800344F8. Scan code range 80022000..80047000. Not proof of absence of indirect invocations.
- Third direct call to damage itself at 8003AC2C, following 8003A960 and 80045054 with a config-dependent sound argument; no local cone gate. Its upstream caller/controller not yet attributed.
- Type1D active helper 800389A0 calls first wrapper at 800389AC. Return -1 calls 80038968 (type31 death transition); other results zero type field. Thus the collision qualifies for destruction independently of whether health deduction was gated off. The proximity threshold is already handled in 800387BC (pass 15), not in the angular wrappers.

## Health smoothing and alarm

JP 800451B4 called before the two simulation passes by MAIN_SEQUENCE. If smoothed health != 0, compute signed halfword difference smoothed - max(actual,0). Move smoothed toward target by 1 for absolute difference <20, 20 for 20..99, 100 for >=100; exact equal exits. This is once per active main callback, not once per object update or stream tick. No divisor or time-based rate. Call order means newly incurred damage is reflected on a later callback. Provisional interpretation: displayed health animation; actual draw consumer still to be verified.

JP 80042B08..80042BF0, after object-driver calls and enclosing gates, latches low-health flag when actual <2000 and smoothed >0, D_800ABFC4 neither 1 nor 2, no already-latched flag. Countdown D_800AC10C initialized to 32, decremented in same call, zero reloads 16. Bit 3 controls assertion of D_800AC06C; at counter 31 and 15 calls 80045054(6), consistent with repeated audiovisual alarm. Existing latch path bypasses new threshold test. Exact effect of flag on HUD and audio ID 6 not yet independently decoded. No claim of seconds cadence.

## Failure vs normal completion

JP 80040460 mode-zero stage dispatcher calls 8002F1F4; only when it returns zero does it increment its separate counter by 2 and test failure. If D_800AC4AC == 0, unsigned stage index D_800ABE94 < 9, Then signed actual health <=0 calls 800423C0 and bypasses normal nested dispatch on that invocation. D_800AC4AC is the effective address for -15188, not yet semantically named. Stage >=9 or override gate skips ordinary failure check.

800423C0 references literal JP 800212B0 "DEAD_END", calls 80022DE0, writes health=-1, stage index=11, D_800ABFC4=2, immediately invokes 80042414 ("DEAD_INIT" at 800212BC) which calls 80044AC0, sets timer 4 and nested phase 1 and increments counter at D_800ABF4C. Subsequent 80042470 ("DEAD_SET2") counts down; 800424EC ("DEAD_FLASH") toggles flag from timer parity, 80042534 ("DEAD_FLASH2") uses timer modulo 3. Later death phases not yet fully traced.

Contrast normal late tick transition 80041B1C: absolute tick >=9988 sets health=-1, D_800ABFC4=2, stage index=10 and nested phase 2, timer=44; not by itself proof of victory or of mission duration. A separate path has literal VICTORY_* and DEFEAT_* strings, requiring full final-state map. Health=-1 is not sufficient to classify outcome; stage index and sequence matter.

## JP/EU corroboration

Opcode/register/shift shape comparison (mask J/JAL target, LUI, ADDIU and memory immediates; structural witness, not binary equivalence). Five representative windows:

| JP start..exclusive end | EU start | Words | Exact | Shape |
|---|---|---:|---:|---:|
| 800351D0..80035418 | 80034E38 | 146 | 124 | 146 |
| 80040460..80040524 | 800400C8 | 49 | 38 | 49 |
| 80042B08..80042BF0 | 80042770 | 58 | 44 | 58 |
| 800451B4..8004525C | 80044E1C | 42 | 37 | 42 |
| 8004483C..80044858 | 800444A4 | 7 | 4 | 7 |
| Total | | 302 | 247 | 302 |

No target-scoped SDK anchor intervals intersect these windows. Central game-owned JP ASM segment 0x14444, EU corresponding central segment. The smoothing routine is in a later ASM segment. No source conversion or build claims.

## Next
Census all non-null object dispatch entries; group by common motion, collision and damage helpers and trace the direct damage caller at 8003AC2C and producers of 80034EC0/80035068. Prioritize boss-like multi-object controllers and named victory/defeat stage sequences. STR extraction remains blocked by container startup errors despite both CHDs now being registered project files.

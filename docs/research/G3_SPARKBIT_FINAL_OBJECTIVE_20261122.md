# G3 type 89: SPARKBIT final objective, countdown interpreter and victory gate

R1 pass 21, 2026-11-22. Input research head 1c93f723338611cdcf2ae003d74948ab3440164b. Original private JP/EU EXE blobs 7b5ad2b5035634abd6873c86c90f486f6a99dffd / e9cfc4ee2bb3a4b474567d371037cfcd6c56cbb7 (SHA-1 verified pass12/15). Static word inspection; no asset publication, matching build or runtime witness. Extends [composite census](G3_OBJECT_CENSUS_COMPOSITES_20261122.md), [Doldva reactor](G3_DOLDVA_REACTOR_20261122.md), [shared health](G3_PROXIMITY_HEALTH_20261122.md).

## 1. Identity and authored root

Only type89 authored spawn: config 48, JP 80088EB4, EU 800896CC; section2 secondary descriptor JP 80079584 / EU 80079D9C, relative tick3880 + section start4609 = absolute8489. Initial resource 1C0. Descriptor+18 -> JP 80078E94 / EU 800796AC (specialized script). Parent creates five phase -1 children from JP 8008ABE0, angles 0,13107,26214,-26215,-13108 (u16 circular spacing approximately 72 degrees), increments +84 active-child count per successful allocation. Each has parent pointer +64, config shared, individual damage/animation state. Parent and children use common type89 dispatcher (signed phase -4..2, pass19).

Parent success sets D_800AC144=-1 at 8003B880. The named SPARKBIT main sequence routine 80041AB0 reads that exact flag at 80041ACC and immediately calls 80041B98, diagnostic SPARKBIT_HAKAI, when nonzero. That selects stage 9, nested phase 2 and damage-state D_800ABFC4=1. Stage9 table 8008AE88 starts VICTORY_INIT and six victory stages (see below). This establishes final objective identity with high confidence; original rendered model identity still requires assets. Internal developer name SPARKBIT, not necessarily a literal on-screen title.

## 2. Separate countdown clock and specialized command stream

JP 80041A50 (SPARKBIT_INIT) calls 80044AC0, sets both timer D_800ABE7C and D_800AC01C to 684, increments phase, immediately calls 80041AB0. SPARKBIT checks success flag first, otherwise decrements both counters once per main callback. At absolute mission tick >=9988, sets shared health=-1, zeros D_800AC01C, sets state D_800ABFC4=2, stage10 phase2, timer44, calls 80044AC0. Thus countdown command clock is distinct from absolute stream clock; no seconds conversion. Transition into SPARKBIT init is reached from the preceding sequence at absolute >=8618, with alternative path from SPARK_BEFORE. 9988-8618=1370 ticks, close to 2*684=1368, consistent with two absolute sample ticks per main callback, but not independent proof of real-time cadence or actual start on every playthrough.

Parent phase1 8003AFE8: if signed countdown nonzero, first test active count zero and countdown positive -> 8003B868 success. Otherwise compare truncation-toward-zero(s16(stream timestamp)/2) <= signed countdown: if true, command is still future, leave stream cursor unchanged. If false (strict countdown < half timestamp), consume opcode and operands through 8003B2FC. On zero return commit cursor; loop. Nonzero return calls 8003B8F4 (clears parent type). At countdown exactly zero the parent skips this block, including success. Its two effect accumulators and other motion/render continue subject to surrounding mission state.

18-entry opcode table JP 80020E70/EU 80020E50, index sign-normalized(op+17), unsigned <=17.

| Signed opcode | Handler JP | Bytes after opcode | Observed effect |
|---:|---|---:|---|
| -17 | 8003B480 | 2 | assign parent+88 |
| -16 | 8003B444 | 2 | assign parent+96 effect rate |
| -15 | 8003B408 | 2 | assign parent+92 effect rate |
| -14 | 8003B3D4 | 0 | set resource +30 from cfg+AE (452 / 1C4) |
| -3 | 80033BEC | 0 | clear +32, common script helper (existing SDK provenance conflict) |
| -2 | 80033BC0 | 0 | set +32=1; clear +68 |
| Others | 80033BB0 | 0 | return -1 |

Actual script decode: 10 commands, descending raw timestamps 900,750,600 twice,450 twice,300 twice,150 twice; four -16 rate changes, five -15 rate changes, one -14 model change. Rate1 values 8,12,17,25,51; rate2 values 256,512,768,1024. Script order preserved, including same-time commands. First 30 halfwords (29 command halfwords + final timestamp -32768) agree regionally. Sentinel -32768 remains future while countdown >=0; do not continue parsing adjacent unrelated data at negative time. No -17/-3/-2 in this bounded authored stream.

With the ordinary 684-start countdown and consecutive decrements, the groups first become eligible at countdown 449,374,299,224,149,74 (strict inequality). Not absolute ticks, not real-time seconds. Parent +92/+94 and +96/+98 are independent rate/accumulator pairs. Crossing 256 calls 8003B53C and 8003B6B4 respectively, potentially multiple calls in one update; negative accumulator handling is retained, not modeled as unsigned wrap equivalence. 256 rate nominally one effect allocation attempt per update at zero carry. First family creates phase -2 short-lived animated effect (30 countdown, resource IDs 170..175 hex); second phase -3 vertical ballistic/spinning effect (resource1C5, velocity/position and RNG-derived offset). No direct player-health deduction in these two measured family paths. Do not assume visual effect = attack.

## 3. Five independent damageable targets

Phase -1 8003B8FC allocates auxiliary type07 child at +84, follows parent transform and renders a paired model (8003BE44), updates each target's yaw = parent+8A + offset, roll += config+BE=512, radius = -(signed parent+86 / 16), world Y=parentY-30. The parent starts +86=8000 (radius magnitude500); during section-relative ticks4560..4745 (absolute9169..9354), if signed +86>=4801 reduces by34 per update. Parent angular step +8C moves toward config+C6 indexed by remaining count-1, at step config+C4=32, and is added to +8A. Thus angular speed changes with surviving target count. Table values at cfg+C6..CE = [1280,896,512,256,128] indexed by count-1; one surviving target -> target step1280 (7.03125 deg/update), five ->128 (0.703125 deg/update). No seconds cadence asserted. Zero-child path at countdown positive succeeds before indexing; zero outside normal lifecycle may access preceding data, no claim of hardened bounds.

Each target has independent cumulative +8E (s16 compared with threshold), stage +8C, hit mask +2A and temporary durability +2E. On hit call 80034C60, add 32 - signed remaining durability to cumulative counter. Compare against cfg+300 + 2*(7*(3*D_800ABDFC + current stage) + D_800AC164). Increment stage once when threshold reached; stage>=3 -> destruction. Else reset durability32 and set hit-feedback model cfg+B8. Normal model before hit = cfg+B6 + 2*stage. Shared parent pointer tracks surviving children, not shared damage; all five have their own thresholds.

8 observed difficulty rows x 3 damage stages x 7 selector columns = 168 s16 values (cfg+300..44F). Whole config range 0x450 bytes JP/EU matches; data table fits within that range. Example final-stage values by difficulty row (seven columns):
0 [20,24,46,66,84,100,114]
1 [20,26,50,72,92,110,126]
2 [20,28,54,78,100,120,138]
3 [20,30,58,84,108,130,150]
4 [20,30,60,90,116,140,162]
5 [32,32,64,96,124,150,174]
6 [20,35,70,102,132,160,186]
7 [20,37,74,108,140,170,198]
Thresholds not raw shots; prior shared hit logic can consume fractional or whole durability stages. Not proof of UI difficulty/selector semantics; row1 is initialized setting from pass18.

Destroying a target decrements parent+84 at 8003BBC8, calls 80045128(cfg+BC=2), allocates type38 fragments from angle table, clears auxiliary type07, transitions target to type31 via 80037DE8/80037D58. Failure to allocate auxiliary or parent type mismatch also reaches child removal/decrement path 8003BE10. Consequently success is *zero remaining allocated targets*, not a rigorous proof that five were destroyed by shots under allocation failure/cancellation.

Child rendering path compares angular relation to current origin yaw with a 90-degree offset; when parent+8E==0 and the unsigned difference gate passes cfg+2E, clears child+68 and calls generic configured action dispatcher 80035418. Parent +8E is set1 in ordinary parent update; order/activation of this action path needs runtime or control trace. No direct player damage call here. Earlier config+2A subdispatch controls actual action; not enough evidence to claim a specific projectile attack.

## 4. Final result and scripted success effect

8003B868 sets D_800AC144=-1, calls 80034E0C(3), increments D_800AC08C, creates phase -4 effect at 8003BF1C (if allocation succeeds), sets parent phase2. Main SPARKBIT 80041AB0 recognizes flag, calls SPARKBIT_HAKAI at 80041B98: D_800ABFC4=1, stage9, phase2, D_800ABE74=1, increments separate counter and calls 80044AC0. SPARKBIT_HAKAI directly jumps to VICTORY_SET3 state; stage9 entries 80041C08/41C88/41D0C/41DA0/41E10/41EE0 correspond VICTORY_INIT/SET2..6. VICTORY_INIT also reachable via separate path, sets D_800ABDDC=1. Phase -4 effect drives parent+90 on landing after staged falling/bouncing animation (8003C2BC), parent phase2 at 8003B8D0 sets D_800ABDDC=-1 and clears itself if +90 nonzero. VICTORY_SET3 waits for nonzero D_800ABDDC before progressing; distinguish this visual cleanup signal from primary success flag D_800AC144. If effect allocation fails, no ordinary completion signal from that effect; not claim of graceful recovery.

Timeout in SPARKBIT at >=9988 sets stage10 and phase2, directly selects DEFEAT_SET3 via table 8008AEA0, distinct from low-health DEAD_END (stage11, pass18). Stage10 index0 at 80042064 logs DEFEAT_INIT, index1 at 800420EC DEFEAT_SET2, index2 at 8004217C DEFEAT_SET3. Named branches establish objective timeout versus successful objective completion versus player health failure. Not every branch or bypass (e.g. earlier missions) fully traced. Parent success check precedes timeout in main dispatcher, but simulation occurs later in same callback, making final-frame ordering important.

## 5. Regional verification

Opcode/register/shift shape mask excludes J/JAL target bits and LUI/ADDIU/load/store immediates. EU=JP-398 throughout sampled code. This is structural, not binary equivalence.

| JP range (exclusive) | Words | Exact | Shape |
|---|---:|---:|---:|
| 8003AFE8..8003B2FC |197|178|197|
| 8003B2FC..8003B4BC |112|94|112|
| 8003B53C..8003B868 |203|178|203|
| 8003B868..8003B8FC |37|30|37|
| 8003B8FC..8003BEEC |380|353|380|
| 8003BF1C..8003C414 |318|284|318|
| 80041968..80041D9C |269|178|269|
| 80042064..8004217C |70|47|70|
| Total |1586|1342|1586|

18/18 opcode table pointers relocate correctly. 30/30 stream halfwords match. 552/552 config halfwords match (0x450 bytes, including 168 threshold values). No intersecting target-scoped SDK anchors in compared windows; shared -3 helper provenance conflict remains open outside ranges. No source, symbol, binary, CI or matching-oracle changes.

## Next

Recover D_800AC164 from its writers and the four gunner records; explain encounter gating, all seven damage selector columns, player count/weapon class interactions, and D_800ABDFC setting. Then trace remaining objective bypasses and nonzero mission alias. Both CHDs remain project inputs; STR/TMD analysis separate until container works.

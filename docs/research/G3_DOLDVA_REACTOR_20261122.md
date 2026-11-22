# G3 type 80: Doldva rotating reactor geometry, damage and result gate

R1 pass 20, 2026-11-22. Input research head 5b68ce60. Same immutable original EXE blob IDs JP 7b5ad2b5035634abd6873c86c90f486f6a99dffd / EU e9cfc4ee2bb3a4b474567d371037cfcd6c56cbb7 (SHA-1 verified pass 12/15). Extends [composite census](G3_OBJECT_CENSUS_COMPOSITES_20261122.md), [shared health](G3_PROXIMITY_HEALTH_20261122.md), [mission scripts](G3_MISSION_SCRIPTING_20261122.md). Static evidence only, no raw asset or source changes.

## 1. Identity: Doldva/carrier result signal

Type 80 config 42 at JP 80088D64, authored at tick 3552, model/resource D9, descriptor 80078714, stream pointer 800AB39C. Secondary descriptor rotation is static initial pose, not the complete motion. Parent initializes +92 from first signed halfword (3888) and advances +5C to next (4096). Both halfwords match EU at 800ABBE0 (JP+844). Parent success helper 8003CA54 at 8003CA74 writes -1 to D_800AC584, increments existing destruction-event-like D_800AC08C, calls 80034E0C(2), selects config+B6 or +B8 audio event based on signed D_800AC1D4 != 0, invokes effect allocator 8003CADC and clears parent type.

JP 800412D8 routine at absolute tick >=4088 (0xFF8) tests D_800AC584. If nonzero, or if word D_800AC41C == 4, calls 80041444, whose literal diagnostic at 80021134 is KUUBO_DIED (carrier destroyed). This clears D_800AC494, selects event 26 at 8004525C, and advances nested phase +2 to bypass failure. Otherwise increments phase and calls 800413A4, literal DOL_FAIL1. Subsequent success handler 800414A0 logs DOL_SUCS; 80041510 logs DOL_SUCS2. Nearby literals DOL_BEFORE_INIT / DOL_BEFORE corroborate the phase family. These are strong internal semantic identifiers, beyond a visual timing guess. We can provisionally name type80 the Doldva reactor controller with high confidence; still no rendered TMD inspection. Do not conflate the carrier result with final mission victory. Other writers to D_800AC584 at 8002454C/2456C and reset sites remain to characterize; not uniquely a boss-generated flag.

## 2. Hierarchy and exact circular layout

Pass19 established maximum 35 children at construction: phase -4 (1), -5 (1), -1 (4), -2 (29). All share parent pointer +64 and type80 until transitions. Phase -1 table (8008AC28) provides four angular offsets at quarter-turn intervals and progress thresholds 1,4,2,3 in stored order. Phase -2 table 8008AC3C has 29 records, each s16 {radius, angular offset, axial offset, minimum surviving stage/index}. Full JP/EU table equivalence pass19.

Grouped structure (not a dump of individual authored records):
- 13 at axial offset 100, stage/index 5: central point radius 0; four at radius 80 offset by 45 degrees from cardinal axes; eight at radius 160 separated by 45 degrees.
- 16 at radius 150: four cardinal-angle groups, each four equally spaced axial positions 200..500, stage indices 1,4,2,3 corresponding to phase -1 groups.

8003D3E0 obtains parent roll and child angular offset, computes packed sin/cos via 80030454 on negative sum, multiplies by signed child radius and truncates fixed point (2*product >>16). It sends local vector (XY radial terms, Z axial offset) through 8003D4D8 using parent's packed orientation words, then adds parent world position and stores child +4/+8/+C. Thus a cylindrical assembly in parent local coordinates, not independent enemies moving along authored paths. Exact angle sign and fixed-point rounding matter; do not replace with a floating-point implementation in matching C.

Parent active phase3 calls 8003CA0C, which adds 384 to u16 object+14, obtains trig pair and renders. In 16-bit full-turn terms this is 2.109375 degrees/update, 170.6667 updates per nominal revolution. Also spins in phase4 while outstanding group count nonzero. No seconds rate asserted: driver runs twice per main callback but stream pace not verified. Parent phase2 retracts +86 by 20 until zero (initial 450), phase5 adds 20 until 450, and phase6 renders. Phase1 and 6 use same render-only helper; phase -4 animation can advance parent phase from 1 to 2. Full jump table already in pass19.

## 3. Hit aggregation, five damage stages, four groups

Phase -2 handler 8003D1E8 checks parent type and child+8E against parent+8E. Clears child when parent type differs or child threshold <= parent progress stage. Parent phases 0..2 set child collision request +28=0; phases 3 and 4 set +28=1 and update cylindrical transform. Nonzero child+2A hit mask ORs into parent+84 at 8003D294. It attempts an auxiliary effect allocation via 80031490 then 80037E0C; effect retains same parent and radial coordinates, phase -3 (not type31 yet). This is not independent health for all 29 collision proxy children.

Parent phase2/3 copies accumulated +84 into +2A and clears +84; 8003CB9C only consumes hits when D_800AC29C == 1 and parent hit mask nonzero. Calls existing hit processor 80034C60, adds (32 - resulting +2E) to cumulative +90, resets +2E=32, compares signed +90 to config+C2 + 2*(7*stage + D_800AC164), increments stage +8E at most once per eligible call. No subtraction of cumulative threshold. Do not equate accumulated damage units with raw shot count; shared hit processing includes class-dependent fractional progression (pass9). No bounds check in table access; ordinary success stage count=5 from config+C0. During phase3 deadline handling may decrement stage back to 4, preventing ordinary advance beyond fifth row under expected flow.

All five rows of seven s16 thresholds JP/EU agree (35 values). Columns selected by D_800AC164 (existing gunner/difficulty mapping unknown). Final thresholds: 80,82,160,234,304,370,432. The first four rows equal 1/2/3/4 times [17,18,35,52,67,82,96]; fifth differs from simple 5x. This proves dynamic scaling of cumulative damage target; not a proven number of players. Config +C0=5 in both regions.

Child phase -1 (8003CE58) updates own roll from parent+14 + angular offset, inherits parent position, renders model resource base config+B0 plus animation byte. In phase3 increases +86 by config+B4 (128) to config+B2 (2304). Once animation threshold met and child+8E <= parent+8E, decrements parent's +8C counter (initial 4), calls 80045128(cfg+AE), creates phase -6 fragments via separate table, turns group itself into phase -3 effect. Thus four group thresholds drive individual visual destruction and the 16 corresponding hit proxies vanish. Phase -6 fragments use their own hit and durability processing (8003D370), else fragment motion 8003DB0C. Phase -3 checks parent existence and updates radial effect then calls 80037D58.

Phase4: surviving phase -1 groups retreat their animation +86 by 128; on crossing <=0 decrement parent+8C. Once this count zero, parent goes to phase5 and retracts. This count represents outstanding groups, not simply damage stages. No claim which original models correspond to each group.

## 4. The timed destruction window

| Tick | Verified meaning |
|---:|---|
| 3552 | Authored type80 creation event |
| 3888 | First stream word / exclusive success cutoff |
| 4088 | Main sequence checks carrier destruction flag, selects named success/failure branches |
| 4096 | Second stream word / active phase3 ends when time reached |
| 4608 | Environment transition (pass17) |

8003C934 phase3: after processing hits, if signed progress >= cfg+C0 (5), compare current unsigned section tick D_800ABFA4 with signed parent+92 (3888). If tick < deadline call 8003CA54 (success). Otherwise decrement progress by one; no success flag from this path. If no success, compare current section tick to next signed halfword at +5C (4096); at or after transition, advance phase to4 and still spin/render. Section start for this object is zero, so these relative ticks coincide with absolute ticks here. Maximum possible authored creation-to-deadline span 336 ticks = 168 sampled stream-clock units; actual shooting window shorter due to opening/animation phases, and no seconds conversion. Condition is strictly before 3888, not <=. Failure path still animates retreat. Stage result check is separate from deadline and has explicit D_800AC41C==4 override.

## 5. Regional differences and verification

Type80 config bytes over 0x12C compared as 150 halfwords: one difference +B8 JP 36, EU 7; +B6=7 in both. This is the alternate sound/event branch, not geometry or threshold change. Do not claim total byte-identical configuration. Prior 156 child-record halfwords already cross-checked.

Structural word compare EU address = JP-398, J/JAL targets and LUI/ADDIU/load/store immediates masked (not full binary equivalent):
| JP range (exclusive) | Words | Exact | Shape |
|---|---:|---:|---:|
| 8003C934..8003CA54 |72|62|72|
| 8003CA54..8003CC58 |129|113|129|
| 8003CC58..8003CD04 |43|37|43|
| 8003CD04..8003CE58 |85|77|85|
| 8003CE58..8003D1E8 |228|211|228|
| 8003D1E8..8003D320 |78|72|78|
| 8003D320..8003D4D8 |110|100|110|
| 800412D8..80041510 |142|102|142|
| Total |887|774|887|

Three nested phase jump tables at JP 80020F04 (7), 80020F24 (7), 80020F44 (6), EU table addresses JP-20, all 20 code pointers relocate -398. No target-scoped SDK anchor intersects the inspected windows. Existing ASM row remains unchanged; not a matching C conversion.

## Next

Type89 late composite: decode specialized stream at 8003B2FC, map its five children and hit/child-count completion, prove its connection to the named final victory/defeat branches. Independently resolve D_800AC164 selector to explain damage thresholds. Actual STR route and TMD extraction remain blocked as of prior container failure.

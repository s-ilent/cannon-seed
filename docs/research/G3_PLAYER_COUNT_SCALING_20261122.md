# G3 effective player count and difficulty scaling

R1 pass 22, 2026-11-22. Input research head a9f783923547506a230dede8c694bcba919a4e8c. Original private EXE blobs JP 7b5ad2b5035634abd6873c86c90f486f6a99dffd / EU e9cfc4ee2bb3a4b474567d371037cfcd6c56cbb7, SHA-1 verified pass12/15. Static analysis, no source/binary edits or runtime witness. Extends [mission inventory](G3_MISSION_INVENTORY_20261122.md), [shared health](G3_PROXIMITY_HEALTH_20261122.md), [Doldva](G3_DOLDVA_REACTOR_20261122.md), [SPARKBIT](G3_SPARKBIT_FINAL_OBJECTIVE_20261122.md).

## 1. Effective player count is distinct from local participation mask

JP D_800AC164 (s16 effective player count), D_800AC17C (u32 participating player mask), D_800AC154 (initial count snapshot). Positive ownership from entry and removal pathways, not inference from scaling values.

- Entry initialization 80042F18 clears mask/count at 80042F50/58. Calls 80043354 (which calls entry update 80043464). Then checks 80045B9C; when return ==3, directly sets count2, ORs mask with9 (slots 0 and3), increments each corresponding record's +44 and calls 80043290. Exact meaning of return3 not established; do not assume menu or attract mode.
- 80043464 iterates exactly four 0x8C-byte gunner records starting with index3 down to0, dispatching on +44. Record base 801474FC. Entry phase0 80043604 checks local input/credits-related state, sets record+44=1, record+46=14, sets bit (1<<slot) in D_800AC17C. Some paths decrement record+3C threshold and do not enter. A parallel four-halfword array at 800ABF6C tracks pending entry flags.
- Entry phase1 800436F4 decrements record+46; while nonnegative sets pending flag, on signed-negative transition increments record+44 and D_800AC164 and clears pending flag. Count can lag the bitmask during entry.
- 800239F4..80023AB0 handles input bit0x10 under specific timer/state gates. When slot's participation bit is set, clears it; if pending flag is zero, decrements D_800AC164 (80023A80); zeros gunner+44/+46 and clears associated state. Do not assume this removal happens throughout active combat; enclosing entry/input gates apply.
- 80044820 clears count; 800448CC snapshots current count in D_800AC154. 8004416C clears snapshot. Not a separate difficulty setting.
- Direct store scan over JP 80022000..80070000 with SH immediate -16028 yielded writes at 80022FD0,80023A80,80042F58,80042FFC,8004374C,80044820. This immediate scan is not exhaustive for indirect writers.

## 2. Explicit 1..6 override during active main sequence

80022F94 calls 80025944(9); if return != -1, main mode D_800AC5AC==4, and unsigned (return-1)<6, writes value to D_800AC164 at 80022FD0. All other values ignored. This admits 5 and 6 independent of the four local records. No corresponding participation-mask write. We can name the value effective player count, not claim six local PSX controller slots or actual six-player runtime support.

80025944 is an indexed accessor over fixed 80010000 memory. JP table 80020480 (18 slots): index9 -> 800259C8 -> sign-extended halfword at 80010B2A. Index3 -> 80025A28 -> halfword at 800100BA or 800105F2 depending on selector word at 80010000. Index9 reads same fixed address regardless selector. Proven interface, producer/transport not yet established. Memory is below EXE load base 80020000; could be external or runtime-initialized control data; no attribution to particular arcade networking/debug protocol without producer evidence. 80045B9C reads signed halfword 80010E04. Four-gunner path remains independent of external count. This is consistent with reuse of six-player balancing data; not proof of arcade code lineage.

## 3. Encounter counts by fixed effective count

Reran bounded traversal of the four JP mode-zero schedule lists (857 entries, 779 primary and 78 secondary). Prior pass13 independently verified regional schedule equivalence. Count primary records if signed minimum gate <= selected count, plus all secondary records; hold count fixed. This is static eligibility, not actual runtime spawns (cursor order, stale timestamps, pool occupancy, secondary descriptor gate, and additional conditions remain). No raw descriptor data published.

| Count | Primary | Secondary | Total | Type60 | Type68 | Type1D |
|---:|---:|---:|---:|---:|---:|---:|
| 0 |614|78|692|465|34|60|
| 1 |614|78|692|465|34|60|
| 2 |646|78|724|490|34|60|
| 3 |777|78|855|599|40|74|
| 4 |778|78|856|600|40|74|
| 5 |779|78|857|601|40|74|
| 6 |779|78|857|601|40|74|

Largest change 2->3: +131 entries. 3 count qualifies 855/857 (99.77%). Relative to 1, count6 adds165 (23.84% more). At count3 only two type60 entries excluded. Other changes: type50 28->34 at2; type79 11->12->13 at2/3; type20 5->6 at3. Both composite boss roots (type80/89) qualify regardless count. All 5 type88 entries unchanged. Config ID18 (not runtime type18) has special primary gate: count>=2, accessor80025944(3)!=1, trunc(signed health/100)>=85. No config18 entry in inventoried mode-zero lists; do not apply this condition to observed counts or claim effect in this mission.

## 4. Separate difficulty setting and boss scaling

D_800ABDFC initialized from third s16 default in JP 8008AF3C at 8004424C, value1. EU defaults at 8008B754: [3,1,1,1,1,0,0] versus JP [3,1,1,0,1,0,0]. Difference fourth field feeds D_800AC1D4 (the alternate audio/event selector in Doldva pass20), not difficulty. User-facing name and persistent override path not proven. Only direct store with matching SH immediate in scanned code is initializer, not proof of immutability.

Ordinary player-contact damage multiplier uses row D_800ABDFC and column count, all seven columns equal in observed eight rows [2,4,6,8,10,13,15,20]. Thus per-contact damage scales by independent difficulty, not by effective count in those rows. Ordinary enemy durability initialized by cfg+14+2*count (pass11).

Doldva cumulative final threshold by effective count0..6: [80,82,160,234,304,370,432]. It does not index D_800ABDFC in this threshold calculation; ordinary hit processing and other effects may still depend on additional settings. SPARKBIT final threshold indexes both settings, at initialized damage row1: [20,26,50,72,92,110,126] per target. Five targets, total nominal threshold across all five = [100,130,250,360,460,550,630]; not raw shot count, threshold overshoot and hit processing matter. Count6 vs count1 Doldva 432/82 (~5.27x), SPARKBIT 126/26 (~4.85x), versus sixfold effective player count. Encounter density rises only ~24%. No claim of exact per-player difficulty without input cadence/weapon analysis.

## 5. Regional verification

Structural comparison mask J/JAL targets, LUI/ADDIU/load/store immediates; not full binary equivalence. Nonuniform regional displacement before central game code measured explicitly.

| JP half-open range | EU start | Words | Exact | Shape |
|---|---|---:|---:|---:|
| 80022F94..80022FE4 |80022FF4|20|17|20|
| 800239F4..80023AB0 |80023A54|47|38|47|
| 80025944..80025AD8 |80025920|101|78|101|
| 80042F18..80043040 |80042B80|74|45|74|
| 80043464..8004354C |800430CC|58|45|58|
| 80043604..80043770 |8004326C|91|78|91|
| 80030EA4..80030FF8 |80030B0C|85|74|85|
| 800441E4..80044278 |80043E4C|37|20|37|
| Total ||513|395|513|

No matching build, source conversion, runtime, or SDK attribution claim. See earlier tables for direct regional data checks.

## Next

Trace fixed 80010000 interface initialization and producers, especially 80010B2A; establish whether the 1..6 override is used by PSX local menus, external/debug control, or shared arcade-era configuration. Then investigate nonzero mission schedule alias and type98 config mutation (pass13 unresolved); verify actual STR metadata and assets when execution environment allows.

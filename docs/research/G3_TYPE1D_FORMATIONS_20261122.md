# G3 type 0x1D encounter formations and model resource map

R1 pass 16, 2026-11-22. Main 173e1dfb; original gameplay PR input 02d8a36e; pass 15 consolidated at dad75d8d. Extends [type 1D controller](G3_TYPE1D_CONTROLLER_20261122.md), [movement segments](G3_MOVEMENT_SEGMENTS_20261122.md) and [mission inventory](G3_MISSION_INVENTORY_20261122.md). Same immutable JP/EU EXE blobs as pass 15 (SHA-1 checked there). All inspections in memory. No game data copies, source edits, build or live runtime trace.

## 1. Six formations, not a continuous 500-tick wave

JP primary list 800878EC (EU +818), section start 4609. Walk 8-byte entries in stored order to FFFF; for each descriptor config 66 hex, inspect flags, positions, angle, first movement record. 74 events, 58 distinct descriptors, all between ticks 5105 and 5185 inclusive. Every event agrees across regions in timestamp, gate, first ten descriptor halfwords (excluding pointers), and all 12 halfwords of corresponding first movement record. 60 gate-0 entries, 14 gate-3 (gate meaning unproven). All descriptor+10 angles zero.

| Absolute tick | Events | Mode 0 | Mode 2 | Speed scalar 10 | Speed scalar 40 | Gate 3 |
|---:|---:|---:|---:|---:|---:|---:|
| 5105 | 6 | 0 | 6 | 6 | 0 | 1 |
| 5153 | 10 | 0 | 10 | 10 | 0 | 2 |
| 5157 | 6 | 0 | 6 | 6 | 0 | 1 |
| 5161 | 10 | 0 | 10 | 10 | 0 | 2 |
| 5169 | 23 | 13 | 10 | 10 | 13 | 4 |
| 5185 | 19 | 19 | 0 | 19 | 0 | 4 |
| Total | 74 | 32 | 42 | 61 | 13 | 14 |

Coordinate component ranges by authored representation (do not combine):
- World mode 0: x 5257..6807, y 2746..4046, z 62656..64256.
- Rotated-origin-relative mode 2: x -1000..900, y -600..500, z 8000..8600. Signed low descriptor halfwords.

There are three entry pointers into the same overlapping stream family: JP 8007CDA4 (42 references), 8007CDD4 (13), 8007CE04 (19). Each begins mode 4, orientation policy 0, target offset (0,0,+4000); desired control words 0x000A0000 / 0x00280000 / 0x000A0000. The physically shared tails can be traversed as 10/8/6 records to a negative terminator, with all compared record halfwords agreeing in regions. **Do not count these tails as active paths:** type 1D calls 800327F8 once; 1C's ordinary active controller does not iterate +5C or call 80032A40. Its two phases use the direct motion helpers. No claim that the tail records are unreachable for other object types.

## 2. Initial movement, exact conditional phase-0 integration

Pass 15 proved config 66 -> config 7B -> type 1C. The spawn mode 2 rotates the initial coordinate with 800326A8; first movement mode 4 subsequently converts it to world coordinates. 80032BC4 adds origin globals 8016AC18/1C/20 to current integer components, and 80032CB8 separately transforms/adds origin to previous target (if needed), then adds the record offset, and 80033080 sets +26=0 and clears coordinate flag 4000. For world mode 0 initial target equals position. For mode 2, the constructor rotates both relevant representations consistently (verify actual origin/rotation values before rendering the positions). 80032880 uses target minus position; 80032984 copies movement angles into model angles for policy 0. The common authored heading for mode 0 is +Z; the same intended world +Z offset for mode 2 follows the frame conversion. Exact mode 2 initial angles remain conditional on identical fixed-point transformed coordinates. The authoring does not establish whether the player is moving toward or overtaking the enemies.

Config 7B values independently read:
- +A4 = 0x00003000 (speed step)
- +B4 = 0x003C0000 (phase 1 desired control, low halfword zero)
- +BE = 0x7FFF (signed phase-0 countdown)
- +BC = -2560 (rotation increment)
Constructor copies low halfword +B4 to +46, hence initial displacement from its direction-scale multiply is zero, and +34 initially zero. +44 is left as first-record desired control. Phase 0 calls 80033274 -> 800334AC -> 800387BC. Phase 1 requires countdown negative and speed threshold passed; no earlier transition observed in this routine. Thus 32768 phase-0 calls are required before the timer permits phase 1. Do not translate to seconds without the clock.

For exact +Z heading and uninterrupted phase 0, confirmed atan table first entry zero at 8008B640; 8008A254 first quadrant sign/offset entries lead to zero angle. 80030454 uses a quarter-wave LUT at 8008D660 with endpoints 0 and 32767 (not 32768). 800334AC has two signed truncations in the Z projection and 800387BC adds signed high velocity halfwords for world mode. The local numerical model is:
```
control = min(desired, control + 0x3000)
v = control >> 16
projected = (2 * 32767 * v) >> 16
z_step = (2 * 32767 * projected) >> 16
```
Positive-speed, zero-angle only. Cap 10 reached on call 54; cap 40 on 214. Both yield cap-2 integer world displacement (8 / 38 units per call) rather than 10 / 40. Checked in an independent integer arithmetic loop: accumulated z displacement after 54 calls is 160 for either cap, after 100 calls 528/715, after 214 calls 1440/3800, after 300 calls 2128/7068. These are **conditional** integration results, not runtime trajectory witnesses; distance/angle culling, damage, changing frame origin may end the object sooner. The movement record's offset is a direction initializer, not a verified waypoint reached in the live controller.

80034748..80034828 proves distance result is squared Euclidean distance to global origin vector for world mode, or squared signed high-halfword position for relative mode 1/2. Arithmetic is 32-bit. 80038888..800388E8 uses relative velocity components (subtract origin velocity globals 8016AC38/3A/3C in world mode), squared and summed, plus 0x10810 or 0x2F44 depending on D_800ABF9C. Proximity calls 800389A0 -> 800351D0. 800351D0 tests two computed angles against bounded unsigned intervals, then calls 80034EC0 and tests the resulting angle; qualifying path calls 80035348 and returns -1. Other paths return 0. Exact side effects of 80035348 still need adjudication. 800388F4 compares distance to 0x17D783FF (400000000 - 1); clears type if exceeded (signed compare). No claim about whether a collision damages the player until callee is traced.

## 3. Full model-ID to asset-index table

**New positive evidence independent of the flight analysis.** JP startup at 8002255C loads pointer 800717A4 -> 80020014, literal `\\DRAGOON\\TMD.DAT;1`, calls archive loader 80024760 at 80022564. Then passes literal 800717C4 to 8002DE2C at 80022574, and calls model-table initializer 8002DE3C at 8002257C.
- 8002DE2C writes pointer to D_800ABBE4.
- 8002DE3C walks 0x14-byte records until first word -1. Reads word +4 as signed asset index. Nonnegative index is passed to 80024910. On nonzero result stores pointer at +10 and calls GsMapModelingData(pointer+4); negative index or zero result stores -1.
- 80024910 indexes the archive's 32-bit offset table at gp+54, returns archive base + rounded offset, or -1 on negative index. Actual archive bytes not available for this pass.
- 8002F368 compares requested ID against **record word +0**, returns word +10 and output words +8/+C. Correction to earlier communication atlas: first word is ID, not count.
- The separate table at D_800ABBEC uses stride 0x34 and is not this model table.

| | JP | EU |
|---|---|---|
| Model table base | 800717C4 | 80072004 |
| Terminal -1 record | 80072FC0 | 80073800 |
| Nonterminal records | 307 | 307 |
| Resource 0x9F record | 80071CEC | 8007252C |
| Zero-based row index | 66 | 66 |

All 307 x 5 initial words agree exactly across the two region images (runtime +10 slots are identical in the images). Resource 0x9F appears once, asset index 57 (0x39), word +8 = 0x40, word +C = 0. Only row with asset index 57. Therefore model resource 0x9F resolves through the TMD archive's index 57, not necessarily the 57th Psy-Q object within a single TMD file. This is a mapping to a disc archive entry, not a visual identification. Via 8003894C -> 800337B8 -> 80031C5C/80031CDC the active 1C controller emits into the communication/render submission system established earlier. No model mesh extracted.

## Next

Trace world origin/velocity writers and mission-clock cadence. Recover archive loader and index offset format (80024760, 80024910) and proximity response 80035348. A local tool can use the 307-entry map to link gameplay and extracted TMD geometry, but the archive itself must be supplied locally. Do not publish raw authored encounter/asset data; no game source conversion before oracle.

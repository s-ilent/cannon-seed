# G3 stream-synchronized mission clock and world origin

R1 pass 17, 2026-11-22. Base main 173e1dfb; gameplay research input 32562e1f. Extends [formation and model atlas](G3_TYPE1D_FORMATIONS_20261122.md), [mission scripting](G3_MISSION_SCRIPTING_20261122.md), [render preparation](G3_RENDER_PREP_ATLAS_20261122.md).

Input: the same immutable JP/EU original EXE blobs (7b5ad2b5035634abd6873c86c90f486f6a99dffd / e9cfc4ee2bb3a4b474567d371037cfcd6c56cbb7) SHA-1 verified in pass 15. No new build witness. In-memory word inspection and tracked assembly. No original movie payload present in available inputs.

## 1. Clock writer found: stream metadata, not increment loop

JP 80022EF0 calls 8002B028, whose return is literal pointer 801387C4 to the current custom metadata block. JP 80022EF8 reads signed halfword at +10 hex; if it is not -1 and D_800AC494 == 1, 80022F20 stores low halfword of value << 1 to D_800AC16C (absolute mission tick).

The prior global store scan of the central object row missed this because it lives in the earlier render-preparation row. Full direct LUI + SH search over JP executable code (within 80 bytes, candidate check) found four direct stores: 80022F20 assigns stream time, 800405A4 / 80044764 / 8004490C reset zero. This does not rule out indirect stores.

Distinguish D_800AC294, updated immediately before this from St header word +8 via 8002B20C and shifted left one. That is a separate stream-header-derived counter, not the mission tick. Do not equate header and custom record fields without actual stream data.

The main callback 80042A80 calls the world origin updater once, then 80042ADC and 80042AEC call the environment/encounter/object driver twice with D_800AC29C = 0 then 1. In particular, absolute mission time is not incremented by either call. Both calls observe the same sampled time in the inspected sequence. This explains why the primary scheduler admits current and previous tick entries: the sampled time is even under the discovered clock writer. This is a structural explanation; skipped stream records or allocation gates can still prevent spawns.

Conditional mapping assuming consecutive metadata samples and clock gate open:
- Environment change at tick 4608 -> metadata clock 2304.
- Section 2 threshold 4609 -> first even tick 4610 (metadata clock 2305).
- First type-1D wave at 5105 -> first even tick 5106 (metadata clock 2553).
- Last wave at 5185 -> first even tick 5186 (metadata clock 2593).
- Difference between first/last wave = 40 metadata clock units, or 80 mission ticks. This is not yet a seconds conversion.

Main frame submission 800231B0..800231D8 invokes VSync(4) when gp+0 == 1, otherwise VSync(0). This is evidence for a vsync pacing policy, not proof of media frame cadence or actual playback time. Do not assert nominal 15/30 fps, PAL/NTSC seconds conversion or consecutive metadata values without sampling stream headers and custom records. Two simulation calls per frame do not establish the absolute mission clock rate.

## 2. Exact metadata extraction contract

80022EA4 calls 8002ADA0 with a2=2. That wrapper calls 8002AE50 and obtains a payload pointer from StGetNext(&payload, &D_800ABB74) at 8002AE80. Its mode-2 path:
- signed halfword at payload+0 is a byte offset;
- unsigned halfword at payload+2 stored as D_800ABB9C;
- block source = payload + 4 + signed offset;
- copy exactly 0x50 bytes to D_801387C4, with aligned and unaligned implementations (8002AF38 / 8002AF8C).
- 8002ADA0 then submits the payload to the decoder (8002AE1C) and frees the ring entry (8002AE24, StFreeRing).

The initialized streaming system calls StSetRing and StSetStream (8002A76C / 8002A784). These are archive-backed Psy-Q LIBCD symbols. The literal stream filename catalogue at JP 80076D84 consists of 0x4C-byte entries; index 0 names `\\DRAGOON\\G3.STR;1`, index 2 `\\GOURB\\G3ORG.STR;1`; other entries include the briefing, alternate XA clips and ending/movie paths. 8002AA68 copies the selected filename and 8002AA74 calls CdSearchFile. Need actual mission stream and selection trace to validate which clip(s) provide mission samples; no STR bytes reconstructed from executable.

8002B028 returns the 80-byte buffer address and writes the separate D_800ABB9C halfword to caller output. Thus there is a direct, proven stream-to-simulation data path.

## 3. Pose and velocity writer

JP 8003E268..8003E454, EU 8003DED0..8003E0BC. Sole direct JP JAL to entry at 80042A80. Copies current mission tick to D_800ABF1C (effective address 800ABF1C; raw low immediate -16612), obtains pointer from 8002B028 and reads fields below (offsets relative to metadata base, hex).

| Offset | Format | Consumer |
|---|---|---|
| 10 | s16 | mission clock at 80022EF8 (-1 sentinel) |
| 12 | u16 | negated into origin angle at 8016AC24 |
| 14 | u16 | copied into origin angle at 8016AC26 |
| 16 | u16 | negated into origin angle at 8016AC28 |
| 18 | s32 | world X -> 8016AC18 |
| 1C | s32 | world Y -> 8016AC1C |
| 20 | s32 | world Z -> 8016AC20 |

Position scaling:
- mode zero (D_800ABF9C == 0), tick < 7942: direct words.
- mode zero, tick >= 7942: each component uses signed integer truncation (component * 100) / 13, via 32-bit shift/add and signed DIV.
- mode nonzero: each component multiplied by signed halfword D_800ABFFC (effective address 800ABFFC). No universal scale fixed yet.

Store the new position and the low 16 bits of new minus old into 8016AC38/3A/3C. These globals are **sample-to-sample displacement**, not velocity in units/second; no time divisor in this writer. This independently confirms the moving-origin vector subtracted from enemy velocity in pass 16.

8003E454..8003E648 (EU 8003E0BC..8003E2B0) converts the three rotation angles with 80030454 into packed Q15 trig pairs at 8016AC2C/30/34. Computes motion yaw/pitch from displacement and stores angles 8016AC42/40, pairs 8016AC4C/48, projected scalar at 8016AC3E. Small deltas (all abs components < 256) are scaled by 256 before angle solve. Finally transforms nominal (0,0,32767) through 8003EEA0, applies 80032598 angle solver, and stores facing angles 8016AC44/46. The earlier movement and laser paths consuming these globals are now tied to the streamed vehicle pose.

The 100/13 scale change at tick 7942 is a genuine late-mission event; whether it corresponds to entry into Cannon Seed or something else is not established.

## 4. Regional corroboration and ownership

Compared little-endian raw instruction words at VA -> file offset VA - 80020000 + 800 hex. Exact vs opcode/register/shift-shape mask (J/JAL target field, LUI and ADDIU/memory immediates excluded; inspect actual operands for semantics, not a proof of binary equivalence).

| JP range (exclusive) | EU start | Words | Exact | Shape |
|---|---|---:|---:|---:|
| 80022EF0..80022F24 | 80022F50 | 13 | 10 | 13 |
| 8002AE50..8002B028 | 8002AE40 | 118 | 106 | 118 |
| 8002B028..8002B048 | 8002B018 | 8 | 6 | 8 |
| 8003E268..8003E454 | 8003DED0 | 123 | 103 | 123 |
| 8003E454..8003E648 | 8003E0BC | 125 | 96 | 125 |
| 80042A78..80042AF4 | 800426E0 | 31 | 17 | 31 |
| Total | | 418 | 338 | 418 |

No intersecting target-scoped SDK anchor intervals in these windows. Positive game-owned behaviour (custom stream metadata, encounter clock and pose globals), distinct from anchored SDK StGetNext (JP 800635FC, EU 80063F8C), StFreeRing (JP 80063728, EU 800640B8), VSync (JP 8004B1C0, EU 8004AB50).

JP backing rows: config/splat.g3_jp.yaml 0x32FC func_80022AFC (render), 0xAADC func_8002A2DC (stream), 0x14444 func_80033C44 (pose + mode). The first two retained assembly rows were inspected directly; last row too large for connector whole-file text so decoded equivalent immutable original executable words. No row split, naming change, census run, or C conversion.

## 5. Narrative cross-check (user-supplied mission description)

Four named sequences: Burn up the space (hangar/catapult cinematic); Fight back a chap (asteroid slalom and interceptors, then main fleet); Destroy possessed enemy (approach Doldva over Red Eye, destroy rotating internal reactor); Spend a restless fight (atmospheric entry, canyon fighter encounter, sudden climb over hill, final defense line, Cannon Seed interior).

The explicit canyon fighter encounter after atmospheric entry strengthens the interpretation of the tick-4608 environment switch and six type-1D waves at 5105–5185, but title-to-tick mapping is not proven. Do not assign visual identity to the model or specific mission events without video/pose samples. The description provides a useful independent hypothesis for correlating camera trajectory (slalom, large turn, canyon, climb) with recovered stream metadata.

## Next and blocker

Need the privately provided original `DRAGOON/G3.STR` (JP first; EU useful) or legally provisioned disc on the user's machine. File-library title search yielded no matching asset; not a proof of absence. Decode reassembled StGetNext payload, not arbitrary raw CD-sector offsets. First validate SDK sector header/chunk ordering, data sizes and signed metadata offset bounds. Then produce a local guarded extractor with synthetic test records; compare stream header count, custom tick and position/angle continuity, detect skips, and overlay mission-event samples. Plot route and formation positions locally without publishing raw copyrighted stream or authored path data. A reusable parser and this spatial overlay are the next useful work; no need to decode MDEC pixels for pose extraction if frame payload is correctly reassembled. No claim of full route or exact timing yet.

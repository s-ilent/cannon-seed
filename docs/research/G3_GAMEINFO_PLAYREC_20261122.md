# G3 gameinfo fixed-memory API, playrec infrastructure and mission-mode distinction

R1 pass 23, 2026-11-22. Input research head af484e58a730c277e60ae579c6f0e696570d1a6c. Original immutable private JP/EU EXE blobs 7b5ad2b5035634abd6873c86c90f486f6a99dffd / e9cfc4ee2bb3a4b474567d371037cfcd6c56cbb7, SHA-1 verified pass12/15. Extends [player-count scaling](G3_PLAYER_COUNT_SCALING_20261122.md), [mission inventory](G3_MISSION_INVENTORY_20261122.md), [health](G3_PROXIMITY_HEALTH_20261122.md). Static inspection, no executable copies or raw data publication, no runtime/build witness.

## 1. Fixed memory has a local initializer and a named API

JP 800252A0 returns 80010000. Adjacent 800252A8 initializes that fixed region: +0,+2,+4=0, +6=-1, four 44-byte records beginning +8, two 1336-byte (0x538) banks at +B8/+5F0, and trailing common settings at +B28..+B36. Each bank receives four arrays of ten 32-byte records copied from distinct constant sources; header/footer initialized separately. +0 selects bank zero when zero, bank one otherwise. No direct JAL to initializer or raw aligned literal pointer to it found in scanned EXE; invocation path may be indirect or external. This is a concrete implemented local initialization routine, not proof it executes in every retail startup path.

JP 80025590 setter and 80025944 getter use indexed 18-entry tables at 80020408 and 80020480. Their error messages explicitly use source filename gameinfo.c and function names set_game_info() / get_game_info(). The setter validates some values through unsigned comparisons, logs invalid cases without store; several other indices are unvalidated. This is a RAM settings API, not evidence of an arcade communications device or external six-player hardware.

| Index | Address or bank offset | Setter range / behavior | Supported meaning |
|---:|---|---|---|
|0|80010000|0..1|mission (diagnostic), bank selector|
|1|80010002|0..1|TV_MODE|
|2|bank+0|1..4|LEVEL|
|3|bank+2|unrestricted s16 store|partner selection/control, exact name pending|
|4|bank+4|copy string length <=9|PARTNER_NAME|
|5|bank+E|-1..3|PLAY_RECORDING|
|6|bank+10|0..4|CLEAR_LEVEL|
|7|bank+12|zero clears, otherwise OR|bitmask, name pending|
|8|80010B28|0..1|PAUSE_DISP|
|9|80010B2A|unrestricted s16 store|effective player-count override (pass22)|
|10|80010B2C|0..1|MUTEKI_MODE|
|11|80010B2E|0..1|MAP_COUNTER_DISP|
|12|bank+536|-1..0|SUPER_BLASTER setter, derived getter gate|
|13|80010B30|unrestricted s16 store|pending|
|14|80010B32|unrestricted s16 store|pending|
|15|80010B34|0..1|TUNE_LEVE (literal spelling)|
|16|bank+534|0..3|PARTNER_G_NUM|
|17|80010B36|unrestricted s16 store|pending|

Index12 getter returns -1 iff first-bank final halfword at 800105EE is -1 and second-bank final halfword 80010B26 is -1; otherwise returns 0. It does not simply return selected bank's stored value. (Addresses derived from +1518 and +2854 at getter 80025A74.) Index4 getter returns pointer, not s16. Initializer sets common indices8..11 = [1,-1,0,0], indices13..15/17 zero; both banks LEVEL=2, partner selection=-1, recording=-1, clear-level/bitmask zero. Initial count override -1 disables override. Setter index9 arm 800256AC stores at 800256B0 with no local range check. Active caller 80022F94 applies explicit 1..6 validation and only updates effective count, not mask. Scan all direct JALs to 80025590 in 80022000..80070000: 9 call sites with observed indices 3,4,16,6,7,12,5,3,4; none explicitly index9. No evidence yet that retail UI invokes override; cannot rule out indirect or externally supplied values. Four local gunner records remain independently confirmed.

## 2. Difficulty and invincibility resolved

Startup/settings routine JP 8002278C calls get_game_info(2) for LEVEL and (15) for TUNE_LEVE. At 80022874 writes computed row into third default halfword 8008AF40, subsequently copied to D_800ABDFC by 8004424C. Mapping proven by branch table:
| LEVEL | TUNE_LEVE=0 | TUNE_LEVE!=0 |
|---:|---:|---:|
|1|1|1|
|2|2|3|
|3|4|5|
|4|6|7|

Row0 exists in tables but this normal validated LEVEL mapping never selects it. Invalid level skips write. The previous initialized difficulty row1 is the static default before this settings mapping; do not call it guaranteed player-visible default. If initializer defaults LEVEL=2 and TUNE_LEVE=0 used, selected row2, contact multiplier6 (not4), provided downstream settings copy executes. Pass18/21/22 numeric comparisons remain valid at specified row1 but should be described as static default-row scenarios, not verified normal menu defaults. Example fighter base25 maps to 150 raw damage for row2. Follow actual launch sequence before asserting runtime defaults.

80022878 calls getter index10 and copies result at 80022884 to D_800ABF84: named MUTEKI_MODE, exact invincibility gate previously recovered in shared health (forces health to1 when nonpositive). 800232D8 reads index11 MAP_COUNTER_DISP. 800234E4/8002376C read index8 PAUSE_DISP. Setter diagnostics ground names without speculative labels.

## 3. Play recording subsystem

JP 80045968 initialization sets s16 80010E00/02/04/06/08=[0,0,0,-1,0]. Fills 80010E0A with FF for 0x52FC bytes = 5311 * 4, then clears 80016106 for 0x298 bytes (664 bytes covers 5312 bits). Function with invalid-mode diagnostics (playrec.c, init_play_record()) has direct calls to 800459D4. The preceding linear listing begins at 800459D0; reconcile exact instruction boundaries with matching oracle before C splitting. Modes0..3:
- 0 writes mode at +4 only.
- 1 sets mode, calls 80025AD8(17,id,metadata), clears four pairs at 80144814.
- 2 sets mode, record ID +6 from argument, clears +2, initializes same sample and bit areas.
- 3 selects another buffer at 80013200, updates mode/flags, calls registration helper, clears state and initializes gp counters. This address overlaps first buffer's nominal extent; do not assume physically independent full buffers.

8002278C reads index5 PLAY_RECORDING; valid 0..3 invokes mode2 with requested ID; otherwise mode0. Later success/failure and loaded-partner paths can select other modes. 80045B9C returns record mode +4 (explains pass22 entry special case mode3 registering two local slots 0 and3); 80045C10 returns record ID +6. Mode3 behavior appears playback/partner-related, not established user-facing option.

80045ED4 recording producer checks game state, mode2, matching ID, unsigned absolute mission tick/2 <5311; otherwise diagnostic move_counter over the record area! (playrec.c). Calls 80046020 to write two input halfwords at 80010E0A + 4*trunc(s16 tick/2), and 800461A8 writes bit in parallel array at 80016106 for sample index. 80045F88 playback reader uses same tick/2 index, returns stored pair, or last per-record-ID pair at 80144814 when both halfwords are -1 (sparse samples). If present, copies pair to fallback cache. 80045CF8 reads stream with mode1 or3, matching record ID, same 5311 limit, reads two halfwords and third bit-like field via helper 800460D4; mode3 adds synthesized periodic bit behavior. Input sample meaning needs caller trace, but data recording/playback structure is confirmed. Do not claim deterministic replay completeness, exact recording duration, or on-disc record format until storage/clock path is traced. 5311 sample slots with stride two absolute ticks independently corroborate mission media clock design.

## 4. Alternate mission caveat: two distinct selectors

80010000 mission selector is used by API bank selection and startup 80022A40 (getter0 passed into 8002B520; mission resource loading lead). Separate D_800ABF9C controls object mission timeline. Its direct writers are 80030848/800308E4 inside 80030838, which sets mode0 on zero input and mode1 otherwise, plus different world scaling and configuration. Only direct JAL found at 800224EC, delay slot a0=0, in startup 800224C0 (JP DRAGOON TIM/TMD setup). No aligned pointer to 80030838 in scanned image. This supports ordinary Dragoon EXE startup selecting mode0; cannot conclude mode1 reachable in retail merely from leftover tables. Do not equate mode1 with the API bank selector or identify it as a separate playable mission without positive call path. The nonzero scheduler alias at 800AB968/type98 still unresolved: next trace writes to that range and alternate EXE/disc data, rather than interpreting it as valid static list. Both API mission values and retained game-mode code may reflect shared engine reuse; no provenance certainty.

## 5. Regional comparison

Structural shape mask excludes J/JAL target bits and LUI/ADDIU/load/store immediates; not full binary equivalence.

| JP range (exclusive) | EU start | Words | Exact | Shape |
|---|---|---:|---:|---:|
|800252A8..80025590|80025284|186|182|186|
|80025590..80025944|8002556C|237|164|237|
|80025944..80025AD8|80025920|101|78|101|
|8002278C..800228C8|800227EC|79|59|79|
|80045968..80045B9C|800455D0|141|120|141|
|80045ED4..80046050|80045B3C|95|82|95|
|80030838..8003098C|800304A0|85|57|85|
|Total||924|742|924|

No target-scoped SDK anchors intersect these windows. Names are from original diagnostics, not recovered debug symbol table or matching C. No build/source edits.

## Next

Analyze actual input/replay consumers and storage path if useful; prioritize nonzero mission alias and type98, and resource archive loader (TMD.DAT/TIM.DAT). Verify CHD extraction environment independently when available.

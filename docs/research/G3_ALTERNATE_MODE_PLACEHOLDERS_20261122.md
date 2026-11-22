# G3 alternate schedule alias, inert type 98 and short configuration records

R1 pass 24, 2026-11-22. Input head bb2c60128e278a2214e175b554860d4f8eed6cb4. Immutable original private JP/EU EXE blobs 7b5ad2b5035634abd6873c86c90f486f6a99dffd / e9cfc4ee2bb3a4b474567d371037cfcd6c56cbb7 (SHA-1 verified pass12/15). Static analysis only. Extends [mission inventory](G3_MISSION_INVENTORY_20261122.md), [object census](G3_OBJECT_CENSUS_COMPOSITES_20261122.md) and [gameinfo/replay](G3_GAMEINFO_PLAYREC_20261122.md).

## 1. The alternate schedule is not a valid static encounter list

JP 80030B68 initializes object simulation and uses signed D_800ABF9C at 80030B7C. Zero branch sets D_800AC244 (section cursor) to 80079C54 and D_800ABE54 (environment cursor) to 8008A274. Nonzero branch sets those cursors to 80079C78 / 8008A2BC. Both reset section index and environment mode. This is separate from gameinfo mission bank selection. Pass23 found only direct JAL to mode setter 80030838 at 800224EC, delay slot a0=0, no aligned literal pointer to setter in scanned image. Do not assume alternate mode reachable in retail.

Nonzero section table in both regions:
| Absolute tick | JP primary pointer | JP secondary pointer | EU primary pointer | EU secondary pointer |
|---:|---|---|---|---|
|0|800AB968|800AB5F8|800AC1AC|800ABE3C|
|6302|800AB968|800AB5F8|800AC1AC|800ABE3C|
|FFFF|0|0|0|0|

Both secondary targets start with FFFF sentinel. The primary target is exactly config-table entry 50's target and begins with words 00000090,019A0098 in BOTH regions. Under observed primary schedule format, this means tick144, gate0, descriptor pointer 019A0098, outside mapped executable RAM (and ordinary 2MB PSX physical RAM). The second word actually is config58's two halfwords, not a valid descriptor reference. No FFFF list termination before that invalid record. At tick144 or current/previous eligibility, if count>=0 and primary allocation succeeds, scheduler would pass that invalid descriptor to 80030FF8 (initial signed halfword read at 8003100C). Do not run forced alternate mode as if valid data; exact abnormal result depends on hardware/emulator/runtime patching. At section6302 it repeats same malformed list. This is evidence of missing/aliased schedule data, not a secret complete alternate mission.

Scanned aligned words in both loaded image ranges: exact primary alias pointer appears three times (two section entries and one config50 entry); config58 pointer once (config table); secondary sentinel pointer 460 times (including descriptor script pointers). A LUI 800B plus same-register immediate scan over JP 80022000..80070000 identified no direct writes into 800AB5E0..800AB99F. Not a whole-program indirect-store proof; do not claim no runtime patch possible. EU identical first words and pointer topology prove not a regional extraction-offset accident.

## 2. Five tightly packed short records

Config table JP 80089D3C / EU 8008A554. Five distinct pointer targets spaced exactly four bytes apart:
| Config | JP | EU | type | second halfword |
|---|---|---|---|---|
|50|800AB968|800AC1AC|90|0|
|58|800AB96C|800AC1B0|98|19A|
|66|800AB970|800AC1B4|1D|7B|
|65|800AB974|800AC1B8|19|61|
|64|800AB978|800AC1BC|19|60|

These are short/overlapping views rather than independently laid out full configurations. Exact four-byte spacing establishes that neighboring logical entries cannot all be disjoint conventional full configs. It does not prove source declaration type or length for final record, nor that every short entry is unused. Constructor types19/1D deliberately rebind config pointer (pass15), so legitimate use of this pattern is already known. Type90 has real dispatch handler 80031628: phase0 sets up a two-halfword result state, reads first stream word as time limit and advances stream pointer; phase1 tests result state and mission mode/time, sets D_800AC2BC=-1 (80031708) and may call 80034E0C(1); type clears at signed section tick >=limit (80031758). This is a distinct controller, not same as type98, and does not make alternate primary pointer into a valid encounter list.

## 3. Type98 authored events are inert in original dispatch

All six config58 entries in mode-zero secondary section1 are at absolute ticks 8073 (1),8257 (1),8476 (4); relative3464,3648,3867. Descriptor first halfword zero required by 800312E4; config ID from descriptor+2 =58. 80031338 creates secondary object from config pointer:
- copy cfg first halfword to type at 80031388; config +0A into +2C, cfg+14+2*effective_count into +2E. cfg58 +0A reads neighboring short cfg65 second halfword (97); sampled +14..+20 values for counts0..6 are [0,0,0,0,29477,0,29253] and include unrelated adjacent storage. Do not infer meaningful durability.
- copy world XYZ, three fixed-point trig pairs via 80030454, set stream pointers +54/+58/+5C to same descriptor+18.
- no render, attack or scoring call in initializer; it sets collision request +28=-1, which is distinct from normal primary +28=1. Do not assert zero possible interaction anywhere before dispatch without full hit/input sequencing.

256/256 dispatch entries normalize exactly across regions by EU code displacement -398. Slot98 = JP 80030D4C / EU 800309B4, exact semantics JR RA with delay-slot SH zero,0(a0). On normal dispatch it clears the object's type and frees slot; no type98 controller body. 80030CC8 walks 124 slots by stride172 after scheduler in 80030BEC, therefore successfully allocated type98 object is cleared during ordinary same driver pass (assuming no intervening mutation), regardless of its incidental copied config fields. No proof of a hidden model or active enemy. Six entries are preserved authored placeholders, not six confirmed enemies. Excluding just these six, earlier 857 total schedule records reduce to851 other entries, NOT a count of actual damaging enemies or valid runtime spawns.

## 4. Pool capacity qualification

JP object base 8016B014, stride AC. Allocator 800315AC scans forward until exclusive end address, free type=0, sets object+A8=100 and +30=-1. Three bounds chosen by wrappers:
| JP bound | Prefix slots | Wrapper(s) |
|---|---:|---|
|8016E1CC|74|80031530,8003155C|
|8016F344|100|800314E0,80031508 (primary scheduler)|
|80170364|124|80031490,800314B8 (secondary and composite children)|

These are nested prefix limits, not three disjoint pools or reserved fixed partitions. 80031580 starts at pool base, forwarding caller bound; 80031508/314B8 can start from supplied pointer (including that slot). Dispatcher visits all124. The 74/100/124 limits imply potential headroom for higher-priority effects or composite allocation, but actual policy needs caller census. Do not conflate 74 authored fighter events with 74-slot prefix. Same driver call may allocate many objects before dispatch, so inert type98 slots can temporarily occupy capacity even if immediately cleared.

## 5. Regional evidence

All 256 table pointers match after normalizing -398. Five short-record pointer targets relocate +844, all ten halfwords match. Nonzero section pointer identity and invalid first primary words match. Structural compare masks J/JAL targets and LUI/ADDIU/memory immediates, does not establish full binary equivalence:
| JP half-open range | Words | Exact | Shape |
|---|---:|---:|---:|
|80030B68..80030BEC|33|21|33|
|80030CC8..80030D54|35|32|35|
|80030DBC..80030EA4|58|40|58|
|8003126C..80031468|127|113|127|
|80031468..800315EC|97|80|97|
|80031628..8003176C|81|70|81|
|Total|431|356|431|

No source changes, binary publication, build/runtime claims. Earlier docs' open questions can now be classified: static nonzero schedule alias is invalid, type98 dispatch is confirmed inert, retail reachability/runtime patching still unproven. Preserve actual authored placeholder entries in faithful reconstruction.

## Next

TMD/TIM archive loader and resource resolution (80024760/80024910 et al), then systemic matching-decompilation plan using independent leaf routines and both build oracles. Actual disc STR/TMD analysis separately when execution becomes available; do not assert parser correctness against uninspected assets.

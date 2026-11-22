# G3 object controller census and composite-object candidates

R1 pass 19, 2026-11-22. Input research head 338b4c7d. Original immutable EXE blobs JP 7b5ad2b5035634abd6873c86c90f486f6a99dffd / EU e9cfc4ee2bb3a4b474567d371037cfcd6c56cbb7, SHA-1 independently verified pass 12/15. Static word inspection; not a fresh matching build or runtime trace. No raw assets published.

Extends [dispatch](G3_RETAIL_DISPATCH_TABLES_20261122.md), [mission inventory](G3_MISSION_INVENTORY_20261122.md), [proximity and shared health](G3_PROXIMITY_HEALTH_20261122.md).

## 1. Authored configuration/time census

Rewalked JP four mode-zero schedule lists with 1000-entry limits and FFFF terminators; same 857 entries. Config IDs differ from runtime types. Counts and absolute min/max tick, not live object count:

| Config | Type | Initial config+2 | Entries | Absolute tick range | Schedule |
|---|---|---|---:|---|---|
| 00 | 60 | 50 | 324 | 512–4272 | primary |
| 01 | 60 | 52 | 18 | 1016–4355 | primary |
| 04 | 50 | 54 | 34 | 389–720 | primary |
| 10 | 20 | 70 | 6 | 2352–2384 | primary |
| 20 | 68 | 180 | 28 | 5313–5729 | primary |
| 21 | 60 | B0 | 84 | 4897–6881 | primary |
| 22 | 60 | B1 | 175 | 7057–9201 | primary |
| 26 | 68 | 180 | 12 | 6209–6721 | primary |
| 41 | 70 | 21 | 5 | 1336 | secondary |
| 42 | 80 | D9 | 1 | 3552 | secondary |
| 43 | 78 | 0 | 1 | 1000 | secondary |
| 44 | 79 | 90 | 13 | 2315–2704 | primary |
| 48 | 89 | 1C0 | 1 | 8489 | secondary |
| 49 | 88 | 0 | 4 | 8017–8487 | secondary |
| 4A | 81 | DB | 37 | 5905–6844 | secondary |
| 4B | 81 | F0 | 14 | 6177–6679 | secondary |
| 4F | 88 | 0 | 1 | 8480 | secondary |
| 50 | 90 | 0 | 1 | 1874 | secondary |
| 51 | 71 | 22 | 5 | 1875 | secondary |
| 52 | 70 | 21 | 2 | 1875 | secondary |
| 58 | 98 | 19A | 6 | 8073–8476 | secondary |
| 64 | 19 | 60 | 11 | 1216–1252 | primary |
| 66 | 1D | 7B | 74 | 5105–5185 | primary |

Initial config+2 is not universally a model ID; 19/1D are constructor families. 98 resolves to default clear slot, possibly mutable aliased config; do not call it a valid active controller. Prior regional schedule verification stands; only JP schedule rewalked here.

## 2. All 29 nondefault dispatch entries: positive behavioural signatures

Entry windows scanned from each entry until first linear JR RA or 0x250 bytes, whichever first. Direct JAL and SH observations followed selectively through helpers. Lack of a listed call is not proof it is absent; indirect phase handlers and later control-flow blocks need full CFG. Count column is authored initial type only.

| Type | JP entry | Authored | Classification / concrete lead |
|---|---|---:|---|
| 01 | 80030D5C | 0 | render 80031C5C |
| 02 | 80030D7C | 0 | render 80031CDC |
| 03 | 80030D9C | 0 | render 80031C9C |
| 07 | 80030D54 | 0 | no-op |
| 12 | 80038434 | 0 | hit, distance, proximity, death effects |
| 13 | 8003DDC0 | 0 | hit, speed/heading update, proximity, death |
| 14 | 8003E060 | 0 | hit, speed/heading update, proximity, alternate render |
| 18 | 8003442C | 0 | distance, simpler proximity wrapper 800352A0 |
| 19 | 8003416C | 11 | constructor shares 8003427C with 1D |
| 1C | 800385F4 | 0 | active fighter after type1D constructor, pass15 |
| 1D | 800341E8 | 74 | constructor, pass15 |
| 20 | 80037280 | 6 | motion init, hit/proximity, five phase-helper calls |
| 28 | 8003822C | 0 | effect/spawn lead 80037F44, RNG, render |
| 29 | 80037FB4 | 0 | effect/spawn lead 80037F44, render, type writes |
| 30 | 80037D0C | 0 | wrapper of 31 |
| 31 | 80037D58 | 0 | death/secondary effect, pass10 |
| 38 | 8003DB0C | 0 | fragments, pass10 |
| 50 | 8003098C | 34 | hit, squared distance and proximity, score/audio-like helper |
| 60 | 80033E44 | 601 | dual-clock script and movement, passes11–14 |
| 68 | 80038A9C | 40 | dual-clock second family, passes11–14 |
| 70 | 80036810 | 7 | phase helper dispatch |
| 71 | 80036E14 | 5 | phase helper dispatch |
| 78 | 8003176C | 1 | hit updates, allocator, RNG |
| 79 | 80039104 | 13 | transforms and allocation via 80031490, two child type writes |
| 80 | 8003C414 | 1 | composite parent and children, decoded below |
| 81 | 80039CC4 | 51 | transform and allocation via 80031490; full CFG pending |
| 88 | 8003A5D4 | 5 | composite group, hit aggregation, proximity damage |
| 89 | 8003ADB8 | 1 | composite parent and children, global end-state flag |
| 90 | 80031628 | 1 | diagnostic/80034E0C lead, command reader pending |

Among 29 nondefault slots 14 have authored initial type counts; one additional authored type 98 maps to default. Zero authored count does not imply unused; 1C/31/38 are proven internal transitions/effects.

## 3. Type 80: large composite controller, Doldva candidate

Config 42 at JP 80088D64, authored once at 3552 before atmospheric switch 4608, config+2 D9. Dispatch uses signed-normalized phase +6, unsigned <=12; table JP 80020ECC. Phases -6,-5,-4,-3,-2,-1,0,1,2,3,4,5,6 map to 8003D370,8003CD04,8003CD44,8003D320,8003D1E8,8003CE58,8003C534,8003C868,8003C888,8003C934,8003CC58,8003CCA4,8003C868. 13 slots, 12 distinct handlers.

Phase zero 8003C534:
- saves initial world position in +48/+4C/+50; loads resource from config+2, initializes +86 to 450, reads first halfword from +5C to +92 and advances pointer.
- allocate children with 800314B8; shared 8003C72C copies type/config, world pose and packed orientation terms from parent, sets child+64=parent pointer, +26=0.
- two children phases -4/-5; next table JP 8008AC28, four 2-halfword records until first-halfword -1 -> four phase -1 children; parent +8C count increments on this group.
- next table JP 8008AC3C, 29 four-halfword records until -1 -> 29 phase -2 children. Fields map to children +88,+8A,+52,+8E, with collision request 0, +2C=50, durability +2E=0, resource +30=0 at init. Do not call all 29 independently destructible at this point.
- full success requires 35 child allocations (36 total objects including parent), calls 8003C7B0 and increments parent phase. Failure clears parent type; cleanup of partly constructed group is not assumed. Child handlers -5 and -4 verify parent type matches their own and clear themselves on mismatched parent.
- 800314B8 calls forward-scan allocator 800315AC with upper bound 80170364 and supplied starting pointer (includes starting slot in search); actual allocation depends on pool occupancy.
- 8003C7B0 computes displaced world pose from saved position and orientation-derived direction scaled by +86. Phase2 8003C888 steps +86 downward by 20 with sign-crossing clamp and advances phase. Child -4 indexes parent phase and can change parent phase at animation threshold. It derives child resource ID from configured base + animation byte, and uses parent's orientation term. Concrete parent-child coupling.

Architecture and authored timing support Doldva hypothesis; exact visual identity, rotating reactor axis and victory condition await further tracing/assets.

## 4. Type 89: late composite controller, Cannon Seed candidate

Config 48 JP 80088EB4, +2=1C0, authored once at 8489. Phase dispatch JP 80020E50 uses signed-normalized phase+4, <=6. Phases -4..2 -> 8003BF7C,8003B7E8,8003B63C,8003B8FC,8003AE98,8003AFE8,8003B8D0.

Constructor 8003AE98 walks table JP 8008ABE0 (five halfword entries, -1 terminator), allocates five children in phase -1, +64=parent pointer, shares type/config, stores table value at +88, parent count +84 increments. On exhaustion or sentinel invokes 8003AF88, which sets phase1 and initializes +86/+88=8000, +8C from config+C4 and four accumulators.

8003AFE8 uses global D_800AC01C, reads +5C stream halfword timestamp-like value divided by two, calls decoder 8003B2FC and advances pointer on success. Two separate +92/+94 and +96/+98 accumulators produce discrete calls to 8003B53C and 8003B6B4 at 256-unit crossings. Uses child count to select config-dependent target +8C and steps toward it. Need full decoder and child hit/parent-count writer next.

When parent child count +84 is zero and signed D_800AC01C positive, 8003B028 calls 8003B868: sets D_800AC144=-1, calls 80034E0C(3), increments D_800AC08C, calls 8003BF1C, advances phase and renders. Phase2 8003B8D0 tests +90; nonzero stores -1 to D_800ABDDC and clears parent type. Same global is read by 80041D28 in late mission phase dispatcher, which only advances when it is nonzero. Note separate writer 80041C4C initializes it to 1; not a unique victory flag, nor proof of exact victory condition. This connects composite lifecycle to main sequence, a stronger lead than mere timing.

## 5. Type 88: repeated composite group and direct damage caller

Configs 49/4F, 5 secondary spawns 8017–8487, base damage 40/50. Five phase slots (-2..2); jump table JP 80020E24 -> 8003A918,8003A8E0,8003A634,8003A80C,8003A850.
- phase0 consumes +5C halfword to object+6A threshold, allocates first child phase -2; then walks JP 8008AADC nine 3-halfword records (signed XYZ offsets) and allocates up to nine phase -1 children. Child +64 parent, +84 linked-list next pointer. Ten child allocations on full success; linked list null termination. Actual allocation not guaranteed. Parent phase1 and animation +88 from next stream halfword <<8.
- phase -1 child's hit mask +2A ORed into parent+8E at 8003A908; calls 8003466C, parent 8003A98C consumes accumulated hits via 80034C60 and updates progress counter +90 after table threshold. Parent phase2 compares +90 against cfg+2C; success calls 8003AAF8, which awards via 80045128 and produces effects.
- phase2 checks global section-relative tick D_800ABFA4 versus parent+6A. At/after threshold calls 8003A938 (cleanup lead). Before threshold calls 80034748, if unsigned squared distance <40000 (radius 200 world units if ordinary Euclidean calculation) calls 8003ABFC at 8003A8C0.
- 8003ABFC performs shared group cleanup 8003A960, calls 80045054(cfg+22), then **direct shared health damage** 80035348 at 8003AC2C, closing pass18 third-caller question. Unlike earlier angular wrappers, this local path uses a squared-distance threshold with no local cone test. Base 40/50 times row multiplier; initialized row 1 -> 160/200 raw damage (1.6/2% starting health). Exact group visual identity/cleanup semantics pending.
- possible hazard/destructible defense group from timing, not a verified name.

## 6. Regional checks

Original code shape mask excludes J/JAL target bits and immediate fields of LUI/ADDIU/memory ops; not binary equivalence. EU displacement -398 hex. JP windows (exclusive end), exact/shape/words:

| JP range | Exact | Shape | Words |
|---|---:|---:|---:|
| 8003C414..8003C530 |45|71|71|
| 8003C534..8003C7B0 |145|159|159|
| 8003ADB8..8003AE98 |38|56|56|
| 8003AE98..8003AFE8 |78|84|84|
| 8003A5D4..8003A818 |138|145|145|
| 8003A98C..8003AA48 |45|47|47|
| 8003ABFC..8003AC34 |10|14|14|
| Total |499|576|576|

Child table data at JP 8008AC28 (4x2), 8008AC3C (29x4), 8008ABE0 (5x1), 8008AADC (9x3) compared against EU +818: 156 data halfwords plus four first-halfword -1 sentinels agree. (8+116+5+27=156.) No raw table content published. SDK attribution review and matching split required before C landing.

## Next

Trace type80 phase3 and negative child handlers to recover actual damage/rotation and parent completion, then type89 decoder 8003B2FC and child-count writers. Follow D_800ABDDC, D_800AC144, and D_800AC08C to victory/defeat state sequence. Do not identify bosses definitively before visual/runtime evidence. CHD STR extraction remains separate and blocked as of prior turn.

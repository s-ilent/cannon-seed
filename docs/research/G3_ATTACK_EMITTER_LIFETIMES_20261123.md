# G3 type-0x18 lifetime provenance: attack cases 1 versus 5/6

**R1 pass 35 — 2026-11-23.** Continues [pass 34](G3_ATTACK_VARIANTS_20261123.md) at branch head `e66ad9f1d92ee5c58be153c1c65928d276522473`. Static JP/EU generated ASM and data-table read; no CHD/retail build, runtime trace, asset/visual identification, source conversion or gameplay edit. Candidate roles are described from write/read/collision behaviour, not asserted on-screen names.

## Result: the type-0x18 anomaly is **producer-specific**, not universal

The previously found `cfg 0x4A / type 0x81 → case 1 → cfg 0x68 / type 0x18` constructs a child whose `+0x6C` starts at **0** in the immutable initial data, so its type-0x18 handler expires it on its first invocation. **But** attack cases **5** and **6** also produce type-0x18 objects and use a **different lifetime source**: `cfg+0x28=300`, not `cfg+0xBE`. Those successfully initialized children pass the first signed-negative lifetime gate and can execute motion, render and vehicle-contact logic. Both game regions agree in all checked config fields and instruction shapes.

| Parent config(s) / type | Authored mode-zero count (pass 19) | Dispatcher method | Child index → runtime type | Constructor and +0x6C source | Initial halfword / first update |
| --- | ---: | ---: | --- | --- | --- |
| `0x4A / 0x81` | 37 | 1 | `0x68 → 0x18` | `80035AA0`, `lhu(child_cfg+0xBE)` | `0 → 0xFFFF` **expires** |
| `0x41, 0x52 / 0x70` | 5+2=7 | 5 | `0x60 → 0x18` | `800355E8 → 80035688`, `lhu(child_cfg+0x28)` | `300 → 299` **survives** |
| `0x51 / 0x71` | 5 | 6 | `0x61 → 0x18` | `8003564C → 80035688`, `lhu(child_cfg+0x28)` | `300 → 299` **survives** |

The table of authored counts is **not** a measured spawn-count: the shared dispatcher checks `parent+0x32` and attack cooldown `+0x68`, producer allocators may exhaust, and methods 5/6 apply an angular gate before establishing the child type. Config `0x40` is an additional type-0x71 method-6 record selecting `0x61` but has **no** initial authored mode-zero entry in pass 19; do not treat it as an observed parent. The type-0x70 and type-0x71 controller families have direct calls to `func_80035418` (JP `80036D0C` and `80036FD4` respectively), so these are live-code producer edges, not merely dormant configuration fields.

## 1. Exact constructor split

**Dispatcher `func_80035418`, JP `80035418..80035528`:**

- Method 1: `80035494 jal func_80035AA0`. It allocates via `func_80031530`, tests `func_800365FC`, populates child config/type via `func_80036704`, then executes `80035B08 lhu v0,0xBE(a1)` and `80035B10 sh v0,0x6C(child)`. For cfg `0x68` this reads JP `80089D3A` / EU `8008A552`, both zero in the initial data (the last halfword before `D_80089D3C` / `D_8008A554`). No intervening direct child lifetime rewrite occurs in the returned constructor path. This **does not prove** that no unrelated or computed runtime writer could affect the memory before first dispatch.
- Method 5: `800354C4 jal func_800355E8`; allocate and call `func_80035688`. Only if initialization succeeds, add `0x28` (40) to the **second position word `child+0x8`** at `80035620..8003562C`.
- Method 6: `800354D4 jal func_8003564C`; allocate and call the **same** `func_80035688`, without the method-5 displacement.
- Shared cases 5/6 constructor: `80035688..800357C8` first obtains a child through `func_800366BC` (resolves `parent_cfg+0x2C` via `D_80089D3C`, copies pointer/type/resource). After two `func_80036658` angular checks and pose setup, `8003574C` receives the selected **child config** pointer, `80035750 lhu v0,0x28(s0)` reads **300** for cfg `0x60` and `0x61`, and `80035760 sh v0,0x6C(s1)` stores it. The same method reads `cfg+0x22` into child `+0x36` at `8003578C..80035794`. It sets `+0x26=0`; method 5 adds the extra second-coordinate offset after success.
- Type `0x18` handler `func_8003442C`: `80034440..80034454` decrements unsigned-loaded `child+0x6C`, writes the low halfword, sign-tests it and branches to `8003458C` to clear `child+0` on negative. Thus **0 expires at first update**, while 300 becomes 299 and reaches `func_800345A4` (motion helper), movement/proximity checks, and potentially shared-health wrapper `func_800352A0`. If unimpeded and updated once per frame, the signed countdown first reaches a negative value on the **301st update** (300→299 on first, 0 on 300th, −1 on 301st); actual frame rate/phase cadence not inferred.

The two live-capable child variants have substantially different proximity/damage parameters:

| Data field | child cfg 0x60 / type 0x18 | child cfg 0x61 / type 0x18 | Consumer |
| --- | ---: | ---: | --- |
| `cfg+0x02` | `0x14` | `0x17` | child resource selector |
| `cfg+0x12` | **20** | **10** | conditional base damage in shared health path |
| `cfg+0x22` | **280** | **100** | copied to child `+0x36` and squared in handler proximity comparison |
| `cfg+0x28` | **300** | **300** | constructor lifetime `child+0x6C` |
| `cfg+0xBE` (initial data) | 0 | 0 | **not used** by methods 5/6 |

The handler also tests global position/view bounds before the near-distance branch. Being within the squared threshold invokes the angular-health wrapper, which still has additional angular and mission-state gates; **not all proximities necessarily damage**. The type-0x18 handler contains no per-gunner hit-processing call or `D_800AC08C` credited-terminal increment. The object's on-screen model identity has not been recovered.

## 2. Why the shorter case-1 templates are especially misleading

All six type-0x18 entries in the 128-item JP config-pointer table correspond to short, **0x30-byte** config records, and have `cfg+0x28=300`. Their *initial* `cfg+0xBE` values come from unrelated following data or the pointer table, rather than within the short record:

| Type-0x18 config ID | JP data pointer | Initial `cfg+0xBE` | Subtract 1, then signed test |
| --- | --- | ---: | --- |
| `0x60` | `80089C1C` | `0x0000` | expire |
| `0x61` | `80089C4C` | `0x0000` | expire |
| `0x68` | `80089C7C` | `0x0000` | expire |
| `0x70` | `80089CAC` | `0x8008` | expire |
| `0x71` | `80089CDC` | `0x8008` | expire |
| `0x72` | `80089D0C` | `0x8008` | expire |

The EU table `D_8008A554` agrees **6/6** in these lifetime values and **6/6** for `cfg+0x28=300`. This table is **a hypothetical method-1 lifetime read**, *not* a claim that each config actually goes through method 1. Specifically, modes 5/6 use the valid `+0x28` field. Other parent configs with method 1 also select cfg `0x70` and `0x71`, but source call-site/phase reachability must be demonstrated separately before counting them as emitted attacks.

The six short records also underscore an important layout discipline: **the same numeric field offset cannot be interpreted as a universal config-member name** when different attack constructors read differently sized/overlapping data. Case 1 accessing `+0xBE` after a 0x30-byte cfg is statically real but not evidence of a meaningful authored lifespan there.

## 3. Bounded write/path audit

- Scanned the primary tracked JP game-code ASM spans `func_8002A2DC.s` and `func_80033C44.s` for direct numeric `+0x6C` stores; these spans have many writers associated with *different object types*, plus the relevant `80035B10`, `80035760`, and handler decrement `8003444C`. The **closed** method-1 and method-5/6 constructor paths do not subsequently overwrite their respective child lifetimes before return.
- The isolated type-0x18 handler does not invoke a shared script decoder or generic lifetime initializer *before* its negative-lifetime test. The object-system per-slot dispatcher chooses its handler from the active type word; it is not evidence of an implicit common `+0x6C` rewrite.
- Direct named references to `D_80089D3C` in those assembly spans are table selections (including `func_800366BC` and `func_80036704`), not direct stores to the zero backing word at `80089D38`. This is **not an exhaustive proof against runtime-computed addressing, broader memory copies or memory corruption**; a write watchpoint would settle the physical value during play.
- No gameplay source changes were made. These are static *initial-state reachability* conclusions, not a witnessed emulator trace.

## 4. JP/EU paired-source corroboration

ASM: `asm/g3_jp/nonmatchings/func_80033C44.s`, `asm/g3_eu/nonmatchings/func_800338AC.s`, data: JP `data_80080048.data.s`, EU `data_8008002C.data.s`. For the bounded windows below `EU VA = JP VA − 0x398`. Instruction shapes keep opcode/register fields and mask immediate operands and J/JAL targets; disassembly comment bytes were byte-reversed to machine-word order before matching.

| JP window (exclusive end) | EU start | Words | Exact words | Matching shapes |
| --- | --- | ---: | ---: | ---: |
| `800355E8..8003564C` method 5 | `80035250` | 25 | 22 | 25 |
| `8003564C..80035688` method 6 | `800352B4` | 15 | 12 | 15 |
| `80035688..800357C8` shared initializer | `800352F0` | 80 | 71 | 80 |
| `800366BC..80036704` config resolver | `80036324` | 18 | 17 | 18 |
| `80036658..800366BC` angular selector | `800362C0` | 25 | 22 | 25 |
| `8003442C..800345A4` type-0x18 handler | `80034094` | 94 | 85 | 94 |
| `80036D0C..80036D24` type-0x70 call site | `80036974` | 6 | 4 | 6 |
| `80036FB4..80036FDC` type-0x71 call site | `80036C1C` | 10 | 8 | 10 |
| **Total** | | **273** | **241** | **273** |

This is cross-region **tracked source-ASM structure comparison**, not full-image retail matching or a gameplay witness.

## 5. Next bounded question and runtime test

**Pass 36:** establish the *actual activation conditions* for type-0x70/0x71 attack methods 5/6, including when their `+0x32` gate is enabled and cooldown becomes negative, then correlate the two resources `0x14/0x17` to model/visual evidence if lawful private assets or a runtime capture are available. Keep **orphan type-0x13 cfg 0x74** as a separate alternate-mode/script-selection question, not `unused` by fiat. The method-1 cfg `0x4A→0x68` zero-lifetime case merits an emulator watchpoint at child `+0x0/+0x60/+0x6C` and the nearby JP `80089D38` backing word to distinguish apparent intentional no-op, mutated runtime data and a dormant/disabled producer. A static source read alone cannot settle developer intent. Results-counter caption/art is still open.

# G3 internally spawned attack objects: types 0x12, 0x13 and 0x14

**R1 pass 33 — 2026-11-23.** Continues [pass 32 counter exclusions](G3_TERMINAL_COUNTER_EXCLUSIONS_20261123.md), [pass 31 credited terminal events](G3_GUNNER_PARTICIPATION_TERMINAL_COUNTER_20261123.md), [pass 19 authored census](G3_OBJECT_CENSUS_COMPOSITES_20261122.md), [pass 18 contact damage](G3_PROXIMITY_HEALTH_20261122.md), [pass 21 SPARKBIT](G3_SPARKBIT_FINAL_OBJECTIVE_20261122.md) and [pass 10 projected requests](G3_PROJECTED_SPRITE_REQUESTS_20261123.md) where available. Branch base: `research/g3-terminal-counter-exclusions-20261123` at `566ecf290815ab656f13dd3cf8f05797b3f8c84d`.

**Scope:** Static read of tracked JP/EU generated assembly and data table text, including `asm/g3_jp/nonmatchings/func_80033C44.s`, `asm/g3_eu/nonmatchings/func_800338AC.s`, `asm/g3_jp/nonmatchings/data/data_80080048.data.s`, `asm/g3_eu/nonmatchings/data/data_8008002C.data.s`, and JP/EU `data_80020000` jump tables. No newly verified private EXE hash, runtime observation, render/asset extraction, game-code edit, or matching build. Terminology *spawned attack/hazard object* is derived from construction, per-weapon attack dispatcher and collision/damage functions; no recovered asset or on-screen name is asserted.

## 1. Result: the omitted 'enemy deaths' are attacks spawned by other enemies

The zero initial-spawn counts for types **0x12, 0x13, 0x14** in the four mode-zero authored encounter lists (pass 19) are expected: these are **secondary, dynamically allocated attack objects**, selected by the generating controller's configuration. Their own destruction is not recorded as an ordinary credited terminal event, even though they have a player-hit processing path and death effects.

| Parent runtime type / authored config(s) | Primary authored entries (pass 19) | Config `+0x2A` attack case | Config `+0x2C` child index | Child config → runtime type | Actual JP dispatch/case |
| --- | ---: | ---: | ---: | --- | --- |
| 0x68, cfg 0x20/0x26 | 28 + 12 | **7** | **0x79** | 0x79 → **0x12** | `800354E4` → `func_800362C4` |
| 0x81, cfg 0x4B | 14 | **8** | **0x76** | 0x76 → **0x13** | `800354F4` → `func_80035E80` |
| 0x89 SPARKBIT, cfg 0x48 | 1 | **9** | **0x75** | 0x75 → **0x14** | `80035504` → `func_800360F4` |
| 0x81, cfg 0x4A (**comparison**) | 37 | **1** | **0x68** | 0x68 → **0x18** | `80035494` → `func_80035AA0` |

This shows **different attack products even within type 0x81**: cfg 0x4A generates a type-0x18 companion, whereas cfg 0x4B generates type 0x13. Neither config type nor the *child index* should be confused with runtime dispatcher ID. A fourth attack-object path, type 0x18, is an independent corroboration of the common mechanism; its full behaviour is not re-audited here.

### Common selection and execution path

`func_80035418` is the shared emission dispatcher called from:
- Type 0x68 path `80038D38` (`func_80038A9C` controller family).
- Type 0x81 at `8003A1D8` and `8003A3AC` (phase-conditional callbacks).
- Type 0x89 SPARKBIT's **phase -1 child** at `8003BB9C`, not necessarily its parent object directly. The five SPARKBIT children share their parent's cfg 0x48 (pass 21); these calls are **attack emissions**, distinct from the five destructible children themselves.

It tests object `+0x32` as signed nonzero and decrements unsigned 16-bit `+0x68` cooldown. When the updated halfword is signed-negative, it loads `s16(cfg+0x2A)`, requires unsigned index `<=10` and jumps through the 11-entry `jtbl_80020D5C`. Cases 7, 8, 9 are the three named producers above. All three call `func_80031530` for an available object. The corresponding cases call `func_800355C8` to reset/advance the attack cooldown (also on allocation failure). This is a conditional producer: table entries **prove available paths**, not an observed number of emissions per encounter.

`func_80036704(parent,child)` at `80036704..80036768`, shared by cases 7 and 8, reads `s16(*(parent+0x60)+0x2C)` as a config-table index, resolves `D_80089D3C[index]`, and sets `child+0x60` to the config pointer, `child+0` to its runtime type, `child+0x30` to config+2, `child+0x28=1` (collision request), `child+0x2A=0`, `child+0x2E=cfg+0x14` (durability) and `child+0x2C=cfg+0xA`. Case 9 uses sibling `func_80036210` at `80036210..800362C4`, which independently resolves the same `cfg+0x2C` index and initializes further rotation fields. **Type is populated from the table data, never from an immediate `sh 0x12/0x13/0x14` in these paths.**

Attack case 7 `func_800362C4` additionally aligns its projectile position/velocity and coordinate-space flag relative to the parent/camera and uses trig/RNG; case 8 `func_80035E80` copies parent world position, motion/animation parameters and lifetime; case 9 `func_800360F4` copies pose and initializes pitch/yaw/time fields for its child. Details in the original ASM; preserving exact fixed-point arithmetic matters for C translation.

## 2. Concrete JP/EU config evidence

JP pointer table: **`D_80089D3C`**, EU: **`D_8008A554`** (table relocation **+0x818**, not gameplay code -0x398). The following low-halfword config fields were read from both regional tracked data objects; all type, attack method, child index, resource, and damage observations agree for the nine explicitly paired configurations. Pointer addresses themselves relocate by +0x818 here.

| Config ID | JP config record | EU config record | Runtime type | Resource cfg+2 | Attack method cfg+2A | Child cfg+2C | Base vehicle damage cfg+12 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 0x20 | `800887B4` | `80088FCC` | 0x68 | 0x180 | 7 | 0x79 | 10 |
| 0x26 | `8008886C` | `80089084` | 0x68 | 0x180 | 7 | 0x79 | 10 |
| 0x4A | `800893CC` | `80089BE4` | 0x81 | 0xDB | 1 | 0x68 | 30 |
| 0x4B | `800895B0` | `80089DC8` | 0x81 | 0xF0 | 8 | 0x76 | 10 |
| 0x48 | `80088EB4` | `800896CC` | 0x89 | 0x1C0 | 9 | 0x75 | 10 |
| 0x79 | `80089BF4` | `8008A40C` | **0x12** | 0x182 | 20 | 0x14 | **30** |
| 0x76 | `80089830` | `8008A048` | **0x13** | 0x1B0 | 0 | 0 | **30** |
| 0x75 | `800898EC` | `8008A104` | **0x14** | 0 | 0 | 0 | **40** |
| 0x74 (unresolved) | `80089774` | `80089F8C` | **0x13** | 0x1B4 | 0 | 0 | **30** |

**Unresolved fourth template, cfg 0x74:** This is a *second* type-0x13 variant with resource 0x1B4 rather than 0x1B0, distinct animation/lifetime constants, and a valid config pointer-table entry. It does **not** appear as a directly authored mode-zero spawn or as `+0x2C` child index of the active case 7/8/9 parent configs examined. Neither “unused in all game modes” nor an alternate attack source is established. Only a narrower negative xref is justified.

Do not infer that cfg 0x79's own `cfg+0x2A=20` creates another child: type 0x12's active handler is **not** the shared `func_80035418` dispatcher. The parent/attack-method interpretation is conditional on the call to that dispatcher.

## 3. Attack handling, vehicle damage and counter exclusion

| Runtime type | Active handler JP | Gameplay mechanics | Vehicle contact | Results counter |
| --- | --- | --- | --- | --- |
| **0x12** | `80038434` | Processes `obj+0x2A` gunner-hit mask via `func_80034C60`; fatal signed `obj+0x2E<0` changes to type 0x31 at `80038598`. Moves relative to authored/parent orientation, submits geometry render via `func_80031C5C` or `func_80031CDC` by `+0x26` | `800385C0` calls angular proximity + shared-health wrapper `func_800351D0` on a distance/boundary path | **No** |
| **0x13** | `8003DDC0` | Processes hit/durability, signed `+0x6C` lifespan, position/heading and render; fatal path retypes to 0x31 `8003DFB4`; expiry clears type `8003DFC8` | `8003DF9C` invokes `func_800351D0` on its near-vehicle path | **No** |
| **0x14** | `8003E060` | Processes hits and lifespan; fatal path retypes to 0x31 `8003E204`; lifespan expiry clears type `8003E218`. **Different render backend:** `8003E1D8` calls type-4 projected sprite producer `func_80031EC0` or `8003E1E8` calls type-5 producer `func_80031F40` according to `+0x26` | `8003E16C` invokes `func_800351D0` within range threshold | **No** |

The proximity wrapper `func_800351D0` only calls direct shared-vehicle-health mutation `func_80035348` on qualifying angular hit and subject to mission-state gating (pass 18). It draws its *base damage* from spawned object's `cfg+0x12`. The values **30, 30, 40** are verified config base values, **not** an assertion of always-applied damage, shot damage, UI percentages or on-screen health loss. In the previously observed initial multiplier row 1 (×4), potential per-qualified-contact health loss is 120 for types 0x12/0x13 and 160 for type 0x14 out of initial 10,000, before other gates/overrides; this is conditional arithmetic, not runtime measurement.

These objects can be destroyed by the player's gunner-hit path, produce the type-0x31 effect, or make contact with the shared vehicle health, but **none** increments `D_800AC08C` on any inspected terminal path (pass 32). This is consistent with *weapons/attacks belonging to counted enemies* being excluded from the credited target/objective tally, while the relevant type-0x68 and type-0x81 parent deaths are count-eligible (pass 31) and the type-0x89 final parent credits its success once.

**Inference boundary:** The origin is confirmed statically by table lookup and call chains. Model/visual classification (missile, laser, beam, shield, etc.), actual emission frequency and probability, and exact results-screen caption still require a runtime trace or private asset inspection.

## 4. JP/EU static comparison

The ten windows below are aligned by **EU code VA = JP code VA - 0x398**. Instruction *shape* compares opcode/register fields, masking I-type immediate and jump targets; full word identity is stricter. This is a paired source-structure comparison, **not** independently verified retail EXE match.

| JP source window (exclusive end) | EU start | Instructions | Identical words | Shape |
| --- | --- | ---: | ---: | ---: |
| `80035418..80035528` common attack dispatcher | `80035080` | 68 | 48 | 68 |
| `800362C4..8003631C` case 7 | `80035F2C` | 22 | 20 | 22 |
| `80035E80..80035F14` case 8 | `80035AE8` | 37 | 32 | 37 |
| `800360F4..80036188` case 9 | `80035D5C` | 37 | 33 | 37 |
| `80036210..80036274` case 9 config select | `80035E78` | 25 | 24 | 25 |
| `80036704..80036768` common config select | `8003636C` | 25 | 24 | 25 |
| `800385C0..800385E0` type 0x12 contact | `80038228` | 8 | 7 | 8 |
| `8003DF9C..8003DFC8` type 0x13 contact | `8003DC04` | 11 | 7 | 11 |
| `8003E16C..8003E188` type 0x14 contact | `8003DDD4` | 7 | 5 | 7 |
| `8003E1C0..8003E218` type 0x14 sprite path | `8003DE28` | 22 | 15 | 22 |
| **Total** | | **262** | **215** | **262** |

Region-specific data table prefixes from tracked data-ASM were separately decoded at identical child-config IDs. No byte-hash or live game validation was undertaken.

## 5. Next bounded pass

1. **Pass 34:** resolve the gameplay/visual intent of the alternative `0x74` type-0x13 configuration and the type-0x18 attack variant (0x81 cfg 0x4A → child 0x68), tracing any secondary mode or script-indexed origin and exact live counters. An unused-looking template should be called *unresolved*, not dead.
2. **Best runtime probe:** watch writes to live `D_800AC08C` and `D_800AC09C` (separate damage-event counter), emitted object `+0` and `+0x60`, and the attack dispatcher `80035418` with parent config IDs. Confirm a 0x12/13/14 object can damage the vehicle or be shot without credit and a type 0x68/81 parent awards a credit only upon its own fatal state.
3. **UI label:** extract the results-number art/caption or capture a post-mission rank screen before concluding the statistic's literal in-game name. The evidence now supports exclusion of spawned enemy *weapons* rather than exclusion of confirmed regular enemies.

# G3 communication buffer: the per-frame scene descriptor pool schema

**R1 pass 6 — 2026-11-22.** Bounded *source-only* JP/EU static analysis. Builds
directly on [the TMD geometry atlas](G3_TMD_GEOMETRY_TO_OT_20261122.md) §6
(the exact next question it banked: the 0x18 descriptor → 0x6C record
construction, the producers, and the per-frame transform state). **No new
live retail SHA-1 comparison, no runtime capture, no C conversion, no
rename, no coverage change.**

## Executive result

`D_80166360` is the game's **Communication Buffer** — the name is literal
source evidence, from the error string
`"Over flow Communication Buffer !\n"` printed when its record count
overflows. It is an **immediate-mode, per-frame pool of 0x18-byte scene
request records**: reset each frame, bump-allocated by multiple game
producer systems, then consumed once by the scene partition
(`func_8002DFD8`) which converts accepted requests into either a
0x6C linked-TMD world record (`D_80138DB4`) or a 0x7C projected-sprite
record (`D_8013F9B4`), both rebuilt **every frame**. There is no
persistent per-record transform update on the render arrays; animation
and transform state live in the **producer-side** object records.

```text
frame loop func_80042C90 region
  └─ func_800444B0  (gate D_800AB26C == 0)
       count D_800AC014 = 0; cursor D_800AC2CC = &D_80166360   # pool reset

producers (one 0x18 record per request, bump-allocated):
  laser/hit system (mylaser.c)   integrator func_8003ECB0 → emitter func_8003ED7C
  object spawn API               func_80031CBC / func_80031CDC → func_80031CFC → emitters
                                 func_80031D44 / func_80031FA8 / func_8003207C
  allocator stub                 func_8003EE70: cursor += 0x18; count += 1

consumer (same frame):
  func_8002DFD8(&count3d, &countProjectedSprite)
    ├─ 15-way type dispatch (jtbl_80020AF0) on desc[0] & 0xF
    ├─ per-type constructor → shared builders func_8002E4B8 (world) / func_8002E770 (projected)
    └─ consumption rule (func_8002E0FC, corrected):
         constructor returned 0                → record dropped
         returned nonzero, type==0xE or !(t&4) → world 0x6C record (s1 += 0x6C, s5++)
         returned nonzero, t&4 set, t!=0xE     → projected 0x7C record (s2 += 0x7C, s4++)
  └─ draw stages func_8002E9F4 / func_8002EC7C (previous atlas)
```

## 1. Pool lifecycle (verified)

| Element | Address (JP) | Evidence |
| --- | --- | --- |
| Reset: count=0, cursor=&D_80166360 | `func_800444B0` (`0x800444B0..0x800444DC`) | `sh zero, D_800AC014`; `sw &D_80166360, D_800AC2CC`; gated `D_800AB26C == 0`; called from `func_80042C90` at `0x80042CA8` (frame-loop region) |
| Bump allocator | `func_8003EE70` (`0x8003EE70..0x8003EEA0`) | cursor `D_800AC2CC += 0x18`; count `D_800AC014 += 1`; **0x18 stride proven by the allocator itself** |
| Capacity gate (record count) | `func_80031CFC` et al. | `slti v0, count, 0x2F4` (756) → else `printf("Over flow Communication Buffer !\n")` (JP string `D_80020B84`; EU twin `D_80020B64` at `0x80020B64`) |
| Secondary byte budget | `func_80031D44` head | `D_800AC16C < 0x21C0` (8640); cleared at `0x800405A4`/`0x80044764`/`0x8004490C`, updated in frame submission `func_80022AFC.s` at `0x80022F20` |
| Enable gate | spawn wrappers | `D_800AC29C != 0` required; set/cleared around `0x80042A7C..0x80042AE8` and `0x800440D8..0x800440EC` (mode/frame control region) |

## 2. Producer systems (verified writers of the buffer)

Only two files reference `D_80166360`/`D_800AC014` tree-wide:
`asm/g3_jp/nonmatchings/func_8002A2DC.s` (consumer + object spawn API) and
`asm/g3_jp/nonmatchings/func_80033C44.s` (laser/hit system + reset).

### 2a. Laser/hit system — source file evidence `mylaser.c`

The 5-entry dispatch `jtbl_80020F8C` sits between the retained strings
`"Invalid lsr_mode=%d (plaser() in mylaser.c)"` (`D_80020F5C`) and
`"Invalid hit_req in hit_check routine\n"` (`D_80020FA0`) — literal
file/function names for this producer family.

- **Integrator `func_8003ECB0`** (`0x8003ECB0..0x8003ED7C`): laser record
  `a3` integrates motion — velocity halfwords `+0x44/+0x46/+0x48/+0x4A`
  scaled through decay table `D_800AB9B4` indexed by `2 - [+0x26]`
  (lifetime-position dependent), position words `+0x3C/+0x3E/+0x40`
  updated, lifetime `+0x26` decremented; at zero the record is killed
  (`sh zero, 0x0(a3)`), while alive it branches to the emitter.
- **Emitter `func_8003ED7C`** (`0x8003ED7C..0x8003EE6C`): writes a
  **type-0xE** descriptor at the cursor: `+0x0 = 0xE`, `+0x2 = lhu +0x28(a3)`
  (effect id), `+0x4/+0x8/+0xC = lh +0x3C/+0x3E/+0x40(a3)` (position triple
  as words), `+0x10 = lhu +0x10(a3)`, `+0x12 = lhu +0x12(a3)`,
  `+0x14 = 0`, `+0x16 = 4`. Then dispatch on `hit_req` (`+0x80`):
  case 0 and `hit_req > 4` → allocator `func_8003EE70`; cases 1–4 rewrite
  `+0x2 += 0x210 / 0x220 / 0x230 / 0x240` respectively (impact-class id
  offsets) via the shared tail `func_8003EE6C`.

### 2b. Object spawn API

Typed spawn helpers `func_80031CBC(a1 = 0x21)` and `func_80031CDC(a1 = 1)`
call the gate `func_80031CFC` (enable gate + 0x2F4 capacity + printf),
which branches into the emitters. Each emitter writes `+0x0 = type`,
`+0x2 = lhu 0x30(a0)` (object id), `+0x4/+0x8/+0xC = lw 0x4/0x8/0xC(a0)`
(position triple) plus further fields from the object record. All three
emitters carry the same `0x2F4` gate (`0x80031D20`, `0x80031F84`,
`0x80032058`).

## 3. The 15-way type dispatch and the corrected consumption rule

`func_8002DFD8` walks the buffer `D_800AC014` times in 0x18 strides;
`type = lhu 0x0(s0)`; nibble `> 0xE` is rejected (advance only).
`jtbl_80020AF0` (15 entries, verified contents):

| Type | Handler | Target array |
| --- | --- | --- |
| 0x0 | `func_8002E184` (world cursor `s1`) | world |
| 0x1 | `func_8002E20C` (world) | world |
| 0x2, 0x3 | `func_8002E270` (world) | world |
| 0x4 | `func_8002E640` (projected cursor `s2`) | projected |
| 0x5 | `func_8002E6A8` (projected) | projected |
| 0x6 | *no constructor* (shared advance) | dropped |
| 0x7 | `func_8002E6EC` (projected) | projected |
| 0x8–0xD | *no constructor* (shared advance) | dropped |
| 0xE | `func_8002E318` (world) | world |

**Consumption rule (`func_8002E0FC`) — corrected this pass:** the
constructors return **-1 on success, 0 on failure** (both shared builders
return 0 when the resource lookup yields -1). On nonzero return:
`type == 0xE` **or** `!(type & 4)` → `func_8002E12C` (`s1 += 0x6C`,
`s5++`, world); only `type != 0xE && (type & 4)` → `s2 += 0x7C`, `s4++`
(projected). On zero return the record is dropped and neither cursor
advances. This makes the arm→array mapping fully coherent (types 4/5/7 all
have bit 2 set; the TMD-linked laser 0xE lands in the world array, matching
its constructor's `GsLinkObject4` work).

## 4. The 0x6C world record layout (verified writes)

From the shared builder `func_8002E4B8` (and the type-0xE path
`func_8002E318`/`func_8002E3AC`/`func_8002E3E4`/`func_8002E400`):

| Offset | Write | Meaning (confidence) |
| --- | --- | --- |
| `+0x00` | type word (copied from descriptor for types 0–3); `3` for the 0xE path | record type/state; **high** for the write, medium for semantics |
| `+0x04` | `GsLinkObject4(model + 0xC, rec + 0x4, 0)` | linked DOBJ-style object header; **high** |
| `+0x08` | `sw` embedded-coordinate pointer (`rec + 0x14`) | coordinate back-pointer; **high** |
| `+0x14` | `GsInitCoordinate2` target (first word zeroed on the 0xE path) | embedded `GsCoordinate2`; **high** |
| `+0x2C/+0x30/+0x34` | `func_80047DA0` outputs, `×2` / negated `×2` | rotation-derived transform words; **medium** |
| `+0x64` | resource lookup result `s0` | model resource pointer; **high** |
| `+0x68` | second lookup output word | per-record parameter; **medium** |

Resource lookup `func_8002F368`: walks the model table `D_800ABBE4`
(first word = count, `-1` sentinel), matches the requested id, emits two
output words through `a1`. The id for the laser path is `desc[+0x2] + 8`
(`a0 = lhu 0x2(s2) + 8`); the impact classes raise it by
`0x210/0x220/0x230/0x240` before the constructor runs. Rotation inputs
are rounded `>> 4` with the `+0xF` negative-rounding idiom
(4096th → 256th rotation units), with an `0x8000` flag on one field.

## 5. Architecture conclusion: immediate-mode scene, no persistent record updates

`D_80138DB4` / `D_8013F9B4` are referenced **only** inside
`func_8002A2DC.s` tree-wide: the partition writes them and the two draw
stages read them. Nothing else updates record transforms after
construction, and the pool itself is reset each frame. The render record
arrays are therefore **frame-local staging**, fully rebuilt from the
Communication Buffer; all animation/transform lifetime lives in the
producer-side records (laser records with velocity/decay/lifetime at
`+0x26..+0x4A`, spawn object records at `+0x4..+0x30`). Any future
semantic-C campaign should target the **producer** structs and the
spawn/integrate functions — converting the record builders without the
producers would strand their meaning.

## 6. EU correspondence

EU `asm/g3_eu/nonmatchings/func_8002A2CC.s` (the JP scene file's twin):
same 6C/7C partition strides (`0x8002DEF0`/`0x8002DEFC`), same `< 0x2F4`
capacity gates ×3 (`0x80031988`, `0x80031BEC`, `0x80031CC0`), same
overflow string at EU `D_80020B64`. The EU draw stages
(`func_8002E7C4`/`func_8002EA4C`) and the pre-existing EU C dispatcher
remain as documented in the TMD atlas; no EU-only deviation in the buffer
schema was found in the windows inspected.

## 7. Next specific R1 question

Recover the **producer-side object record schema**: the laser record
(`+0x0` active/type word, `+0x10/+0x12`, `+0x26` lifetime, `+0x28` effect
id, `+0x3C..+0x40` position, `+0x44..+0x4A` velocity, `+0x80` hit_req) and
the spawn-API object record (`+0x4..+0xC` position, `+0x30` id) — their
pool bases, sizes, and the callers that create/destroy them. Second: the
`D_800ABBE4` model table builder (`func_8002DE3C`/`GsMapModelingData`
resource pass) — which CD assets (`\\DRAGOON\\TMD.DAT;1`) fill it and how
resource ids map to TMD entries. Do not convert any builder until a
producer-side landing decision is made.

**Ownership guard (carried):** EU `src/func_80052038.c` stays untouched;
SDK attribution of the dispatchers remains a separate lane.

# G3 producer-side records: the D_8016B014 object pool, the D_80163944 laser pool, and the D_800ABBE4 model table

**R1 pass 7 — 2026-11-22.** Bounded *source-only* JP static analysis with EU
pool-base cross-checks. Builds directly on [the communication buffer
schema](G3_COMM_BUFFER_SCHEMA_20261122.md) §7 (the exact question it banked:
the producer-side record schemas, their pool bases/sizes/creators, and the
`D_800ABBE4` model table + `\DRAGOON\TMD.DAT;1` mapping). **No new live retail
SHA-1 comparison, no runtime capture, no C conversion, no rename, no coverage
change.**

## Executive result

The two producer systems behind the Communication Buffer are backed by two
**fixed-capacity pools in the g3_jp data/BSS arena** whose shapes are proven by
their own allocators and per-frame walks:

- **Object pool `D_8016B014`** — **124 slots × 0xAC bytes** (`D_8016B014` +
  124·0xAC = `D_80170364`, the pool end bound the allocator itself receives).
  Two scan bounds share the one arena: the definition-spawner scans all 124
  slots; a live handler's spawner scans only the first **74**
  (`D_8016E1CC` = base + 74·0xAC exactly). Per frame every slot dispatches on
  its `+0x0` type word through a **256-entry table `D_8008A2F4`**; the default
  entry kills the slot (`sh zero, 0x0(a0)`).
- **Laser pool `D_80163944`** — **32 slots × 0x84 bytes**, hand-rolled
  allocator `func_8003F7E4`, per-frame walk `func_8003E784` dispatching on the
  `lsr_mode` field `+0x24` (0/1/2 handlers, else the literal
  `"Invalid lsr_mode=%d (plaser() in mylaser.c)"` printf).

The `D_800ABBE4` model-table machinery is fully decoded **and carries this
pass's negative result**: the pointer setter, both mapper walks, and the whole
`\DRAGOON\TMD.DAT;1` loader family have **no static caller anywhere in the
extracted g3_jp image** (exhaustive address search), while `D_800ABBE4`
image-initializes to 0 and the proven consumer chain dereferences it — the
runtime population path is outside the currently walked surfaces.

```text
per-frame object system entry func_80030BEC
  ├─ func_80030C7C   (frame-globals save area D_800ABE3C..)
  ├─ func_80030DBC   (descriptor prep; reads D_800AC244 ptr + D_800AC16C budget)
  └─ func_80030CC8   (walk D_8016B014, 124 × 0xAC)
       ├─ v0 = lh +0x0(rec);  handler = D_8008A2F4[type];  jalr(rec)
       ├─ func_80031468 (per-object RNG step: D_800AC50C = 5·x + 1)
       └─ (stride 0xAC, count 0x7C)

per-frame laser system (laser file, func_80042A78 @0x80042AB0)
  └─ func_8003E784
       ├─ clear obj+0x2A flag over 124 slots (0x7C × 0xAC from D_8016B014)
       └─ walk D_80163944, 32 × 0x84 → func_8003E814 lsr_mode dispatch
            0 → func_8003E8A4 (aim)   1 → func_8003EAB4
            2 → func_8003ECB0 (integrate + emit desc, pass 6)
            else printf "Invalid lsr_mode=%d (plaser() in mylaser.c)"
```

## 1. The object pool (verified)

| Element | Address (JP) | Evidence |
| --- | --- | --- |
| Pool base | `D_8016B014` | every allocator/walk site loads `%hi/%lo(D_8016B014)` |
| Slot stride | **0xAC** | walk `addiu s0, 0xAC`; allocator `addiu a0, 0xAC` |
| Full capacity | **124** (`D_80170364` end bound) | `0x80170364 − 0x8016B014 = 0x5350 = 124·0xAC` exactly; `func_80031490` passes it as the scan end |
| Handler-spawn sub-arena | **74** slots (`D_8016E1CC` bound) | `func_80031530` → `func_80031580(D_8016E1CC)`; `0x8016E1CC − 0x8016B014 = 0x31B8 = 74·0xAC` exactly |
| Allocator scan | `func_800315AC(base, end)` | loop: `lh 0x0(a0)` == 0 → take; else `a0 += 0xAC` while `a0 < end`; exhausted → 0 |
| On allocate | `func_800315D4` | `sh 0x64, 0xA8(a0)` (**+0xA8 = 100**); `sh -1, 0x30(a0)` (**+0x30 = −1**) |
| Kill (default handler) | `func_80030D4C` | `jr; sh zero, 0x0(a0)` — clears the type word; the slot is reusable next scan |
| Per-object RNG step | `func_80031468` | `D_800AC50C = 5·D_800AC50C + 1` (sh back); handlers then draw `andi 0x3`/`andi 0x7` (e.g. `func_80031920`) — a scramble stream, not a counter |

**Type dispatch `D_8008A2F4`** (256 `.word` entries, `data_80080048.data.s`
14360–14617; index = `lh +0x0(rec)`). Verified live handlers (all others =
`func_80030D4C` kill):

| Type(s) | Handler | Note |
| --- | --- | --- |
| 0x1 / 0x2 / 0x3 | `func_80030D5C` / `func_80030D7C` / `func_80030D9C` → `func_80031C5C`/`func_80031CDC`/`func_80031C9C` | the Communication-Buffer spawn wrappers (types 0/1/3 descriptors via `func_80031CFC`; `func_80031C7C` emits type 0x23) |
| 0x7 | `func_80030D54` | no-op (survives the walk) |
| 0x13 / 0x14 / 0x15 | `func_80038434` / `func_8003DDC0` / `func_8003E060` | gameplay handlers (bodies not opened this pass) |
| 0x19 / 0x1A | `func_8003442C` / `func_8003416C` | gameplay handlers |
| 0x1D / 0x1E | `func_800385F4` / `func_800341E8` | gameplay handlers |
| 0x21 | `func_80037280` | gameplay handler |
| 0x29 / 0x2A | `func_8003822C` / `0x80037FB4` | gameplay handlers |
| 0x30 / 0x31 | `func_80037D0C` / `func_80037D58` | gameplay handlers |
| 0x36 | `func_8003DB0C` | gameplay handler |
| 0x47 | `func_8003098C` | gameplay handler |

## 2. Creation paths into the object pool (verified)

1. **Spawn-from-definition** — `func_800312E4(src)` allocates one slot via
   `func_800314B8` (full 124 bound), then `func_80031338(src, new)` fills it:
   `+0x60 = D_80089D3C[src+0x2]` (definition pointer table in ROM,
   `data_80080048.data.s` 13839–13903; most entries point at the default
   definition `D_8008849C`, specific ones at `D_800884C0`/`D_80088574`/
   `D_800886F0`/`D_800887B4`/`D_80088924`/`D_800889D8`/`D_8008886C`);
   `+0x0 = lh(def+0x0)` (**the type comes from the definition, not the
   source**); `+0x28 = −1`, `+0x24 = 0`, `+0x2A = 0`, `+0x32 = 1`, `+0x68 = 0`,
   `+0x26 = 0`; `+0x2C = lhu(def+0xA)`; `+0x2E = lhu(def+0x14 + src_sub·2)`
   (definition tail = halfword array indexed by the source's `+0x2`);
   `+0x4..+0xC = src position`; `+0x10/+0x12/+0x14 = src halfwords` each also
   converted by `func_80030454` into `+0x18/+0x1C/+0x20`; `+0x5C/+0x54/+0x58 =
   src+0x18` (script cursor word to three fields).
2. **Clone-chain builder** — `func_8003A5D4`/`func_8003A66C` (laser file): a
   source record with a **script cursor** (`+0x5C` read cursor, `+0x6A` last
   token) clones itself: `func_800314B8` per clone, `+0x84(prev) = clone` (the
   child link), clone type = source type, `+0x24 = −2` then `−1` for chain
   members, `+0x26 = 0`, position/halfword fields copied `+0x4..+0x20`, `+0x30
   = 0`, `+0x28 = 0`; the clone stream reads halfwords from a `−1`-sentinel
   table at `D_8008AADC` (`lh 0x0(s1)`; `beq v1, −1 → stop`).
3. **Live-handler spawner** — `func_80031920` branch family: gate
   `D_800ABFA4 < lh(rec+0x6C)` (a rate/count gate), reload timer `+0x70`
   (decrement, refilled from the RNG draws), allocate via `func_80031530`
   (**74-slot bound**), set `+0x0 = 0x31` (**type 0x31**), `+0x26 = 0`, then
   `func_80037E0C(parent, new)` initializes from the parent.

## 3. Object record field map (verified writes; handlers may overload)

| Offset | Field | Evidence |
| --- | --- | --- |
| `+0x00` | **type word** — dispatch key, kill = 0 | walk `lh 0x0`; kill handler; spawners |
| `+0x02` | definition sub-index (drives `def+0x14[sub·2]`) | `func_80031338` |
| `+0x04..+0x0C` | position words ×3 → descriptor `+0x4..+0xC` | emitters `func_80031D44`/`func_80031DC8` |
| `+0x10/+0x12/+0x14` | rotation/param halfwords → descriptor `+0x10/+0x12/+0x14` | emitters |
| `+0x18/+0x1C/+0x20` | converted forms of the above via `func_80030454` | `func_80031338` |
| `+0x24` | fire counter (mode-tag −1/−2 on clone chains) | `func_8003F6E8` increment; clone builder |
| `+0x26` | cleared at spawn | spawners |
| `+0x28` | −1 at def-spawn; cleared on clones | `func_80031338` |
| `+0x2A` | **per-frame laser-contact flag** — cleared every frame by the laser walk before dispatch | `func_8003E784` head |
| `+0x2C/+0x2E` | definition-sourced words (`def+0xA`, `def+0x14+sub·2`) | `func_80031338` |
| `+0x30` | **model resource id** (−1 = unset); `== 0x1C0` forces descriptor id `0x1C2`, else copied to descriptor `+0x2` | emitters |
| `+0x32` | 1 at def-spawn | `func_80031338` |
| `+0x54/+0x58/+0x5C` | script/data cursor word ×3 (clone chains read `+0x5C` live; fire logic reads `+0x5C` as fire-mode) | `func_80031338`, `func_8003F6E8`, clone builder |
| `+0x60` | definition pointer (`D_80089D3C[...]`) | `func_80031338` |
| `+0x64` | **laser back-link** — the slot's live laser record | laser allocator `func_8003F7E4` (`sw a1, 0x64(a0)`) |
| `+0x68` | 0 at def-spawn | `func_80031338` |
| `+0x6C/+0x70` | rate gate + reload timer (handler pair) | `func_80031920` |
| `+0x84` | **child/next object pointer** (clone chains) | `func_8003A66C` |
| `+0x88` | **hit_req source word** — copied to the laser record `+0x80` at creation | laser allocator |
| `+0xA8` | 100 on allocation (init constant) | `func_800315D4` |

## 4. The laser pool and its lifecycle (verified)

| Element | Address (JP) | Evidence |
| --- | --- | --- |
| Pool base | `D_80163944` | allocator/walk/memset sites |
| Capacity | **32 × 0x84** | allocator `slti a2, 0x20` + stride `0x84`; clear loop `memset(rec, 0, 0x84)` × 0x20 |
| Allocator | `func_8003F7E4` | first slot with `lh +0x0 == 0`; returns 0 if none |
| On allocate | `func_8003F7FC` | `+0x0 = 8` (**active word 8**); `+0x24 = 0` (→ mode 0 aim next frame); `+0x28 = lhu(owner+0x0)` (owner type); `+0x2C = owner`; `+0x80 = lhu(owner+0x88)` (hit_req); **`owner+0x64 = laser ptr`** back-link |
| Fire gate | `func_8003F79C` | `D_800AB26C == 0` required (the comm-buffer reset gate); sound `func_80029FC0(0xB)`; sets `0x74C($gp) = 1` on success |
| Fire sites | 4 × `jal func_8003F79C` at `0x8003F650/0x8003F724/0x8003F750/0x8003F784` | fire-control dispatch on the owner record's weapon type (`0xC0`/`0xC8`/`0xCC` arms; `func_8003F6E8` = repeat-fire counter logic on `+0x2C`/`+0x5C`) |
| Per-frame walk | `func_8003E784` from `func_80042A78` (`0x80042AB0`) | clears `obj+0x2A` ×124, then 32-laser dispatch |
| Mode dispatch | `func_8003E814` | `lh v1, 0x24(rec)`; 0 → aim `func_8003E8A4`; 1 → `func_8003EAB4`; 2 → integrator `func_8003ECB0`; else `printf("Invalid lsr_mode=%d (plaser() in mylaser.c)")` |
| Mode-0 aim | `func_8003E8A4` | `+0x26 = 2` (**lifetime init**); start position `+0x36/+0x38/+0x3A = lhu(owner+0x52/0x54/0x56)`; delta vs `owner+0x6/+0xA/+0xE`; direction via `func_80032598`; rotations via `func_80030454` |
| Kill-all | `func_8003E734` | memset × 0x20; called from `func_800447A8` (`0x80044868`) and `func_80044950` (`0x800449F4`) — the same reset family that clears the byte budget (pass 6) |
| Kill (lifetime 0) | integrator tail | `sh zero, 0x0(a3)` (pass 6) |

**Laser record field map** (verified): `+0x0` active/type word (8 on spawn, 0
on kill); `+0x10/+0x12` copied to descriptor `+0x10/+0x12`; `+0x24` lsr_mode
(0/1/2); `+0x26` lifetime (init 2, decremented by the integrator; decay table
`D_800AB9B4` index `2 − [+0x26]`); `+0x28` effect id (owner type at spawn) →
descriptor `+0x2`; `+0x2C` owner pointer (mode-0 aim reads it); `+0x36..+0x3A`
aim/start position halfwords (owner +0x52..+0x56); `+0x3C..+0x40` current
position words (integrator-updated) → descriptor `+0x4/+0x8/+0xC`;
`+0x44..+0x4A` velocity halfwords (decay-scaled by the integrator);
`+0x5C/+0x5E` hit-check state pair (`func_8003F854`); `+0x80` hit_req
(`+0x210/+0x220/+0x230/+0x240` impact-class id offsets, pass 6).

## 5. The D_800ABBE4 model table: schema fully decoded

- **Setter stub** (`0x8002DE2C`): `sw a0, D_800ABBE4` — stores the table
  pointer. `D_800ABBE4` sits in `data_80080048.data.s` image-initialized
  **`0x00000000`** (line 79435).
- **Mapper walk** (`0x8002DE3C..`): reads `table[0]`; `−1` = empty; per
  **0x14-byte row**: source index at `row+0x4`; if ≥ 0 → resolver
  `func_80024910(idx)`; nonzero result → `row+0x10 = resolved` and
  `GsMapModelingData(resolved + 4)` (the Psy-Q TMD mapper); zero/negative
  source → `row+0x10 = −1`; advance until `row+0x0 == −1`.
- **Row layout** (cross-checked against the consumer lookup
  `func_8002F368`): `+0x0` = **id** (the lookup key, `−1` sentinel), `+0x4` =
  source index, `+0x8` = output word 1 (→ `a1`), `+0xC` = output word 2 (→
  `a2`), `+0x10` = resolved TMD pointer (mapper-filled). Pass 6's consumers
  (`func_8002E318` type-0xE path at `0x8002E38C`, world builder
  `func_8002E4B8` at `0x8002E508`) call exactly this lookup.
- **Second table** `D_800ABBEC` (setter stub `0x8002DECC`): same shape with
  **0x34-byte rows** (lookup `func_8002F3D4`: id at `+0x0`, output from
  `+0xC`, return cursor `+0x10`); the `func_80024AD8` site resolves through
  the same directory then builds a TIM/texture path (`func_8002F9B0` +
  `GetTPage`).
- **Resolver** `func_80024910(idx)`: `base = 0x54($gp)`; word = `base[idx·4]`;
  return `base + round4(word)` (the `+3`/`sra`/`sll` idiom aligns down to 4,
  up for negatives) — **the loaded TMD.DAT image plus an offset-directory
  entry**.
- **Loader family** (`func_80022AFC.s`): `func_800247C8(name)`: `CdSearchFile`
  → sector math (`sra 11` = /2048) → `malloc(0x60000)` (384 KB) → `0x54($gp)`
  → `memset(buf, 0, 0x66000)` (417,792 — observed as written, larger than the
  allocation; recorded as-is) → read loop; sibling retry wrappers
  `func_80024760`/`func_80024954` loop `0xFFFFFFF` times then
  `printf(D_800200F4 / D_80020128)`; unload = `func_80024738` (`free(0x54($gp))`).
  The filename strings live in `data_80020000.data.s`:
  `\DRAGOON\TIM.DAT;1` (`D_80020000`), **`\DRAGOON\TMD.DAT;1`** (`D_80020014`),
  `\DRAGOON\%s%d.DAT;1` (`D_80020098`).

## 6. Negative result: the table setter and the TMD.DAT loaders are unreached (this pass)

Exhaustive search over the extracted g3_jp surfaces (`asm/g3_jp/`
nonmatchings code + data, `src/`, curated symbols):

- The **only** write to `D_800ABBE4` in the image is the setter stub at
  `0x8002DE30`.
- **No branch, no `jal`/`j`, and no jump-table `.word` targets**
  `0x8002DE2C`/`0x8002DE3C`/`0x8002DF4C` from anywhere; the block sits between
  `func_8002DDFC` (ends `jr ra` at `0x8002DE24`) and the next walked function,
  internally branch-consistent (e.g. `0x8002DF3C → func_8002DF4C`) but with no
  external entry.
- The loader family (`func_80024738`/`func_80024760`/`func_800247C8`/
  `func_8002488C`/`func_80024954`/`func_800249BC`) likewise shows **no
  callers** in code or data tables.
- The resolver `func_80024910` **is** called — at `0x8002DE7C`/`0x8002DF68`
  (inside the unreached mapper block) and `0x80024AE0`/`0x800250B8` (the
  texture sites) — so the resource-resolution machinery is real code, and its
  *callers above it* are what the walk does not surface.
- Yet the proven consumer chain dereferences `D_800ABBE4` every frame
  (`func_8002F368` loads it before any row read).

**Conclusion (evidence-qualified):** either a caller outside the currently
extracted/attributed g3_jp surfaces reaches the setter at runtime, or the
population happens through an indirect mechanism this pass has not proven
(function pointer built at runtime, or a path in a region the walk emits as
raw bytes). This is the note's open question — **not** resolved by guessing.

**Next specific check (concrete):** byte-level scan of the retail g3_jp
executable for `jal`/`j` encodings targeting `0x8002DE2C`
(`0x0C00B78B`/`0x0800B78B` word values and conditional-branch encodings), then
a PCSX-Redux watchpoint/trace on `0x8002DE2C` and `D_800ABBE4` per
`docs/RUNTIME.md` — the runtime recipe already in the tree.

## 7. EU correspondence (pool bases cross-checked)

| Element | JP | EU | Note |
| --- | --- | --- | --- |
| Object pool base / end | `D_8016B014` / `D_80170364` | `D_8016B138` / `D_80170488` | identical shape: 124 × 0xAC (`0x5350`); EU walk at `0x80030944` (stride/count verified) |
| Laser pool base | `D_80163944` | `D_80164270` | 32 × 0x84; EU memset twin `func_8003E3B8`, clear `slti 0x20` + stride `0x84` verified; EU walk dispatches the same `lsr_mode` set (string `D_80020F3C` at `0x8003E4EC`) |
| Laser/scene files | `func_80033C44.s` / `func_8002A2DC.s` | `func_800338AC.s` / `func_8002A2CC.s` | the producer systems are address-shifted siblings; no schema deviation found in the windows inspected |

## 8. Verified vs inferred summary

- **High confidence:** both pool shapes (base/stride/count/bounds, arithmetic
  exact), the allocators' on-alloc writes, the kill semantics, the type
  dispatch table contents, the fire gate `D_800AB26C` linkage, the laser
  creation bindings, the mode-0 aim field reads, the 0x14/0x34 model-table row
  layouts, the resolver offset-directory arithmetic, the loader family's CD
  calls and sizes.
- **Medium confidence:** gameplay semantics of the named fields (type word =
  "object kind", `+0xA8 = 100` as an energy/init constant, `+0x6C/+0x70` as
  rate/reload) — the writes/reads are verified, the gameplay words are
  interpretation.
- **Negative/blocked:** the `D_800ABBE4` runtime population path (§6).

## 9. Next specific R1 question

Open the four type-0x1x/0x2x/0x3x gameplay handler bodies
(`func_8003442C`/`func_8003416C`/`func_800385F4`/`func_800341E8`) to extend the
object field map into the `+0x34..+0x54` and `+0x6C..+0x84` handler-owned
regions, and pair that with the §6 population check (byte-level branch scan →
runtime trace). The pass-6 producer-field list (laser `+0x26/+0x28/
+0x3C..+0x40/+0x44..+0x4A/+0x80`; spawn `+0x4..+0xC/+0x30`) is hereby superseded
by the complete maps in §3/§4.

**Ownership guard (carried):** EU `src/func_80052038.c` stays untouched;
SDK attribution of the dispatchers remains a separate lane. No builder or
record is converted before a producer-side landing decision (WORK_QUEUE R1
gate).

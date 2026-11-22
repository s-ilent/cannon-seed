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

---

**R1 pass 8 — 2026-11-22 (same day, second bounded run).** The §9 question
answered in full: the §6 population check is **closed at byte level on both
twins**, and the four gameplay handler bodies are decoded, extending the
object field map into `+0x34..+0x54` and `+0x6C..+0x84` (plus mechanizing
`+0x30`). Method: every 32-bit word of the witnessed retail executables
(`baselines/g3_jp.bin` sha1 `994a680c…`, 143,872 words; `baselines/g3_eu.bin`
sha1 `39030a75…`, 144,384 words) was scanned for immediate-encoded references
to the unreached block; the handler bodies were read from
`asm/g3_jp/nonmatchings/func_80033C44.s` / `func_8002A2DC.s`. No C conversion,
no rename, no coverage change.

## 10. §6 closed at byte level: no static reference reaches the block

Scan script swept **all 143,872 (JP) / 144,384 (EU) words** of the retail
images (not just extracted rows) for every statically encodable reference
form. VA mapping `VA = 0x80020000 + off − 0x800` validated at the setter stub
itself (`0x8002DE2C`: `lui $at, 0x800B; sw $a0, 0xBBE4($at); jr ra; nop` —
words `3C01800B AC24BBE4 03E00008 00000000`).

**JP targets scanned:** `0x8002DE2C` (setter), `0x8002DE3C` (mapper walk 1),
`0x8002DECC` (second-table setter), `0x8002DF4C` (mapper walk 2), loader
family `0x80024738`/`0x80024760`/`0x800247C8`/`0x8002488C`/`0x80024954`/
`0x800249BC`; tables `0x800ABBE4`/`0x800ABBEC`.

1. **`jal`/`j` encodings** (`0x0Cxxxxxx`/`0x08xxxxxx`): **zero hits** for all
   ten functions across the whole image.
2. **Literal address words** (`.word`-style data references): **zero hits**
   for the ten function addresses and both table addresses — not even a
   data-side pointer to `D_800ABBE4` exists in the image.
3. **`lui` + `ori`/`addiu` materialization pairs** building any scanned
   address: **zero hits** outside the setter stubs themselves.
4. **Conditional branches** targeting the block window
   `[0x8002DE2C, 0x8002DFD8)`: **ten hits, every one with both source and
   target inside the block** (sources `0x8002DE60`–`0x8002DFAC`; targets the
   walk bodies `0x8002DEB4`–`0x8002DFB4`, including the two 0x14-row and
   0x34-row loop-backs `0x8002DEAC→0x8002DE6C` and `0x8002DFAC→0x8002DF3C`).
   The block is **branch-closed**: nothing enters it.

A wider first-pass window `[0x8002DE2C, 0x8002E100)` produced exactly one
additional branch — `0x8002E144 → 0x8002E040` — classified as the
**Communication Buffer consumer's own loop**: `func_8002E134` counts `s3`
against `lh(D_800AC014)` (the request count, pass 6) advancing `s0` by the
0x18-byte request stride, back into its own request-processing body
`func_8002E040`; its dispatch arms advance the record cursor by **0x7C** for
bit-4 requests (`addiu $s2, $s2, 0x7C` at `0x8002E120`), re-confirming pass
6's corrected consumption rule at the instruction level. Its span merely
abuts the unreached block; it does not enter it.

**EU corroboration:** the EU twin of the block was located and scanned
(`baselines/g3_eu.bin`). Setter stub **`0x8002DBFC`** =
`lui $at, %hi(D_800AC428); sw $a0, %lo(D_800AC428)($at); jr ra; nop` — the EU
model table is **`D_800AC428`** (JP `D_800ABBE4` twin, new bank); mapper walk
**`0x8002DC0C..0x8002DC84`** (0x14-row walk, −1 sentinel, resolver
`func_80024970` = JP `func_80024910` +0x60, `GsMapModelingData(resolved+4)`
at `0x8002DC68`); loader family = the JP six at +0x60
(`0x80024798`/`0x800247C0`/`0x80024828`/`0x800248EC`/`0x800249B4`/
`0x80024A1C`, confirmed by the `0x54($gp)` sites at `0x80024798`–
`0x800248E0`). Scan result over 144,384 words: **zero `jal`/`j`, zero
literal words, zero lui-pairs; four branch hits, all four with source AND
target inside the walk** (`0x8002DC30→0x8002DC84`, `0x8002DC44→0x8002DC5C`,
`0x8002DC54→0x8002DC64`, `0x8002DC7C→0x8002DC3C`).

**Conclusion (§6 resolved, evidence-maximal):** no statically encodable
reference — jump, branch, literal, or immediate materialization — reaches
the setter stubs, the mapper walks, or the loader family in **either** retail
image. Combined with §6's original finding (the only write to `D_800ABBE4`
is the stub store), the population path is now confined to
**runtime-computed control flow** (`jalr` through a register, or a pointer
built at run time) — forms that cannot appear as static encodings by
definition. The definitive check is the **PCSX-Redux watchpoint/trace on
`0x8002DE2C` / `D_800ABBE4` per `docs/RUNTIME.md`**, unchanged as the next
step; the static side of the question is closed.

## 11. The four gameplay handler bodies (types 0x18/0x19/0x1C/0x1D)

Dispatch rows verified in `data_80080048.data.s` (the 256-entry table
`D_8008A2F4`): `0x8008A354 → func_8003442C` (type **0x18**), `0x8008A358 →
func_8003416C` (**0x19**), `0x8008A364 → func_800385F4` (**0x1C**),
`0x8008A368 → func_800341E8` (**0x1D**); the flanking entries are the shared
default `func_80030D4C`.

**Shared machinery:**

- **`func_8003427C(obj)` — the definition-chain step** (called at entry by
  the 0x19 and 0x1D handlers): `func_800327F8` life-check first (via
  `func_80032A40` halfword sign test; non-negative → `func_80032838`); then
  the object's definition pointer `+0x60` is **replaced by
  `D_80089D3C[def+0x2]`** — the definition chain advances one step through
  the same pointer table pass 7's spawner uses — and the object's type word
  `+0x0` is **rewritten** from `newdef+0x0` (halfword). So the type word is
  *not* spawn-immutable: the chain walk retypes the object every step.
  `+0x30 = lhu(newdef+0x2)` (the resource selector, below), and the three
  angle fields `+0x10/+0x12/+0x14` are evaluated through **`func_80030454`
  — the quadrant-dispatched trig evaluator (LUT `D_8008D660`, `andi 0x3FFE`
  index mask)** — into `+0x18`/`+0x1C`/`+0x20`; `func_80032364` mixes the
  `+0x18`/`+0x1C` trig pair into three halfword outputs consumed by the
  per-`+0x26` velocity assembly.
- **`func_80034974(obj, out, out2)` — the space-dispatched coordinate
  extract:** `+0x26` selects 0 → word path (`+0x4/+0x8/+0xC` minus the
  camera triple `D_8016AC18/1C/20`, through `func_80032448`), 1/2 → halfword
  path (`lh +0x6/+0xA/+0xE`), else `printf(D_80020CD0)`. `func_80034748`
  dispatches the same selector for its distance metric (0 → squared word
  distance from the camera triple; 1/2 → squared halfword norms; else
  `printf(D_80020C8C)`).
- **`func_800352A0(obj)`** — the destruction-effect spawn (position extract
  via `func_80034EC0`, `D_800ABF9C`-selected constants `0x1A4F`/`0x16C1`
  with base `0x1555`, capped jitter, `func_80035348`).

**Type 0x18 — `func_8003442C`** (0x5C + fall-through cluster): countdown
`+0x6C` (lhu) −−, kill on negative; `func_800345A4` advances the travel
accumulator `+0x34` by `clamp(+0x44 − +0x34, ±lw(def+0x24))`; velocity
assembly `func_800345E8`: **`+0x3C = 2×(+0x36 × lh(+0x18))`**,
`mid = (2×(+0x36 × lh(+0x1A)))>>16`, **`+0x38 = 2×(mid × lh(+0x1C))`**,
**`+0x40 = 2×(mid × lh(+0x1E))`** — heading `+0x36` scaled by the halves of
the trig words (Q16 velocity: high half = integer part, low = fraction).
Then the integration twin: position `+0x4/+0x8/+0xC` += velocity>>16 (the
`+0x26==0` path sra's first, the `+0x26!=0` path integrates the full words —
per-type coordinate-space selection), `func_80034974` heading extract
`+0x4000`-biased; `(heading+0x4000) < (+0x36)²` → `func_800352A0` + kill;
`> 0xF423FF` → kill; else the **phase counter `+0x6E`**: `+= lhu(def+0x2C)`
wrapped against `lhu(def+0x2A)` (modulo), then **`+0x30 = lhu(def+0x2) +
(phase>>4)`** — the resource selector advances with the phase; finally spawn
`func_80031C5C(obj)` (`+0x26==0`) / `func_80031CDC(obj)` (else) — both are
`func_80031CFC(obj, flag)` with flag 0/1.

**Type 0x19 — `func_8003416C`** (0x54): chain step; live objects: `+0x6E = 0`,
`+0x28 = 0`, `+0x36 = lh(+0x46)`, `+0x6C = lhu(def+0x28)` (reload timer from
the new definition); **`+0xA4 = (lh(+0x46) + (lh(D_800ABF9C) ? 0x104 :
0x6E))²`** — the square, with `D_800ABF9C` selecting the addend.

**Type 0x1C — `func_800385F4`** (0x5C + cluster): if `+0x2A != 0`:
`func_80034C60(a1=def)` (indexes the `D_801474FC` table by `lh(D_800ABE5C)`,
stride `0x8C`); **`+0x30 = lhu(def+0x2 + 2×(+0x2A))`** — the laser-contact
halfword pass 6 banks selects a resource sub-table at `def+0x2`;
`lh(+0x2E) < 0` → **`func_80038968`: type word `+0x0 = 0x31` (the object
MORPHS to type 0x31)** + `func_80037E0C`/`func_80037D58`. If `+0x2A == 0`:
`+0x24` selects 0 → countdown arm `func_8003869C` (`+0x6C`−−, kill negative;
`+0x36 ≥ +0x46` state gate; transition path sets `+0x24 = 1` and **`+0x44 =
lw(def+0xB4)`**), 1 → **`func_80038734`: `+0x48 = D_8016AC18, +0x4C =
D_8016AC1C, +0x50 = D_8016AC20` — the camera position triple copied into the
object** (else a five-call update chain), then the integration twin
`func_800387BC` (same shape as 0x18's, relative-motion source triple
`D_8016AC38/3A/3C`, squared-radius gate `D_800ABF9C ? 0x10810 : 0x2F44`,
re-roll path `func_8003890C`: `+0x14 += lhu(def+0xBC)`, trig refresh, then
`func_800337B8`).

**Type 0x1D — `func_800341E8`** (0x84): chain step; inits from the new
definition: `+0x24 = 0`, `+0x28 = 1`, `+0x2A = 0`, `+0x6C = lhu(def+0xBE)`,
`+0x2E = lhu(def+0x14)`, `+0x34 = lw(+0x44)`, `+0x2C = lhu(def+0xA)`,
`+0x46 = lhu(def+0xB4)`, `+0x48 = +0x4C = +0x50 = 0`,
**`+0xA4 = (lh(+0x46) + 0x6E)²`**.

## 12. The object field map, extended (pass 8 regions in bold)

| Field | Meaning (verified writes/reads) | Owner |
| --- | --- | --- |
| `+0x0` | type word — **rewritten by the chain step and the 0x31 morph** | prologue / `func_80038968` |
| `+0x4/+0x8/+0xC` | position words, `+=` Q16 velocity>>16 per frame | 0x18/0x1C integration |
| `+0x10/+0x12/+0x14` | **angle inputs** (`func_80030454` operands; `+0x14 += lhu(def+0xBC)` on re-roll) | prologue / re-roll |
| `+0x18/+0x1C/+0x20` | **trig evaluations of the angles** (word-valued; halves feed the velocity assembly) | prologue / `func_80030454` |
| `+0x24` | **state selector** (0x1C: 0 countdown → 1 camera-anchor; init 0 for 0x1D) | 0x1C cluster |
| `+0x28` | contact flag (laser walk clears; **0x19 inits 0, 0x1D inits 1**) | both |
| `+0x2A` | **laser-contact index** — selects `def+0x2 + 2×(+0x2A)` resource sub-table; 0x1D inits 0 | 0x1C read |
| `+0x2C` | **0x1D init `lhu(def+0xA)`** | 0x1D |
| `+0x2E` | **0x1D init `lhu(def+0x14)`; 0x1C signed gate for the 0x31 morph** | 0x1D/0x1C |
| `+0x30` | resource selector — **mechanized**: chain step `lhu(newdef+0x2)`; 0x18 phase add `(phase>>4)`; 0x1C contact-indexed | prologue + handlers |
| `+0x34` | **travel accumulator** (0x18: chase `+0x44` clamped `±def+0x24`; 0x1D init `= +0x44`) | `func_800345A4` |
| `+0x38/+0x3C/+0x40` | **Q16 velocity words** (high = integer integrated, low = fraction; assembly arithmetic verbatim in §11) | `func_800345E8` |
| `+0x44` | **travel target** (0x18 chases; 0x1C transition writes `lw(def+0xB4)`) | 0x18/0x1C |
| `+0x46` | **heading halfword** (0x1D init `lhu(def+0xB4)`; feeds 0x19's `+0xA4` square and 0x1C's state gate) | 0x1D |
| `+0x48/+0x4C/+0x50` | **camera-anchor words** (0x1C arm copies `D_8016AC18/1C/20`; 0x1D inits 0) | `func_80038734` |
| `+0x52..+0x56` | laser aim source (pass 6, untouched here) | laser |
| `+0x6C` | **per-type timer** (0x18/0x1C: countdown, kill negative; 0x19 init `def+0x28`; 0x1D init `def+0xBE`) | handlers |
| `+0x6E` | **0x18 phase counter** (`+= def+0x2C` mod `def+0x2A`; 0x19 inits 0) | `func_8003442C` |
| `+0x70..+0x80` | **not touched by any of the four bodies or their helpers** — open | — |
| `+0x84` | clone-chain child link (pass 7) | `func_8003A66C` |
| `+0xA4` | **squared constant** `(lh(+0x46) + (D_800ABF9C ? 0x104 : 0x6E))²` | 0x19/0x1D |

**New globals banked:** camera world triple `D_8016AC18/1C/20` (three
independent clusters agree); relative-motion halfword triple
`D_8016AC38/3A/3C` (0x1C); mode modifier `D_800ABF9C` (0x19 `+0xA4` addend,
0x1C radius bound `0x10810 : 0x2F44`, 0x352A0 constants); trig LUT
`D_8008D660`; per-wave table `D_801474FC` × `lh(D_800ABE5C)` stride `0x8C`;
**EU model table `D_800AC428`**; EU block addresses (§10).

**Definition-side fields consumed:** `def+0x0` (type word), `def+0x2`
(resource base + sub-table), `def+0xA`, `def+0x14`, `def+0x24` (travel
clamp), `def+0x28`, `def+0x2A` (phase period), `def+0x2C` (phase step),
`def+0xB4`, `def+0xBC`, `def+0xBE`.

## 13. Verified vs inferred (pass 8) and the next question

- **High confidence:** every field write/read above (instruction-exact), the
  byte-level scan method and its zero-hit results on both twins, the
  branch-closed block, the dispatch rows, the EU block addresses.
- **Interpretation (medium):** "position/velocity/heading/angle" names; the
  Q16 fixed-point reading of `+0x38/+0x3C/+0x40` (the high/low half usage is
  instruction-verified, the fixed-point framing is inference); the
  laser-contact → resource sub-table link via `+0x2A` (the field is written
  by the laser walk per pass 6 and read as an index here — the *mechanism*
  is proven, the gameplay wording is interpretation).
- **Negative closed:** no static reference reaches the model-table block on
  either twin (§10) — the §6 static question is done; only the runtime trace
  remains.
- **Next specific R1 question:** the PCSX-Redux trace on `0x8002DE2C` /
  `D_800ABBE4` per `docs/RUNTIME.md` (the runtime-computed-control-flow
  hypothesis is the only one left), and/or continue the handler map into the
  remaining type bodies (`0x13/0x14/0x15/0x1A/0x1E/0x21/0x29/0x2A/0x30/
  0x31/0x36/0x47`) — the 0x31 morph target body is the natural next read.

**Ownership guard (carried):** EU `src/func_80052038.c` stays untouched;
SDK attribution of the dispatchers remains a separate lane. No builder or
record is converted before a producer-side landing decision (WORK_QUEUE R1
gate).

---

**R1 pass 9 — 2026-11-22 (third bounded run, same window).** The §13 next
read executed: the 0x31 morph-target body. Dispatch row verified:
`D_8008A2F4 + 0x31·4 = 0x8008A3B8 → func_80037D58` (`data_80080048.data.s`
line 14410).

## 14. Type 0x31 — the emitter body

**Morph sequence recap (from §11):** the 0x1C handler's `lh(+0x2E) < 0` arm
runs `func_80038968`, which sets the type word `+0x0 = 0x31` **and then
calls the 0x31 pair inline** — `func_80037E0C(obj, obj)` then
`func_80037D58(obj)` — before the next frame's dispatch ever sees the new
type.

- **`func_80037E0C(obj_new, obj_old)`**: reads `lh(def_old+0xC)` (the dying
  object's definition field `+0xC` = the **template selector**) and calls
  `func_80037E38(obj_new, idx)`.
- **`func_80037E38(obj, idx)`** — the 0x31 initializer: copies a **packed
  8-halfword parameter template from `D_8008A740`** (16 bytes per entry,
  `idx × 0x10`): `template[0..4] → +0x10/+0x12/+0x14/+0x16/+0x18`,
  `template[5] → +0x1C` and **`+0x1A = −template[5]`** (the phase starts
  negated), `+0x1E = 0`, `+0x28 = 0`.
- **`func_80037D58(obj)`** — the per-frame emitter step (the dispatch-table
  handler for 0x31): `+0x12 += lhu(+0x1E)` (0 at init); the phase
  `sum = lhu(+0x1A) + lhu(+0x1C)` stored back to `+0x1A`; **live gate:
  `(sum & 0xFFFF) < lhu(+0x18)`** (template[4] = the lifetime modulus) —
  falling through while alive, `sh zero, +0x0` (kill) once the phase reaches
  the modulus; while alive: **`+0x30 = lhu(+0x10) + (sum>>4)`** (the
  resource selector advances with the phase, same shape as the 0x18 phase
  path) and a spawn arm per `+0x26`: `== 0 → func_80031EC0` (=
  `func_80031F60(obj, 4)`), `!= 0 → func_80031F40` (=
  `func_80031F60(obj, 5)`).
- **`func_80031F60(obj, flag)`** — the spawner core behind all the
  spawn-family entries met in passes 6–9: gates on **`lh(D_800AC29C)`**
  (pass 6's enable word) and the **756-record capacity check
  `lh(D_800AC014) < 0x2F4`** (else `printf(D_80020B84)`), i.e. the request
  is written into the Communication Buffer. The flag selects the request
  kind: 0/1 (`func_80031C5C`/`func_80031CDC` via `func_80031CFC`, the 0x18
  arms), **4** (`func_80031EC0`, the 0x31 emitter) and **5**
  (`func_80031F40`).

**Field semantics for type 0x31 (per-type overlay on the 0xAC record):**
`+0x10..+0x18` = the template's parameter halfwords (period/modulus/lifetime
class), `+0x1A/+0x1C` = the phase pair (init `−template[5]` /
`template[5]`), `+0x12` angle advance by `+0x1E`, `+0x30` = phase-indexed
resource selector. The pass-8 `+0x18/+0x1C/+0x20` trig reading applies to
the prologue-running types; type 0x31 re-purposes the same bytes — the field
map is per-type.

**New globals banked:** template table `D_8008A740` (0x10-byte entries,
indexed by `def+0xC`); spawner core `func_80031F60` with flags 0/1/4/5.

**Next read (R1, unchanged priority):** the PCSX-Redux trace (§10/§13), then
the remaining type bodies — the emitter's spawn arms make `func_80031F60`'s
flag-4/5 request formats the natural companion read.

## 15. Pass 10 — the spawn-request kinds end to end, and the remaining type bodies

All reads below are from the witnessed retail images (`baselines/g3_jp.bin`,
`baselines/g3_eu.bin`), disassembled with the operative mapping
`VA = file_off + 0x8001F800` (verified twice: the allocator body the atlas
attributes to `func_800315AC` sits at file_off 0x11DAC, and the 256-entry
dispatch table the walk loads as `D_8008A2F4` sits at file_off 0x8AAF4 —
256 pointer words, every one 0x8003xxxx-0x8004xxxx).

### 15.1 The producer cores

The request-writing system decomposes into **16 wrapper thunks + two live
cores + one dead core**. Every wrapper is the same 24-byte thunk:
`addiu sp,sp,-24; sw ra,16(sp); jal CORE; li a1,K; lw ra; jr; addiu sp,sp,24`
— the only difference is the immediate `K`, the **request kind**.

- **`func_80031CFC(obj, kind)` — core A** (the world-family writer): gates on
  `lh(D_800AC29C)` (the pass-6 enable word) and `lh(D_800AC014) < 756` (else
  `printf(D_80020B84)`, the "Over flow Communication Buffer !" string). The
  record is written at `lw(D_800AC2CC)` (the bump cursor):
  - **plain form**: `+0x0 = kind`; `+0x2 = lhu(obj+0x30)` (the resource id);
    `+0x4..+0xF` = the three words `obj+0x4/+0x8/+0xC` (position);
    `+0x10 = lhu(obj+0x10)`, `+0x12 = lhu(obj+0x12)`, `+0x14 = lhu(obj+0x14)`;
    **`+0x16 = 4`**; then `count+1 → D_800AC014`, `cursor += 0x18`.
  - **special form** (`obj+0x30 == 0x1C0` **and** `lhu(D_800AC16C) < 0x21C0` —
    the byte budget): identical layout but **`+0x2 = 0x1C2` forced** — the
    pass-7 model-table fact ("`+0x30 == 0x1C0` forces desc id `0x1C2`") is
    here **proven at the producer side** for the first time.
- **`func_80031F60(obj, kind)` — core B** (the projected-family writer, the
  0x31 emitter's spawn core): same two gates; record layout differs in the
  halfword tail — `+0x10 = lhu(obj+0x12)`, `+0x12 = lhu(obj+0x14)`,
  `+0x14 = lhu(obj+0x16)` (one halfword later than core A), `+0x16 = 0`.
- **`func_80032034` — core C** (kind `0xC` hardcoded): plain-form fields,
  `+0x16 = 0` — **zero static callers, dead**.

### 15.2 The wrapper table (whole-image jal census on the retail g3_jp image)

| thunk | kind | core | static jal refs | callers |
|---|---|---|---|---|
| `func_80031BFC` | 0x22 | A | 0 | dead |
| `func_80031C1C` | 0x2 | A | 0 | dead |
| `func_80031C3C` | 0x20 | A | 15 | 0x800318dc (walk region) + 14 handler sites |
| `func_80031C5C` | 0x0 | A | 23 | the 0x18 arms (pass 8) + walk region + 20 handler sites |
| `func_80031C7C` | 0x23 | A | 0 | dead |
| `func_80031C9C` | 0x3 | A | 8 | 0x80030da4 + seven sites in the 0x800456xx-0x800458xx cluster |
| `func_80031CBC` | 0x21 | A | 1 | 0x800395dc |
| `func_80031CDC` | 0x1 | A | 8 | always paired with a kind-0 site |
| `func_80031E60` | 0x26 | B | 0 | dead |
| `func_80031E80` | 0x6 | B | 0 | dead |
| `func_80031EA0` | 0x24 | B | 0 | dead |
| `func_80031EC0` | 0x4 | B | 2 | the 0x31 emitter + the 0x14 handler |
| `func_80031EE0` | 0x27 | B | 0 | dead |
| `func_80031F00` | 0x7 | B | 0 | dead |
| `func_80031F20` | 0x25 | B | 0 | dead |
| `func_80031F40` | 0x5 | B | 2 | the 0x31 emitter + the 0x14 handler |

**Live kinds: 0x0/0x1/0x3/0x20/0x21 (world family) and 0x4/0x5 (projected
family).** Ten producer paths (kinds 0x2/0x6/0x7/0xC/0x22-0x27) are
assembler-emitted but unreached from any static `jal`.

### 15.3 The consumer dispatch — the request kind's meaning

`func_8002DFD8` (the pass-6 consumer) walks `D_800AC014` records in 0x18
strides and dispatches on **`kind & 0xF`** through the 16-entry jump table at
**`D_80020AF0`** (`jr` at 0x8002e06c):

| case | target | meaning |
|---|---|---|
| 0x0 | `func_8002E184` | world constructor (`a1` = s1 cursor, `D_80138DB4`) |
| 0x1 | `func_8002E20C` | world constructor |
| 0x2 | 0x8002e134 | **drop** (record skipped) |
| 0x3 | `func_8002E270` | world constructor |
| 0x4 | `func_8002E640` | projected constructor (`a1` = s2 cursor, `D_8013F9B4`) |
| 0x5 | `func_8002E6A8` | projected constructor |
| 0x6 | 0x8002e134 | **drop** |
| 0x7 | `func_8002E6EC` | projected constructor |
| 0x8-0xD | 0x8002e134 | drop |
| 0xE | `func_8002E318` | world constructor (the 0xE special) |
| 0xF | `0x61766E49` | **string bytes, not code** — unreachable garbage slot |

So the `0x20`-bit forms (`0x20/0x21/0x22/0x23`) are a two-bit modifier the
jump table ignores (`0x20→case 0`, `0x21→case 1`, `0x22→case 2 = drop`,
`0x23→case 3`). Combined with the accept rule (nonzero return + kind == 0xE →
world; kind & 4, != 0xE → projected; else world — pass 6), the live kinds
mean: **0x0/0x1/0x3/0x20/0x21 → world 0x6C TMD records; 0x4/0x5 → projected
0x7C records**. The 0x31 emitter's spawn arms (`func_80031EC0`/`func_80031F40`,
pass 9) therefore spawn **billboard/projected sprites**, not world TMDs.

### 15.4 The walk and the corrected type map

Entry `func_80030BEC` = pre-step `func_80030C7C` (an 8-byte-row stream
stepper: pointer `D_800ABE54` advances while `lh(D_800AC014)` is below the
row's count halfword, storing `D_800ABF5C`/`D_800ABE3C`) + pre-step
`func_80030DBC` (the byte-budget twin, pointer `D_800AC244`) + walk
`func_80030CC8`: 124 slots × 0xAC from `D_8016B014`, `handler =
D_8008A2F4[type]`, `jalr`, then `func_80031468` (the per-object RNG step)
after every slot. The walk itself never frees — handlers decide everything.

**Correction of the pass-6 note** ("0x13/14/15/19/1A/1D/1E/21/29/2A/30/31/36/47
gameplay handlers"): the table rows for **0x15/0x1A/0x1E/0x21/0x2A/0x36/0x47
are all the two-instruction KILL stub `0x80030D4C`** (`jr ra; sh zero,0(a0)`
— kill = type word → 0 = the allocators' free marker). These seven are
kill-on-walk marker types. The real gameplay handler set is
**{0x13, 0x14, 0x18, 0x19, 0x1C, 0x1D, 0x29, 0x30, 0x31}**, plus 0x1/0x2/0x3
= three mini-thunks (`0x80030D5C/D7C/D9C`) that emit the kind 0x0/0x1/0x3
world-render requests for the object while it lives, and 0x7 = no-op.

### 15.5 The remaining type bodies

- **Type 0x30 — `func_80037D0C` (moving emitter)**: `+0x4/+0x8/+0xC +=`
  `lw(+0x38/+0x3C/+0x40)` (the pass-8 velocity triple, raw words — no Q16
  shift here), then **falls into `func_80037D58` inline** — the full 0x31
  emitter step (phase/lifetime/kill-at-modulus, resource selector, kind-4/5
  spawn arms). A velocity-driven emitter sharing the 0x31 machinery.
- **Type 0x29 — `func_80037FB4` (timed burst)**: countdown `+0x6C` per frame;
  at the countdown==2 arm: `+0x70` decrement (0 → `+0x6C = 0` → morph next
  frame), `+0x6E = lhu(+0x84)`, then spawn a child via
  `func_80037F44(obj)` — the **reverse first-free allocator** over the live
  bound `D_8016E1CC` (= base + 74·0xAC, walking DOWN to base; sibling
  `func_80037F1C` scans from the full bound `D_80170364`). Child init:
  type = 0x31, `+0x26 = lhu(obj+0x26)`, position = obj position + a
  fixed-point direction triple composed from `lh(+0x18/+0x1A/+0x1C)` and
  scaled ×−100 (normalized by extra `<<1 >>16` rounds only when `+0x26==0`),
  then `func_80037EA0(old, new)` — the angle-rate divider (calls the template
  init, then `new+0x1E = (lhu(new+0x12)/2) / (lhu(new+0x18)/4)` with
  break-guarded division, `new+0x12 = lhu(new+0x12)/2`). Every frame (not
  just the transition arm) fires a kind-0/1 request for the object itself by
  `+0x26`. At expiry (countdown wrap or child spawn failed): `func_8003D87C`
  (reads `def+0xE`, indexes the handler-pointer table `D_8008A220`, spawns via
  `func_80031558` when the row is valid), then **type = 0x30** and the 0x31
  init + emitter step inline — the same morph sequence as the 0x1C/0x13 arms.
- **Type 0x13 — `func_8003DDC0` (the wander body)**, the richest:
  (1) `lh(+0x2A)` != 0 → `func_80034C60(obj, def)` — a per-bit `srav` scan of
  `lh(+0x2A)` against a 4-row × 0x8C table at `D_801474FC` indexed by the
  rotating counter `lh(D_800ABE5C)` (the walk pre-step's stored halfword);
  (2) `lh(+0x2E) < 0` → the 0x31 morph arm (`func_80037E0C(obj,obj)`, type =
  0x31, `func_80037D58`);
  (3) countdown `+0x6C` → kill at wrap;
  (4) `func_80033274` + `func_8003DFE4` + `func_800334AC` — the 0x6E secondary
  countdown inside `func_8003DFE4` re-arms the **camera-anchor triple**
  `+0x48/+0x4C/+0x50 = D_8016AC18/1C/20` when `+0x26==0` (pass 8's 0x1C
  pattern), then `func_800332C4`;
  (5) velocity integration with the Q16-shift-when-`+0x26==0` rule, then
  `func_80034748(obj)` — the **distance-from-camera-anchor evaluator**
  (Σ(pos−anchor)² per axis when `+0x26==0`);
  (6) radius gate: return < `lw(+0xA4)` → `func_800351D0(obj)` (a marker/HUD
  registration keyed on the pass-8 conditional `D_800ABF9C` with the constant
  pairs `0x1555/0x16C1` vs `0x1A4F`) then **morph to 0x31**; world bounds
  |pos| > 0xF423FF (±16,000,000) → kill;
  (7) resource selector with a **mod-3 phase twist**:
  `+0x30 = lhu(def+0x2) + (countdown % 3)`;
  (8) wander angles: `+0x10 = lhu(D_800ABF34) + ((rng>>3 & 0x3FF) − 512)` →
  trig (`func_80030454`) → `+0x18`; same shape for `+0x12`/`D_800ABF44` →
  `+0x1C` and `+0x14` → `+0x20`; then `+0x14 += lhu(def+0xBA)` → trig →
  `+0x24` (rng = `D_800AC50C`, pass 7);
  (9) `func_800337B8(obj)`.
- **Type 0x14 — `func_8003E060` (looping mobile emitter)**: the 0x13 frame
  body (def chain, anchor arm, sub-steps `func_80033274`/`func_8003E22C`/
  `func_800334AC`, Q16/raw velocity integration, anchor-distance radius gate
  → `func_800351D0` → **morph 0x31**, ±16M kill, countdown kill) PLUS the
  emitter phase path **with the wrap twist**: `sum = lhu(+0x1A) + lhu(+0x1C)`;
  if `(s16)sum < lh(+0x18)` → `+0x1A = sum`, else **`+0x1A = sum − lh(+0x18)`**
  — the phase **wraps by the modulus instead of killing** (a looping emitter,
  vs 0x31's one-shot kill-at-modulus); then `+0x30 = lhu(+0x10) +
  ((u16)phase >> 4)` and the kind-4/5 spawn arms by `+0x26` — the exact
  0x31 emitter tail.

### 15.6 Argument-order correction (pass 9, §14)

`func_80037E0C(a0, a1)` reads the definition from **a0** (`lw(a0+0x60)`,
`idx = lh(def+0xC)`) and initializes **a1** (`a0 = a1` then
`func_80037E38(a1, idx)`). The true signature is therefore
**`func_80037E0C(def_source, init_target)`** — pass 9's "(obj_new, obj_old)"
label had the arguments flipped. The substance stands (the template selector
comes from `def+0xC` of the dying object; the object being initialized
receives it) because every morph-arm call site passes `(obj, obj)`; the
0x29 child spawn is the one site where the order is visible:
`func_80037EA0(old, new)` → `func_80037E0C(old, new)` — the **old object's**
template drives the **child's** init.

### 15.7 EU twin corroboration

The EU walk (`0x80030944`) reads the same shape: pool base `D_8016B138`,
124 × 0xAC slots, dispatch table **`D_8008AB0C`** (256 words, 227 = the kill
stub `0x800309B4`), RNG step `func_800310D0` per slot. The EU kill stub is
**byte-identical** to JP's (`jr ra; sh zero,0(a0)`). Every gameplay handler
sits at a **uniform −0x398 block shift** from its JP twin (0x13→0x8003DA28,
0x14→0x8003DCC8, 0x18→0x80034094, 0x19→0x80033DD4, 0x1C→0x8003825C,
0x1D→0x80033E50, 0x29→0x80037C1C, 0x30→0x80037974, 0x31→0x800379C0) — the
type-handler block is body-identical across the twins. The kill-shared type
set {0x15, 0x1A, 0x1E, 0x21, 0x2A, 0x36, 0x47} is identical in both tables.

### 15.8 New globals banked

Consumer jump table `D_80020AF0` (16 words, `kind & 0xF`); kill stub
`0x80030D4C` (EU `0x800309B4`); flag table `D_801474FC` (4 × 0x8C) with its
counter `D_800ABE5C`; handler-pointer table `D_8008A220` (indexed by
`def+0xE`, consumed by `func_8003D87C`); reverse allocators `func_80037F1C`
(full 124-span) / `func_80037F44` (live 74-span); anchor-distance evaluator
`func_80034748`; marker registration `func_800351D0` (`D_800ABF9C`-modeled);
angle divider `func_80037EA0`; pre-morph spawn-from-table `func_8003D87C`;
stream steppers `D_800ABE54` (8-byte rows) and `D_800AC244` in the walk entry.

**Next read (R1):** the consumer constructors themselves
(`func_8002E184/2E20C/2E270/2E318` world, `func_8002E640/2E6A8/2E6EC`
projected — the 0x6C/0x7C record build from the 0x18 request, which closes
the request→render-surface chain end to end), and/or the PCSX-Redux trace
(§10/§13, the only remaining §6 hypothesis).

## 16. Pass 11 — the consumer constructors: the 0x18 request → 0x6C/0x7C record build

Reads from the witnessed retail `baselines/g3_jp.bin` (same mapping as §15).
The dispatch slots of §15.3 decode as follows (`desc` = the 0x18 request
record, `rec` = the 0x6C/0x7C record cursor; the returned value is −1 on
success, 0 on lookup failure — the consumer drops zero-return records, the
pass-6 convention re-confirmed at every constructor).

### 16.1 World constructors (a1 = the D_80138DB4 cursor)

- **case 0 — `func_8002E184`**: kind → `rec+0x0`; the position words
  `lw(desc+0x4/0x8/0xC)` are **camera-relative** — each is reduced by the
  camera anchor `D_8016AC18/1C/20` before `func_8002E4B8(rec, resid,
  relX, relY, relZ, lhu(desc+0x10), lhu(desc+0x12), lhu(desc+0x14))`. The
  case-0/kind-0x20 producers therefore emit positions in CAMERA SPACE.
- **case 1 — `func_8002E20C`**: the absolute variant — the position is the
  three **upper halfwords** `lh(desc+0x6/0xA/0xE)` of the same words
  (16-bit absolute coordinates), no anchor subtraction.
- **case 3 — `func_8002E270`**: the halfword coordinates
  `lh(desc+0x6/0xA/0xE)` go through **`func_800326A8`** (a three-word
  transform of the local triple) before the shared builder.
- **case 0xE — `func_8002E318` (the laser descriptor constructor)**: the
  position words go through `func_800326A8`; the resource id is
  `lhu(desc+0x2) + 8` (the pass-6 laser-id fact) through
  `func_8002F368`; a model header is copied into `rec+0x14` and mapped at
  `rec+0x4` (`func_8004F12C`/`func_80051BE4`), `rec+0x8 = rec+0x14` (the
  coordinate pointer), `rec+0x64 =` the resource pointer; the three angle
  halfwords round `>>4` (bgez + 15) and feed a rotation set
  (`func_80047DA0`/`func_8002F534`/`func_8004A1B0` with the `0x4000/0x4000/
  0x2000` scale triple); `rec+0x2C/0x30/0x34` = the transformed position
  doubled with Y negated; **`rec+0x0 = 3` forced** (the pass-6 note), the
  resource word → `rec+0x4`.

### 16.2 Projected constructors (a1 = the D_8013F9B4 cursor)

- **case 4 — `func_8002E640`**: camera-relative words minus the anchor, no
  angle halfwords → `func_8002E770`.
- **case 5 — `func_8002E6A8`**: absolute halfword coordinates →
  `func_8002E770`.
- **case 7 — `func_8002E6EC`**: halfword coordinates through
  `func_800326A8` → `func_8002E770`.

### 16.3 The shared builders

- **`func_8002E4B8(rec, resid, X, Y, Z, a0, a1, a2)`** — world: resource
  lookup `func_8002F368(resid, out0, out1)`; −1 → return 0 (drop). Copy the
  model header to `rec+0x14`, map at `rec+0x4` (`func_8004F12C`/
  `func_80051BE4`), `rec+0x8 = rec+0x14`, `rec+0x64 =` resource; the three
  angle halfwords round `>>4`; **the third angle gets a +0x8000 half-turn
  bias** before the rotation set; Z lands via the stack.
- **`func_8002E770(rec, resid, X, Y, Z)`** — projected: resource lookup
  **`func_8002F3D4`** (a different table — see §16.4); −1 → return 0;
  **AND `rec kind == 7` → return 0 even on a successful lookup** — kind 7 is
  a dead end end-to-end (the jump table still routes it, the builder
  rejects it). Build: header copy to `rec+0x2C` (`func_8004F12C`),
  `rec+0x44/0x48/0x4C = 0`, sprite-style build from the resource words into
  `rec+0x4..`.

### 16.4 The two resource lookups — the §6 population question sharpens

- **`func_8002F368(id, out0, out1)`** — the **world/TMD lookup**: walks rows
  of 0x14 bytes whose head pointer is **`lw(D_800ABBE4)`** (the pass-7 model
  table pointer!); row `+0x0` = id (−1 sentinel terminates), match reads
  `+0x8 → out0`, `+0xC → out1`, `+0x10 →` return. This is a THIRD accessor
  beyond the unreached setter/mapper walks of §5/§10 — and it is on the
  **per-frame consumer path**: every world constructor calls it. Since
  `D_800ABBE4` image-initializes to 0 (pass 8) and the game demonstrably
  renders, **the table must be populated at run time** — the strongest
  constraint yet on the remaining §6 hypothesis (the PCSX-Redux trace).
- **`func_8002F3D4(id, out0)`** — the **projected/sprite lookup**: walks rows
  of 0x34 bytes whose head pointer is **`lw(D_800ABBEC)`** (the pass-7
  second table); row `+0x0` = id (−1 sentinel), match reads `+0xC → out0`
  and returns row `+0x10` as the base. Same runtime-population constraint.

**Pass-11 verdict:** the request→render-surface chain is closed end to end —
producer core record format (§15.1) → consumer `kind & 0xF` dispatch
(§15.3) → per-case constructor semantics (this section) → shared builders →
the two resource tables whose runtime population is the last open question.
**Next read (R1):** the PCSX-Redux trace on `0x8002DE2C`/`D_800ABBE4`/
`D_800ABBEC` per RUNTIME.md — now with the sharp question "what writes the
two table head pointers at runtime"; optionally `func_800326A8` (the
constructor transform) to label the case-3/7 coordinate space.

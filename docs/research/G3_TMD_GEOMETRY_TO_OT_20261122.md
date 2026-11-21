# G3 world TMD model path: scene records to GPU ordering table

**R1 pass 5 — 2026-11-22.** Bounded *source-only* JP/EU static call/data-flow analysis. Builds directly on [the FOBJ 2D sprite atlas](G3_FOBJ_SPRITE_PATH_20261122.md) and [frame/OT atlas](G3_HUD_QUEUE_FRAME_LOOP_20261122.md). **No new live retail SHA-1 comparison, executable runtime capture, C conversion, SDK rename, or history rewrite.**

## Executive result

The 3D scene has a **verified chain** from game-owned descriptor traversal to Psy-Q TMD polygon callbacks that directly write GPU packets and link an ordering table (OT), which is finally submitted through `GsDrawOt`.

```text
frame → func_80022FE4 (JP)
  → func_8002DFD8(&count3d, &countProjectedSprite)  # scan game descriptor list
      → bounded per-type creation helpers
          → func_8002E318: GsInitCoordinate2, GsLinkObject4(TMD+0xC,...)
  → ... independent FOBJ, FONT, 2D HUD submission ...
  → func_8002E9F4(activeOT, count3d)
      → for each 0x6C-byte TMD scene record
          → GsGetLw / matrix transforms in PS1 scratchpad
          → GsGetLs, GsSetLightMatrix, GsSetLsMatrix
          → func_800526D4(GsDOBJ2-like object, activeOT, shift, scratchpad)
              → TMD primitive-mode dispatch, named GsTMDfast*/GsTMDdiv* tables
                  → e.g. GsTMDfastF3L:
                       GTE rtpt, nclip, avsz3, nccs
                       → write 20-byte polygon DMA packet
                       → splice packet into active OT depth slot
  → func_8002EC7C(activeOT, countProjectedSprite)
      → GTE-projected **sprites**, not TMD polygons; GsSortSprite
  → ... GsSwapDispBuff → GsDrawOt(activeOT)
```

**Ownership boundary:** descriptor allocation, game-state-driven model creation, scene list partitioning and transforms are important targets for **game-owned semantic C**. The TMD dispatch and primitive packet functions are consistent with **Psy-Q SDK internals**, not proof that the game authors invented a geometry renderer. The dispatcher has a likely `GsSortObject4J` identity, but archive/member ownership is **not yet independently adjudicated**.

## 1. Source coordinates and the three rendering paths

All JP addresses below are virtual addresses from tracked `g3_jp` assembly; EU addresses are **not** interchangeable. The [JP splat map](../../config/splat.g3_jp.yaml) records its `func_800526D4` assembler row beginning at offset `0x32ED4` (VA `0x800526D4`, **0x710 bytes**); [EU splat](../../config/splat.g3_eu.yaml) instead maps `func_80052038` to **C** at offset `0x32838` (**0x7F0 bytes**) in [the pre-existing EU matching C file](../../src/func_80052038.c).

| Rendering family | JP source | Verified distinguishing edge |
| --- | --- | --- |
| FOBJ two-dimensional overlay | `func_80044614` → `func_8002E894` → `func_8002EF14` | 100 × 6-byte resource/x/y commands → `GsSortSprite` (previous pass) |
| Game-owned TMD world objects | `func_8002DFD8` → `func_8002E9F4` → `func_800526D4` | **GsLinkObject4**, coordinate matrices, `GsTMDfast*/div*` polygon packet callbacks |
| Projected 3D-positioned sprites/billboards | `func_8002EC7C` | GTE position/screen bounds checks → **GsSortSprite** at JP `0x8002EED0`; this is **not** the TMD object path |

The two separate object renderers and FOBJ sorter run during frame submission `func_80022FE4`, as shown in [JP frame submission ASM](../../asm/g3_jp/nonmatchings/func_80022AFC.s): scene-list partition at **`0x80023004`**, TMD draw-stage call **`0x80023120`**, projected sprites **`0x80023144`**, and eventual **`GsDrawOt` at `0x800232B8`** via `func_80023268` after swap. The latter is conditional on the surrounding frame-control branches; **do not assert unconditional hardware submission on every path**. Prior atlas identifies the actual frame loop `0x80042C6C..` and its call to `func_80022FE4`.

## 2. Descriptor → linked TMD object → two record classes

In [JP scene/model ASM](../../asm/g3_jp/nonmatchings/func_8002A2DC.s):

- `func_8002DE3C` is a **model resource-table pass**: accesses stored model list pointer `D_800ABBE4`, walks in **0x14 strides**, resolves an input reference with `func_80024910`, then calls anchored `GsMapModelingData` at **JP `0x8002DE98`** with resolved pointer **+4**. The game includes the literal CD path `\\DRAGOON\\TMD.DAT;1` in [retained data](../../asm/g3_jp/nonmatchings/data/data_80020000.data.s); **which particular asset is loaded here remains to be established from its callers and file reads**.
- `func_8002DFD8` processes the game descriptor array `D_80166360` in **0x18-byte input strides**, bounded by signed count `D_800AC014`. At **JP `0x8002E040..0x8002E0F8`**, its 15-position nibble dispatch `jtbl_80020AF0` chooses a bounded constructor/helper by low four bits of the record type (the out-of-range code is rejected; not all slots imply a valid handler).
- One concrete model constructor **`func_8002E318`** calls `GsInitCoordinate2` at **`0x8002E3B0`**, then **`GsLinkObject4` at `0x8002E3C4`** with `a0 = model_pointer + 0xC, a1 = record + 4, a2 = 0`; stores an initialized coordinate pointer at **record +0x8** and model resource pointer at **record +0x64**. Another constructor calls `GsLinkObject4` at **`0x8002E54C`**.
- Accepted descriptors are partitioned into two compact arrays: **`D_80138DB4` of 0x6C-byte world/TMD records** and **`D_8013F9B4` of 0x7C-byte projected sprite records**. The loop at **`0x8002E10C..0x8002E150`** advances either scene-list write cursor and records counts to output pointers, with the split depending on the type/status, including a special-case type `0xE` and bit `&4`. These same count pointers are used by the frame render caller.
- This is the *game-owned* location to recover model-instance/animation lifetime and material/object semantics. **Do not name the arrays as universal mesh pointers without confirming all type subcases.**

### 3D draw stage arguments and scratchpad

`func_8002E9F4`, from **JP `0x8002E9F4..0x8002EC7C`** (EU `func_8002E7C4`), reads count `a1`, starts at `D_80138DB4`, and iterates **0x6C bytes per record**. It loads scratch pointer **`0x1F800000`** (the PS1 scratchpad) into `s3`; `GsGetLw` at **`0x8002EB98`** and intermediate matrix helpers populate the scratch matrix. It invokes **`GsGetLs` at `0x8002EC14`**, **`GsSetLightMatrix` at `0x8002EC1C`**, **`GsSetLsMatrix` at `0x8002EC24`**, and then **`func_800526D4` at `0x8002EC40`** with registers:

| Argument | Source at call | Meaning/confidence |
| --- | --- | --- |
| `a0` | `s1 + 4`; `s1` is current 0x6C scene record | linked `GsDOBJ2`-like object; **high** |
| `a1` | `s6` (original frame `a0`) | **same active GsOT pointer** as 2D paths; **high** |
| `a2` | `lw 0(s0)`; `s0` points 0x68 into current 0x6C record | depth/OT shift/control word; **high** for offset, medium for semantics |
| `a3` | `s3 = 0x1F800000` | scratchpad workspace/matrix; **high** |

The core 3D draw stage and separate billboard stage are **distinct loops**; `func_8002EC7C` projects its separate 0x7C records and invokes `GsSortSprite` at **`0x8002EED0`**, instead of passing them to the TMD primitive dispatcher.

## 3. Inside the TMD dispatcher: primitive mode → callback family

In [JP `func_800526D4.s`](../../asm/g3_jp/nonmatchings/func_800526D4.s), `func_800526D4` is a `0x710`-byte **TMD primitive walker/dispatcher**, not a sprite sorter:

1. At **`0x80052708..`**, reads the linked object flags and sets work mode/lighting state using `GsSetLightMode_lmode` and object attribute bits.
2. At **`0x80052808..0x80052824`**, reads linked object's TMD primitive data pointer/count, vertex and normal-array pointers. It exits early on a zero primitive count.
3. At **`0x8005283C..`**, reads primitive mode byte at **`primitive[3]`**, masks with `0xFD`, subtracts `0x20`, checks `< 0x1E`, and jumps through **`jtbl_80021B30`** (30 entries, source [JP table data](../../asm/g3_jp/nonmatchings/data/data_80020000.data.s)).
4. Branches in `0x80052874..0x80052D8C` select mode/lighting tables, load a primitive callback into a register, and invoke it using **`jalr $v0`**, passing remaining primitive stream, matrix/OT state, packet cursor, vertex/normal pointers and counts. The callback's returned packet cursor is stored at `D_8016AA40`.
5. Primitive stream advance depends on decoded primitive format: **16/20/24/28/32/36 bytes per primitive**, as shown by mode-specific count-dependent strides, with an additional 12-byte* count branch for some variants. Avoid assuming a single TMD polygon structure.

The function pointer table group at [JP `D_80098180..D_80098278`](../../asm/g3_jp/nonmatchings/data/data_80080048.data.s) resolves to **named Psy-Q polygon assembly**: `GsTMDfastF3L`, `GsTMDfastF3LFG`, `GsTMDfastF3NL`, `GsTMDdivF3NL`, `GsTMDfastG3L`, `GsTMDfastG3NL`, textured `TF3*/TG3*` families, flat/Gouraud quad `F4/G4` families and others. Mode selection also depends on runtime lighting and per-object flags. This is **direct pointer/table evidence**, not guessed symbols from signatures alone.

### Actual polygon OT packet proof

The named, anchored [`GsTMDfastF3L` MIPS](../../asm/g3_jp/nonmatchings/func_80054DC4.s) at JP `0x80054DC4..0x80054F0C` is a concrete primitive callback:

| JP VA | Observed instruction effect |
| --- | --- |
| `80054E24` | GTE `rtpt`: transform/project three vertices |
| `80054E74` | `nclip` face/visibility test |
| `80054E88`, `80054E9C` | `avsz3` depth calculation and `nccs` shading |
| `80054E9C..80054EB4` | derive OT slot from depth and read existing OT tag |
| `80054EBC..80054EC8` | construct and write GPU packet/DMA header at packet cursor `a3` |
| **`80054EDC`** | **write updated link into OT slot** (`sw $v1, 0($t6)`) |
| `80054EE0..80054EEC` | write screen/color words into polygon packet |
| `80054EF0` | advance packet cursor by **`0x14` (20 bytes)** |
| `80054F00..` | return updated packet cursor for next primitive |

The **actual OT pointer mutation** is proven by MIPS stores and table flow; this is stronger than merely seeing the symbol `GsTMDfastF3L`. The frame's later **`GsDrawOt`** consumes this active OT. Geometry may be culled and does not necessarily produce a packet for every primitive.

**SDK boundary:** `GsTMDfastF3L` is already anchored in [`config/sdk_anchors.txt`](../../config/sdk_anchors.txt) to a Psy-Q/LIBGTE library member. The high-level TMD dispatcher is functionally the **`GsSortObject4J`-style** four-argument call path. `config/sdk_anchors.txt` currently does **not** anchor the JP dispatcher `0x800526D4` as such. This is an **attribution hypothesis** that needs a specific SDK archive/member/symbol cross-check before altering names or coverage classifications; do not count it as independently written game source.

## 4. EU comparison and pre-existing matching C: important ownership caution

In [EU scene ASM](../../asm/g3_eu/nonmatchings/func_8002A2CC.s), the corresponding stages are:

| Operation | JP | EU |
| --- | --- | --- |
| Scene partition/count generation | `func_8002DFD8` | `func_8002DDA8` |
| TMD-scene object draw loop | `func_8002E9F4` | `func_8002E7C4` |
| Projected sprite loop | `func_8002EC7C` | `func_8002EA4C` |
| Linked TMD primitive dispatcher | `func_800526D4` (ASM 0x710) | `func_80052038` (**already C**, 0x7F0) |
| One named polygon callback | `GsTMDfastF3L` 0x80054DC4 | `GsTMDfastF3L` 0x80054808 |

The already committed [`src/func_80052038.c`](../../src/func_80052038.c) carries a **historical claim of exact 2032-byte EU retail match** and is intentionally mapped to a C row in [EU YAML](../../config/splat.g3_eu.yaml). Its code explicitly dispatches on `s0[3] & 0xFD`, iterates a count and calls named `GsTMD*` routines through the `D_80098998...` family of tables. EU [TMD table data](../../asm/g3_eu/nonmatchings/data/data_8008002C.data.s) corroborates named callback pointers. The existing match **has not been rerun**; retain the matching C unchanged.

**Critical implication:** if independent SDK member attribution confirms the dispatcher is `GsSortObject4J` or an SDK variant, the project may have classified a **matching SDK routine as “game function #15”**. This does **not** invalidate its previously reported byte match, but does change its semantic/coverage provenance. Do not silently rename the already matched function or alter the owner-held coverage/rule set. Produce a separate archive-backed, target-specific naming/ownership adjudication first. The JP and EU dispatchers are similar in role but differ in size; **never assume byte-identical regional implementation**.

## 5. Static JP/EU comparisons

Using full committed ASM instruction streams and the project `compare_asm_windows.py`-style little-endian word, opcode/register and J-target-shape comparison (**not** a fresh retail oracle):

| JP start → EU start | Instructions | Byte-identical instruction words | Matching instruction shape |
| --- | ---: | ---: | ---: |
| `8002DFD8 → 8002DDA8` scene enumeration | 107 | 87 | **107/107** |
| `8002E03C → 8002DE0C` type branch window | 70 | 54 | **70/70** |
| `8002E3B0 → 8002E180` TMD link window | 8 | 6 | **8/8** |
| `8002E9F4 → 8002E7C4` TMD draw stage | 162 | 146 | **162/162** |
| `8002EC7C → 8002EA4C` projected sprite stage | 166 | 156 | **166/166** |
| `80054DC4 → 80054808` named library polygon callback | 82 | 81 | **82/82** |
| **Total** | **595** | **530** | **595/595** |

Comparisons cover **only these bounded windows**; the EU dispatcher is already C and deliberately not included. Source-only structural agreement is **not** proof of full-function identity, asset compatibility, executed runtime behavior or successful eight-target retail SHA-1 rebuild. To reproduce two main windows locally, run:

```sh
python3 tools/compare_asm_windows.py \
  --left asm/g3_jp/nonmatchings/func_8002A2DC.s \
  --left-start 0x8002E9F4 --left-end 0x8002EC7C \
  --right asm/g3_eu/nonmatchings/func_8002A2CC.s \
  --right-start 0x8002E7C4 --require-shape

python3 tools/compare_asm_windows.py \
  --left asm/g3_jp/nonmatchings/func_80054DC4.s \
  --left-start 0x80054DC4 --left-end 0x80054F0C \
  --right asm/g3_eu/nonmatchings/func_80054808.s \
  --right-start 0x80054808 --require-shape
```

## 6. Highest-value next R1 investigation

**Recover the game-owned scene descriptor and model instance contract, not SDK polygon primitives.** Follow the **0x18 input descriptor → 0x6C linked-TMD record** construction through `func_8002DFD8` and `func_8002E318` (plus its sibling constructor), then find producers/updaters for `D_80166360`, `D_800AC014` and the 0x6C object transform fields. Identify animation, object lifetime and level geometry ownership; use EU to constrain type/pointer layout. Avoid converting until the original executable oracle is available for matching and semantic verification.

**Separate SDK provenance lane:** check whether `func_800526D4` / EU `func_80052038` truly correspond to Psy-Q `GsSortObject4J` in the linked library build. Consult archive/member maps and matched SDK functions; preserve the already matched EU C and require owner review before any cross-target naming/coverage change.

Other open questions carried forward: 0xE100 GPU packet buffer bounds, the unresolved 2D resource ID `0x707`, bounds for other staging buffers, and current eight-executable retail SHA-1 witness. **No historical Git rewrite.**

# G3 14-bit ordering table, reverse layering and decoded-video VRAM path

R1 pass 28, 2026-11-23 (Adelaide local). Input HEAD `e73701b4526c8f1373755668b739ea75445d10ce` (PR #10). Continues [pass 27](G3_RESOURCE_RENDER_METADATA_20261122.md), [render preparation](G3_RENDER_PREP_ATLAS_20261122.md), [frame loop](G3_HUD_QUEUE_FRAME_LOOP_20261122.md), and [stream clock](G3_STREAM_CLOCK_POSE_20261122.md). **Read-only original EXE/assembly and SDK-static evidence; docs only.** The local container returned ClientError again, so no CHD extraction, real stream sample, guarded compiler verification, or live video/GPU capture. Original retail EXE identities from pass 25; not a fresh hash audit.

## 1. Fully specified GsOT and its physical allocation

JP game-owned startup [`func_80024224`](../../asm/g3_jp/nonmatchings/func_80022AFC.s), instructions `80024250..800242AC`:
- `GsInitGraph(0x200,0xF0,0,0,...)` (512 × 240); `GsDefDispBuff(0,0,0,0xF0)`. Display/video framebuffer environment distinct from CPU ordering table.
- `80024278` materializes `0x0E`, stores to both header lengths (`D_8016AF20` at `80024280` and `D_8016AF34` at `80024298`).
- Stores `GsOT.org` to `D_8016AF24` = `D_800AC5C4` at `80024290`, and `D_8016AF38` = `D_800BC5C4` at `800242A8`.
- Thus each header has 14-bit width, **16384 tags × 4 bytes = 0x10000 bytes = 64 KiB**, and two adjacent physical arrays totaling 128 KiB, `800AC5C4..800BC5C4` and `800BC5C4..800CC5C4` end-exclusive. The headers are 20 bytes each, at `8016AF20`/`8016AF34`, *not* part of the tag arrays.
- [Existing matched `GsClearOt` C](../../src/GsClearOt.c) sets header+8/+0C to the two zero arguments, tag pointer +0x10 = `org + (4 << length) - 4`, calls `GsClearOt_clear(org, 1 << length)`.
- JP frame preparation [`80022F70..80022F90`](../../asm/g3_jp/nonmatchings/func_80022AFC.s) calls `GsClearOt(0,0,ot)` for the active buffer; input +8 OT offset is zero. Packet work memory is **separate**, at `D_8014773C + active_buffer * 0xE100` (57,600 bytes / buffer) passed to `8005DBE0`, which updates SDK packet cursor `D_8016AA40`. Do not confuse packet allocation space and OT tag array capacity.

**Four retail scenario targets independently inspected** for unique 13-word startup initialization window (raw tracked original PS-X EXEs, skip 0x800 header, little-endian words):

| Executable | Init VA | `GsOT[0]` | OT0 org | `GsOT[1]` | OT1 org |
|---|---|---|---|---|---|
| Dragoon JP | `80024278` | `8016AF20` | `800AC5C4` | `8016AF34` | `800BC5C4` |
| Dragoon EU | `800242D8` | `8016B044` | `800ACE14` | `8016B058` | `800BCE14` |
| Gourb JP | `80024C54` | `80178BD4` | `800B94F8` | `80178BE8` | `800C94F8` |
| Gourb EU | `80024C6C` | `80178CBC` | `800B9D0C` | `80178CD0` | `800C9D0C` |

All four have 13/13 identical register/opcode shapes (different data addresses). Both headers' width is literal 14, and both org pointers differ by `0x10000` in every executable. The windows are unique best matches in scanned `80022400..80035000` (JP 13/13, EU 7/13, Gourb JP 1/13, Gourb EU 1/13 exact instructions; differences are relocations).

## 2. OT sorting direction and equal-depth tie behavior

The [target-scoped SDK anchors](../../config/sdk_anchors.txt) establish (not speculative LIBGS attribution):

| Contract | Dragoon JP | Dragoon EU | Gourb JP | Gourb EU |
|---|---|---|---|---|
| `ClearOTagR` | `8004BE60` | `8004B7D0` | `800492FC` | `80048C24` |
| `DrawOTag` | `8004BF58` | `8004B8C8` | `800493F4` | `80048D1C` |
| `GsDrawOt` | `8005DBF0` | `8005E254` | `8005B08C` | `8005B6A8` |

JP `GsClearOt_clear` [ASM](../../asm/g3_jp/nonmatchings/func_8004BE60.s) invokes the anchored ClearOTagR backend. [GsDrawOt](../../asm/g3_jp/nonmatchings/func_8005DBF0.s) reads header+0x10 and invokes the anchored DrawOTag backend. This proves reverse tags **16383 → 0** for all four, consistent with Sony's [ordering table primer](https://psx.arthus.net/sdk/Psy-Q/DOCS/TECHNOTE/ordtbl.pdf) and [lib overview](https://psx.arthus.net/sdk/Psy-Q/DOCS/Devrefs/Libovr.pdf).

The [anchored F3L polygon callback](../../asm/g3_jp/nonmatchings/func_80054DC4.s) `80054EA0..80054EDC` computes bucket, reads prior head tag and writes the new packet/link back to the bucket (**head insertion**). Consequently **within one bucket last inserted is drawn first, earliest inserted last**. Note that alpha/blending means *visual* compositing is not always equivalent to opaque overwrite.

A measured 3D callback computes `bucket = (((uint32_t)(OTZ - ot.offset)) >> (shift & 31)) & 0xFFFF` with `ot.offset=0` after normal clear. Hardware OT has only **14 valid bits**: the callback masks 16, not 14, and no bounds check is visible in this sampled F3L path. Do not silently modulo 16384 or clamp a native renderer; the real range of OTZ for shift-zero resources needs an instrumentation/asset witness. An OT-range validation check is a useful future emulator probe.

### Concrete 2D ordering tiers

Original JP 273 authored texture table rows at `80072FD4` (pass25 proves all corresponding non-index words equal EU):

| Direct `GsSortSprite` priority | Rows | Illustrative logical IDs |
|---|---:|---|
| 0 (drawn last) | 105 | `0x700,0x707,0x708` — direct HUD callers known |
| 1 | 16 | all `0x100..0x10F` |
| 2 | 138 | `0x16B..` cluster, among others |
| 12 | 10 | exactly `0x1FB..0x204` |
| 14 (drawn first among authored sprite tiers) | 4 | exactly `0x3FA..0x3FD` |

Draw order of these authored sprite-only buckets is `14 → 12 → 2 → 1 → 0`. The font glyph sorter also passes hard-coded priority 0. Resource group clustering is **evidence of authored priority bands**, but sprite images/classifications still need actual TIM assets; IDs alone do not prove "cockpit" or "background" identity.

Model 307-row shift histogram from pass27: shift 0:225, 8:54, 9:6, 10:21, 11:1; 274 resources have unlit bit6. Correlating known model IDs:
- Fighter `0x9F`: attribute `0x40`, shift 0; adjacent `0xA0,0xA1`: `0x40`, shift 8.
- Doldva parent `0xD9`: `0x40`, shift 0.
- SPARKBIT parent/change/effect `0x1C0,0x1C4,0x1C5`: `0x40`, shift 0.
- The lone shift-11 row is ID `0x36`; no object identification established.
This **rules out a simple “bosses always use coarse depth shift” inference**. No role assigned to `0xA0` merely by numeric adjacency.

## 3. The video lives in the VRAM background, not inside the OT

The [JP frame submission](../../asm/g3_jp/nonmatchings/func_80022AFC.s) invokes all HUD/font/sprite/world draw packet constructors first (`80023038..80023148`), then `GsSwapDispBuff` at `80023278`, `func_8002AC04(D_8016AEA8, active_buffer)` at `80023290`, and finally `GsDrawOt(active_ot)` at `800232B8`. Separate conditional exceptional exit before swap remains possible; **normal active submission path** is analyzed.

[JP video upload `8002AC04..8002ACD4`](../../asm/g3_jp/nonmatchings/func_8002A2DC.s) reads:
- signed halfword at stream/video state `+0x14`, truncates toward zero /16 for number of horizontal strips;
- `+0x20` and `+0x22` unsigned halfwords as `RECT.w` and `RECT.h`;
- `+0x0C` as source image pointer;
- for strip index i: `RECT.x = 16*i`, `RECT.y = active_buffer==0 ? 0x110 : 0x20`, image pointer `base + 2*(16*i)*signedHeight` (`lh +0x22` for stride calculation), `LoadImage(&rect,imagePointer)`. Repeating `x += 16` is direct. The input width+0x14 is **not** proven to equal output framebuffer width; do not assert a fixed strip count or pixel dimensions without data.
- after the loop, `DrawSync(0)` is called unconditionally.
- [SDK anchors](../../config/sdk_anchors.txt) identify JP `8004BC1C` as **LoadImage** and `8004B9F4` as **DrawSync**; this isn't a guessed function signature.

The video upload uses **VRAM pixels**. The OT holds packet-linked TMD polygons and sprites; the streamed image is **not another OT member**. The normal frame protocol ensures the upload completes before GPU OT drawing, so the world/HUD are rendered onto an already supplied video image. This is a meaningful preservation constraint for a native renderer: reconstruct video as the frame background/VRAM upload stage, preserving sprite OT layering and draw order, rather than treating video as a polygon with arbitrary depth. Do not claim the original decoder's pixel format, actual strip sizes or exact synchronization cadence until the STR is inspected; two-byte source stride is observed but not a full image-format proof.

The full video upload routine is **52 instructions / 0xD0 bytes**, uniquely matching in all four original EXEs:

| Program | Entry | Matching instruction shapes | Word-identical vs JP | Delta explanation |
|---|---|---:|---:|---|
| Dragoon JP | `8002AC04` | 52/52 | 52/52 | baseline |
| Dragoon EU | `8002ABF4` | 52/52 | 49/52 | two SDK calls, local jump relocation |
| Gourb JP | `8002B8AC` | 52/52 | 49/52 | two SDK calls, local jump relocation |
| Gourb EU | `8002B854` | 52/52 | 49/52 | two SDK calls, local jump relocation |

All 3 non-identical instructions per sibling are J/JAL target encodings (at JP word indices 39,41,43), meaning the **entire 52-instruction body is relocation-equivalent** across the four targets without immediate masking beyond branch targets. Two adjacent final frame windows also agree in opcode/register shape: 11-word OT clear and 18-word swap/video/draw span each 11/11 and 18/18 across targets. Four-target startup and backend SDK anchors independently corroborate the shared architecture.

## 4. Order of events and renderer fidelity

For ordinary live frames:

```text
stream metadata → mission pose/scripting  (pass 17)
     ↓
GsGetActiveBuff → packet workbase → GsClearOt(0,0)
     ↓
HUD/font/FOBJ + 3D world + projected sprite sorters
     ↓
VSync / GsSwapDispBuff
     ↓
stream video strips → LoadImage ... → DrawSync(0)
     ↓
GsDrawOt → DrawOTag(last OT tag)
     ↓
execute reverse bucket chain (high → low)
```

Do not reinterpret creation order as screen compositing order: a sprite registered before geometry may appear later because of lower OT bucket, and ties are head-inserted. No evidence of a PS1 Z-buffer; model OTZ computations and sprite priorities are distinct mechanisms.

**Open questions:** exact video block dimensions/format and MDEC output timing, whether special modes bypass uploads, fill/clear primitives and effects sharing priority 0, source of OTZ bounds for shift-zero models, actual 0xE100 packet allocation high-water mark/overflow detection, asset-based visual identities for priority tiers. CHD extraction still blocked in the current container, and no runtime trace, all-eight SHA-1 match or C conversion was performed.

**Next specific R1 pass:** investigate the low-priority sprite groups and model +11/+10 resources against resource names/script producer paths; recover fill/clear packet insertion and whether the streaming backdrop can be obscured by a full-frame GPU clear on normal frames. A runtime validation should record ordering bucket maximum and packet work-buffer high-water mark without changing retail code.

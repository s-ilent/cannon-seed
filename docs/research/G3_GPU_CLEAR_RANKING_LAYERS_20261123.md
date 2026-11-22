# G3 GPU clear ownership and ranking-screen sprite layering

R1 pass 29, 2026-11-23. Pinned input: PR #10 branch `research/g3-laser-pool-20261122` at `f3f89307dc56e4656affa3340000b97fd8e54227`. Static study of tracked original EXEs and the retained JP ASM/SDK anchors. Continues [pass 28 OT/video atlas](G3_OT_VIDEO_LAYERING_20261123.md), [pass 27 metadata](G3_RESOURCE_RENDER_METADATA_20261122.md) and [FOBJ queue ownership](G3_FOBJ_SPRITE_PATH_20261122.md). **No runtime capture, compiler witness, CHD extraction, rendered-asset verification, or source-code landing.** Container still returns ClientError. Original EXE identities per pass 25, not newly independently hashed.

## Executive conclusions

1. **Normal scenario frame submission does not directly clear the display framebuffer.** In JP [frame renderer](../../asm/g3_jp/nonmatchings/func_80022AFC.s) `80022FE4..800232D0` there is no direct `GsSortClear` or `ClearImage`. The normal path inserts game HUD, font, FOBJ, 3D model and 3D-projected sprite packets, then swaps, uploads stream image with `LoadImage`/`DrawSync` and draws the OT. This matters: a native replacement must not insert an unconditional black clear between decoded video and game polygons. Indirect GPU commands and transparent/opaque full-viewport sprites are not ruled out by this negative.
2. **The game has a different black-background *static-image/transition* render path.** JP `8002FB20..8002FC68` calls `ClearImage` on full VRAM rectangle `(0,0,0x200,0x1E0)` with RGB 0, then (on the bounded s0<2 path) clears the active OT, sorts a prepared sprite at priority 0, VSyncs, swaps buffers, `GsSortClear(0,0,0,ot)` at `8002FC30`, and draws the OT. The clear packet is inserted at the *highest-index* OT tag, so it draws before the sprite at bucket 0. Two iterations of the inner swap/sort loop are bounded by `s2<2`. Do not equate this with the per-frame video path; no video `8002AC04` call occurs in this subroutine.
3. **Ranking-screen sprite tiers decoded.** The `0x1FB..0x204` ten-resource group (priority 12) is a decimal-digit glyph set, indexed by `0x1FB + digit` while rendering numeric fields. The `0x3FA..0x3FD` four-resource group (priority 14) is a four-column status/indicator set, selected by a 4-bit mask, paired with `0x3B2..0x3B5` (priority 0) in the same columns. **Both live in the named `SLAVE_RANKING` rendering path, system-mode index 8**; artwork identities remain unverified. These are *rank-screen elements*, not proof of generic scrolling background sprites.
4. The direct clear calls and three game-owned ranking windows have corresponding opcode/register skeletons in all **four** scenario executables.

## 1. Direct GPU clear call inventory

For each tracked original PS-X EXE: decode base64 bytes, skip `0x800` header, interpret little-endian MIPS words from load VA `0x80020000`; scan JALs starting `0x80022400` up to `0x80090000` or available decoded length; reconstruct absolute target, match exact target-scoped entries in [SDK anchors](../../config/sdk_anchors.txt). The scan may pass into non-code bytes near its upper bound, but the matched calls below are in recognized code. This inventory **does not count indirect jalr, indirect GPU commands, or raw packet producers**.

| Target | ClearImage direct sites | GsSortClear site | GsClearOt | GsDrawOt | LoadImage |
|---|---|---|---:|---:|---:|
| Dragoon JP | `8002262C`, `8002FB84` | `8002FC30` | 3 | 3 | 5 |
| Dragoon EU | `80022690`, `8002F814` | `8002F8C0` | 3 | 3 | 5 |
| Gourb JP | `80022FA4`, `8003097C` | `80030A28` | 3 | 3 | 5 |
| Gourb EU | `80022FBC`, `800305C4` | `80030670` | 3 | 3 | 5 |

`GsClearOt` itself **does not black-fill the framebuffer**; it clears/rebuilds CPU OT links through `ClearOTagR`. `ClearImage` is immediate VRAM transfer/clear, whereas `GsSortClear` makes a GPU packet added to the OT. Two direct `SetBlockFill` calls per executable are in SDK clear-packet initialization (JP `8004EF94/9C`), *not* game frame code.

The first JP `ClearImage` at `8002262C` also has immediate 512×480 rect and zero RGB arguments (`80022608..80022630`); it appears in early setup, before the normal renderer. Source ownership of the entire early boot function still requires carve/call-context adjudication; do not conflate it with the second call in the transition image renderer.

## 2. Exact transition path and clear packet ordering

See [JP scene ASM](../../asm/g3_jp/nonmatchings/func_8002A2DC.s):
- `8002FB20` is a real prologue; scanner `func_8002FBAC` at `8002FBAC` is **an interior loop**, not an independent function. Epilogue `8002FC4C..8002FC64`, next prologue `8002FC68`.
- `8002FB44` builds a 36-byte sprite template from `D_800773B0` through `8002F838` (the display is a prepared image/sprite; the actual artwork is not identified).
- `8002FB60..8002FB8C`: stack RECT `(x=0,y=0,w=512,h=480)`, `ClearImage(&rect,0,0,0)` then `DrawSync(0)`; optional `VSync(16)` when input s0=1.
- `8002FBAC..8002FC40`: per active buffer workbase reset, `GsClearOt(0,0)`, `GsSortSprite(&sp[0x10],ot,0)`, `VSync(0)`, `GsSwapDispBuff`, then `GsSortClear(0,0,0,ot)` and `GsDrawOt`. Loop runs two times; no `LoadImage` here.
- `GsSortClear` is SDK-owned [JP `8004EFC4..8004F12C`](../../asm/g3_jp/nonmatchings/func_8004EFC4.s). Sets RGB byte fields of a per-`PSDIDX` block-fill primitive (two 16-byte records at `D_80144978+16*PSDIDX`), updates rectangle fields from render globals, then calls `AddPrim(ot->tag, blockFill)` (`8004F10C..8004F118`). Thus the clear packet is prepended at **bucket 16383**, before sprite priority 0 in reverse DrawOTag execution. `SetBlockFill` is invoked on the two preallocated records by [SDK initialization `valiable_init`](../../asm/g3_jp/nonmatchings/func_8004ED48.s) at `8004EF94/9C`; preserving the shipped spelling is not asserting a symbol decompilation.
- This explains how a black screen/splash is generated **without modifying normal streamed-video compositing**. Only these observed subroutine behaviors are established; specific on-screen title/logo and execution frequency remain unproven.

Cross-target transition call sequence `JP 8002FC04..8002FC44` is 16 instructions with 16/16 opcode/register shape in every target (unique best aligned windows in narrowed transition ranges). Starts: JP `8002FC04`, EU `8002F894`, Gourb JP `800309FC`, Gourb EU `80030644`. Exact raw words relative to JP: 16, 11, 11, 11. Three neighboring call windows were matched separately in pass 28, so this confirms the distinct clearing entry point rather than merely matching one GsDrawOt call.

## 3. Proving rank-screen ownership of high-priority groups

The mode dispatcher [JP `80046304..80046424`](../../asm/g3_jp/nonmatchings/func_80044B4C.s) indexes `jtbl_8002158C` with `D_800AC044` (range 0..11). In the *original JP executable*, table entry **8** points to `800463C4`, which calls `8004709C`. That routine passes the original retained ASCII `SLAVE_RANKING` at `8002163C` to the existing text/path helper (`800470A4..800470B0`). No game-mode inference based only on neighboring labels is required.

### Rank columns

`8004710C` calls `func_800471FC` with a selected bitmask. That builder loops i=0..3, testing `a1 & (1 << i)`, with x = `-200 + 132*i`. For each set bit it calls `80047290` and `800472DC`. The first helper queues:
- resource `0x3B2+i` at (x,-25), **OT priority 0**;
- resource `0x3FA+i` at (x,+55), **OT priority 14**.

Both are direct calls to the six-byte FOBJ enqueue function `80044614`; queue staging and `GsSortSprite` take priority from the resource table. The two groups share each column's X but **not** its Y, so do not call them alpha-overlaid copies of one image. What the badges depict is unknown without TIM extraction. Model the four bits as four status columns, not four confirmed player IDs.

### Decimal digits

`800473BC..80047490` reads `D_800AC394`, divides the value by 100 and 10, then enqueues resources `0x1FB + (quotient/remainder)` as numeric glyphs around x=-38,-30,-22, y=-40; the special branch uses fixed `0x1FC,0x1FB,0x1FB` at the same row. `80047508..800475B0` similarly divides another field `D_800ABD9C` by 10, and emits three `0x1FB + digit` glyphs at varying x values. Therefore `0x1FB..0x204` are **numeric digit resources (0–9)**, not background scenes, as inferred independently from their contiguous IDs and the concrete decimal conversion code. These sprites have **priority 12**.

### Table witnesses and implications

In the original Dragoon JP 273-row texture catalogue at `80072FD4` (52-byte stride):
- `0x1FB..0x204`: 10 rows, **priority 12**, archive indices 160..169;
- `0x3FA..0x3FD`: four rows, **priority 14**, archive indices 171..174;
- `0x3B2..0x3B5`: four rows, **priority 0** (not priority 14).
Thus all are submitted via ordinary FOBJ sorting, but appear in different OT buckets. In reverse OT order, `14` draws before `12`, before `0`. They are composited **after** the streamed image in the normal frame path, regardless of being earlier among authored sprite tiers. The ranking screen may be visible in a different game state from mission footage; overlap of ranking and live video is not established.

## 4. Four-target static control-flow equivalence

Original loaded executable MIPS 32-bit words: compare bounded JP game-owned windows with normalized J/JAL, LUI, ADDIU and memory addressing fields masked **for search only**; unique full 100% structural best hits when scanning `80042000..80049000` (Gourb display block is earlier than Dragoon). Addresses/end-exclusive and exact-word counts:

| Bounded JP function window | Words | Dragoon EU start / exact | Gourb JP start / exact | Gourb EU start / exact |
|---|---:|---|---|---|
| `8004709C..8004712C` rank handler | 36 | `80046D04` / 25 | `80044538` / 19 | `80044158` / 19 |
| `800471FC..80047290` four columns | 37 | `80046E64` / 35 | `80044698` / 35 | `800442B8` / 35 |
| `800473BC..80047490` decimal glyphs | 53 | `80047024` / 46 | `80044858` / 45 | `80044478` / 45 |

Total 126/126 normalized instructions in all three siblings. Raw equal words: Dragoon EU 106/126, Gourb JP 99/126, Gourb EU 99/126. These three windows are **not full four-function semantic equivalence proofs**, and the exact runtime table values/asset matches of Gourb require their own data inspection. Their instruction skeletons, two APIs and compiler idioms are compelling enough to treat them as corresponding bounded code. Earlier restricted search of `80046000..` alone would miss Gourb and must not be used to claim the ranking path is absent!

## Preservation implications and next run

- Native GPU pipeline should keep normal **video upload → OT drawing** sequencing. Avoid introducing a per-frame ClearImage/black background that erases streamed pixels.
- Provide a separate black-screen transition/splash routine using a **bucket-16383 fill packet** and lower-priority sprite. This is **not** the same operation as `GsClearOt`, which only clears OT tags.
- Group rank-screen resource keys by their FOBJ producer: digit tiles `0x1FB+digit`, four rank-status `0x3FA+i`, companion `0x3B2+i`; preserve OT tier ordering. No art-name guess until decoded TIM evidence.
- **Next bounded pass:** explore rank status state `D_80170394`, score/progress writer `D_800AC394`/`D_800ABD9C`, and whether name/score arrays tie to player channels. Or study runtime OTZ bounds and packet buffer cursor if a runnable emulator/oracle becomes available. CHD extraction remains separately blocked; no video/assets should be committed.

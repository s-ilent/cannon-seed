# G3 FOBJ command queue → sprite sorting and slave-system display atlas

**R1 pass 4, 2026-11-22.** Bounded JP-first static analysis of tracked MIPS/data, compared against EU. **Source-only:** no retail image, fresh ELF/ROM oracle, live capture, C conversion, symbol rename, or history rewrite.

Prior work: [G3 HUD/font and frame loop](G3_HUD_QUEUE_FRAME_LOOP_20261122.md) and [main-game sequence dispatcher](G3_MODE_SEQUENCE_ATLAS_20261122.md).

## Findings and corrected object hypothesis

We now have a **complete direct 2D render path**:

```text
Main frame loop: func_800444B0()                       reset independent FONT and FOBJ
  → MAIN_SEQUENCE game-state processing
  → func_80022FE4()                                     submit frame
      → func_80046304()                                 12-way slave/system-mode dispatch
          → e.g. func_80046E48() / SLAVE_MISSION
              → func_80046EA8(), func_80046EF0()
                  → func_80044614(resource, x, y)       FOBJ append
      → accepted = func_8002E894()                      resource → GsSPRITE staging
      → func_8002F200(active_ot)                        separate HUD sprite
      → func_8002F660(active_ot)                        separate FONT queue
      → func_8002EF14(active_ot, accepted)
          → GsSortSprite(sprite, active_ot, priority)
      → ... GsDrawOt(active_ot)
```

**FOBJ is a 2D sprite command queue, not a 3D mesh/object queue.** The original strings `SLAVE_MISSION`, `SLAVE_TITLE` etc. name the game's system-mode display handlers. Neither direct `MAIN_SEQUENCE` helper investigated below is itself a proven polygon submitter. The actual 3D geometry path is still open.

## 1. Separate queue ABI and allocation boundary

Relevant [JP control ASM](../../asm/g3_jp/nonmatchings/func_80033C44.s), [EU control ASM](../../asm/g3_eu/nonmatchings/func_800338AC.s) and [JP literal data](../../asm/g3_jp/nonmatchings/data/data_80020000.data.s):

| Item | JP | EU | Observed |
| --- | --- | --- | --- |
| Reset | `800444B0..8004450C` | `80044118..80044174` | `sh 0,0x798($gp)`; FOBJ cursor to fixed base; independent `FONT` count at GP+0x79A reset |
| FOBJ append | `80044614..80044690` | `8004427C..800442F8` | signed count tested `< 100`; on overflow prints **Over flow FOBJ packet!** |
| Count getter | `80044690..8004469C` | `800442F8..80044304` | signed halfword GP+0x798 |
| Base getter | `8004469C..800446AC` | `80044304..80044314` | JP `D_8014419C` / EU `D_80144A84` |
| Next FONT base | `D_801443F4` | `D_80144CDC` | both FOBJ-to-FONT base differences **0x258 = 600 bytes = 100 × 6** |

The append routine stores the first, second and third arguments as halfwords at offsets `+0,+2,+4` and advances the cursor by exactly **6**. If the **signed 16-bit first argument is negative**, it is replaced with zero before storage (`8004461C..80044628`). No x/y clamping is seen in this bounded append body.

**Proposed semantic ABI, not source code committed:**

```c
typedef struct {
    uint16_t sprite_resource_key; // negative input clamped to zero on append
    int16_t x;
    int16_t y;
} FObjSpriteCommand32; // 6 bytes
```

The `FONT` queue documented in pass 2 is different: 10 entries × 8 bytes `{text pointer, x, y}`. Both are reset once at the start of the current frame iteration.

## 2. Consumer: six-byte record → 40-byte sprite staging

[JP scene ASM](../../asm/g3_jp/nonmatchings/func_8002A2DC.s), `func_8002E894..0x8002E9F4`; [EU scene ASM](../../asm/g3_eu/nonmatchings/func_8002A2CC.s), `func_8002E664..0x8002E7C4`.

- JP `8002E8BC` calls `func_80044690` (queued count); `8002E8C4` calls `func_8004469C` (base).
- JP `8002E8E4/8002E8E8` reads signed key at **command +0** and calls `func_8002F3D4(key, &priority)`. The `-1` result skips the command.
- JP `8002E908..8002E93C`: copies **36 bytes** of resolved `GsSPRITE` template to `D_80142A24 + accepted * 0x28`.
- JP `8002E940..8002E964`: moves command **+2 → copied sprite +4 (x)**; command **+4 → copied sprite +6 (y)**; writes the lookup output **OT priority** into staging record offset `+0x24`.
- An additional conditional at JP `8002E960..8002E9A4` adjusts x by **±18** if `D_800AC044` equals 2 or 7 and `func_80025944(1)` returns 1. It is not unconditional.
- Every consumed source command advances **+6**; only successful template lookups advance the destination **+0x28** and accepted count. Return `v0` is the **accepted** count, not necessarily the total queued count.

The natural staged ABI is **`{ GsSPRITE sprite; uint32_t ot_priority; }`**, size `0x24+4=0x28`. This stride is proven; the entire staging allocation bound is not yet proven.

### Direct GPU sorter witness

JP `func_8002EF14..0x8002EF84` (EU `func_8002ECE4..0x8002ED54`) iterates accepted sprites with `0x28` stride. At **JP `0x8002EF54` / EU `0x8002ED24`**, it calls anchored Psy-Q **`GsSortSprite`** with sprite pointer as `a0`, the active **`GsOT*`** as `a1`, and the 32-bit priority loaded from sprite staging `+0x24` as `a2`.

The caller in [JP graphics ASM](../../asm/g3_jp/nonmatchings/func_80022AFC.s) confirms staging at `0x8002300C`, return count saved at `0x80023020`, and sorting at `0x8002307C`, with FONT and first HUD sprite functions between these calls. All occur inside `func_80022FE4`, called from the known game frame loop at `0x80042D18`.

[EU graphics ASM](../../asm/g3_eu/nonmatchings/func_80022B5C.s) has the corresponding sequence starting `0x80023044`, with `func_80045F6C` system dispatch, `func_8002E664` staging and `func_8002ECE4` sorting. **Same-frame sequencing is supported by control flow, not a captured runtime trace.**

## 3. A concrete producer, with named game-owned state

JP `func_80046304..0x80046424` in [large control/overlay ASM](../../asm/g3_jp/nonmatchings/func_80044B4C.s) dispatches on unsigned-byte **`D_800AC044`**, with an unsigned bound **0..11**, via **`jtbl_8002158C`**. The out-of-range branch prints the shipped literal **`Invalid system_mode = 0x%x (in slave)`**. This is a **separate 12-entry table**, *not* the eight-entry sequence controller `D_8008AF1C`.

The nearby [retained strings](../../asm/g3_jp/nonmatchings/data/data_80020000.data.s) and diagnostic call sites identify: `SLAVE_CLR_MSG_BOARD`, `SLAVE_WINDOW_MGR`, `SLAVE_ENTRY`, `SLAVE_TAKEOFF`, `SLAVE_DEPATURE` (original misspelling), `SLAVE_MISSION`, `SLAVE_TITLE`, `SLAVE_GAMEOVER`, `SLAVE_RANKING`, and `SLAVE_ENDING`. These are shipped diagnostic labels, **not proven on-screen captions**.

**Direct path for system mode 5:**

- `0x80046394` calls `func_80046E48` (diagnostic label `SLAVE_MISSION`).
- It tests signed `D_800AC3C4` for nonzero before calling `func_80046EA8` and again before calling `func_80046EF0`.
- These two functions in [JP display ASM](../../asm/g3_jp/nonmatchings/func_80046C30.s) call **`func_80044614` directly** with literal resource keys and screen coordinates:

| Call site | Key | X | Y |
| --- | ---: | ---: | ---: |
| `80046EB8` | `0x3DC` | -50 | 0 |
| `80046EC8` | `0x3DD` | -10 | 0 |
| `80046ED8` | `0x3DF` | -10 | 20 |
| `80046F00` | `0x3E8` | 10 | 0 |
| `80046F10` | `0x3E9` | 50 | 0 |
| `80046F20` | `0x3E0` | 10 | 20 |

This yields a fully connected **system mode → sprite-ID enqueue → template resolution → GsSortSprite → GsOT** chain. Asset art/meaning for these numeric IDs is **not** established.

There is a second source path in `func_80046830..0x80046954` (JP control/overlay ASM). It enqueues a **FONT** string via `func_800446AC(text,x,40)` at `800468EC` and a **FOBJ** command at `8004690C` (plus a conditional second FOBJ at `80046934`). The first FOBJ key is **-1**, therefore appended as **0** due to the established negative-key clamp. It demonstrates mixed 2D text/sprite generation, not a shared queue.

**Scanner pitfall:** `func_800468FC` and `func_8004693C` labels are **interior** blocks of `func_800467E8/80046830` control flow, not independent functions just because spimdisasm emitted labels. Trace the earlier prologue and actual epilogue before converting C.

## 4. The two MAIN_SEQUENCE helpers, reclassified

The main controller calls both directly, but **they do not directly enqueue FOBJ or sort OT sprites**:

- **`func_80044F60..0x80045054`** (EU `0x80044BC8..`): conditional on **`D_800AC3C4 & 0x20`**, reads a 16-bit stream through `D_800ABE14`. Signed -1 terminates; a positive operation calls `func_80045088`; negative high-bit operations consume three further signed 16-bit operands and call `func_800450F4`. Under `D_800ABF9C==1`, operation IDs **12–15** are skipped. Stream cursor is stored back at `0x8004503C`. Both downstream routines eventually use guarded `func_8002FA9C`. **Gated script/command consumption, not established 3D drawing.**
- **`func_80044B7C`** (EU `func_800447E4`): inspects the `D_800AC17C` bitmask; processes **four** `0x8C`-stride records starting `D_801474FC`; uses word offset `+0x34`; sorts an intermediate four-entry, eight-byte-per-entry record list at `D_80144714` using adjacent comparisons/swaps; and writes selected state/visibility fields at `D_80170394` and source-record `+0x38`. **Four-record sorting and derived-state preparation, not direct GPU primitive sorting.**

Both source functions belong to game-owned state logic. The separate `SLAVE_*` dispatcher explains actual 2D FOBJ generation in the frame submission step; do not infer 3D mesh ownership from the `FOBJ` name.

## 5. JP/EU static equivalence — exact bounded windows

The following were compared against full committed source texts using the same little-endian MIPS decoding, J-type target masking and opcode/register shape rules as [`tools/compare_asm_windows.py`](../../tools/compare_asm_windows.py). All covered instruction positions exist. **All shape comparisons agree**, with regional/address immediates accounting for word differences.

| JP start | EU start | Instructions | Identical words | Shape matches |
| --- | --- | ---: | ---: | ---: |
| `80044614` | `8004427C` (FOBJ append) | 31 | 26 | **31/31** |
| `80044690` | `800442F8` (getters) | 7 | 6 | **7/7** |
| `800468FC` | `80046564` (interior producer window) | 16 | 13 | **16/16** |
| `8002E894` | `8002E664` (consumer preparation) | 88 | 81 | **88/88** |
| `8002EF14` | `8002ECE4` (sprite sorting) | 28 | 26 | **28/28** |
| `80022FE4` | `80023044` (submission prefix) | 26 | 16 | **26/26** |
| `80044B7C` | `800447E4` (ranking window) | 108 | 97 | **108/108** |
| `80044F60` | `80044BC8` (command stream) | 61 | 53 | **61/61** |

Example reproducible checks:

```sh
python3 tools/compare_asm_windows.py \
  --left asm/g3_jp/nonmatchings/func_8002A2DC.s \
  --left-start 0x8002E894 --left-end 0x8002E9F4 \
  --right asm/g3_eu/nonmatchings/func_8002A2CC.s \
  --right-start 0x8002E664 --require-shape

python3 tools/compare_asm_windows.py \
  --left asm/g3_jp/nonmatchings/func_80033C44.s \
  --left-start 0x80044614 --left-end 0x80044690 \
  --right asm/g3_eu/nonmatchings/func_800338AC.s \
  --right-start 0x8004427C --require-shape
```

**No claim of retail match, executed test, or complete function identity** is implied by source-only shape matching. Function ownership remains game-code for these queue and display routines; `GsSortSprite` itself is the previously SDK-identified Psy-Q library callee.

## 6. Next bounded R1 question

**Find the actual 3D/world geometry producer and its OT sorter.** Examine other draw stages (`func_8002E9F4`, `func_8002EC7C`) and their coordinate/matrix/TMD inputs; prove one game-owned 3D object or polygon → GPU ordering-table edge rather than assuming `FOBJ` means 3D. The FOBJ 2D path is now mapped; do not repeat it as a new discovery.

Still open: exact staged-array allocation bounds, resource key `0x707`, the `0x3DC`-family sprite assets, 0xE100 packet workbase allocation, and retail/runtime oracle-gated verification. No game C/ASM/YAML, toolchain files, SDK members or history changed in this pass.

# G3 projected-sprite request path: object type 0x31 to GsSortSprite

**R1 pass 10 — 2026-11-23.** Read-only JP static call/data-flow reconstruction with exact EU instruction-window corroboration. Continues [G3 producer records](G3_PRODUCER_RECORDS_20261122.md) pass 9 and [Communication Buffer schema](G3_COMM_BUFFER_SCHEMA_20261122.md). Source surfaces: tracked `asm/g3_jp/nonmatchings/func_8002A2DC.s` and `asm/g3_eu/nonmatchings/func_8002A2CC.s`. **No executable execution or new retail SHA-1 oracle, no CHD read, no gameplay C edits, no SDK attribution or renaming, no rebuild or coverage claim.**

## Result

The type-`0x31` object's phase-selected sprite resource id is sent through the same **0x18-byte per-frame Communication Buffer** established in pass 6. Its `+0x26` field chooses a **type-4** or **type-5** request. The two request types contain *identical stored fields* but the renderer converts their 3D positions differently. Both feed the same resource-table lookup and 0x7C-byte projected-sprite staging builder, eventually ending at `GsSortSprite` in the renderer. This is the producer-to-renderer link that pass 9 left open.

```text
object 0x31 handler func_80037D58
  +0x30 = lhu(obj+0x10) + (phase >> 4)
  +0x26 == 0 -> func_80031EC0(obj) -> func_80031F60(obj, 4)
  +0x26 != 0 -> func_80031F40(obj) -> func_80031F60(obj, 5)
   -> Communication Buffer [0x18 request]
   -> func_8002DFD8
       type 4: func_8002E640 (world 32-bit position minus camera triple)
       type 5: func_8002E6A8 (signed upper-halfword positions)
          -> func_8002E770 (0x34-row sprite resource lookup)
          -> 0x7C projected sprite record in D_8013F9B4
   -> func_8002EC7C -> perspective/clip/size -> GsSortSprite
```

## 1. The producer request is byte-specific

JP wrapper `func_80031EC0` at `0x80031EC8` calls `func_80031F60` with `a1=4`; wrapper `func_80031F40` at `0x80031F48` uses `a1=5`. Both wrappers are eight instructions long. The core `func_80031F60` checks `lh(D_800AC29C) != 0`, then `lh(D_800AC014) < 0x2F4` (756); otherwise it prints the established Communication Buffer overflow string. Its writer `func_80031FA8` stores:

| Request offset | Value from object | Exact JP write |
| --- | --- | --- |
| `+0x00` | type parameter `4` or `5` | `80031FB4 sh a1,0(v1)` |
| `+0x02` | `lhu(obj+0x30)` — phase-selected resource id | `80031FC0` |
| `+0x04/+0x08/+0x0C` | `lw(obj+0x04/+0x08/+0x0C)` | `80031FCC/31FD8/31FE4` |
| `+0x10` | `lhu(obj+0x12)` | `80031FF0` |
| `+0x12` | `lhu(obj+0x14)` | `80031FFC` |
| `+0x14` | `lhu(obj+0x16)` | `80032020` (register loaded `80032000`) |
| `+0x16` | literal zero | `8003201C` |

The same writer increments `D_800AC014` and advances `D_800AC2CC` by `0x18` at `0x80032008..0x80032018`. Note the **resource-base/object field distinction**: type-0x31's template `+0x10` supplies the *base for phase-derived `obj+0x30`*, but request `+0x10` comes from **object `+0x12`**, not `+0x10`. This is per-type field overloading; pass 8's general trig labels must not be applied blindly to 0x31.

## 2. Type 4 vs 5: different position interpretation

Both constructors write request type to the 0x7C output record at `+0x0` and pass request `+0x2` (resource id), three position components and the record to `func_8002E770`.

| Property | Type 4 — JP `func_8002E640` | Type 5 — JP `func_8002E6A8` |
| --- | --- | --- |
| Input position | 32-bit `lw(req+4/8/C)` | signed `lh(req+6/A/E)` (the upper halves of the stored position words) |
| Camera compensation | subtract 32-bit `D_8016AC18/1C/20` from each component | **none inside this constructor** |
| Common resource/build call | `func_8002E770(rec, req+2, x,y,z)` | same |
| JP first VA | `0x8002E640` | `0x8002E6A8` |
| EU first VA | `0x8002E410` | `0x8002E478` |

These are *verified register data flows*. A high-half/Q16 representation is **plausible**, but the constructors alone do not prove the world-space unit or explain which object categories select each path; `obj+0x26` is the direct choice for 0x31.

## 3. Projected-sprite record and texture resource

At JP `func_8002E770` (`0x8002E770..0x8002E894`), `func_8002F3D4(id, &out)` reads the **second 0x34-row resource table** `D_800ABBEC`: row id `+0x0`, output word `+0xC`, and return pointer `row+0x10`. A lookup miss returns `-1`, which the builder returns as **failure 0**; accepted rows are staged as follows:

| Projected record | Write/reader | Interpretation |
| --- | --- | --- |
| `+0x00` | request type | retained type |
| `+0x04..+0x27` | **0x24 bytes** copied from returned resource pointer (`0x8002E7F4..0x8002E828`); later `GsSortSprite(rec+4,...)` | **GsSPRITE-compatible 36-byte template** |
| `+0x28` | second-table `row+0xC` output; later `lw(rec+0x28)` passed as the third argument to `GsSortSprite` | OT sort parameter (not the phase-derived resource id) |
| `+0x2C...` | `GsInitCoordinate2(0, rec+0x2C)`; `func_80047DA0` transforms incoming 3D position into translation words at `+0x44/+0x48/+0x4C` (middle negated) | embedded coordinate and matrix state; exact semantic name pending SDK type check |

The later projected-sprite loop `func_8002EC7C` walks exactly **0x7C bytes per entry**. It calls `GsGetLs(rec+0x2C,...)`, performs a transform/projection and culls out-of-bounds or nonpositive-depth results; accepted sprites have projected x/y written to `rec+0x08/+0x0A`, scaled w/h to `rec+0x20/+0x22`, then `GsSortSprite(rec+0x04, active_OT, lw(rec+0x28))` at **JP `0x8002EED0`** (EU counterpart **`0x8002ECA0`**). In other words, this shared record is neither a TMD/mesh nor the independent FOBJ overlay queue.

### A newly identified dead-on-this-path arm: request type 7

Pass 6 listed type `7` as a projected candidate because the 15-way dispatcher calls `func_8002E6EC`, which indeed does preparatory conversion through `func_800326A8` and then calls `func_8002E770`. But `func_8002E770` contains an explicit check **`lh(rec+0) == 7` → return 0** at `0x8002E7BC..0x8002E7D0` (after successful resource lookup, before any template initialization). On lookup failure it already returns 0. Thus **type 7 cannot result in an accepted 0x7C staging record through this constructor**, even though a switch arm exists. This revises the earlier table's *effective outcome*; it is not proof that type 7 is unused elsewhere, nor proof of why it was disabled.

## 4. Cross-region measurement

Direct comparisons of the tracked instruction words (no live executable oracle) gave:

| Window | JP → EU | Instructions | Identical 32-bit words |
| --- | --- | ---: | ---: |
| Type-4 wrapper | `31EC0 → 31B28` | 8 / 8 | 7 |
| Type-5 wrapper | `31F40 → 31BA8` | 8 / 8 | 7 |
| Shared producer `31F60` | `31F60 → 31BC8` | 53 / 53 | 45 |
| Writer tail `31FA8` (overlaps producer) | `31FA8 → 31C10` | 31 / 31 | 28 |
| Type-4 constructor | `2E640 → 2E410` | 26 / 26 | 22 |
| Type-5 constructor | `2E6A8 → 2E478` | 17 / 17 | 16 |
| Common builder `2E770` | `2E770 → 2E540` | 73 / 73 | 69 |

The differing instructions in the inspected windows are cross-region branch/call address and global-relocation differences; aligned code order and immediate/field operations agree. The type-7 explicit-rejection branch is present in the EU common-builder twin as well. This is **structural corroboration, not a new eight-target binary build or full-function identity proof**.

## 5. Consequences and next checks

1. The source of per-frame graphics requests from **type 0x31 is proven end-to-end**: template/phase → render-resource id → type 4/5 → temporary descriptor → 0x7C staging → hardware sprite OT. This is a good semantic-C candidate on the **producer side** once the repository's owner/provenance gates allow it.
2. Resource `D_800ABBEC` (the second table) must be treated as a real separate dependency from `D_800ABBE4` (TMD table); the earlier table-population negative and its runtime trace remain open. **Do not infer** a stable lookup mapping without initialization evidence.
3. **Next bounded question:** determine where object `+0x26` is assigned for the 0x31 chain, and whether it labels coordinate-space modes rather than distinct gameplay types. Follow `func_80037E0C`/`func_80037E38` and clone/definition updates, then investigate one additional active handler that emits type 0–3 or 4–5. Runtime PCSX-Redux watchpoints on the resource-table setter/global remain the definitive separate experiment.
4. Keep `src/func_80052038.c`, generated `asm/`, SDK attribution and all coverage/retail-match claims unchanged.

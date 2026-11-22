# G3 gunner participation masks and credited terminal-event counter

**R1 pass 31 — 2026-11-23.** Continues [pass 30, four-gunner results and mission counters](G3_GUNNER_RESULTS_RANKING_20261123.md), [pass 22, effective player count](G3_PLAYER_COUNT_SCALING_20261122.md), [pass 20 Doldva](G3_DOLDVA_REACTOR_20261122.md), and [pass 21 SPARKBIT](G3_SPARKBIT_FINAL_OBJECTIVE_20261122.md). Baseline: `research/g3-laser-pool-20261122` at `bea652d5e9386c870bd7bcdad5a9d9857780b6aa`. **Static source-only read of tracked JP and EU assembly and data; no fresh executable SHA-1/hash oracle, build, runtime capture, asset inspection, or C/ASM/YAML edits.** The phrase *credited terminal event* below is a research label, not a recovered UI string.

## Executive result

1. **The masks are successive phases of the same participation state.** Live `D_800AC17C` (JP 32-bit bitset, four local gunner slots) is built during entry and used by hit/laser/score/ranking logic. `D_800AC2F4` (16-bit) is its *low-halfword snapshot*, stored in the results-transfer routine `func_80044514`; it is the display selector for the four `SLAVE_RANKING` columns. It is **not** an independently evolving second player configuration. Its freezing preserves columns even if live state subsequently resets.
2. **The global `D_800AC08C` is not an all-objects-processed or all-objects-despawned counter.** Five direct increment sites count qualified *fatal/terminal transitions* in ordinary object types and **two special objective-success events**. One increment site is shared by three active object types; some non-counted despawns clear their type without incrementing. Its results-screen value is a 16-bit snapshot, rendered in decimal and locally capped at 9999. Calling the exact displayed metric “enemies destroyed” remains an unproven artwork/label interpretation.
3. The eight checked JP/EU source windows agree in instruction **opcode/register shape 352/352**, including both mask and four of the five counter sites plus shared helpers (256/352 identical full instruction words). This is paired static source agreement, **not** a new retail rebuild or runtime witness.

## 1. Live mask producer, snapshot, and consumers

| Step | Japanese VA | Proven effect |
| --- | --- | --- |
| Entry start | `80042F50` in `func_80042F18` | `sw zero,D_800AC17C`; simultaneously clears `D_800AC164` effective count at `80042F58` |
| Gunner admitted | `800436C0..800436D8` in `func_80043604` | `D_800AC17C |= (1 << slot)`; source gunner +0x44 receives 1 and +0x46 receives 14 on this path |
| Special path | `80042FC8..80043028` | `func_80045B9C()` == 3 branch sets effective count `D_800AC164=2` and ORs `0x9` into live mask: **slots 0 and 3**. Exact context/meaning of return 3 unknown; **not** proof of a named two-player mode |
| Gunner entry progression | `func_800436F4` | Delayed update of `D_800AC164` after gunner +0x46 countdown/phase transition; effective count can temporarily lag mask |
| Results snapshot | `80044560` → `800445DC` in `func_80044514` | `lhu t3,D_800AC17C; sh t3,D_800AC2F4`; called at `80042CB0` |
| Ranking column reader | `800470F0` → `8004710C`, then `func_800471FC` | Selects four columns using each bit of frozen mask; column i positions are `x=-200+132*i`; previous atlas confirms resources `0x3B2+i` and `0x3FA+i`, as well as per-gunner score |
| Other frozen-mask reader | `80047894..800478A0` | Bitwise gates rank-related icon column for each gunner |
| Reset | `80044810/80044818` in `func_80044738` | Clears live 32-bit and frozen 16-bit mask separately |

`D_800AC17C` additionally guards per-gunner score allocation (`80034E68` → `func_80034D94`), laser participation (`8003F4B8`), and four-gunner rank selection (`80044B94`, `80044CE0`). The two bits/count concepts **must not** be conflated with a six-person scene: `D_800AC164` can be overridden independently to 1..6 via the gameinfo path proved in pass 22, without creating more than four actual gunner record slots.

**Negative result:** In the examined original game ASM, frozen `D_800AC2F4` has one nonzero-capable writer (the snapshot) and one zeroing writer (reset). Its rank-display role is a **copy** of the live mask, not a separately authored four-bit rule. This is an ASM xref conclusion, not a blind memory write completeness proof against arbitrary runtime-computed stores.

## 2. Five count increments are qualified terminal transitions

JP `D_800AC08C` is read as `lhu`, incremented by `addiu 1`, stored as `sh`. Every listed site increments once per **execution of that terminal branch**, not per enemy hit. The `u16` store can wrap; no saturation at the producer sites.

| Increment store JP | Dispatch owner / ingress | Proven branch and effect | Confidence |
| --- | --- | --- | --- |
| `80030B44` | type `0x50` → `func_8003098C` | `80030A6C`: signed durability `obj+0x2E < 0` takes `80030B0C`; zeroes velocity `+0x38..+0x40`, calls event `func_80045128`, retypes `obj+0` to **`0x29`**, clears collision `+0x28`, increments, emits object descriptor via `func_80031C5C` | High |
| `8003379C` | shared `func_800336E0` used by types `0x60` (`80033F64`), `0x20` (`8003725C`), `0x68` (`80038F18`) | All three callers reach the helper from a negative `obj+0x2E` fatal state; integrates position, calls `func_80045128`, sets `+0x6C=0, +0x6E=1, +0x70=5, +0x84=3`, retypes to **`0x29`**, clears collision, increments, then `func_800337B8` | High |
| `8003A050` | type `0x81` → `func_80039CC4` | Fatal routes `8003A180` and `8003A324` branch to `8003A008` when `obj+0x2E < 0`; clears linked object back-link `+0x64`, increments linked object +0x8A, calls `func_8003D87C` and event `func_80045128`, increments, initializes emitter via `func_80037E0C`, retypes to **`0x31`** and runs `func_80037D58` | High |
| `8003B8A0` | type `0x89` final objective, `func_8003B868` | Reached from `8003B028` only after parent remaining-child count `+0x84 == 0` with signed countdown `D_800AC01C > 0`; writes victory signal `D_800AC144=-1`, calls per-gunner award `func_80034E0C(3)`, increments, launches completion effect `func_8003BF1C`, advances parent phase | High |
| `8003CAB8` | type `0x80` Doldva reactor, `func_8003CA54` | Reached `8003C994` after completed damage stage `obj+0x8E >= cfg+0xC0` and **before** `D_800ABFA4 < obj+0x92` deadline; writes reactor success `D_800AC584=-1`, calls per-gunner award `func_80034E0C(2)`, selects cfg event, increments, launches `func_8003CADC`, clears parent type | High |

**Important counterexamples to “objects processed” and “every object destroyed”:** `8003B854` clears type on an ordinary object boundary without increment; `8003B8E8` and `8003B8F8` clear type for another state without increment; numerous other animation/effect and default-kill paths also clear type without the global increment. The two named final-objective sites increment upon success states, not a general zero-health kill site. There is no invariant in the inspected code that each spawn/despawn maps one-to-one to this global. Five **stores** are not five **object classes**: the shared fatal helper admits at least three.

Event helper `func_80045128` is *not* the score award: its body gates on `D_800AC3C4 & 0x20` and conditionally calls `func_8002FA9C`. By contrast, `func_80034E0C` selects an award from `D_80089FAC[7*class+D_800AC164]` and loops `D_800AC17C` to invoke `func_80034D94` for participating gunners. This keeps **gunner score** and the **global count** distinct.

### Reset, snapshot, and display

- **Live resets:** `800447C4` and `8004496C` clear `D_800AC08C` during two initialisation paths; these are not frame-local resets.
- **Transfer:** `80044588` reads the live count and `80044604` stores its 16-bit value in `D_800ABD9C` in the same results snapshot that freezes the gunner mask.
- **Display:** `func_80047508` reads `D_800ABD9C`, locally caps the value at **9999**, splits digits and queues decimal glyph IDs `0x1FB+digit`. Local display clamping is **not** producer-side saturation.
- **Interpretation:** a **credited destruction / objective-completion event count** is the narrow evidence-based description. Exact screen caption, inclusion of unsampled execution paths, and whether the game visually calls this “destroyed enemies” are not yet verified.

## 3. JP–EU source-level comparison

The tracked JP source in `asm/g3_jp/nonmatchings/func_8002A2DC.s` and `func_80033C44.s` was compared with EU counterparts `func_8002A2CC.s` and `func_800338AC.s`. Alignment is exactly `EU VA = JP VA - 0x398` **in these measured windows**, not globally. Instruction words are little-endian text fields; *shape* requires identical opcode/register fields, ignoring address-dependent J/JAL target bits and I-format immediate fields. This is deliberately a more permissive structural check than byte-for-byte identity.

| JP start | EU start | Instructions | Identical 32-bit words | Matching shapes |
| --- | --- | ---: | ---: | ---: |
| `80042F18` | `80042B80` | 74 | 45 | 74 |
| `80043604` | `8004326C` | 56 | 48 | 56 |
| `80044514` | `8004417C` | 64 | 35 | 64 |
| `8003B868` | `8003B4D0` | 26 | 20 | 26 |
| `8003CA54` | `8003C6BC` | 34 | 27 | 34 |
| `8003A008` | `80039C70` | 27 | 20 | 27 |
| `800336E0` | `80033348` | 54 | 48 | 54 |
| `80030B0C` | `80030774` | 17 | 13 | 17 |
| **Total** | | **352** | **256** | **352** |

EU alias map from same windows: live participation `D_800AC9CC`, frozen participation `D_800ACB44`, live count `D_800AC8DC`. These should not be substituted as JP addresses.

## 4. Next bounded questions and limitations

1. **Exact visual meaning:** identify the ranking screen's counter label and four-column indicators from TIM/STR resources or a controlled PCSX-Redux rank-screen trace. Until then, keep *credited terminal-event counter* as an evidence-qualified term rather than a canonical game string.
2. **Boundary/negative test:** trace non-counted death/timeouts vs the five credited terminal classes; determine whether all expected scenario-wide success and generic kill paths participate, whether alternative state branches bypass counting, and whether the results screen ever snapshots before the last terminal event.
3. **Verification gate:** rerun retail-image hashes and (if appropriate) runtime watchpoints with a functioning private game oracle before making byte-match or displayed-label claims. No changes to game source, generated ASM, segmentation, symbols, SDK attribution, or owner-gated naming rows in this pass.

# G3 terminal-event counter exclusions and the Doldva timing-gate correction

**R1 pass 32 — 2026-11-23.** Continues [pass 31 participation / terminal-counter producers](G3_GUNNER_PARTICIPATION_TERMINAL_COUNTER_20261123.md), [pass 20 Doldva](G3_DOLDVA_REACTOR_20261122.md), [pass 21 SPARKBIT](G3_SPARKBIT_FINAL_OBJECTIVE_20261122.md) and [pass 19 object census](G3_OBJECT_CENSUS_COMPOSITES_20261122.md). Research-base commit `a245cf4a7d8dd0f23f6ba8bcbbabb6b30d8cc849`. Sources: tracked original disassemblies `asm/g3_jp/nonmatchings/func_80033C44.s`, `asm/g3_eu/nonmatchings/func_800338AC.s` and previous source-linked findings. **Read-only game-code investigation; document corrections only, no CHD extraction, live gameplay trace, fresh retail hash, compiler build, executable or game-code modification.**

## Result

1. **A shared death/effect presentation does not imply inclusion in the global results counter.** The fatal `obj+0x2E < 0` branches of runtime object types **0x12, 0x13 and 0x14** convert to type **0x31**, run the emitter initializer `func_80037E0C` and emitter `func_80037D58`, but do not add to `D_800AC08C`. By contrast, type **0x81** fatal route `8003A008` also converts to type 0x31, and **does** add to the count at `8003A050`. Thus neither hit death nor the type-0x31 conversion alone is the statistic's inclusion rule.
2. **Five individually damageable SPARKBIT type-0x89 children do not contribute five global events.** A child's terminal damage stage reduces parent `+0x84` at `8003BBC8`, plays effects and converts the child to type 0x31 (`8003BDDC`); neither path contains a `D_800AC08C` increment. The count is incremented once at parent success `8003B8A0`, when parent `+0x84==0` and countdown `D_800AC01C>0`. Importantly, the separate child cancellation/removal branch (`8003BDF0..8003BE14`) also decreases parent `+0x84` without recording an individual kill; “remaining allocated children == 0” is **not** strictly identical to five successful shot-destroys if cancellation/allocation failures arise. Such unusual playthroughs are unobserved; this is a CFG possibility.
3. **Doldva success timing was inverted in pass 20 and repeated in pass 31.** The instruction pair `8003C988 slt v0,v0,v1` / `8003C98C bnez v0,8003C9A4` branches away from success when **current tick < obj+0x92 (3888)**. That branch decrements the achieved damage stage. `func_8003CA54` (the only type-0x80 count-incrementing success helper) is called only when **tick >= 3888** and the final required stage is reached. This is an **earliest-permitted completion gate**, not the last-chance cutoff described previously. The later 4096 stream transition is a separate changeover. Both JP and EU have the same comparison and branch polarity, with critical words **identical**.
4. **Expiration/scripted removal does not count.** Examples: type-0x13 and -0x14 negative lifespan branches clear `obj+0` at `8003DFC8` and `8003E218`, respectively; SPARKBIT's nonzero script-termination helper `8003B8F4` clears the parent type; the global SPARKBIT mission timeout at `80041B1C..80041B84` enters defeat/stage 10 without incrementing `D_800AC08C`. Other later counted branches, if they executed earlier, are unaffected by this negative.
5. **Additional shot-fatal exclusion:** the Doldva type-0x80 auxiliary fragment handler `8003D370`, reached via the type-0x80 phase dispatcher, also calls `func_80034C60` and on negative `+0x2E` morphs to type 0x31 (`8003D3A8`) with no count.

These facts rule out both **all object despawns** and **all damageable object kills** as exact definitions of `D_800AC08C`. It remains a **selectively credited fatal/objective terminal-event tally**, snapshotted for the result display at `80044588→80044604`. This is a semantic research label, not a recovered screen caption.

## A. Matched counted / uncounted fatal paths

| JP code, runtime type | Fatal predicate | Terminal action | Global `D_800AC08C` |
| --- | --- | --- | --- |
| `8003845C..800385AC`, 0x12 | nonzero hit mask `+0x2A`; after `func_80034C60`, signed `+0x2E<0` branches `80038478→80038594` | `sh 0x31,obj+0` at `80038598`, `func_80037E0C`, `func_80037D58` | **No** |
| `8003DDE8..8003DFBC`, 0x13 | `8003DDF8 bltz +0x2E` after shared hit routine | `8003DFA8` initializer; `8003DFB4 sh 0x31,obj+0` then emitter | **No** |
| `8003E080..8003E20C`, 0x14 | `8003E090 bltz +0x2E` after shared hit routine | `8003E1F8` initializer; `8003E204 sh 0x31,obj+0` then emitter | **No** |
| `8003D390..8003D3BC`, 0x80 auxiliary fragment phase | `8003D3A0` negative `+0x2E` after shared hit | `8003D3A8 sh 0x31,obj+0`, initialize and emit | **No** |
| `8003A15C/8003A314→8003A008`, 0x81 | negative `+0x2E` reached through its damage branches | linked-object accounting, emitter conversion `8003A060`, **one producer increment `8003A050`** | **Yes** |

The dispatch identifications for these types are from the 256-entry `D_8008A2F4` table established in [pass 12](G3_RETAIL_DISPATCH_TABLES_20261122.md), not inferred merely from adjacency. **Caveat:** Pass 19's mode-zero census gives **zero authored initial spawns** for 0x12/0x13/0x14 despite these real active handlers; they may be internally spawned objects or effects. It is safe to call them *damageable runtime object types*, **not** confirmed ordinary enemy models or player-visible enemy kills. Their uncounted fatal branches still refute “every damageable object death is credited.”

## B. SPARKBIT: an entire five-target objective counts once

- Five phase -1 children are created through `func_8003AE98` (pass 21); each has independent hit mask, health progression and stage, with parent link `child+0x64`. Only successful allocations increment the parent's outstanding count `parent+0x84`.
- Child threshold: `8003BA44` increments `child+0x8C`; `8003BA54` tests stage <3 and on reaching 3 branches to `8003BBB4`. `8003BBC4..8003BBC8` decrements the parent's 16-bit outstanding count, **without** touching `D_800AC08C`. Visual effects are produced; at `8003BDD0..8003BDE0` the child is initialized and retyped to 0x31.
- Separate cleanup/cancellation: `8003BDF0..8003BE14` clears an auxiliary, decrements the same `parent+0x84`, then clears the child type; no global event count. The path's prerequisites must be exercised at runtime to distinguish cancellation from ordinary failure. The negative result concerns the direct stores.
- Parent: `8003B010..8003B028` checks `parent+0x84==0` and `D_800AC01C>0`; `8003B868` sets the SPARKBIT objective success flag, invokes `func_80034E0C(3)` to award participating gunners, then increments `D_800AC08C` at `8003B8A0`. There is **one** parent increment, irrespective of how many children were removed.
- Timeout is a *different branch*: `func_80041AB0` first checks the success flag `D_800AC144` at `80041ACC`. If unset and the mission tick reaches 9988, `80041B1C..80041B84` sets negative mission condition, stage 10 (defeat), clears countdown and advances a separate counter `D_800ABF4C`, **not** `D_800AC08C`. `func_8003B8F4` clears an object type without touching the count.

The parent success flag and auxiliary visual completion flag are distinct (pass 21); a delayed particle or animation cleanup is not an additional counted kill.

## C. Doldva tick-gate polarity — explicit correction

The relevant **JP instruction words** are:

```asm
8003C960  lh    v1,0xC0(s1)         # required damage stage, 5 in authored config
8003C964  lh    v0,0x8E(s0)         # achieved stage
8003C96C  slt   v0,v0,v1            # achieved < required
8003C970  bnez  v0,8003C9B4        # not complete: continue scene
8003C97C  lhu   v0,D_800ABFA4      # current section tick
8003C980  lh    v1,0x92(s0)         # gate loaded from stream, 3888
8003C988  slt   v0,v0,v1            # current < gate
8003C98C  bnez  v0,8003C9A4        # if EARLY, decrement achieved stage
8003C994  jal   func_8003CA54      # if current >= gate, success
8003C9A4  lhu   v0,0x8E(s0)
8003C9AC  addiu v0,v0,-1
8003C9B0  sh    v0,0x8E(s0)
```

The EU twin at `8003C5C8..8003C618` has exactly the same `slt` / `bnez` decisions, with the region-specific timeline global `D_800AC7F4`. Correct semantically:

```c
if (achieved_stage >= required_stage) {
    if (current_section_tick < gate_3888)
        --achieved_stage;       /* prevent early completion */
    else
        complete_and_credit();  /* increments D_800AC08C once */
}
```

Reaching stage 5 early does not merely wait for 3888: it **reduces back to stage 4**, so the final stage must be earned again at/after the gate. At/after the separate second stream timestamp 4096, the regular phase3 path can transition to phase4 and cease processing this success branch; an actual frame at the boundary has not been traced. **Do not describe tick 3888 as the last chance to win.** Pass-20 prose and pass-31 summary were previously inverted; this pass corrects both.

## D. JP/EU corroboration

Compared tracked source instruction words, address-shifted `EU = JP - 0x398` *for these windows only*. `shape` compares opcode/register fields and masks immediate fields of I-type instructions and target of J/JAL. All ten listed sequences have full shape agreement; instruction-word identity is a stricter count. This does not establish full-function equivalence, exhaust runtime `jalr`, or constitute a retail hash/build test.

| JP window (exclusive) | EU start | Instructions | Identical words | Matching shapes |
| --- | --- | ---: | ---: | ---: |
| 38594..385B8 (0x12 fatal) | 381FC | 9 | 6 | 9 |
| 3DFA8..3DFC8 (0x13 fatal) | 3DC10 | 8 | 5 | 8 |
| 3E1F8..3E218 (0x14 fatal) | 3DE60 | 8 | 5 | 8 |
| 3D390..3D3C8 (type80 fragment fatal) | 3CFF8 | 14 | 10 | 14 |
| 3BBB4..3BBD8 (child count) | 3B81C | 9 | 8 | 9 |
| 3BDB8..3BDE8 (child morph) | 3BA20 | 12 | 10 | 12 |
| 3BDF0..3BE18 (child cancellation) | 3BA58 | 10 | 10 | 10 |
| 41B1C..41B88 (main timeout) | 41784 | 27 | 17 | 27 |
| 3C960..3C9B4 (Doldva gate) | 3C5C8 | 21 | 18 | 21 |
| 3A008..3A06C (0x81 fatal/count contrast) | 39C70 | 25 | 19 | 25 |
| **Total** | | **143** | **108** | **143** |

The comparison was computed from the two tracked generated source files. It is **source-level corroboration only** and does not independently witness original EXE SHA-1s or a running gameplay state.

## E. Next specific question

> **Pass-33 closure of this specific question:** [attack-child provenance](G3_ATTACK_CHILD_PROVENANCE_20261123.md) establishes the three zero-authored-initial-count runtime types are emitted by the attack dispatcher from type 0x68, 0x81 and SPARKBIT type 0x89 configurations. Their uncredited deaths are now understood as spawned attacks, rather than evidence that routine authored enemy deaths are not credited. The separate display-artwork question remains open.

Determine the **producer/origin and intended gameplay role** of the zero-authored-initial-count but damageable 0x12/0x13/0x14 types, then determine whether the results-screen artwork names the credited event count (or contains only a number). Their origin matters before arguing the count excludes ordinary “enemies.” For a runtime sanity experiment, watch `D_800AC08C`, `D_800AC144`, `parent+0x84` in SPARKBIT and the `3888/4096` gate in Doldva, recording whether all expected success/timeout states can reach the results snapshot. Keep private retail assets out of Git.

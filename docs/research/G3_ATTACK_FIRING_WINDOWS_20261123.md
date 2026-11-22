# G3 scripted attack windows, activation phases and cooldown tables

**R1 pass 36 — 2026-11-23.** Continues [pass 35 type-0x18 emitter lifetime provenance](G3_ATTACK_EMITTER_LIFETIMES_20261123.md) from prior branch HEAD `0006e5dbf363ab17290642157ed07ada8cff698f`. Static, bounded inspection of existing generated JP/EU assembly and data; **no new retail oracle**, runtime watchpoint, game visual/asset attribution, gameplay patch or C conversion. Scripts and rows are authored data, **not measured successful projectiles**.

## Finding

For the **12 authored mode-zero secondary encounters** with config `0x41` (type `0x70`), `0x51` (type `0x71`) and `0x52` (type `0x70`), the data contains two separate section-tick milestones: an **attack-enable time** and a **deadline**. **In every one of these events the enable time is before its scheduled spawn tick**; the gate is therefore eligible immediately following successful initialization, rather than only after another long wait. Method 5/6 emitters use a 6×7 table of per-attempt cooldown bases and a signed random adjustment. Two controller families take structurally different paths to the same shared 11-way dispatcher.

### 1. Authoritative mode-zero schedule / timer rewalk

Rewalked JP secondary lists in mode zero (first section begins at absolute tick 0) from `D_80078E14` and `D_80079A54`; the relevant **12** entries all belong to the **first** section. Each 8-byte event has `u16 tick` and a descriptor pointer at `+4`. Secondary descriptor `+2` selects config and `+0x18` is the pointer copied to object `+0x5C`. Recovered the first two `u16` values at each such timer pointer; verified the **same 12** event configs, event ticks, and timer pairs against the corresponding EU `D_8007962C` / `D_8007A26C` secondary lists. Descriptor pointers shift by `+0x818` JP→EU; for the timer data here, script pointers shift by `+0x844` (e.g. JP `800AB394`→EU `800ABBD8`). This is consistent with earlier inventory findings that not all tables relocate by one common delta.

| Config / runtime type | Scheduled number | Section spawn tick | First script halfword (enable) | Second script halfword (deadline) | Eligible interval after authored spawn |
| --- | ---: | ---: | ---: | --- | --- |
| `0x41 / 0x70` | 5 | 1336 | 1024 | 1792 (all five) | `[1336, 1792)` = 456 ticks |
| `0x51 / 0x71` | 5 | 1875 | 1536 | **2186, 2189, 2176, 2167, 2153** (script order) | 311, 314, 301, 292, 278 ticks |
| `0x52 / 0x70` | 2 | 1875 | 1280 | **2173, 2185** | 298, 310 ticks |

These are **scripted opportunity windows, not guaranteed continuous operation**. Object pool exhaustion, phase transitions, hits/destruction, per-update cooldown, the angular predicate and possible event scheduling conditions can reduce or eliminate actual successful spawns. No game FPS, seconds conversion, number of projectile objects fired or visual name follows from this static comparison. The event window's lower bound is the authored spawn tick because all first-script times precede it; child allocation/dispatch may delay the actual first opportunity. All 12 timer pairs agree JP↔EU.

### 2. Type-0x70: parent with a second type-0x70 child state machine

- Dispatcher entry `func_80036810` reads signed object `+0x24` and dispatches `-1→80036A54`, `0→8003688C`, `1→800369F4`.
- Parent phase zero `8003688C..800369F4` attempts `func_800314B8` allocation for a *linked child of the same type* with **phase -1**, parent `+0x64 → child`, child `+0x64 → parent`, and child `+0x84=0`. It copies the first timer halfword from `parent+0x5C` into `child+0x86` and advances the parent's `+0x5C` by 2 bytes. On successful setup the parent changes to phase 1; allocation failure clears its type. No claim of a child allocation every scheduled encounter when the pool is full.
- Parent phase 1 `800369F4..80036A54` compares section tick `D_800ABFA4` against `*(u16*)parent+0x5C` (now the **second** scripted value). While the deadline is in the future it renders; at or after the deadline it clears the linked child type (if still linked) and its own type. This gives the **window end**.
- Linked child phase -1 `80036A54` uses `+0x84` as an internal three-state controller. State 0 `80036BE0` waits for `D_800ABFA4 >= child+0x86` (the **first** scripted value). On reaching it, it writes `child+0x32=1`, `child+0x68=0`, increments `+0x84` to state 1, then **immediately calls** state-1 handler `func_80036C3C`.
- Child state 1 `80036C3C..80036D2C` adjusts orientation relative to streamed position and calls the shared attack dispatcher `func_80035418` at `80036D0C`, followed by rendering. Thus **the first eligible state-1 invocation already attempts an emission**: `0→0xFFFF` through the signed-predecrement cooldown logic.
- Hit/death processing in `80036A54` may invoke `80036B3C` and advance `+0x84` to **state 2**, replacing attack calls with the death/final-effects path `80036D2C` (including a separate `child+0x6C` countdown). Thus the scripted deadline is *not* a guaranteed firing duration after a player destroys the linked child. The parent can also clean it up on the deadline. Child `+0x32` should not be conflated with *parent config `+0x32`*, which is the cooldown jitter parameter.

### 3. Type-0x71: direct phase controller and second cut-off

- Entry `func_80036E14` handles phases **0, 1, 2** at `80036E90`, `80036EF4`, `80037094`.
- Phase 0 `80036E90` copies the **first** stream halfword to object `+0x70`, advances `+0x5C` to the second halfword, clears `+0x32` and `+0x68`, sets phase 1, and falls through to `func_80036EF4` **in the same invocation**.
- Phase 1 `80036EF4`: while `D_800ABFA4 < *(u16*)obj+0x5C` (**second**, deadline), it checks `D_800ABFA4 >= obj+0x70` (**first**, enable); if satisfied, sets `obj+0x32=1` and calls `func_80035418` at `80036FD4`. At/after the second timestamp, `80036FEC` clears the type. An additional *mode-specific early-cutoff* branch applies only when cfg `+0xAE` is nonzero, `D_800ABF9C == 1`, `D_800AC2BC != 0`, and tick **>= `0x898` (2200)**. Because these 12 events are in mode zero and their ordinary deadlines are all <2200, it is not an alternate ending for the verified mode-zero windows.
- A fatal hit can invoke `80037004` and transition from phase 1 to phase 2; `80037094` then runs countdown/debris/final effects, **not** the method-6 firing call. Therefore destruction can close firing earlier than the authored deadline.
- Config `0x40` is another type-0x71/method-6 record selecting child `0x61`, but is not included among the 12 authored mode-zero encounters; this report does not claim it is never reachable in other modes.

### 4. Shared firing mechanism and cooldown equation

`func_80035418`:
1. If object `+0x32 == 0`, return without decrementing the attack timer.
2. Otherwise predecrement unsigned-loaded `+0x68`, store low 16 bits, then **sign-test the decremented halfword**. Nonnegative means no emission; negative dispatches method `cfg+0x2A` through an 11-slot jump table (`0..10`).
3. Method 5 → `800355E8`; method 6 → `8003564C`. Both allocate from `func_80031530`, conditionally initialize the child through `80035688`, and unconditionally invoke `func_800355C8 → 8003552C` to reset the cooldown, including on allocation/angle rejection.
4. `80035688` supplies the type-0x18 child's `+0x6C` from `cfg+0x28 = 300`; case 5 additionally displaces the child's second position component by `+40` if successful (pass 35). No runtime success established.

`func_8003552C`, exact signed/fixed-point structure, writes a halfword to `obj+0x68`:

```c
// Structural pseudocode, not matched game C.
row = (s16)D_800ABDFC;
column = (s16)D_800AC164;
base = *(s16 *)(cfg + 0x34 + 2 * (7 * row + column));
jitter = *(s16 *)(cfg + 0x32);
func_80031468();  // modifies RNG state
rng = (s16)D_800AC50C;
obj->attackCooldown = (s16)(base + ((2 * jitter * rng) >> 16) - jitter);
```

**Caution:** This is a table-index formula, not a verified attribution of row/column to difficulty, gunner count or game mode. It assumes indices in the authored 6×7 range when describing the data grid; this pass has not established out-of-range safety. Signed multiplication, arithmetic right shift and low-halfword storage matter. A reset value `N >= 0` yields the next attempt after `N+1` enabled dispatcher invocations under otherwise continuous updates, because countdown is **pre**decremented. The signed RNG distribution has not been established.

| Parent config | Runtime type | Child | `cfg+0x32` jitter | 6×7 base-delay table |
| --- | --- | --- | ---: | --- |
| `0x41` | `0x70` | cfg `0x60` / type `0x18` | 5 | rows 0–5: `55 55 55 50 50 45 45`; `50 50 50 45 45 40 40`; `50 50 50 45 45 40 40`; `45 45 45 40 40 35 35`; `45 45 45 40 40 35 35`; `40 40 40 35 35 30 30` |
| `0x51` | `0x71` | cfg `0x61` / type `0x18` | 5 | all **42** cells equal **40** |
| `0x52` | `0x70` | cfg `0x60` / type `0x18` | 5 | same 42 base values as cfg `0x41` |

Also compared unscheduled cfg `0x40` jitter **8** and all 42 cells with EU, in addition to the three scheduled configs: **172/172** compared halfwords (`cfg+0x32` plus 42 table values for each of four configs) are identical JP/EU. The array base does not by itself define human-readable labels for the global selectors. Parent and child `+0x32` mean different things.

### 5. JP/EU control-flow corroboration

JP source `asm/g3_jp/nonmatchings/func_80033C44.s`; EU source `asm/g3_eu/nonmatchings/func_800338AC.s`. All windows below use **EU VA = JP VA − 0x398**, exclusive upper bound. Instruction words were recovered by undoing comment-byte endianness; shapes retain opcode/register fields and mask jump targets and I-type immediates (R-type words verbatim). Some windows overlap earlier passes; the total is the **scope of this pass's paired comparison**, not an assertion of wholly new unique coverage.

| JP range (exclusive end) | Subject | Words | Exact | Same shapes |
| --- | --- | ---: | ---: | ---: |
| `80035418..8003552C` | attack dispatcher | 69 | 49 | 69 |
| `8003552C..800355E8` | cooldown computation/reset | 47 | 42 | 47 |
| `80036810..800369F4` | 0x70 dispatch/parent construction | 121 | 112 | 121 |
| `800369F4..80036A54` | 0x70 parent deadline | 24 | 21 | 24 |
| `80036A54..80036BE0` | 0x70 child state machine/death | 99 | 86 | 99 |
| `80036BE0..80036D2C` | 0x70 child enabling/firing | 83 | 69 | 83 |
| `80036D2C..80036E14` | 0x70 child end-state | 58 | 54 | 58 |
| `80036E14..80037094` | 0x71 dispatch/enable/death | 160 | 140 | 160 |
| `80037094..80037250` | 0x71 final-effect handler | 111 | 104 | 111 |
| **Total** | | **772** | **677** | **772** |

JP data: `data_80071790.data.s`, `data_80080048.data.s`. EU data: `data_80071FD0.data.s`, `data_8008002C.data.s`. No assumption that normalized instruction shape comparison proves full retail matching or execution.

## Open questions / Pass 37

1. **Conditional firing versus contact:** the actual angular gates `func_80036658`, producer allocator occupancy and child orientation may reject attempted shots even in the verified windows. A runtime trace should record `obj+0x32/+0x68/+0x24`, parent config `+0x2A/+0x2C`, child `+0x60/+0x6C`, `D_800ABFA4`, the first/second script halfwords and successful vs failed `func_80035688` return values.
2. **Shot geometry/visual identity:** correlate cfg `0x60` resource selector `0x14` (radius 280, damage 20) and cfg `0x61` resource `0x17` (radius 100, damage 10) to private TMD or runtime capture; no speculative on-screen identification.
3. **Harder static continuation:** trace whether `D_800ABDFC` and `D_800AC164` are restricted to the 6×7 configured cooldown grid, and what `func_80031468` does to the signed RNG halfword so cooldown intervals can be precisely bounded. Also preserve the independent `cfg 0x4A→0x68` zero-lifetime runtime watchpoint and orphan cfg `0x74` alternate-mode question.

This report establishes **conditional firing windows and the code paths that attempt attacks**, not witnessed gameplay shot counts, damage events or results-counter credits.

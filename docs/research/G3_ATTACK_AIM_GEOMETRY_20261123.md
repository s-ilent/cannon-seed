# G3 pass 37 — angular emission predicates, tracking limits and vehicle-contact geometry

**R1 pass 37 — 2026-11-23.** Continues [pass 36 firing windows](G3_ATTACK_FIRING_WINDOWS_20261123.md) from branch `research/g3-attack-firing-windows-20261123` at `a192cb99438e076b8ae73f8cc2c580fabe6780b2`. Bounded **static analysis** of tracked JP/EU generated code and configuration data. No game runtime, private retail binary/CHD, new hash oracle, source conversion, matching build, assets, or observed shot count. The word *projectile* names the type-`0x18` moving, proximity-triggered attack object; no on-screen model identity asserted.

## Result: three scheduled patterns are materially different

| Mode-zero parent cfg / runtime type | Method / child cfg | Angular fields `+0x2E / +0x30` | Type-0x70 tracking cap | Child contact bound / base damage |
| --- | --- | --- | --- | --- |
| `0x41 / 0x70` | 5 / `0x60` | `-1 / 0` | **±`0x1000`**, 22.5° from initial yaw | radius **280**, damage **20** |
| `0x51 / 0x71` | 6 / `0x61` | `-1 / 0` | no type-0x70 tracking controller | radius **100**, damage **10** |
| `0x52 / 0x70` | 5 / `0x60` | `-1 / 0` | **`0x8000`** (180°), effectively **unrestricted** signed yaw deviation | radius **280**, damage **20** |
| `0x40 / 0x71` (comparison, *not* among the 12 scheduled mode-zero events) | 6 / `0x61` | `-1 / 0` | no type-0x70 tracking controller | radius **100**, damage **10** |

Parent config addresses: JP `0x40=80088A8C`, `0x41=80088B40`, `0x51=80088BF8`, `0x52=80088CAC`; EU addresses are each **+0x818**. For **all four**, JP/EU agree at `cfg+0x2A` (method), `+0x2C` (child index), `+0x2E=-1`, `+0x30=0`, `+0x32` (cooldown jitter), `+0xAE` and `+0xB2`: **28/28 compared fields**. The decisive `cfg+0xB2` values are **0** for `0x41` and **1** for `0x52`. The child radii/damage are data already decoded in pass 35, not freshly witnessed contacts.

## 1. The firing predicate does not act as a conventional narrow cone in these records

At `func_80035688`, `800356A4` calls `func_800323B0(parent)`, which computes two temporary angular globals `D_800ABF34` and `D_800ABF44` from a relative position vector. For parent `+0x26=0` it derives that vector from `D_8016AC18/1C/20 - parent+0x4/+0x8/+0xC` (truncated to signed 16-bit components), then calls `func_80032598` to write the angular values.

At `800356AC..800356BC`, constructor `func_80035688` calls `func_80036658(parent, s16(cfg+0x2E))`. If it returns zero, the initializer returns zero **before copying the prospective child's pose or assigning its type/config**. The case-5/6 caller has already asked the pool allocator `func_80031530` for a slot; failure or angle rejection still proceeds to the shared parent cooldown reset. Success requires both unsigned halfword comparisons below. Exact structural pseudocode:

```c
uint16_t width = (uint16_t)(2 * (int16_t)angle);
bool eligible =
  (uint16_t)(D_800ABF34 + (uint16_t)parent_at_0x10 + angle) < width &&
  (uint16_t)(D_800ABF44 - (uint16_t)parent_at_0x12 + angle + 0x8000) < width;
return eligible ? -1 : 0;
```

The function uses `sll/sra/andi` to form the 16-bit `width`, `sltu` in both comparisons, and `negu` to return `-1` for true. **With angle=-1, width is `0xFFFE`, not a tiny angle.** Each comparison rejects only the two possible unsigned results `0xFFFE` and `0xFFFF`. This is an almost-unconditional emitter gate, but **not literally unconditional**. It proves neither allocation nor contact; no assumption about a statistical angle distribution is made.

The earlier method-1 emitter uses sibling `func_800365FC`: first comparison `D_800ABF34 - parent+0x10` instead of the method-5/6 `+`, and no `+0x8000` in the second. Do **not** indiscriminately apply the method-5/6 orientation equation to the method-1 `0x4A` anomaly.

## 2. The second predicate disables the randomized aimed branch

After the first gate passes, `func_80035688` copies `parent+4/+8/+C` to child and calls `func_80036658(parent, s16(cfg+0x30))` at `800356F0`. If this second call returns `-1`, it invokes `func_8003593C`, which calculates an angular aim toward a randomized target offset using two LCG samples, target/parent coordinates, and `func_80032598`.

**For all four reviewed configs `cfg+0x30=0`; unsigned `width=0`, so both strict `sltu < 0` tests cannot succeed.** Thus this randomized aiming path is *not executed* by these configs in the unchanged static data. The constructor instead runs:

```c
child->angle_0x10 = (uint16_t)(-parent->angle_0x10);
child->angle_0x12 = (uint16_t)(parent->angle_0x12 - 0x8000);
```

at `80035720..8003573C`; `func_800366BC` then resolves child type/config, `cfg+0x28` provides its 300-count lifetime, and `func_80030454` initializes trigonometric fields. Parent angles can already have been updated by the parent/controller; the fallback rule is **not** equivalent to every shot flying in a globally fixed world direction.

## 3. Type 0x70 actually adjusts its aiming before firing; 0x41 and 0x52 differ by one bit

The type-`0x70` parent allocates its same-type **phase -1 linked child** in `8003688C..800369F4`. Initialization sets `child+0x88 = child+0x12` (the stored initial horizontal angle) and normally `child+0x8A=0x1000`. If **`parent_cfg+0xB2 != 0`**, code `8003699C..800369B4` replaces `child+0x8A` with `0x8000`.

During the attack-enabled child state 1, `func_80036C3C` runs **before** `func_80035418` at `80036D0C`. It computes an aim bearing using:

```c
target_x = D_8016AC18 + 8 * (int16_t)D_8016AC38;
target_z = D_8016AC20 + 8 * (int16_t)D_8016AC3C;
bearing = angle_from_xz(target_x - child->x, target_z - child->z);
error = (int16_t)(bearing - 0x8000 - child->angle_0x88);
delta = clamp(error, -(int)child->limit_0x8A, (int)child->limit_0x8A);
child->angle_0x12 = (uint16_t)(child->angle_0x88 + delta);
// child+0x1C trig component refreshed; then invoke attack dispatcher.
```

The live globals at `D_8016AC38/3C` are **8× offsets** in this specific computation; their full world-space semantic provenance has not been separately re-audited. The clamp is **relative to the immutable copied baseline `+0x88`**, not an accumulated 22.5° turn per tick. Thus `0x41` remains within ±22.5° of its initial orientation while `0x52` can choose any signed halfword yaw error (the maximum magnitude is `0x8000`). Both shots still use the fallback child-angle mapping of §2.

By contrast, the inspected type-`0x71` phase-1 path `80036EF4..80036FEC` handles hits, deadline/cutoff, enabling `+0x32`, dispatch at `80036FD4`, and render; it does **not** invoke `func_80036C3C` or rewrite `parent+0x10/+0x12` as part of that active handler. A type-`0x71` shot therefore inherits the phase controller's existing orientation, subject to any independent state writers not established here.

## 4. A successful emission is still not a successful hit

Type-`0x18` handling `func_8003442C` is a **multi-gate**, single-contact design:

1. **Lifetime:** `child+0x6C` is decremented before motion; 300 survives the first update, negative expires (`80034440..80034458`).
2. **Motion:** `func_800345A4` adjusts a Q16 motion magnitude `+0x34` toward `+0x44`, limited by the child cfg `+0x24`, then recomputes three vector components `+0x38/+0x3C/+0x40` from `+0x18/+0x1C` trigonometric state. `80034464..800344A8` integrates them into `+0x4/+0x8/+0xC`. There is **no per-update recomputation of aiming angles `+0x10/+0x12` in this handler**: tracking belongs to the emitter *before emission*, not a demonstrated homing projectile after emission.
3. **Behind/visibility exit:** `func_80034974` computes view-relative angles; if its first returned angle plus `0x4000` is signed-negative, `800344C4` expires the object before near-contact.
4. **Near-distance test:** for child `+0x26=0` (set in method-5/6 constructor), `func_80034748` uses the three world-position differences from `D_8016AC18/1C/20` to compute squared distance. `800344DC..800344F0` requires `dist2 < (s16)child+0x36 squared`; this is **280²=78,400** for cfg `0x60`, **100²=10,000** for cfg `0x61` in the intended numeric range. Outside the near range, a separate large unsigned distance cutoff can expire the shot, otherwise it continues moving/rendering.
5. **Angular *contact* test:** inside the range, `800344F8` invokes `func_800352A0`. Its `func_80034EC0` derives two angles from a relative **motion** vector: for `+0x26=0`, child velocity high halfwords at `+0x3A/+0x3E/+0x42` minus `D_8016AC38/3A/3C`, passed through the coordinate/angle helpers. In G3 mode zero, `func_800352A0` checks modular angular halfwidths **`0x1555` (~30°)** for its second angle and **`0x16C1` (~32°)** for its first. Other modes use `0x1A4F` (~37°) for the first. Only both passes lead to `func_80035348`, which has additional mission/health gates.
6. **Critical near-miss behaviour:** the branch at `800344F8..80034504` **clears child type immediately after calling the angular-health wrapper regardless of whether it applied damage**. Entering the near sphere consumes the attack; angular rejection is a *near miss*, not a persistent projectile that can try to collide again later.

The emitter's almost-unconditional **launch** gate and the later, much narrower **relative-motion impact** gate are independent; merging them into one "hit chance" would be incorrect. Likewise radius values are not guaranteed real-world hit distances under overflowing 32-bit arithmetic or unknown runtime state; the code uses low-word MIPS multiplication and unsigned compares.

## 5. Paired-region control-flow corroboration

JP `asm/g3_jp/nonmatchings/func_80033C44.s`; EU `asm/g3_eu/nonmatchings/func_800338AC.s`. All compared code windows use **EU VA = JP VA - 0x398**, upper bound exclusive. Each comment-byte instruction was reordered into its MIPS machine word. Exact matches compare full words; shape compares retain opcode/register fields but mask immediate fields and J/JAL destinations; R-type words remain whole.

| JP window | Mechanism | Words | Exact | Shape |
| --- | --- | ---: | ---: | ---: |
| `800365FC..80036658` | method-1 angular predicate, contrast | 23 | 20 | 23 |
| `80036658..800366BC` | method-5/6 angular predicate | 25 | 22 | 25 |
| `80035688..800357C8` | constructor / two tests / fallback | 80 | 71 | 80 |
| `80036C3C..80036D2C` | type-0x70 aim and dispatch | 60 | 50 | 60 |
| `80036EF4..80036FEC` | type-0x71 firing-phase path | 62 | 52 | 62 |
| `800352A0..80035348` | angular impact gate | 42 | 37 | 42 |
| `8003442C..800345A4` | type-0x18 lifetime/motion/contact | 94 | 85 | 94 |
| **Total** | | **386** | **337** | **386** |

The short-angle conversion helpers `func_800323B0` / `func_80032598` were inspected from JP `asm/g3_jp/nonmatchings/func_8002A2DC.s`; not included in the 386-word paired total. This is structural corroboration from tracked files, **not a newly verified retail image match or a runtime observation**.

## 6. Runtime test / Pass 38

Static analysis now distinguishes **firing attempts**, **successful child setup**, **trajectory**, **near-sphere arrival**, **angular impact acceptance**, and **actual health mutation**. It cannot yet tell how often the authored encounter positions and moving vehicle intersect over the 12 scripted windows. A bounded emulator instrumentation probe should log, per attempt:

- Section tick `D_800ABFA4`; parent config, phase `+0x24`, `+0x32` enable and `+0x68` cooldown; allocator result and `func_80036658` return at the first gate.
- Type-`0x70` child `+0x88` baseline, `+0x8A` clamp, and updated `+0x12` before dispatcher; type-`0x71` parent `+0x10/+0x12` at dispatch.
- Spawned child config/type, `+0x6C` lifetime, angles `+0x10/+0x12`, current and previous `+4/+8/+C`, velocity `+0x38/+0x3C/+0x40`, distance² and near-bound, `func_800352A0` angular result and whether `func_80035348` changed shared health.
- Outcomes classified separately as allocation failed, angular launch rejected, emitted but expired, near sphere and angular miss (consumed), angular pass but mission/health-gate suppressed, and verified damage.

An offline deterministic trajectory replay based on **scripted initial object states plus the logged vehicle motion vector** could then estimate which of the 12 authored encounters can ever connect, without asserting an unmeasured "accuracy percentage". A type-`0x70` cfg `0x41` vs `0x52` side-by-side is especially discriminating: identical child `0x60` physics but different target-heading coverage. Separately preserve the `cfg 0x4A→0x68` zero-lifetime watchpoint and cfg `0x74` alternate-mode question; neither is resolved by this pass.

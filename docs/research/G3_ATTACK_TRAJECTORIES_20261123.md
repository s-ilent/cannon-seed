# G3 pass 38 — authored attack formations and exact type-0x18 trajectories

**R1 pass 38 — 2026-11-23.** Continues [pass 37 angular and impact geometry](G3_ATTACK_AIM_GEOMETRY_20261123.md), based on branch `research/g3-attack-aim-geometry-20261123` at `f5799655ecb5d64b49879a29603335209e6779d5`. Scope: bounded static analysis of tracked JP/EU ASM/data, with pure arithmetic on recovered constants. **No CHD/retail-byte oracle, live trace, model or FMV identification, gameplay modification, matching C build or measured hits.** Script tick ≠ established display frame or wall-clock second.

## Result

The first section of mode zero contains 12 precisely arranged timed emitters, not 12 unrelated spatial placements: **five cfg 0x41 arranged longitudinally along their baseline projectile direction, five cfg 0x51 arranged transversely to their fixed projectile direction, and two cfg 0x52 arranged longitudinally along a baseline direction orthogonal to cfg 0x51.** The type-0x18 child `cfg+0x22` is both its **integer movement magnitude (upper halfword of object `+0x34`)** and its **proximity radius** (object `+0x36`); `cfg+0x24=0` disables acceleration. The resulting child motion is constant-direction, integer-quantized, without homing in the active handler. A separate **4000-unit distance cull** normally removes shots well before their 300-update lifespan if they leave the region around the Dragoon anchor.

## 1. Original 12 placements, not synthetic spawn samples

The mode-zero first section `D_80079C54` points to secondary list `D_80078E14` in JP. The EU counterpart is `D_8007962C` (JP + `0x818`). Each list entry is `u16 local_tick; u16 unused_here; u32 descriptor_ptr`. Descriptor is `u16 flag, u16 cfg_index, s32 x/y/z, s16 angle0/angle1/angle2, u16 padding, u32 script_ptr`. Fields below were read by address from the tracked JP list and then paired against EU at **JP+0x818** for event addresses and descriptor pointers.

| Cfg | Tick | JP descriptor | X | Y | Z | Angle `+0x10` | Yaw `+0x12` | Angle `+0x14` |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 41 | 1336 | `800783B0` | -2624 | -5147 | 27043 | -3491 | -8738 | 1 |
| 41 | 1336 | `800783CC` | -3116 | -5377 | 27487 | -3491 | -8738 | 1 |
| 41 | 1336 | `800783E8` | -3609 | -5608 | 27930 | -3491 | -8738 | 1 |
| 41 | 1336 | `80078404` | -4101 | -5838 | 28373 | -3491 | -8738 | 1 |
| 41 | 1336 | `80078420` | -4593 | -6068 | 28816 | -3491 | -8738 | 1 |
| 51 | 1875 | `8007874C` | -14836 | -8500 | 33845 | 0 | -17334 | 0 |
| 51 | 1875 | `80078768` | -14822 | -8500 | 33683 | 0 | -17334 | 0 |
| 51 | 1875 | `80078784` | -14851 | -8500 | 34006 | 0 | -17334 | 0 |
| 51 | 1875 | `800787A0` | -14866 | -8500 | 34170 | 0 | -17334 | 0 |
| 51 | 1875 | `800787BC` | -14880 | -8500 | 34319 | 0 | -17334 | 0 |
| 52 | 1875 | `800788D4` | -15278 | -8258 | 33989 | 0 | -950 | 0 |
| 52 | 1875 | `800788F0` | -15249 | -8258 | 33670 | 0 | -950 | 0 |

Descriptor angle is stored in the game's **0x10000-units-per-turn** fixed-angle convention; the two 1875-tick parent yaws differ by **exactly `16384 = 0x4000` (90°)**. The 12 records are in the *first* section, not the second-section `D_80079A54` list. The packed descriptor word at `+0x10` contains the first two signed 16-bit angles.

EU corroboration: all **12** event tick/descriptor-index pairs agree, EU descriptor pointer = JP +0x818; among the **84 checked descriptor words** (`+0,+4,+8,+C,+10,+14,+18`, seven per record), **84/84** agree after accounting for the `+0x844` regional adjustment to the script-pointer word at `+0x18`. This verifies the pose/position fields in both tracked regional data sets, not live object states.

**Launch position:** method 5 `func_800355E8` adds **40 to the second coordinate (Y)** after successful child initialization. The nominal world launch point is `(x,y+40,z)` for cfg 41/52 and `(x,y,z)` for method 6 cfg 51, subject to allocation and predicate success. Phase handlers for 0x70/0x71 do not integrate the parent position in their inspected active paths; unrelated runtime writers are not exhaustively excluded.

## 2. The crucial speed/radius alias

For spawned type 0x18 `cfg 0x60 / 0x61`, the initializer `func_80035688` writes `lhu(child_cfg+0x22)` to **child `+0x36`** at `8003578C..80035794`, and again to **child `+0x46`** in the delay slot at `800357A8`. These are the *high halfwords* of 32-bit fields `+0x34` (current motion magnitude) and `+0x44` (target magnitude), respectively. The initializer also sets child `+0x26=0` (world-position mode), lifetime `+0x6C=300`, and angle/trig state from the parent.

| Child config | `cfg+0x22` high half of speed / collision radius | `cfg+0x24` motion step cap (u32) | `cfg+0x28` lifetime | Base damage |
| --- | ---: | ---: | ---: | ---: |
| `0x60` | **280** | **0** | **300** | 20 |
| `0x61` | **100** | **0** | **300** | 10 |

All **14/14** region-paired halfword observations at offsets `0,2,0x12,0x22,0x24,0x26,0x28` agree for the two short 0x30-byte configs. `cfg+0x24` and `cfg+0x26` together form the zero 32-bit motion-step cap. `func_800345A4` clamps `(+0x44)-(+0x34)` to `±cfg+0x24`, so current magnitude cannot change through this helper when the cap is zero. The lower halfword of `+0x34` is not independently written by this initializer, but **the movement vector and near-distance radius are derived from its overwritten signed upper halfword**, so stale lower bits do not prevent reconstruction of the inspected active movement calculation. The normal pool allocator `func_800315AC` does not clear a full slot, which is why this distinction matters.

## 3. Recovering actual integer displacement from the original sine table

`func_80030454` packs two signed 16-bit trig values (low = sine, high = cosine) using `D_8008D660`, with a quarter-turn lookup and quadrant sign/swap handling. The JP lookup has **8193** two-byte elements for offsets `0..0x4000` inclusive, from `0` to `32767`. All **8193/8193 halfwords** agree against EU at `D_8008DE78` (JP+0x818).

Let `m = s16(child+0x36)` and let pitch/yaw sine/cosine be the signed high/low halfwords populated in the constructor. In world-position mode `+0x26=0`, `func_800345A4` computes, in MIPS integer operations:

```c
int32_t flat = (2 * m * cos_pitch) >> 16;  // signed arithmetic shift
int32_t vx_word = 2 * flat * sin_yaw;
int32_t vy_word = 2 * m * sin_pitch;
int32_t vz_word = 2 * flat * cos_yaw;
dx = vx_word >> 16;
dy = vy_word >> 16;
dz = vz_word >> 16;
// After the lifetime decrement, world coordinates x/y/z += dx/dy/dz.
```

The code stores `vx_word/vy_word/vz_word` at `+0x38/+0x3C/+0x40` and adds their high signed halfwords to `+4/+8/+C`. Both constructor trigonometric input angles are fixed for each child. The fallback constructor mapping is `child_pitch = -parent_angle_0x10`, `child_yaw = parent_angle_0x12 - 0x8000` modulo 65536. `func_80030454` masks the low angle bit for its lookup; exact values below use those original table samples, not floating-point sine/cosine.

| Parent cfg | Hypothetical parent yaw at launch | Child pitch | Child yaw | **Exact world step** `(dx,dy,dz)` |
| --- | ---: | ---: | ---: | --- |
| 41 | initial `-8738`; **live parent tracks ±0x1000** | `3491` | `24030` = ~132.00° | **`(+196,+91,-177)`**, only at **initial baseline yaw** |
| 51 | `-17334`; phase-1 controller doesn't re-aim | `0` | `15434` = ~84.78° | **`(+98,0,+9)`**, fixed from the inspected handler/initial data |
| 52 | initial `-950`; **live parent tracks up to ±0x8000** | `0` | `31818` = ~174.78° | **`(+25,0,-278)`**, only at **initial baseline yaw** |

For **cfg 51**, the first launch at `(-14836,-8500,33845)` gives the exact pre-cull hypothetical trajectory `P(n)=(-14836+98n,-8500,33845+9n)` after `n` successful child updates. This is not a claim that it actually survives `n` updates. The 0x70 child/parent aiming update `func_80036C3C` runs before each emission: its `+0x88` stored orientation is clamped by `+0x8A`, `0x1000` for cfg41 versus `0x8000` for cfg52, so **do not substitute the baseline rays for measured cfg41/52 shot vectors**. There is no homing-angle update in the type-0x18 child handler after spawn.

## 4. Geometry: a longitudinal column, transverse curtain, and orthogonal baseline pair

Using the Euclidean angle between adjacent spawn-point displacement vectors and the **baseline** integer projectile step:

| Formation | Adjacent origin separations | Angle of spacing vs projectile velocity | Static inference |
| --- | --- | --- | --- |
| Five cfg41 | `~700.9..701.9` units | `179.76..179.87°` | Almost exact **longitudinal axis**; actual targeting can bend ±22.5° from baseline |
| Five cfg51, sorted by Z | `149.7..164.7` units | `89.69..90.12°` | Almost exact **transverse row** to fixed horizontal shot, all `Y=-8500` |
| Two cfg52 | `320.3` units | `179.94°` | Longitudinal **baseline** pair; live tracking may change the shot direction |

The cfg51 row emits parallel world-motion rays (`+98,0,+9`). Its adjacent *ray-to-ray* separations are below **200 = 2× the radius-100 near-contact bound**, so the mathematical radius-100 tubes around their full infinite rays overlap. **This is only geometric coverage**, not proof that simultaneously fired, short-lived, angularly accepted collision spheres form a continuous barrier in gameplay. The parent cfg51 and cfg52 yaws are an exact quarter-turn apart, supporting a deliberately orthogonal arrangement at rest. Actual cfg52 aiming is dynamic and may depart from that baseline.

This spatial classification is stronger evidence of distinct encounter patterns than a mere tally of projectile-producing records. No in-game visual names (turret, laser grid, missile, etc.) follow from the numeric geometry.

## 5. The 4000-unit outer contact/cull sphere

The type-`0x18` handler `8003442C..800345A4` first decrements `+0x6C`, computes motion and advances position, then runs a view-relative angular exit via `func_80034974`. It next calls `func_80034748` to obtain **unsigned low-32-bit squared distance** between the child and the `D_8016AC18/1C/20` world anchor in the child `+0x26=0` mode.

- `dist² < (s16 child+0x36)²` invokes `func_800352A0` to perform angular contact/health gates. **Regardless of that function's return or actual damage**, the child type is then cleared at `80034504`: entering the proximity sphere is a single-use event.
- If that near test fails, `80034508` constructs `0x00F423FF = 15,999,999`; if `dist² > 15,999,999`, it clears child type. In the ordinary no-overflow Euclidean range this means **distance ≥4000** eliminates the attack, after its movement step. At exactly radius 280/100 the strict near test still fails.
- Otherwise the child continues to animate/render and may approach again. The preceding angle/visibility test can also destroy it.

Thus the 300-count lifespan is only an *upper bound*; it is wrong to infer a guaranteed 30,000/84,000-unit useful range by multiplying nominal speed by 300. Conversely, an emitter's script deadline clears the producer and, for 0x70, its linked **same-type phase child**; those handlers do **not** clear every independently emitted type-0x18 attack object. An already-emitted attack can continue past the producer deadline until its own lifetime, view exit, near-contact, or distance cull.

Exact reachability at tick `t` requires the **live vehicle anchor and motion** from `D_8016AC18/1C/20`, the producer's live parent bearing (cfg 41/52), actual parent/child allocation, and the downstream impact-angle/mission-state check. The static script positions do **not** encode that full moving vehicle path in the bounded inputs rewalked here. Arithmetic overflow is faithfully 32-bit in the game; do not generalize the 4000-radius interpretation to hypothetical huge 32-bit coordinate differences without checking wrapped multiplication.

## 6. Paired JP/EU instruction comparison

JP sources `asm/g3_jp/nonmatchings/func_8002A2DC.s` and `func_80033C44.s`; EU equivalents `func_8002A2CC.s` and `func_800338AC.s`. For these instruction windows EU code VA = JP VA **−0x398**, upper bounds exclusive. MIPS machine words decoded by reversing comment byte order. Exact = full word equality; shape retains R-type complete and other opcode/register bits while masking I-type immediates/JAL destinations.

| JP window | Scope | Words | Exact | Shape |
| --- | --- | ---: | ---: | ---: |
| `80030454..800305C0` | packed trigonometry | 91 | 78 | 91 |
| `80031530..800315EC` | object-pool allocation | 47 | 40 | 47 |
| `8003442C..800345A4` | child update and cull | 94 | 85 | 94 |
| `800345A4..8003466C` | speed/direction | 50 | 49 | 50 |
| `80034748..80034828` | distance comparison | 56 | 49 | 56 |
| `80035688..800357C8` | method-5/6 child constructor | 80 | 71 | 80 |
| `800355E8..8003564C` | +40 Y launch shift | 25 | 22 | 25 |
| `8003688C..800369F4` | type-70 linked child setup | 90 | 87 | 90 |
| `800369F4..80036A54` | deadline producer cleanup | 24 | 21 | 24 |
| `80036E90..80036EF4` | type-71 phase 0 | 25 | 24 | 25 |
| **Total** | | **582** | **526** | **582** |

Some windows overlap earlier passes; these are compared source windows, not 582 wholly new MIPS words. All have zero missing instruction addresses in the paired generated text. The region comparison supports behavioral equivalence of these tracked sources, not an independently hashed retail oracle.

## 7. Next — recover the Dragoon rail position to close reachability

**Pass 39 candidate:** trace writers/producers of **`D_8016AC18/1C/20`** (world anchor) and **`D_8016AC38/3A/3C`** (relative motion/lead-vector components) across the game tick, and relate them to any authored rail/camera path or external timing source. Recover the motion sample at first section ticks 1336 and 1875, and whether this state is a predetermined movie-synchronized path, player-controllable offset, or both. That would let us evaluate:

1. Per-shot launch angle at the actual emitter position: cfg41 clamp `0x1000` versus cfg52 clamp `0x8000`; cfg51 remains fixed from the inspected controller.
2. For each potential child update, `P(n)`, vehicle position `V(t+n)`, distance², the `4000` cull and near radius; then separately the mode-zero angular impact gate.
3. Timing: actual emission cooldown, object slot exhaustion, destruction and possible post-deadline residual shots. Don't equate authored window length with emitted shot count or infer an in-game hit probability from static geometry alone.

Best runtime oracle: dump a compact tuple `(tick, D_8016AC18/1C/20, D_8016AC38/3A/3C, object-slot identity, parent config, child position and angles, dist2, hit return)` around the two encounter clusters. The exact raw binary, CHD/STR visuals, and player gameplay capture are still unexamined in this pass. Preserve previous cfg4A lifetime and cfg74 alternate-mode questions as separate tracks.

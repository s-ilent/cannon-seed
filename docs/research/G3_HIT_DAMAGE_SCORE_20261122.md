# G3 hit arbitration, damage, score and four-gunner limit

R1 pass 9, 2026-11-22. Static review at main 173e1dfb and preceding
research branch 86cea71c. Extends [gunner and target pools](G3_GUNNER_TARGET_POOL_20261122.md).
No fresh retail oracle, runtime trace, C conversion, coverage change
or fresh local census.

## Result

Four is a hard-coded gameplay limit in the inspected executable, not
merely an allocation size: the hit-award routine rotates through
exactly four gunners and a separate handler explicitly walks indices
3 to 0. The target hit mask itself is 16 bits wide, so widening the
player records alone would not lift the limit. Network and cabinet
protocol limits are not established.

The damage path implements a two-level target durability model
(+0xA8 fractional accumulator and +0x2E whole-stage counter),
rotating per-gunner award order, distinct score additions for
nonfatal/fatal phases, and a table-driven death-state transition.
The exact damage class-to-jump-table-arm mapping remains unverified.

## Source and regional evidence

JP [game assembly](../../asm/g3_jp/nonmatchings/func_80033C44.s)
(YAML ROM 0x14444, size 0x10EF4) and EU
[game assembly](../../asm/g3_eu/nonmatchings/func_800338AC.s)
(ROM 0x140AC, same size). Windows compare normalized mnemonic/register/
operand text (address-bearing labels only replaced), plus exact
raw instruction words, with EU = JP - 0x398 in these windows.

| Responsibility | JP VA half-open | JP ROM half-open | EU VA start | Words | Exact | Normalized |
| --- | --- | --- | --- | ---: | ---: | ---: |
| Damage and alternate hit helper | 80034AA8..80034C60 | 152A8..15460 | 80034710 | 110 | 103 | 110 |
| Rotating hit arbitration | 80034C60..80034D94 | 15460..15594 | 800348C8 | 77 | 68 | 77 |
| Packed-decimal score addition | 80034D94..80034E0C | 15594..1560C | 800349FC | 30 | 30 | 30 |
| Example target hit/update | 80036EF4..80036F54 | 176F4..17754 | 80036B5C | 24 | 21 | 24 |
| Example death-state transition | 80037004..80037094 | 17804..17894 | 80036C6C | 36 | 33 | 36 |
| Alternate multi-hit consumer | 8003A468..8003A584 | 1AC68..1AD84 | 8003A0D0 | 71 | 65 | 71 |
| Total | | | | 348 | 320 | 348 |

No overlapping committed SDK anchors in these target windows
(checked against config/sdk_anchors.txt for all except the death-state
window; it lies within the same game assembly region and has positive
game field/call evidence). Game-specific hit, score and object state
provide positive ownership evidence.

## 1. Four-player evidence and arbitration

- 8003F198 loops 4 times, stride 0x8C, from D_801474FC.
- 80034C60 takes target and configuration pointer. Its initial index
  comes from D_800ABE5C, and the computed record address is base + index*0x8C.
  Every iteration advances index BEFORE inspecting a bit, wraps at 4
  (80034CC4), and checks target+0x2A >> index & 1. A counter initialized
  to 3 (80034C94), decremented on the tail, permits four iterations.
  D_800ABE5C is written with each encountered set-bit index
  (80034CF8). This rotates priority across calls; a fatal hit can stop
  the scan early, assigning its credit to the gunner who crosses the
  threshold, not necessarily the lowest index.
- When D_800AC29C != 1, damage and score calls are bypassed, but the
  encountered bit still affects the rotating index and return flag.
- 8003A468 uses a separate descending 3..0 loop from D_801476A0
  (D_801474FC + 3*0x8C), tests the same mask, and calls the alternate
  hit helper and score helper per selected gunner.
- 800439B4..80043A14 copies gunner+38 to +3A over 4 records;
  80043FF0..8004402C OR-reduces +3C over 4 records, and
  80044A0C..80044A34 clears each gunner+34 32-bit accumulator.
  These are independent hard-coded assumptions, not a single constant.
- Prior pass established 16-bit target hit mask and index-based
  notification. The four-record extent is 0x230 bytes, ending
  exclusively at 0x8014772C (EU 0x80148058). This is an observed
  logical extent, not proof of adjacent symbol ownership.
  A cap expansion must also audit input masks, HUD, per-player tables,
  network serialization and neighboring storage. No assertion of a
  universal engine or protocol maximum.

## 2. Common damage helper and hit arbitration return

80034AA8 dispatches on signed gunner+0x88, unsigned range test <=4,
through jtbl_80020CF4. Three observed code arms:

| Arm JP | Effect |
| --- | --- |
| 80034AEC | subtract 75 from target+0xA8; if signed result <=0, decrement target+0x2E if nonnegative, add 100 back to +0xA8; if +0x2E remains nonnegative add score from config+6 |
| 80034B48 | if +0x2E nonnegative decrement it; zero +0xA8; if new +0x2E nonnegative add score from config+6 |
| 80034B7C | out-of-range fallback: decrement nonnegative +0x2E and zero +0xA8; no score call in this arm |

No jump-table entries were read for this pass, so do not assign
individual 0..4 classes to arms or assume every class uses one of
the first two bodies. The earlier allocator initializes +0xA8=100;
the 75/100 subtraction/carry pattern supports a fractional
durability interpretation, not necessarily displayed HP units.
+0x2E is signed; negative is the terminal threshold.

After the helper, 80034C60 inspects +0x2E. If negative it returns 0
early; if exactly -1, it first adds a config+8 award for the current
gunner. If +0x2E remains nonnegative and signed +0xA8 <=0 it adds
config+6. Otherwise it continues. At least one encountered mask bit
sets return flag 1; no bits gives 0. The routine is NOT a player-index
return. Example 80036EF4 uses 2*return as a table selector for
target+0x30 and branches to 80037004 on +0x2E < 0.
There are 16 direct jal sites to 80034C60 in the inspected JP game
assembly, spanning 80033F48 through 8003E080. These are potential
family-recovery entry points, not necessarily 16 unique object types.

80034BA8 instead increments target+0x88 at a fractional threshold,
or directly, using a separate table jtbl_80020D0C indexed by
gunner+0x88. 8003A468 invokes it for each gunner mask bit; then
divides target+0x88 by a config value indexed by D_800AC164 and
subtracts the quotient from a linked record's +0x2E (sets linked
+0x88=2 on nonzero quotient); writes remainder to source+0x88.
The alternate family's exact object identities and table arms remain
unknown.

## 3. Score encoding

80034D94 is a complete, straight-line 0x78-byte leaf, 30/30 exact
instruction words JP/EU. It decodes four nibbles of its second
argument:
  score_delta = 1000*((arg>>12)&15) + 100*((arg>>8)&15)
              + 10*((arg>>4)&15) + (arg&15);
then adds it (sign-extended 16-bit delta) to gunner+0x34, a 32-bit
counter. It does not validate that nibbles are <=9. This is packed
decimal-style input, ordinary integer accumulation, not packed BCD
storage. Award call sites use target configuration +6/+8 (nonfatal/
fatal paths) and the alternate config +E4. This makes +0x34 a strong
score field identification; exact displayed score and award scaling
are not yet traced.

## 4. Representative destruction transition

80036EF4 reads target+0x2A and config+2; if hit it calls 80034C60,
selects config+2+2*return as model ID +0x30, and calls 80037004 when
+0x2E becomes negative. 80037004 optionally decrements a global
counter through D_800ABCD4 when config+0xAE !=0, calls 80045128 with
config+0x10, clears target collision mode +0x28, sets +0x30 from
config+0xB0, +0x6E=0, +0x24=2, +0x6C from config+0xA4 and
calls scene helper 80031C5C. This is an explicit non-collidable
death-state/model transition, not immediate slot release.
The following 80037094-family path decrements +0x6C and +0x6E,
uses a 74-slot allocator at 80037148, and has a target+0 clear at
80037238; exact phase dispatch and effect meanings still need tracing.

## Next

Decode the two damage jump tables from available non-copyrighted
symbolic evidence or a witnessed local baseline, then map target
configuration and death stages, especially constructor 8003D9FC
and table D_8008A220. Small future matching candidate: the complete
80034D94 score decoder, with independent per-target retail verification;
no conversion here. Do not add a player-cap patch before the
matching baseline and networking/HUD audit.

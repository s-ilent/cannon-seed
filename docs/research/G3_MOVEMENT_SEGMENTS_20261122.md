# G3 movement segment interpreter

R1 pass 14, 2026-11-22. Main 173e1dfb; research input 35c60d17.
Extends [mission inventory](G3_MISSION_INVENTORY_20261122.md).
Uses the same immutable JP/EU private EXE blobs (7b5ad2b5/e9cfc4ee)
hash-verified in pass 12. No raw authored paths or binary copies published.

## Evidence

JP scene assembly func_8002A2DC.s / EU func_8002A2CC.s.
For all ranges below EU code address = JP - 398 hex. JP ROM offset
= JP VA - 8001F800. Normalization replaces address-bearing symbols.

| JP range (exclusive end) | Words | Exact | Normalized |
| --- | ---: | ---: | ---: |
| 800327F8..80032A40 | 146 | 125 | 146 |
| 80032A40..80032BC4 | 97 | 75 | 97 |
| 80032BC4..800330C4 | 320 | 292 | 320 |
| 800330C4..80033274 | 108 | 106 | 108 |
| 80033274..800334AC | 142 | 135 | 142 |
| Total | 813 | 733 | 813 |

No overlapping target-scoped SDK anchors in 800327F8..80033560.
Static comparison, not rebuilt retail or runtime witness.

## 1. Decoder and layout

Object+5C is a persistent cursor to 24-byte movement segment records
for types 60 and 68. 80032A40 reads signed halfword at +0; negative
returns signed value without advancing. Nonnegative loads flags and
target control, converts coordinate representation where needed,
dispatches by +8 low 3 bits, advances +5C by 0x18, returns zero.
No explicit bounds check in original decoder.

| Record offset | Type | Proven meaning |
| --- | --- | --- |
| 0 | s16 | Negative terminator; low 2 bits select orientation policy |
| 2 | unknown | Unread here |
| 4 | u32 | Desired control/speed word -> object+44 |
| 8 | u16 | Coordinate/destination mode, low 3 bits |
| A | unknown | Unread here |
| C,10,14 | 3 words | Target coordinates or low halfword components |

The actual jump table JP 80020BE0 / EU 80020BC0 has 7 entries
with identical relative code targets; mode 7 fails bounds check.

| Mode | JP arm | JP implementation | Observed behaviour |
| --- | --- | --- | --- |
| 0 | 80032B20 | 80032C7C | Absolute world target words |
| 1 | 80032B34 | 80032DAC | Absolute origin-relative target halfwords |
| 2 | 80032B48 | 80032F1C | Absolute rotated-origin-relative target halfwords |
| 3 | 80032B98 | diagnostic | Invalid |
| 4 | 80032B5C | 80032CB8 | Offset from previous target in world coordinates |
| 5 | 80032B70 | 80032EAC | Offset from previous target in origin-relative coordinates |
| 6 | 80032B84 | 80032F58 | Offset from previous target in rotated-origin-relative coordinates |

Mode 0/4 finish via 80033080: +26=0, clear +24 bit 4000.
1/5 finish via 80033094: +26=1, clear bit 4000.
2/6 finish via 800330AC: +26=1, set bit 4000.
All store target at object+48/4C/50 (word) or +4A/4E/52
(halfword subfields). Relative target is relative to prior *target*,
not necessarily current position. Frame origin globals D_8016AC18/1C/20
and transform helpers 800326A8 / 80032448 convert frames.
Do not call those full arbitrary rotation matrices until traced.
80032BC4 / 80032C24 transform current position when changing world /
origin-relative representation. World mode uses integer positions;
relative mode stores 16.16-like coordinates in words, integer components
in their high halfwords, with bit 4000 affecting transformation.

## 2. Motion integration

800327F8 initializes first segment (80032A40), returns negative
on exhaustion, else 80032838 initializes motion state.
80032838 zeros speed word +34, velocity words +38/3C/40 and angular
step halfwords +72/74/76; calls 80032880 and 80032984.
80032984 switches +24 low two bits:
0 copies motion +78/+7A to model +10/+12;
1 copies global +D_8016AC40/42;
2 sets +10=0, copies D_8016AC42 to +12;
3 copies D_8016AC40 to +10 and motion +7A to +12.
These are initialization policies, not a proof of every subsequent
orientation behaviour.

Both type 60 and 68 run the common motion sequence:
- 800332C4: destination minus current position (coordinate conversion
  where needed); 80032598 solves desired angles; limit angular-step
  changes by config+A8/AA, reset steps on sign reversal, accumulate
  motion angles +78/+7A.
- 80033274: move current control word +34 toward desired +44 using
  config+A4 as signed step magnitude, clamping to target.
- 800334AC: use +36 (high halfword of +34) and angle helper 80030454
  to generate three velocity words +38/3C/40 (exact intermediate
  signed truncations and shifts must be preserved).
- 800330C4: world mode adds signed high velocity halfwords to
  integer position words; relative mode adds full velocity words,
  converts high halfwords for comparison, optionally transforms target.
  Computes squared distance to target; returns -1 if signed
  distance squared <= speed-halfword squared, else 0.
  This is a proximity threshold, not exact waypoint snapping.

Type 60 at 80033F74..80033FB8 advances path when integration returns
-1; clears type on negative decoder result, otherwise resets steps
+72/+74. Type 68 at 80038C9C..80038CF8 also advances on nonzero
integration return; negative decoder result routes through 80038F3C
cleanup. Type 68 initialization additionally allocates linked
type-07 slot, calls specialized helpers 80038DE8/80038E20.
No claim of exact trajectories without origin/angle helper semantics,
scheduler cadence, and object-specific behaviours.

## 3. Actual path inventory

For mode-zero primary events of types 60/68, deduplicate +5C
descriptor pointers. Read 24-byte aligned records, guard image
range, reject coordinate modes 3/7, bound each path to 1024 records;
require region equality of all 12 halfwords in every record and
terminal halfword. 261/261 streams terminate at FFFF; 553/553 records
match JP/EU byte-for-byte. Zero failures. Count per distinct pointer,
not per spawn or per distinct content.

| Mode | Segments |
| --- | ---: |
| 0 | 39 |
| 1 | 51 |
| 2 | 55 |
| 4 | 93 |
| 5 | 308 |
| 6 | 7 |

Length distribution: 48 paths x 1, 148 x 2, 51 x 3, 14 x 4.
Orientation low flags: 0=515, 1=1, 2=31, 3=6.
Mode 5 dominates (308/553). Relative-to-prior-target segments make
shared compact paths possible; cross-spawn reuse established,
not yet exact transformed path preview.

## 4. Atmosphere-transition hypothesis and spike

User hypothesizes largest spawn-density spike corresponds to the
initial rush during descent into atmosphere. Static data supports
a nearby environment transition: mode-zero environment row at
absolute tick 4608 changes environment mode 0 to 1; section two
starts 4609. Peak bin [5000,5500) has 114 primary events:
74 type 1D, 27 type 60, 13 type 68; no secondary events.
The type 1D handler 800341E8 calls 8003427C, which in turn calls
800327F8 (same movement initialization). Its subsequent code sets
collision request 1, zeroes hit mask, copies config+14 durability
and config+BE timer, config+A into +2C, and sets +48/4C/50 to zero.
This establishes use of movement initialization and hit-capable
state, not visual enemy identity or rush direction. Next investigate
type 1D continuation 8003427C..8003442C, linked type/config transitions,
and include valid paths from this family in a separate inventory.

Clock writer unresolved: inspected direct named D_800AC16C stores
in central object assembly, all are reset stores, no increment.
Absolute tick to seconds still unproven; investigate other modules
and indirect stores / sound-time sources. Do not assign 60 Hz by
assumption. Distinct from local object+6A counter which advances in
the per-object driver. Type 90 uses a different +5C format (pass 11
reader 80031684 takes one halfword); do not parse it as a path.

## Next

Trace dominant type 1D and its configuration 66 hex, recover model
references, and find mission clock writer. Then create guarded local
extractor and eventually a movement preview using target coordinate
transforms and fixed-point dynamics. No source/binary changes here.

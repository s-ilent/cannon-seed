# G3 table-driven fragment/debris objects

R1 pass 10, 2026-11-22, static analysis at main 173e1dfb and research
branch 963070fe. Extends [damage and score](G3_HIT_DAMAGE_SCORE_20261122.md).
The earlier proposed general constructor at 8003D9FC is actually a
specialized type-0x38 fragment constructor. This is a positive scope
correction, not evidence that the general encounter parser is recovered.

## Sources and comparison

JP [assembly](../../asm/g3_jp/nonmatchings/func_80033C44.s), YAML row
ROM 0x14444 length 0x10EF4; EU [assembly](../../asm/g3_eu/nonmatchings/func_800338AC.s),
ROM 0x140AC same length. Half-open instruction windows, EU = JP - 0x398
within these windows. Compare raw instruction words and separately
disassembly text with only address-bearing symbols normalized.

| Responsibility | JP VA range | JP ROM range | EU VA start | Words | Exact | Shape |
| --- | --- | --- | --- | ---: | ---: | ---: |
| Fragment spawner A | 8003D614..8003D87C | 1DE14..1E07C | 8003D27C | 154 | 142 | 154 |
| Fragment spawner B | 8003D87C..8003D9FC | 1E07C..1E1FC | 8003D4E4 | 96 | 88 | 96 |
| Common constructor | 8003D9FC..8003DB0C | 1E1FC..1E30C | 8003D664 | 68 | 64 | 68 |
| Motion and lifetime | 8003DB0C..8003DC5C | 1E30C..1E45C | 8003D774 | 84 | 73 | 84 |
| Boundary clamp | 8003DC5C..8003DD84 | 1E45C..1E584 | 8003D8C4 | 74 | 65 | 74 |
| Effect transition | 8003DD84..8003DDC0 | 1E584..1E5C0 | 8003D9EC | 15 | 13 | 15 |
| Hit-aware wrapper | 8003D370..8003D3E0 | 1DB70..1DBE0 | 8003CFD8 | 28 | 23 | 28 |
| Total | | | | 519 | 468 | 519 |

No overlap with known target-scoped committed SDK anchors across
these windows. Direct object-field writes/allocator and effect callers
establish game relevance. No fresh local census/build/runtime verification.

## 1. Table format and selection

Both spawners read parent+0x60 as configuration pointer and signed
config+0xE as an index into the pointer array JP D_8008A220
(EU D_8008AA38). They iterate the selected pointer in **10-byte**
increments; signed first halfword <0 terminates. There is no inline
count or bounds guard on the index in either spawner.

| Offset | Width | Evidence-backed interpretation |
| --- | --- | --- |
| 0 | s16 | Model ID / negative list terminator |
| 2 | u16 | Initial lifetime ticks |
| 4 | s16 | Motion magnitude |
| 6 | s16 | First direction angle input |
| 8 | s16 | Second direction angle input |

Exact authored table values, number of lists, and angle conventions
are not present in the inspected assembly. This schema comes from
the five halfword reads and 0xA stride. Don't reconstruct values
from the code or commit retail asset data.

Each iteration uses caller-start allocator 80031558 (74-slot prefix),
starting at D_8016B014 and then at the previous returned slot.
As the constructor sets +0=0x38 before the next scan, the allocator
advances past it when further entries exist. On allocation failure
the spawner exits, leaving already-created fragments in place.
Visual effects consequently compete with other users of the shared
object prefix. Exact allocation policy for other classes is open.

## 2. Common construction at 8003D9FC

Arguments: parent, allocated child, table-entry pointer.

| Child field | Initial value |
| --- | --- |
| +0x00 | 0x38 (type) |
| +0x28 | 0 (collision mode disabled initially) |
| +0x26 | copy parent coordinate-mode field |
| +0x04/08/0C | copy parent position words |
| +0x10/12/14 | copy parent angle halfwords |
| +0x18/1C/20 | copy parent angle-derived words |
| +0x30 | table +0 (model ID) |
| +0x6C | table +2 (lifetime) |
| +0x48/4C/50 | zero word stores |
| +0x4A/4E/52 | one selected halfword = 0x500, or all zero |

80031468 updates the global u16 D_800AC50C as
(old*5+1) modulo 65536. The constructor then masks it with 0xC;
values 4,8,12 select +0x4A,+0x4E,+0x52 respectively, 0 selects none.
This is deterministic pseudo-random-style axis selection; no claim
about seeding or distribution in a specific playthrough.
The halfwords are actual angular increments because 8003DBDC adds
them to +0x10/12/14 and regenerates the angle-derived words.
The constructor does not zero the entire child record.

## 3. Two launch policies

Spawner A (8003D614): child+0x84=0 and lifetime logically shifted
right by one (half). Relative direction computed via 80030454 and
80032364 from signed entry+6 >>2 plus global angle halfword
D_8016AC44, and signed entry+8 >>1 plus next global halfword.
Multiply each signed direction component by signed entry+4 and
double (wrap semantics as MIPS word arithmetic).
In parent mode +0x26==0, also add three global signed halfwords
(D_8016AC38..3C) shifted left 16. Finally add another derived vector
based on negated parent+0x78, parent+0x7A+0x8000 and parent+0x36.
Store results at child+0x38/3C/40.

Spawner B (8003D87C): child+0x84=1, keep full lifetime.
Direction angles are parent+0x78/7A plus signed table+6/8.
Use the same magnitude multiplication and doubling, but add
arithmetic right-shifted parent velocity words (+0x38/3C/40 >>1).
No extra global halfword vector in this variant.
Exact world axes and trig helper scale remain open.

Direct call sites show A at 80034050 and 8003A130; B at 8003812C
and 8003A028. The B callers also transform the parent to types
0x30/0x31 and invoke effect helpers. A's first caller can instead
clear parent+0 if 800351D0 returns zero. Together with child
model/lifetime/motion and initially disabled collision, these
support destruction fragment/debris interpretation, not a
general enemy spawn routine. Exact named effects unverified.

## 4. Motion, lifetime and boundary conversion

8003DB0C:
- decrement u16 +0x6C; if interpreted signed negative clear +0
  and exit without rendering. A lifetime N admits N nonexpired
  updates (assuming no other mutation).
- load velocity words +0x38/3C/40. If +0x26==0 arithmetic shift
  each >>16 before adding to position words +4/8/C; otherwise
  add full words. These are two coordinate representations.
- if D_800ABF5C !=0 add signed 0xFFFEDE78 (-74120) to +0x3C,
  after position integration, then call boundary helper 8003DC5C.
  This is gravity-like acceleration in a conditional environment,
  not a measured physical acceleration in SI units.
- nonzero boundary result calls 8003DD84, which changes +0 to 0x31,
  calls 80037DE8(child,child,3), then 80037D58(child), and exits.
  The effect object's exact visual identity remains unknown.
- otherwise, if boundary processing was enabled and child+0x84!=0,
  set lifetime to 1 (not immediate removal).
- add angular delta halfwords to three angle halfwords, regenerate
  angle-dependent words via 80030454. Submit via 80031C5C when
  mode==0, else 80031CDC.

8003DC5C converts nonzero mode to world coordinates via >>16 and
adds origin D_8016AC18/1C/20. Tests signed second coordinate against
D_800ABE3C, plus conditional unsigned first/third-coordinate
boundaries (D_800ABF5C thresholds 2/3). On any clamp, mode becomes
0 and adjusted coordinates are written back; returns 1. Otherwise
returns 0 without storing converted coordinates. Geometry/collision
map meaning not yet established.

8003D370 is a separate hit-aware wrapper: tests +0x2A, calls common
hit arbitration, and if +0x2E negative changes +0 to 0x31 and calls
80037E0C/80037D58. Otherwise invokes motion helper 8003DB0C.
The shared motion helper thus also serves a hit-participating path;
do not infer every object reaching it is inherently non-collidable.

**Pass 11 continuation:** [mission scripting atlas](G3_MISSION_SCRIPTING_20261122.md) resolves 80030FF8 as a general spawn constructor, 80030DBC as an encounter scheduler and 80034068 as a variable-width object-local command decoder used with two clocks.

## Next

The actual general spawn/configuration path is still open.
Candidate entry: 80034068 consumes a halfword from *a1, advances
the cursor by 2, then dispatches signed values -17..0 through
jtbl_80020C44. This is only a script-like decoder lead, not yet
a proven mission parser. Trace callers and the larger object
dispatch (especially 80030BEC from the frame scheduler).
The damage jump tables still require witnessed data or symbolic
evidence. Future C landing candidates are the already mapped
score leaf and the fragment effect transition 8003DD84 (0x3C),
subject to full matching oracle. No code changes in this pass.

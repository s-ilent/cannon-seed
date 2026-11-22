# G3 mode-zero mission inventory and script decoding

R1 pass 13, 2026-11-22. Main 173e1dfb, research input 40148012.
Uses the exact private original EXE blobs verified in
[G3 retail dispatch tables](G3_RETAIL_DISPATCH_TABLES_20261122.md)
(JP 7b5ad2b5, EU e9cfc4ee; oracle SHA-1s there).
Fetched the same immutable blobs and decoded little-endian fields in
memory, with VA mapping file offset = VA - 80020000 + 800.
No raw asset bytes or executable copies published. Counts describe
authored schedule entries, not measured runtime active objects.

## 1. Mode-zero mission sections

Mode flag D_800ABF9C selects the original 12-byte section timeline.
JP D_80079C54 / EU D_8007A46C, two sections followed by tick FFFF,
null pointers. Each referenced primary and secondary list has
8-byte entries ending at first FFFF timestamp (primary terminal
pointer zero, secondary FFFFFFFF). All four lists in each image
walked with bounded iteration and image-range pointer checks.
Neither nominal timestamp unit nor semantic game-mode name attributed.

| Section start tick | Primary JP list | Primary events | Secondary JP list | Secondary events |
| ---: | --- | ---: | --- | ---: |
| 0 | 80086C34 | 406 | 80078E14 | 15 |
| 4609 | 800878EC | 373 | 80079A54 | 63 |
| Total | | 779 | | 78 |

857 events; 730 distinct descriptor pointers (652 primary, 78
secondary across both sections), 23 distinct config indices.
Primary unique descriptors per section 342/310; secondary 15/63.
All 857 regional entries agree in timestamp, threshold/unread
halfword, config index and resolved type. All descriptor pointers
relocate by +818 hex EU relative to JP. All config pointers relocate
by +818 or +844; primary script-pointer fields likewise (933/1404
of 2337 field comparisons respectively), not a universal data delta.

Primary gates: 614 threshold 0; 32 threshold 2; 131 threshold 3;
one each threshold 4 and 5. These are authored entries, NOT a
proven difficulty name or active count. All 78 secondary descriptor
gate halfwords equal zero. Low coordinate initializer bits take
0/2 in section one, 0/1/2 in section two (observed flags values).
Primary section 1 has one timestamp inversion (4323 -> 4320);
secondary section 2 has one (1504 -> 1310). Preserve stored order:
sorting would change execution given the scheduler's cursor and
current/previous tick filtering. The environment schedule also
has a nonmonotonic pair; do not silently normalize it.

## 2. Type distribution

| Runtime type (hex) | Section 1 | Section 2 | Total |
| --- | ---: | ---: | ---: |
| 19 | 11 | 0 | 11 |
| 1D | 0 | 74 | 74 |
| 20 | 6 | 0 | 6 |
| 50 | 34 | 0 | 34 |
| 60 | 342 | 259 | 601 |
| 68 | 0 | 40 | 40 |
| 70 | 7 | 0 | 7 |
| 71 | 5 | 0 | 5 |
| 78 | 1 | 0 | 1 |
| 79 | 13 | 0 | 13 |
| 80 | 1 | 0 | 1 |
| 81 | 0 | 51 | 51 |
| 88 | 0 | 5 | 5 |
| 89 | 0 | 1 | 1 |
| 90 | 1 | 0 | 1 |
| 98 | 0 | 6 | 6 |
| Total | 421 | 436 | 857 |

641 events use the two recovered dual-clock types 60/68 (74.8%
of all events). Type 98 is a real descriptor-resolved value but
its dispatch slot is the default clear handler. Config index 58
hex points at JP 800AB96C, within the same near-global-data region
as other referenced short configurations (50/64/66 hex).
This is not proof of an unused enemy: inspect writes to these
addresses before interpreting static initial values as immutable.
Do not confuse config indices with runtime type values.

## 3. Structural decode of known script families

All primary descriptor pointer fields: 280 distinct +14 pointers,
112 distinct +18 pointers, 77 distinct +1C pointers (counts by
field, including shared empty-stream pointers).
Restrict semantic decoder to types 60 and 68, whose command consumers
are established. Deduplicate by (field, pointer), not by spawn.
For each script: bound to 1024 records, require pointer in loaded
image, 2-byte alignment, nondecreasing timestamps, known active
opcodes -10..-2, 4-byte alignment of opcode -10 word operand,
operand extent within image. Stop at timestamp FFFF or explicit
opcode -1/0. Any other condition is an unresolved decode, not an
invented record. These guards are analysis policy, not original
engine checks.

| Clock | Distinct stream references | Active commands | FFFF timestamp stop | Explicit -1 stop | Max active commands/stream |
| --- | ---: | ---: | ---: | ---: | ---: |
| Section-relative (+54 object) | 100 | 111 | 90 | 10 | 2 |
| Object-local (+58 object) | 77 | 132 | 76 | 1 | 4 |
| Total | 177 | 243 | 166 | 11 | |

All 177 field-qualified streams decode without guard failures and
match corresponding EU streams in timestamps, opcodes and every
active operand halfword. All explicit stops are -1 (none zero).
FFFF timestamp stops are future timestamp guards, not executed
terminators in normal time ranges. Counts exclude terminal records.
No reproduction of complete authored scripts here.

| Opcode | Section clock | Local clock |
| ---: | ---: | ---: |
| -10 | 22 | 8 |
| -9 | 0 | 8 |
| -8 | 0 | 0 |
| -7 | 10 | 16 |
| -6 | 4 | 1 |
| -5 | 1 | 35 |
| -4 | 0 | 24 |
| -3 | 0 | 0 |
| -2 | 74 | 40 |

Notably no -8/-3 commands in these two families' inventoried
streams; this does not prove unused engine functionality.
Third stream +5C not decoded; 280 unique descriptor references
are not necessarily 280 unique movement paths.

## 4. Mode-nonzero schedule: explicit blocker/lead

JP D_80079C78 / EU D_8007A490: two normal entries at ticks
0 and 6302, then FFFF terminal. Both entries in JP reference
the same primary 800AB968 and secondary 800AB5F8.
EU counterparts relocate +844. Secondary begins with FFFF.
Primary initial bytes do NOT form valid static encounter list:
first apparent timestamp 144 and pointer 019A0098 outside image.
The same initial words are observed in EU. Do not walk past
this invalid pointer, call the nonzero mode empty, extrapolate
content, or claim both game modes decoded. The primary pointer
also serves as config index 50 hex (runtime type 90), so trace
runtime setup, table mutation or deliberate overlay semantics.
No independent runtime witness yet.

## 5. Next

Trace third stream and +5C consumers (especially type 90 and types
60/68), then derive the mission tick writer and its cadence.
Investigate the nonzero mode's shared mutable/aliased addresses and
type 98 before assigning narrative labels or counting real enemies.
A reusable local extractor should reproduce this bounded inventory
with strict SHA-1/PS-X header checks and synthetic malformed-data
tests, emitting summarized JSON rather than raw game data to Git.
No source changes, retail builds, runtime checks or new binary
commits in this pass.

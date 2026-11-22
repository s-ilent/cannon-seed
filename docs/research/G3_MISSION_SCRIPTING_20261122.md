# G3 mission scheduling, encounter creation and object command streams

R1 pass 11, 2026-11-22. Static analysis at main 173e1dfb and research
branch 76b92402. Extends [fragment effects](G3_FRAGMENT_EFFECTS_20261122.md).
This pass resolves the general authored-object creation path at 80030FF8,
rather than the specialized fragment constructor.

## Evidence and regional comparison

JP [scene assembly](../../asm/g3_jp/nonmatchings/func_8002A2DC.s)
(YAML ROM AADC, length 9910), [object assembly](../../asm/g3_jp/nonmatchings/func_80033C44.s)
(ROM 14444, length 10EF4). EU [scene](../../asm/g3_eu/nonmatchings/func_8002A2CC.s)
and [object](../../asm/g3_eu/nonmatchings/func_800338AC.s).
EU = JP - 398 hexadecimal in these windows. Half-open addresses;
compare raw words and disassembly with address-bearing labels normalized.

| Responsibility | JP VA range | JP ROM range | EU start | Words | Exact | Shape |
| --- | --- | --- | --- | ---: | ---: | ---: |
| Timeline init and top-level driver | 80030B68..80030C1C | 11368..1141C | 800307D0 | 45 | 30 | 45 |
| Environment and object dispatch | 80030C7C..80030D4C | 1147C..1154C | 800308E4 | 52 | 44 | 52 |
| Encounter scheduling | 80030DBC..80030FF8 | 115BC..117F8 | 80030A24 | 143 | 114 | 143 |
| General spawn constructor | 80030FF8..8003126C | 117F8..11A6C | 80030C60 | 157 | 144 | 157 |
| Secondary spawn timeline/constructor | 8003126C..80031468 | 11A6C..11C68 | 80030ED4 | 127 | 113 | 127 |
| Dual object command-stream driver | 80033E44..8003402C | 14644..1482C | 80033AAC | 122 | 100 | 122 |
| Command decoder | 80034068..8003416C | 14868..1496C | 80033CD0 | 65 | 45 | 65 |
| Selected command handlers | 80033C44..80033E44 | 14444..14644 | 800338AC | 128 | 121 | 128 |
| Total | | | | 839 | 711 | 839 |

No overlapping known target-scoped committed SDK anchors in these
windows. The command decoder has a call labelled SsGetNck in a
separate anchored row; its semantics are not attributed in this pass.
The game-specific clocks, pointer tables and object state establish
positive ownership of the selected windows. No fresh local census,
retail builds, runtime traces or raw authored data inspection.

## 1. Timeline hierarchy

80030B68 (called 800429E8) selects data based on D_800ABF9C:

| Stream | Mode 0 start JP | Nonzero mode start JP | Cursor |
| --- | --- | --- | --- |
| Encounter section timeline | D_80079C54 | D_80079C78 | D_800AC244 |
| Environment timeline | D_8008A274 | D_8008A2BC | D_800ABE54 |

Also clears section index D_800ABE8C and rotating hit index
D_800ABE5C; calls 80030C1C to bit-reverse the low four player-mask bits.
The exact game-mode meanings remain pending.

80030BEC orders environment step (80030C7C), encounter scheduler
(80030DBC), then object dispatch (80030CC8). It is called twice at
80042ADC and 80042AEC with D_800AC29C first zero then s0; prior damage
atlas identifies the ==1 gate. Do not assume all simulation counters
advance exactly once per displayed frame. D_800AC16C is a u16
absolute mission-time-like counter (reset to zero at 800405A4,
80044764, 8004490C); exact writer/time-unit still needs tracing.

Environment entry, 8 bytes:
- +0 u16 absolute tick
- +2 u16 environment-mode value -> D_800ABF5C
- +4 s32 boundary value -> D_800ABE3C

If timestamp <= current absolute tick, advance cursor by 8 and apply.
At most one entry per call, unlike encounter loops. Both values are
consumed by the debris boundary/acceleration system (pass 10).

Encounter section entry, 12 bytes:
- +0 u16 absolute start tick -> D_800AC1FC
- +2 unknown/unread halfword
- +4 pointer to primary encounter list -> D_800AC2EC
- +8 pointer to secondary list -> D_800AC11C

Consume all due entries; increment section index for each and invoke
800315EC (sets D_800ABBFC from D_8008A6F4 indexed by section).
Compute section-relative tick D_800ABFA4 = absolute tick - section
start when signed/unsigned comparison at 80030E70 permits.
Pointer loops have no explicit length bounds; no sentinel values
or table contents recovered. Any skipped section data is replaced
by the latest due section pointers.

## 2. Primary encounter list and general constructor

Primary entry, 8 bytes: u16 section-relative timestamp, s16 minimum
threshold (compared against D_800AC164), pointer to object descriptor.
80030EA4 loops over due entries, consuming them before the gate.
Normally only records timed for current or previous tick are eligible;
older due events are skipped. One special case under D_800ABF9C==1
allows timestamp 0x157E once through gp+0x710. Threshold and special
case semantics unverified. Allocator 80031508 searches 100-slot prefix,
with previous result as next starting point; allocation failure skips
the event and subsequent primary allocations in that invocation.
Descriptor ID 0x18 has additional condition gates (80030F54..FCC);
exact player/difficulty semantics not assumed.

80030FF8 indexes configuration pointer table D_80089D3C by signed
descriptor+0. Copies config pointer to object+60, config+0 to +0
(type), config+A to +2C, config+14+2*D_800AC164 to +2E (durability).
Initializes collision request +28=1, +24/+2A/+32/+7C/+7E=0, +A8=100.
Descriptor+2 low three bits select one of three initializers.
Other values emit a diagnostic, but still reach common tail.

| Primary descriptor offset | Observed meaning |
| --- | --- |
| 0 | s16 configuration index |
| 2 | u16 flags; low 3 bits select coordinate initializer |
| 4,8,C | Three coordinate components (words or low signed halfwords) |
| 10 | angle copied to object+14 |
| 12 | not read in this constructor |
| 14 | pointer copied to object+5C |
| 18 | pointer copied to object+54 (section-time command stream) |
| 1C | pointer copied to object+58 (object-local-time command stream) |

Observed extent at least 0x20 bytes, not proof of array stride.
Mode 0 (8003114C) sets object+26=0, flags+24=0x800, copies full
coordinate words both to +4/8/C and +48/4C/50.
Mode 1 (8003118C) sets +26=1, +24=0x800, stores low halfwords to
+6/A/E and +4A/4E/52 (not full-word initialization).
Mode 2 (800311D0) similar but +24=0x4800 and runs three-component
transform 800326A8. Common tail initializes local timer +6A=-1.

## 3. Secondary encounter list

8003126C loops over all due entries (8-byte stride, u16 timestamp
+0, descriptor pointer +4, +2 unread); no current/previous-tick
restriction shown. Calls 800312E4 then advances regardless of result.
Allocator searches full 124-slot prefix from its base for each event.
Constructor 80031338 called only if allocated and descriptor+0==0.

Secondary descriptor observed extent at least 0x1C bytes:
+0 gate, +2 configuration index, +4/8/C full positions,
+10/12/14 angle halfwords, +18 pointer copied to object+54/+58/+5C.
Config table same D_80089D3C; type and durability same as primary.
Collision request starts -1 rather than 1, +32=1, +68=0, +26=0.
Do not assume these are universally scenery vs enemies before
examining descriptor values and dispatch table.

## 4. Persistent object dispatch

80030CC8 walks all 124 records stride AC, including type 0.
Loads function pointer from D_8008A2F4 + 4*signed(object+0),
calls it with object pointer, advances iterator in delay slot.
No bounds check or occupancy test in caller. 80031468 advances
the 16-bit pseudo-random recurrence after every callback.
Actual type -> function table entries remain unavailable, including
type-zero mapping; no claim that labels correspond to particular IDs.

## 5. Two script clocks per object

80033E44 and another family at 80038BA8..80038C4C use the same
decoder with separate cursors +54 and +58. First family gates
activation with +24 bit 0x8000 and 800327F8, then:
1. Read u16 timestamp from object+54; if <= section-relative D_800ABFA4
   decode following command using a temporary cursor pointer.
2. Return 0 commits advanced cursor to +54 and loops to consume due
   commands. Nonzero clears object+0 and exits in first family.
3. When next timestamp is in future, increment object+6A (initialized
   -1 by the primary constructor); process +58 identically against it.
4. On future local timestamp, proceed to hit/damage, movement and
   rendering logic. Exact per-frame cadence depends on scheduler gates.

A command record is thus timestamp(u16), opcode(s16), variable operands.
80034068 reads opcode, increments cursor by 2, sign-normalizes
(opcode+17) as s16, admits values -17..0 and indirect-jumps through
jtbl_80020C44. Out-of-range calls 80033BB0 (returns -1).
The branch arms reference nine visible handler calls; table entries
not recovered so no exact opcode number assigned. 80033BB8 returns 0.
Some arms use other pre-row helpers; one is labelled SsGetNck in
the committed assembly. No unsupported SDK semantic attribution.

| Handler | Operand bytes after opcode | Observable writes |
| --- | ---: | --- |
| 80033BC0 | 0 | +32=1, +68=0 |
| 80033C44 | 0 | clear +24 bits 0xC00 |
| 80033C74 | 2 | set +24 bit 0x1000; operand to +7C |
| 80033CC0 | 2 | clear +24 bit 0x1000; operand to +7C |
| 80033D0C | 2 | set +24 bit 0x2000; operand to +7E |
| 80033D58 | 2 | clear +24 bit 0x2000; operand to +7E |
| 80033DA4 | 6 | set +24 bit 0x400; read word and s16; store angle difference in +80 and signed step in +76 |
| 80033E14 | 0 | clear +24 bit 0x400 (adjacent helper, not a proven decoder arm) |

80033DA4 computes difference word - current signed +14 angle,
negates step if difference negative, stores step and negated
difference. Word load implies alignment constraint in authored data;
no invented padding rules. Exact motion flag meaning needs consumers.

**Pass 12 correction and closure:** [retail dispatch atlas](G3_RETAIL_DISPATCH_TABLES_20261122.md) recovers the actual 18-entry opcode and full 256-entry object dispatch tables. Type 60 is the first scripted family, 68 the second, 38 the fragment updater. The opcode -3 handler is game-specific despite the current SsGetNck SDK anchor; adjudication pending. Source-only uncertainty about these table entries is superseded by the independently SHA-1 verified private executable inputs.

## Next

Recover actual data table entries using a witnessed local extraction
of non-sensitive symbolic/structural metadata (not raw copyrighted
assets). Priority addresses: mission/environment tables, object
config pointer table D_80089D3C, object dispatch D_8008A2F4,
command jump table jtbl_80020C44, damage jump tables.
Trace third object cursor +5C and movement handlers, and the global
mission tick writer. The full path from scripted encounter to live
object to hit processing and rendering is now structurally established.
Potential future matching candidates: 8003114C (0x40) and 8003118C
(0x44) after oracle; no executable source changes this pass.

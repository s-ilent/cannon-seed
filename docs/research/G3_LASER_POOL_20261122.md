# G3 player-laser producer pool and lifecycle

R1 pass 7 (bounded laser sub-family), 2026-11-22. Static source review at
`173e1dfb434caac71ef4cecf1bf815443ca16037`. No new retail oracle, runtime trace,
C conversion, name adoption or coverage edit. Extends the
[Communication Buffer schema](G3_COMM_BUFFER_SCHEMA_20261122.md).

## Result

The persistent laser pool is **32 × 0x84-byte records**, JP
`D_80163944` (exclusive end 0x801649C4), EU `D_80164270`
(exclusive end 0x801652F0). It is separate from the immediate scene-request
pool. An allocation binds a laser to a caller-owned object in both
directions. A three-stage state machine runs setup, hit-processing and a
short endpoint-effect lifetime, with intentional same-call fallthrough.

## Source and regional evidence

JP [asm](../../asm/g3_jp/nonmatchings/func_80033C44.s), YAML row ROM
0x14444/VA 0x80033C44, size 0x10EF4; EU
[asm](../../asm/g3_eu/nonmatchings/func_800338AC.s), ROM 0x140AC/VA 0x800338AC,
same row size. These row labels are not individual function extents.
Comparison below uses half-open windows, parsing address, 4-byte opcode
word and disassembly from each committed file. Normalize address-bearing
func_/D_/jtbl_/L_ labels only; compare the remaining mnemonic, register and
operand text, and separately count completely identical words.

| Responsibility | JP VA start..end | JP ROM start..end | EU VA start | Words | Exact words | Normalized |
| --- | --- | --- | --- | ---: | ---: | ---: |
| Pool reset and scan | 8003E734..8003E814 | 1EF34..1F014 | 8003E39C | 56 | 51 | 56 |
| Mode dispatcher | 8003E814..8003E8A4 | 1F014..1F0A4 | 8003E47C | 36 | 28 | 36 |
| Setup and hit-processing | 8003E8A4..8003ECB0 | 1F0A4..1F4B0 | 8003E50C | 259 | 237 | 259 |
| Endpoint/lifetime | 8003ECB0..8003ED7C | 1F4B0..1F57C | 8003E918 | 51 | 50 | 51 |
| First-free allocator | 8003F7E4..8003F854 | 1FFE4..20054 | 8003F44C | 28 | 26 | 28 |
| Total | | | | 430 | 392 | 430 |

No overlapping committed SDK anchor in either target between the first
window and allocator end (checked target-scoped intervals in
[config/sdk_anchors.txt](../../config/sdk_anchors.txt)). The literal
mylaser.c diagnostic plus the game-specific pool and mode behavior are
positive game-ownership evidence; SDK memset is a callee, not the owner.
No fresh archive extraction or census execution was performed.

## Allocation and lifetime

- `8003E734..8003E784`: clears each slot with memset(slot,0,0x84),
  increments by 0x84 and loops exactly 0x20 times. Calls at 80044868 and
  800449F4.
- `8003E784..8003E814`: first clears halfword +0x2A in 124 records of
  stride 0xAC at D_8016B014 (EU D_8016B138); then scans the 32 laser slots
  and calls 8003E814 only for nonzero signed halfword +0x0. Called from
  80042AB0. Do not equate that separate 0xAC array with the allocator's
  caller object without an incoming-pointer proof.
- `8003F7E4..8003F854`: first free slot (halfword +0x0 == 0); writes
  +0x0 = 8, +0x2C = caller pointer, +0x28 = caller halfword +0x0,
  caller +0x64 = slot pointer, +0x24 = 0, +0x80 = caller halfword +0x88.
  Returns 1 on success, 0 if no slot. It does NOT clear the entire slot
  when reused. Wrapper 8003F79C calls 80029FC0(0xB), then allocates if
  D_800AB26C == 0; success sets gp+0x74C halfword to 1. Wrapper callers
  in this file: 8003F650, 8003F724, 8003F750, 8003F784.
- `8003E814`: signed halfword +0x24 selects mode 0 (8003E8A4),
  1 (8003EAB4), 2 (8003ECB0); otherwise diagnostic. The calls at
  8003E860, 8003E868, 8003E870 are consecutive: mode 0 executes
  0→1→2 in one call, mode 1 executes 1→2, mode 2 executes only 2.
  Each of the first two handlers increments +0x24.
- Mode 0 sets +0x26=2, derives origin, orientations and intermediate
  vectors from the caller object, including +0x52/+0x54/+0x56.
  Mode 1 processes collision-related spatial data and advances mode;
  exact hit-test semantics and gate globals remain open.
- Mode 2 recomputes endpoint halfwords +0x3C/+0x3E/+0x40 from
  origin halfwords +0x36/+0x38/+0x3A and scaled direction terms,
  indexed by 2 - lifetime. It is not cumulative integration.
  Lifetime decrements at 8003ED5C. On zero, 8003ED78 clears +0x0
  **and falls through into the descriptor emitter** 8003ED7C.
  On nonzero the branch at 8003ED70 goes directly to that same emitter.
  Thus the final active scan still submits one type-E request even
  when the slot becomes free. This corrects the implication in pass 6
  that only surviving records emit; the position fields are halfwords
  rather than words in the producer, widened to words in the request.

## Partial field map (offsets within 0x84 record)

| Offset | Storage / role | Evidence |
| --- | --- | --- |
| 0x00 | u16 occupancy/type, 0 free, allocator writes 8 | allocator/reset/scan |
| 0x10, 0x12 | u16 request orientation inputs | setup and emitter |
| 0x24 | s16 lsr_mode, 0/1/2 | dispatcher, literal diagnostic |
| 0x26 | s16 lifetime, initialized to 2 | 8003E8C0, 8003ED5C |
| 0x28 | u16 effect/resource selector from caller+0 | allocator/emitter |
| 0x2C | 32-bit caller/owner pointer | allocator and mode 0 |
| 0x36..0x3A | three s16 origin coordinates | mode 0 copy, mode 2 reads |
| 0x3C..0x40 | three s16 recomputed endpoint coordinates | mode 2 writes; request widens |
| 0x44..0x4A | two word-initialized pairs, consumed as s16 direction/scale terms | mode 0 stores at +44/+48; mode 2 reads four halfwords |
| 0x80 | s16 hit class, copied from caller+0x88 | allocator; emitter dispatch |

Do not name the unresolved direction terms as independent x/y/z
velocities: mode 2 multiplies the second term by the third/fourth
for two axes; +0x44 is used separately. The original fixed-point
representation needs its own review. Caller +0x64 is a back-reference,
but whether it is cleared after slot release remains unproven.

**Pass 8 continuation:** [gunner and target pool atlas](G3_GUNNER_TARGET_POOL_20261122.md) resolves all four caller arguments to the separate 4×0x8C gunner array, not the 124×0xAC collision participant pool. It also confirms the inspected release path leaves the owner back-reference unchanged.

## Candidate landing and next step

The reset loop and first-free allocator are reasonable small semantic-C
candidates (0x50 and 0x70 bytes respectively, complete entry/exit bodies),
subject to separate landing decision and full retail oracle. The latter
depends on a partial definition of the caller object; avoid premature
global type names or field semantics.

Next: trace wrapper caller arguments at 8003F650/724/750/784 back to
their pool(s), determine whether the 124×0xAC array is the parent pool,
and map allocation/release/back-reference maintenance and hit-class
writers. Separately the spawn-API object structure and D_800ABBE4 model
table/TMD.DAT mapping remain pending. EU dispatcher ownership gate stays
untouched.

# G3 player/gunner records and collision-participating object pool

R1 pass 8, 2026-11-22, static source review at main 173e1dfb and
preceding laser atlas branch 011b6e4e. Extends
[G3 laser pool](G3_LASER_POOL_20261122.md). No fresh retail build,
runtime trace, source conversion or coverage modification.

## Result: separate owner and target pools

The four callers of the laser wrapper converge on a **four-entry 0x8C
player/gunner record array** at JP D_801474FC (EU D_80147E28).
The 124×0xAC array D_8016B014 is NOT that parent pool: it is scanned
as collision participants and also allocated by game-object creators.
Its three contiguous allocator endpoints divide it into 74, 26 and 24
records; the wrappers scan prefix ranges rather than isolated partitions.

## Source and cross-region comparison

JP [game/laser assembly](../../asm/g3_jp/nonmatchings/func_80033C44.s)
(row ROM 0x14444, size 0x10EF4) and [scene/object helpers](../../asm/g3_jp/nonmatchings/func_8002A2DC.s)
(row ROM 0xAADC, size 0x9910). EU counterparts are
[game/laser](../../asm/g3_eu/nonmatchings/func_800338AC.s) and
[scene/object helpers](../../asm/g3_eu/nonmatchings/func_8002A2CC.s).
All comparison windows use end-exclusive VAs, with EU = JP - 0x398 for
these windows. Normalize only address-bearing symbol labels in the
disassembly and separately compare raw words, as in the preceding atlas.

| Window | JP VA | JP ROM | EU VA start | Words | Exact | Normalized |
| --- | --- | --- | --- | ---: | ---: | ---: |
| Gunner iteration and update | 8003F198..8003F6E8 | 1F998..1FEE8 | 8003EE00 | 340 | 287 | 340 |
| Trigger cadence and wrapper | 8003F6E8..8003F7E4 | 1FEE8..1FFE4 | 8003F350 | 63 | 56 | 63 |
| Hit notification | 8003EC1C..8003EC7C | 1F41C..1F47C | 8003E884 | 24 | 22 | 24 |
| Target scan | 8003FAA8..8003FBB4 | 202A8..203B4 | 8003F710 | 67 | 56 | 67 |
| Target reset | 80044A6C..80044A90 | 2526C..25290 | 800446D4 | 9 | 8 | 9 |
| Object allocator family | 80031490..800315EC | 11C90..11DEC | 800310F8 | 87 | 72 | 87 |
| Total | | | | 590 | 501 | 590 |

Committed target-scoped SDK anchor intervals do not overlap these
windows; caller/target state and literal mylaser.c/hit_check diagnostics
give positive game ownership evidence. No fresh SDK archive extraction
or live census was run.

## 1. Player/gunner ownership and trigger schedule

At JP 80042AA8 calls 8003F198, immediately before the laser update call
at 80042AB0. The former iterates D_801474FC, 4 entries, strides 0x8C,
and calls 8003F1E0 for each at 8003F1B4. 8003F200 saves its argument
in s2; no reassignment to s2 in the gunner update. The four wrapper
calls preserve the same pointer:

| Wrapper call | Entry | Origin |
| --- | --- | --- |
| 8003F650 | direct | s2 |
| 8003F724 | 8003F6E8 | s2 passed at 8003F620, preserved in s0 |
| 8003F750 | 8003F6E8 | same s0 |
| 8003F784 | 8003F77C | s2 passed at 8003F630, argument preserved |

The 80034C60 region also indexes and wraps this four-record array by
gunner index and consults a bit mask; 8003F204 reads +0 as the index used
to select a halfword from D_80165E4C and test D_800AC17C. These and the
aiming/firing logic support the player/gunner identification. The precise
cabinet/port/network mapping remains open.

At 8003F494 the update bypasses firing if D_800ABE74 < 2. A special
D_800AC37C == 4 route goes directly to firing, otherwise the active-index
mask and D_80165E4C value gate the dispatch. The signed 16-bit key
(player+24 << 4) OR player+28 selects these observable actions
(offsets hexadecimal; key values hexadecimal):

| Key | Action |
| --- | --- |
| 00 | no-op |
| 04, 40, 44, 4C, C4 | cadence function 8003F6E8 |
| 08, 48, 80, 84, 88, 8C, C8 | immediate attempt via 8003F77C |
| 0C, C0, CC | reset +2C to 0 |
| other | bypass |

The cadence function increments u16 +2C (written in branch delay slot),
calls the wrapper if +5C == 1, then independently tests the counter.
If +5C == 0 and the incremented counter is negative it exits;
otherwise odd counters skip, counter 4 sets it to -1, and other even
counters call the wrapper. Thus a +5C==1 path may attempt allocation twice
in the same call; no assumption that it is a menu/button bit or that
all combinations are reachable. This is an instruction-level table,
not observed firing rates or a guessed controller map.

## 2. Collision participants and object allocation

80044A6C clears each 0xAC record's +0 active/type halfword from
D_8016B014 through 124 slots. EU base D_8016B138. The hit scan at
8003FAA8 initializes laser+68 to -1, iterates that same array, skips
inactive records, and dispatches on signed target+28:

| Value | Action |
| --- | --- |
| 0 | no-op 8003FBB4 |
| 1, -1 | 8003FBBC, rejects negative target+2E, switches on target+26 (0/1/2) |
| 2 | no-op 800403FC |
| other | literal Invalid hit_req diagnostic |

80040404 computes sum of squared three components, compares unsigned
against laser+68 and updates +68 and +6C (target pointer) on a smaller
value. The exact callers/geometry of this helper are a follow-up.
The scan accepts values <= 0x17D783FF using an unsigned comparison;
do not conflate that with all geometric tests or assume its world units.

The scene-file first-free allocator family supplies three end bounds.
All starts are caller-provided or D_8016B014 via 80031580.

| Exclusive bound JP | EU | Prefix slots | Incremental region | Base-start wrapper / caller-start wrapper |
| --- | --- | ---: | ---: | --- |
| 8016E1CC | 8016E2F0 | 74 | 74 | 80031530 / 80031558 |
| 8016F344 | 8016F468 | 100 | 26 | 800314E0 / 80031508 |
| 80170364 | 80170488 | 124 | 24 | 80031490 / 800314B8 |

800315AC scans +0 == 0, stride AC; on success writes +A8=100 and
+30=-1, returns the pointer, does not mark occupancy or memset the slot.
On exhausting bound it returns NULL. The bound is checked after advancing,
so callers must supply an in-range start; not an independently safe
general allocator. No semantic meaning for the subranges is yet established.
Creators 80039714 and 8003AB40 use the 124-bound wrapper and write
type 0x31 and +30; 8003D690/8003D8E0 use the 74-bound wrapper,
then 8003D9FC initializes a record from a table. Position words at
+4/+8/+C and model id +30 align with earlier spawn emitter evidence.
No assumption that every active record is a damageable enemy.

## 3. Hit notification and ownership teardown

8003EC1C calls the target scan; on nonzero return it reads laser+6C
as target, laser+28 as shift index, ORs (1 << index) into target+2A
(halfword), and writes 1 to owner+60 through laser+2C. The preceding
laser update (8003E784) clears every target+2A before iterating active
lasers. This is a shared hit-mask accumulation over that pass.
If target+28 is negative and target+26 == 0 it additionally calls
8003F068. Exact score/damage consumers remain pending.
The release instruction 8003ED78 only clears laser+0; no owner+64
clear occurs on this release path. The first-free allocator overwrites
owner+64 on successful creation; external clearing and pointer validity
rules are not established. Do not treat the pointer as an owning smart
reference or assume exclusivity (the same owner can attempt multiple
allocations). No exhaustive cross-file pointer-use claim.

## Next

Follow target+2A consumers and target creation/teardown, especially
8003D9FC and its table D_8008A220, to reconstruct damage and object
types. Also pending: model-table D_800ABBE4/TMD.DAT resource mapping.
Small potential C candidates are reset 80044A6C (0x24) and
800315AC (0x40), subject to full oracle and separate landing decision.

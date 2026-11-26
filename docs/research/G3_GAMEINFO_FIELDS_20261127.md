# R1 pass 24 — the gameinfo field maps completed: the
# instruction-verified set_game_info binding, the player-record pass
# (get_player_info pinned, both 73-slot tables mapped), and the
# caller censuses

Date: 2026-11-27 (window cron-20261126-2209, same window as passes
22-23 — the refreshed R1 questions (a)+(b)). Scope: g3_jp only,
JP-first discipline. Docs + one curated bank; zero source, YAML, asm
or oracle change; zero renames.

## 1. The set_game_info binding — instruction-verified (closes the
## pass-23 honest gap)

Every setter case body was read; the store target and the validation
window are now pinned per id. The key register fact that fixes the
picture: in the setter cases **a1 = the flag cell 0x80010000** (left
over from the prologue's flag read) and **s1 = the flag-selected
record base** (0x800100B8 / 0x800105F0) — so the two "flag" fields
and the record fields are distinguishable, and each setter store
matches its getter twin exactly:

| id | field (the case's own error string) | store target | validation |
|----|-------------------------------------|--------------|------------|
| 0x0 | mission | flag+0x0 = 0x80010000 | val < 2 |
| 0x1 | TV_MODE | flag+0x2 = 0x80010002 | val < 2 |
| 0x2 | LEVEL | record+0x0 | (val-1) < 4 → val 1..4 |
| 0x3 | (unvalidated) | record+0x2 | — |
| 0x4 | PARTNER NAME ("Too long PARTNER NAME", D_800202C0, line 0x114) | record+0x4 (strcpy) | strlen < 10 |
| 0x5 | PLAY_RECORDING | record+0xE | val+1 < 5 → 0..3 |
| 0x6 | CLEAR_LEVEL | record+0x10 | val < 5; the tail also clears record+0x12 when val == 0 |
| 0x7 | (unvalidated bitfield) | record+0x12 | OR'd in on nonzero, cleared on zero |
| 0x8 | PAUSE_DISP | 0x80010B28 | val < 2 |
| 0x9 | (unvalidated) | 0x80010B2A | — (the field getter(9) reads — the mode-4 step-count source pass 22 armed D_800AC164 from) |
| 0xA | MUTEKI_MODE | 0x80010B2C | val < 2 |
| 0xB | MAP_COUNTER_DISP | 0x80010B2E | val < 2 |
| 0xC | SUPER_BLASTER | record+0x536 | val+1 < 2 |
| 0xD | (unvalidated) | 0x80010B30 | — |
| 0xE | (unvalidated) | 0x80010B32 | — |
| 0xF | TUNE_LEVE[L] | 0x80010B34 | val < 2 |
| 0x10 | PARTNER_G_NUM | record+0x534 | val < 4 |
| 0x11 | (unvalidated) | 0x80010B36 | — |

The id-0xC cross-base consistency check: the setter stores
`s1 + 0x536` — 0x800105EE under base A (0x800100B8) or 0x80010B26
under base B (0x800105F0) — exactly the two words getter(0xC)'s slot
probe reads (a1+0x5EE and a1+0xB26 absolute from 0x80010000). The
getter probes BOTH bases' slot words; the setter writes the CURRENT
base's. The string order is NOT the id order (PAUSE_DISP is id 8,
MUTEKI_MODE id 0xA, TUNE_LEVEL id 0xF, PLAY_RECORDING id 5...) —
the pass-23 table-order guess was wrong in detail and is superseded
by this verified map. Verified consequences: **record+0x0 = LEVEL**
(the pilot loader's getter(2) numeric switch), **the flag halfword
0x80010000 = mission**, and getter(2) vs getter(6) in the metric-rank
tail = LEVEL vs CLEAR_LEVEL.

The pilot loader's three set_game_info writes (raw words in the
code-in-data region): **set_game_info(3, -1)** at 0x80022A98 (record
field 0x2 parked at -1), **set_game_info(4, src)** at 0x80022AA8 with
src = 0x800BB2B0 — runtime RAM beyond the image, not a static string
(the partner name comes from loaded data) — and
**set_game_info(0x10, func_80045C10() >> 16)** at 0x80022AD0, the
PARTNER_G_NUM from a runtime read, followed by the D_800ABE44 = -1
park.

## 2. get_player_info pinned — func_80025C1C

The getter block func_80025C1C (0x80025C1C..0x80025D94) is the
player twin of get_game_info's structure: a1 = the record index
scaled by the **stride-0x2C** record computation (x11*4) onto the
base **0x80010008**, a0 = the id offset by **-0x10** and range-checked
against **0x49** (ids 0x10..0x58), the error tail func_80025D94
printing get_player_info's string (line 0x241), dispatch through
**jtbl_80020660**, case bodies = lhu at per-field offsets returning
sign-extended through func_80025DB0. The id space therefore runs
**0x10..0x58** (73 slots), NOT 0..0x11 — the player family and the
game family are two separate id spaces.

## 3. Both 73-slot tables mapped — 22 live fields, 51 error-padded

Both tables are padded with their own error path for unmapped ids
(the setter pads with func_80025BF4, the getter with func_80025D94):
only 22 ids have real fields. The live map (offsets relative to the
record head; v1 = head+6):

- **ids 0x10 / 0x11 / 0x12** → head+0x0 / +0x2 / +0x4
- **ids 0x20..0x24** → head+6+0x0 / +0x2 / +0x4 / +0x6 / +0x8
- **id 0x30** → head+6+0xA
- **ids 0x40 / 0x41 / 0x42** → head+6+0xC / +0xE / +0x10
- **ids 0x50..0x58** → head+6+0x12 / +0x14 / +0x18 / +0x1C / +0x20 /
  +0x24 / +0x16 / +0x1A / +0x1E / +0x22 (the non-monotonic tail order
  is identical in both tables)

So the player record = a 0x2C-byte structure at 0x80010008 + rec*0x2C
with three head halfwords and a halfword tail at bytes 0x6..0x2A;
the table's scattered order groups the fields by stride bands, not
by offset order. Every unmapped id slot is a loud error path — no
silent zero returns.

## 4. The caller censuses

**get_player_info (5 sites)**: func_80044B4C.s 0x80044E6C
(get_player_info(0x11, s0) → stored to a caller record+0x2C) and
0x80045C4C (get_player_info(0x11, lh(D_80010E06)) — the record index
from a below-image cell); func_80046C30.s 0x80046DA0
(get_player_info(0x11, (short)a0) — the index is the caller's
argument); func_80022AFC.s 0x80022C2C (get_player_info(0x11,
lh(D_800ABE44)) — the metric formatter, the same function that reads
get_game_info(2), and 0x80023EC8 (get_player_info(id, (short)s5)).

**set_player_info (3 sites)**: func_80044B4C.s 0x80045A54
(set_player_info(0x11, rec, lh(D_80010E08)) — the value from a
below-image cell, with D_80010E04 written alongside);
func_80022AFC.s 0x80022C90 / 0x80022CA8 — the paired
set_player_info(0x10, rec, 1) / set_player_info(0x10, rec, 0)
(the metric formatter's flag set/clear on field head+0x0).

The dominant ids are 0x10 / 0x11 (the record head); the record
indices come from below-image cells 0x80010E04 / 0x80010E06 /
0x80010E08 and the game-side record word D_800ABE44 — the player
records are per-player slots selected by the launcher's hand-off
state, and the game writes them back (the metric formatter's
0x10 = 1 / 0 = 0 pair).

## 5. The curated bank (inert, scan-time input)

One name banks under `// target: g3_jp`, closing pass 23's
deliberate hold:

- `get_player_info = 0x80025C1C` — the entry point is now pinned
  (prologue + 0x49 range check + jtbl_80020660 + its own error
  string's tail), the same evidence class as its three siblings.

## What this closes and what it opens

Closed: the refreshed R1 questions (a) (the player-record pass —
entry pinned, both tables mapped, the record schema measured) and
(b) (the set_game_info binding verified per case, superseding the
pass-23 table-order reading).

Open: (a) the field SEMANTICS beyond the named strings — what the
player record's 22 fields hold at runtime (the below-image cells
0x80010E04/06/08's roles, D_800ABE44's record-number source) is
runtime territory; a PCSX-Redux trace per RUNTIME.md would name
them; (b) the EU corroboration walk (passes 20..24); (c) the
stride-12 work base (unchanged); (d) the attract state timer
D_800ABE7C's per-state value map (unchanged); (e) when disc links
return, runbook Phase A/B; fresh-set request rides every report.

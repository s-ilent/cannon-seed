# R1 pass 23 — the gameinfo accessor family: get_game_info's complete
# id map, its set_game_info write twin, and the player_info pair

Date: 2026-11-27 (window cron-20261126-2209, same window as pass 22 —
the R1 queue's refreshed next-question (a)). Scope: g3_jp only,
JP-first discipline. Docs + one curated function-name bank; zero
source, YAML, asm or oracle change; zero renames (the curated names
are INERT scan-time inputs per the c32d807d convention).

## The question this pass closes

Pass 20's item (e), carried through pass 22's refresh: the getter
func_80025944 id map (the pass-20 ids 0x11/2/3/4/5/0xA/0xF plus the
pass-22 in-situ pair 8/9) including the stateful slot-2 wrinkle.

**Verdict: the getter is `get_game_info()` of `gameinfo.c`** — its
own bad-id printf names both (the format string
`"%s(%d):Invalid mode switch in get_game_info()\n"` at D_80020450
with a1 = D_80020174 = the literal "gameinfo.c" and a2 = 0x194, the
source line number). The pass-20 "stateful slot-2 wrinkle" resolves
mechanically: ids 2/3/4/5/6/7/0x10 read from a record base that the
prologue selects by the halfword at 0x80010000 — 0x800100B8 when the
flag is 0, 0x800105F0 when nonzero.

## get_game_info(id) = func_80025944 — the structure

Prologue: `a1 = 0x80010000`, `flag = lh(0x80010000)`; record base
`v1 = flag ? 0x800105F0 : 0x800100B8` (the two candidate record
regions of the below-image resident block). The id is sign-extended
halfword, range-checked `0x11 < id` (unsigned) — ids beyond 0x11 go
to the printf error path (and return the caller's stale s0 — the
undefined-value path). Valid ids 0x00..0x11 dispatch through the
18-entry table **jtbl_80020480** (0x80020480) to per-field case
bodies; every case returns a sign-extended halfword except id 4.

The complete id map (case address → what it reads → return class):

| id | case | reads | class |
|----|------|-------|-------|
| 0x0 | 0x800259A4 | lh 0x80010000 (the flag itself) | signed halfword |
| 0x1 | 0x800259B0 | lhu 0x80010002 | signed |
| 0x2 | 0x80025A1C | lh *record_base* (stateful) | signed |
| 0x3 | 0x80025A28 | lhu *record_base* + 2 | signed |
| 0x4 | 0x80025A3C | — | **POINTER** (record_base + 4) |
| 0x5 | 0x80025A44 | lh record+0xE | signed |
| 0x6 | 0x80025A50 | lh record+0x10 | signed |
| 0x7 | 0x80025A5C | lh record+0x12 | signed |
| 0x8 | 0x800259BC | lhu 0x80010B28 | signed |
| 0x9 | 0x800259C8 | lhu 0x80010B2A | signed |
| 0xA | 0x800259D4 | lhu 0x80010B2C | signed |
| 0xB | 0x800259E0 | lhu 0x80010B2E | signed |
| 0xC | 0x80025A74 | the slot probe: lhu 0x800105EE — if != -1 return 0; else lhu 0x80010B26 → return -1 iff it is 0 | -1 / 0 |
| 0xD | 0x800259EC | lhu 0x80010B30 | signed |
| 0xE | 0x800259F8 | lhu 0x80010B32 | signed |
| 0xF | 0x80025A04 | lhu 0x80010B34 | signed |
| 0x10 | 0x80025A68 | lh record+0x534 | signed |
| 0x11 | 0x80025A10 | lhu 0x80010B36 | signed |

The epilogues: func_80025AC4 (`v0 = s0`, falls through) and
func_80025AC8 (restore ra/s0, return) — the return value is always
v0 = s0.

## set_game_info(id, val) = func_80025590 — the write twin

Identical prologue (flag-selected record base), identical 0..0x11
range check, its own 18-entry table **jtbl_80020408** (0x80020408),
and its own error path func_80025918 printing
`"%s(%d):Invalid mode switch in set_game_info()\n"` (D_800203D4,
line 0x140). The per-field setters validate before storing, and the
validation strings give the FIELD NAMES — the gameinfo block's
documented schema:

- id 0 = **mission** ("Invalid mission value", D_80020140, line 200;
  the setter requires val < 2)
- id 1 = **TV_MODE** ("Invalid TV_MODE value", D_80020180, line 207;
  val < 2)
- **PAUSE_DISP** (D_800201B4, line 211), **MUTEKI_MODE** (the
  invincible mode, D_800201E8, line 215), **MAP_COUNTER_DISP**
  (D_80020220, line 219), **TUNE_LEVE[L]** (D_8002025C, line 223),
  **LEVEL** (D_80020290, line 225), **PLAY_RECORDING** (D_800202F4,
  line 231), **CLEAR_LEVEL** (D_8002032C, line 235),
  **PARTNER_G_NUM** (D_80020364, line 239), **SUPER_BLASTER**
  (D_8002039C, line 243) — the setter's per-field validation errors
  at source lines 200..243 of gameinfo.c.
- The exact id → field-name binding for the strings' ids is the
  setter cases' own order (jtbl_80020408: id 0 → 0x800255F8 mission
  check, id 1 → 0x80025634 TV_MODE check, ...) — each case prints
  its own string with its own __LINE__ constant, so the id binding
  is as printed: mission=0, TV_MODE=1, and the rest map in the
  table's case order (0x2..0x11 → PAUSE_DISP..SUPER_BLASTER, with
  the mode-switch error on the out-of-range path). One honest gap:
  the string-to-id binding beyond the two decoded cases (mission /
  TV_MODE) follows the case order but only the first two cases were
  instruction-verified this pass; the rest are recorded as the
  table-order reading, not per-case verified.

The reset func_800252A8 wipes the block header
(0x80010000/0x80010002/0x80010004/0x80010006 ... with 0/-1 patterns)
— the game-side gameinfo wipe before use.

## set_player_info / get_player_info — the second pair

The same data row carries a SECOND accessor family named by its own
strings: `"%s(%d):Invalid mode switch in set_player_info()\n"`
(D_800204C8) and `"...in get_player_info()\n"` (D_80020628). The
setter is **func_80025AD8** (its error tail func_80025BF4 prints the
set_player_info string): it takes an id range-checked against
**0x49 = 73 fields**, a record index (stride **0x2C** bytes — the
x*11*4 scaling), a base of **0x80010008**, and dispatches through
**jtbl_80020500** (73 entries) storing the value at per-field
offsets. The getter's error tail sits at func_80025D94
(get_player_info string, line 0x1xx). The full 73-field
player-record enumeration and the getter's entry-point pin are the
honest remainder — parked as the next read.

## The caller census — 35 sites

25 direct `jal func_80025944` sites in the asm rows plus 10 raw
jal-encoded words (0x0C009651) inside the code-in-data boot pilot
loader func_8002278C (pass 20's second code-in-data function,
0x8002278C..0x80022AF8 across both data rows). The id distribution:

- **id 0** (the flag): 5 sites — main-region 0x80022A0C / 0x80022A40,
  the func_80026354 and func_800263F4 launcher-state reads, and the
  accessor wrapper func_80045BCC's -1 path (`func_80045BCC(-1)` =
  getter(0); a real id normalizes to slot = id-1 and continues into
  func_80045BEC — the getter-family's own convenience wrapper).
- **id 1**: 0x8002E974 (the frame region).
- **id 2** (the stateful record flag): 4 — the metric-rank tail
  func_80022B6C (paired with id 6: at attract_outcome == 1 the flow
  compares getter(6) < getter(2) and on the less-than path calls
  func_80025590(6, getter(2)) — the game WRITING BACK the launcher's
  own field), the metric formatter func_80022BBC (a0 carried in from
  the branch delay slot — the honest passthrough site), and the
  pilot loader's pair 0x80022950 / 0x800227C0.
- **id 3**: 4 — 0x80030F74 (frame region), 0x80046E04 (func_80046C30),
  0x80022CD4, pilot loader 0x800228B8 (pass 20's "getter(3)==1 gates
  the pilot chain").
- **id 4** (the pointer return): 2 — 0x80046848, pilot loader
  0x800228D0 (pass 20's "getter(4) = the name string" — the strcmp
  source pointer).
- **id 5**: 1 — pilot loader 0x80022888.
- **id 6**: 2 — 0x80022BA0 (the metric-rank comparison above),
  0x8002629C.
- **id 7**: 1 — 0x800262A8.
- **id 8**: 3 — 0x8002F224 (frame region), 0x800234E4, and the vsync
  prologue 0x8002376C (return == 1 joins the vsync tail — the
  pass-22 find).
- **id 9**: 1 — func_80022F24 (arms D_800AC164 at mode 4 — the
  pass-22 find; getter(9) is the mode-4 step-count source).
- **id 0xA**: 1 — pilot loader 0x80022878.
- **id 0xB**: 1 — 0x800232D8.
- **id 0xC**: **ZERO call sites in g3_jp** — the slot-free probe is
  the launcher-side accessor the game module never uses.
- **id 0xD**: 1 — 0x800244B8.
- **id 0xE**: 4 — the scene-reset family 0x80024524 / 0x8004477C /
  0x80044924 and 0x8004055C.
- **id 0xF**: 1 — pilot loader 0x800227CC.
- **id 0x10**: 1 — 0x80046E18 (func_80046C30).
- **id 0x11**: 1 — pilot loader 0x800227A4 (pass 20's
  "getter(0x11)==1 → func_800299BC" — the below-image-resident
  check).

Every observed id except 0xC has at least one caller; all 18 slots
plus the error path are now mapped.

## The below-image region semantics

The whole gameinfo block lives BELOW the payload (0x80010000..
0x8001FFFF — runtime RAM that survives module swaps, the same region
as pass 16's resident VAB words at 0x80016600/0x8001EC24). The game
module reads the launcher's hand-off state through
get_game_info/set_game_info, and the player records (stride 0x2C at
0x80010008, 73 fields) through the player_info pair — the launcher
(mainmenu, lane-owned) is the writer side of the hand-off. The one
in-image write to the flag word is func_800252A8's header wipe
(sh zero). The block's layout agreement between the two candidate
bases (0x800100B8 vs 0x800105F0, 0x538 apart) stays an open reading.

## The curated bank (inert, scan-time input)

Three function names bank under `// target: g3_jp` — the strongest
evidence class in the repo (each function's OWN printf names it, the
__FILE__/__LINE__ pattern):

- `get_game_info = 0x80025944`
- `set_game_info = 0x80025590`
- `set_player_info = 0x80025AD8`

`get_player_info` is deliberately NOT banked — its entry-point
address is not yet pinned (only its error tail func_80025D94 is
located); it lands with the player-record pass. None of the three
addresses carries a name in any other target's namespace, and the
EU twins' addresses stay unbanked until their own walk verifies
them (the JP-first discipline).

## What this closes and what it opens

Closed: pass 20's item (e) — the getter id map complete (18 ids + the
error path + the caller census), the stateful slot-2 wrinkle resolved
mechanically (the record-base selection by the 0x80010000 flag), and
the accessor family identified at source level (gameinfo.c).

Open: (a) the player-record pass — get_player_info's entry point, the
73-field set_player_info field map, the stride-0x2C record schema;
(b) the setter case-order → string binding verification for ids 2..11
(the two decoded cases mission/TV_MODE are instruction-verified; the
rest are the table-order reading); (c) the EU corroboration walk
(passes 20+21+22+23); (d) the stride-12 work base (unchanged); (e)
when disc links return, runbook Phase A/B; fresh-set request rides
every report.

# R1 pass 27 — the EU corroboration of the gameinfo family: the same
# source compiled with different carve seams, and the below-image
# hand-off block is region-identical in every address the accessors
# touch

Date: 2026-11-27 (window cron-20261127-0609, job 540513's nineteenth
fire — same window as passes 25-26). Scope: g3_eu as the comparison
image for passes 23+24 (JP-first discipline). Docs only; zero source,
YAML, asm or oracle change; zero renames; zero curated banks (the four
EU twin entries stay unbanked per the JP-first discipline — pass 23's
rule that EU addresses bank only after their own walk, which THIS pass
is; banking them is the follow-up once Silent's curated-lane call is
in, since curated banks are inert but the pass convention this window
is docs-only).

## The question this pass closes

Pass 26's refreshed next-question (a): the gameinfo family's EU
addresses — do EU's accessors carry the gameinfo.c strings, and do the
18-id game map and the 73-slot player tables hold at the same
addresses?

**Verdict: the gameinfo family is two-image. EU carries the complete
gameinfo.c string family (all four error printfs, the "gameinfo.c"
literal, and the full 12-string validation schema), the four accessors
are body-verified twins at a uniform −0x24 band with their jump tables
at +0x18, the __LINE__ constants match (same source lines), and — the
decisive fact — the below-image hand-off block is REGION-IDENTICAL:
flag cell 0x80010000, both record bases 0x800100B8/0x800105F0, the
0x80010B28.. halfword array, the player-record base 0x80010008 with
stride 0x2C, the id space 0x10..0x58 (offset −0x10, range 0x49), and
the record-index cells D_80010E04/06/08 are the same bytes in both
retail images. The caller censuses reconcile exactly (35 = 35, 9 = 9,
6 = 6, 23 = 23), with one pass-24 erratum: JP's set_player_info census
was undercounted.**

## The string family — EU carries the whole schema

EU data_80020000.data.s holds, at a uniform +0x18 shift of JP's
string-table band:

| string | JP | EU |
|---|---|---|
| "gameinfo.c" | 0x80020174 | **0x8002018C** |
| set_game_info mode-switch error | 0x800203D4 | 0x800203EC |
| get_game_info mode-switch error | 0x80020450 | 0x80020468 |
| set_player_info mode-switch error | 0x800204C8 | 0x800204E0 |
| get_player_info mode-switch error | 0x80020628 | 0x80020640 |

and the full validation schema at 0x80020158..0x800203EC (EU):
Invalid mission / TV_MODE / PAUSE_DISP / MUTEKI_MODE /
MAP_COUNTER_DISP / TUNE_LEVE / LEVEL / Too long PARTNER NAME /
PLAY_RECORDING / CLEAR_LEVEL / PARTNER_G_NUM / SUPER_BLASTER —
pass 23's documented schema, byte-present in EU.

## The four accessors — twins at −0x24, one carve split

| accessor | JP (passes 23/24) | EU twin | verification |
|---|---|---|---|
| get_game_info | func_80025944 | **func_80025920** (entry) + **func_8002594C** (dispatcher piece) | EU's carve SPLITS the getter: the entry reads the flag and selects the base, then `j func_8002594C` for the range check + table dispatch — a differently-carved compilation of the same source; one EU caller jals the dispatcher piece directly |
| set_game_info | func_80025590 | **func_8002556C** | −0x24; error path func_8002590C's family |
| set_player_info | func_80025AD8 | **func_80025AB4** | body-verified: the ×11×4−x1 stride-0x2C computation, base lui/ori **0x80010008**, `addiu a0, −0x10`, `sltu` vs **0x49**, error → func_80025BD0 (the set_player_info printf with a2 = **0x1EA**), `v1 = a1+6` (head+6), jtbl_80020518 dispatch |
| get_player_info | func_80025C1C | **func_80025BF8** | same prologue shape, error → **func_80025D70** (= JP func_80025D94 −0x24), jtbl_80020678 |

The jump tables, all +0x18 in the data row: jtbl_80020480 →
**jtbl_80020498**, jtbl_80020408 → **jtbl_80020420**, jtbl_80020500 →
**jtbl_80020518**, jtbl_80020660 → **jtbl_80020678**.

The __LINE__ evidence: JP's set_player_info error tail func_80025BF4
prints with a2 = 0x1EA (490); EU's func_80025BD0 prints with a2 =
**0x1EA** — the same source line of gameinfo.c compiled in both
regions.

## The hand-off block is region-identical

Every below-image address the accessors touch is the SAME in both
retail images (these are the module-swap-surviving hand-off cells, so
per-region shifts would have broken the launcher hand-off — and none
exist):

- the flag cell **0x80010000** (EU entry: `lui a1, 0x80010000; lh v0,
  0(a1); bnez → base B`) — mission/TV_MODE per pass 24;
- the two record bases **0x800100B8 / 0x800105F0** (EU entry's
  base-select: `lui v1, 0x8001 / ori 0x00B8` vs `ori v1, 0x5F0`);
- the halfword array **0x80010B28..** (EU dispatcher pieces read
  `lhu 0xB28/0xB2A/0xB2C(a1)` with a1 = 0x80010000);
- the player-record base **0x80010008**, stride **0x2C**, id space
  0x10..0x58 (offset −0x10, range 0x49), the head+6 tail — all in EU's
  set/get_player_info prologues verbatim;
- the record-index cells **D_80010E04 / D_80010E06 / D_80010E08** (EU
  writes them at 0x800455E8..0x80045600 in the launcher-adjacent row:
  `sh zero → D_80010E04; sh v0 → D_80010E06; sh zero → D_80010E08`,
  and the set_player_info(0x11) pair at 0x80045768/0x80045788 reads
  the same cells).

## The caller censuses reconcile exactly

| accessor | JP | EU | verdict |
|---|---|---|---|
| get_game_info | 25 name-jals + 10 raw words (0x0C009651 in the pilot loader) = 35 | **25 name-jals + the same 10 raw words (0x0C009648 in EU's pilot row)** = 35 | 35 = 35 |
| set_game_info | 6 name-jals + 3 raw writes | **6 name-jals + the same 3 raw words (0x0C00955B)** | 9 = 9 |
| set_player_info | **6 sites** (4 name-jals — func_80044B4C.s 0x80045A54, func_80022AFC.s 0x80022C90/CA8, func_8002A2DC.s **0x80026610** — plus 2 raw words 0x0C0096B6 at 0x80045B00/B20 in the launcher-adjacent row's data tail) | **6 name-jals** (the twins incl. 0x800265EC = the 0x80026610 twin −0x24, and the launcher-adjacent row func_800447B4.s carves the two sites as CODE: jals 0x80045768/0x80045788 where JP stores raw words) | 6 = 6 |
| get_player_info | 23 name-jals, no raw words | **23 name-jals**, no raw words | 23 = 23 |

**Pass-24 erratum (census, not reading): pass 24's "set_player_info x3"
undercounted JP** — the func_8002A2DC-row jal at 0x80026610 and the two
raw words 0x0C0096B6 at 0x80045B00/0x80045B20 are real call sites the
census missed (the same-VA-different-carve trap in reverse: JP stores
the launcher-adjacent pair as data words, so a name-only census cannot
see them). The corrected JP count is 6, which matches EU's 6 exactly.
Pass 24's field-map reading is unaffected (the sites it decoded are
correct; the census total was wrong).

The launcher-adjacent rows twin at −0x398 (EU func_800447B4.s = JP
func_80044B4C.s) with DIFFERENT carve seams around the set_player_info
pair — the row-seam lesson (carve units, not functions) applied to the
census one more time.

## Evidence table (verified vs inferred)

| Claim | Level | Backing |
|---|---|---|
| EU carries the complete gameinfo.c string family | verified | data-row reads (+0x18 shifts) |
| four accessors twinned at −0x24, get_game_info split | verified | per-body reads (prologue/base select/range check/jtbl/error tails) |
| four jtbls at +0x18 | verified | lui/addiu sites in the dispatcher pieces |
| hand-off block region-identical | verified | flag/base/array/record-base/cell reads, all addresses equal |
| __LINE__ constants identical (0x1EA) | verified | both error tails' `ori a2` |
| caller censuses 35/9/6/23 | verified | full-tree name-jal counts + raw-word sweeps both sides |
| pass-24 census erratum (3 → 6) | verified | JP's missed sites read |
| the EU record base selection is stateful the same way (flag-selected) | verified | EU entry body |
| whether EU's split-carve getter changes any return path | open (low) | the pieces chain by tail jump; all case bodies read on the shared lines |

## What this closes and what it opens

Closed: pass 26's next-question (a) — the gameinfo family is
two-image, and the below-image hand-off block is byte-identical in
address across regions; the passes 20..24 EU corroboration walk
(passes 25-27) is COMPLETE.

Open: (a) banking the four EU accessor twins in curated (docs are
ready; the bank is a one-line-per-name append under `// target: g3_eu`
— left for a lane window that runs the suite, since this window's
convention is docs-only); (b) the stride-12 work base (unchanged);
(c) D_800ABE7C's per-state value map (attract-machine owner);
(d) when disc links return, runbook Phase A/B; the fresh-set request
rides every report.

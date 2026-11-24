# G3 R1 pass 15 — the script commands are VAB note-ons (the sound-semantics decode)

**R1 pass 15 — 2026-11-25 (window cron-20261124-2209, same window as
pass 14).** Bounded **JP-first read-only static decode** continuing
[G3_SCRIPT_ABSENT_COMMANDS_20261125.md](G3_SCRIPT_ABSENT_COMMANDS_20261125.md):
the pass-14 note left "label the 46 handlers through the multiplier
values and the SsSetSerialVol sites" as the open next read. This pass
decodes the handler executor func_80029FC0 end to end and identifies
its two callees. Source-only: no retail SHA-1 comparison, no runtime
capture, no C conversion, **no rename** (the sdk identity below is
recorded, not exercised), no YAML or oracle change. Two pass-12
readings are corrected here.

## func_80029FC0 — the note-on executor (0x70, verified instruction-level)

Verified from `asm/g3_jp/nonmatchings/func_800280A4.s`
(glabels func_80029FC0..func_8002A180):

1. Handler id (`a0`, sign-checked; negative → bare epilogue return).
2. `mult = lh(D_80076CEC + id*2)` — the 64-halfword per-program table
   (mapped static data inside `data_80071790`, blob offset +0x555C).
3. **Volume chain** (both scaled products with the gcc `break`
   zero-check plumbing):
   - `volL = clamp(mult * lhu(D_800ABB54) / 0x7F, <= 0x7F)`
   - `volR = clamp(mult * lhu(D_800ABB5C) / 0x7F, <= 0x7F)`
4. Per-program tone bytes from the **runtime-RAM** table
   `D_800CFF88` (stride 0x20; both reads are `lbu`):
   `noteByte = lbu(D_800CFF88 + id*32)`,
   `fineByte = lbu(D_800CFF88 + id*32 + 1)`.
5. `voice = func_80068BF8(lw(0x80016600), id, 0, noteByte - 0x18,
   fineByte, volL, volR)` — 7 arguments (the 5th..7th ride the stack
   slots at caller sp+0x10/0x14/0x18).
6. `voice == -1` → `printf(D_80020830)`; the mapped string is
   **"keyon err\n"**.
7. Else `sh voice → D_800D0744 + id*2` (the per-program voice-handle
   cache, runtime RAM), then `func_80069B18(voice, volL, volR)`;
   `== -1` → `printf(D_8002083C)` = **"set VVol err\n"**.

## The callee identity — four independent legs

`sdk_members.py`'s placement file (`config/sdk_members.txt`, g3_jp
section) places the whole block 0x800681AC..0x80069C5C as psyq
LIBSND VMANAGER members, and **27 consecutive yaml rows align 1:1
with 27 member placements — zero interior placements, zero
mismatches** (machine-checked this window):

| row | extent | member |
| --- | --- | --- |
| func_80068834 | 0x3c4 | SpuVmSetVol |
| **func_80068BF8** | 0x3e8 | **SsUtKeyOn** |
| func_80068FE0 | 0x200 | SsUtKeyOff |
| func_800691E0 | 0x3ec | SsUtKeyOnV |
| func_800695CC | 0x118 | SsUtKeyOffV |
| func_800696E4 | 0x90 | SsUtPitchBend |
| func_80069774 | 0x158 | SsUtChangePitch |
| func_800698CC | 0xec | SsUtChangeADSR |
| func_800699B8 | 0x58 | SsUtGetDetVVol |
| func_80069A10 | 0x7c | SsUtSetDetVVol |
| func_80069A8C | 0x8c | SsUtGetVVol |
| **func_80069B18** | 0x9c | **SsUtSetVVol** |
| func_80069BB4 | 0x54 | SsUtAutoVol |
| func_80069C08 | 0x54 | SsUtAutoPan |
| func_80069C5C | 0x1f8 | SsUtAllKeyOff |

The three corroborating legs: (a) the arg shapes match
`psyq/3.3/PSX/INCLUDE/LIBSND.H` exactly — `SsUtKeyOn(short, short,
short, short, short, short, short)` and `SsUtSetVVol(short, short,
short)`, and SsUtKeyOnV's documented parameter order
`(voice, vabId, prog, tone, note, fine, voll, volr)` fixes the
7-argument call's reading as
`(vabId, prog, tone, note, fine, voll, volr)`; (b) the two error
strings "keyon err\n" / "set VVol err\n" sit exactly at the two
failure printf sites; (c) the caller census — **both callees have
exactly one caller each** (func_80029FC0), so the game's entire
note-on path runs through the script executor.

The psyq `SsSeqCalledTbyT_guard` reference at func_80068BF8's head
(the sequencer tick-mode flag) corroborates the libsnd provenance.
Per R2 discipline this is a recorded identity, NOT a rename: the rows
keep their func_ names (sdk-curation lane governs adoption).

## What the script system plays

Every dispatchable script command is **a VAB note-on keyed by the
command's handler id**:

- **prog = handler id** (0x00..0x39 — 46 table-reachable programs).
- **tone = 0** always; **note = noteByte − 0x18** (a two-octave
  offset from the runtime byte); **fine = fineByte**.
- **volL/volR** = the per-program multiplier scaled by the global
  L/R volume words and clamped to unity.
- The voice handle is cached per program in `D_800D0744[prog*2]`
  (runtime RAM), then its L/R volume is set again via SsUtSetVVol
  (a second volume touch on the freshly keyed voice).
- The **vab id** is the word at `0x80016600` — the first
  **below-image** runtime-RAM reference found (the g3_jp image loads
  at 0x80020000; 0x80016600 sits 0x9A00 below the base in the
  resident lower region; single reference campaign-wide; the store
  site is the open follow-up — presumably the VAB-open chain).

The combined table (command table D_800772F4 × multiplier table
D_80076CEC, both machine-dumped this window) — 46 records, the
volume character per band:

| opcode band | progs | mult | ×0x7F |
| --- | --- | --- | --- |
| 0x00..0x05 | 0x00..0x05 | 0x78 / 0x5A | ×0.94 / ×0.71 — the quiet opening cues |
| 0x39..0x3C, 0x06, 0x09, 0x23, 0x08, 0x22, 0x12..0x1D, 0x10, 0x25, 0x3E, 0x40, 0x3D, 0x41..0x45 | (respective) | 0x7F | ×1.00 unity |
| 0x07, 0x11, 0x0B | 0x1C, 0x1D, 0x1E | 0x9D | ×1.24 |
| 0x0C..0x0F (the mode-1-suppressed class) | 0x1F..0x22 | 0xB1 | ×1.39 — the loudest band |
| 0x3F | 0x34 | 0xB1 | ×1.39 |

The corpus scripts now read as **note sequences**: the 13-step ladder
D_8008B09C (payloads 0x12..0x1D/0x10) keys 13 distinct programs at
unity volume over its frame gates; the announce sequence
D_8008B0E8 mixes long-form 0x8009/0x8000 events (which the table does
not serve) with present note-ons; the twin-ladder mode-1 variants
play EU's present payloads as real notes while JP's absent band
(0x26..0x38) keys nothing — JP's mode-1 runs are silent beat tracks
over identical timing.

## The direct-fire census (10 sites + the table walker)

func_80029FC0 has **10 direct callers** beyond the command-table
walker func_8002FA9C — the game fires cues directly with hardcoded
program ids (the id sits in each jal's delay slot `ori $a0, ...`):

| caller | prog | mult | notes |
| --- | --- | --- | --- |
| func_800234D4 | 0x08 | 0x5A ×0.71 | |
| func_80023554 | 0x36 | 0x7F ×1.00 | |
| func_800237F8 | 0x0A | 0xB1 ×1.39 | **prog 0x0A is direct-fire only** |
| func_80023930 | 0x0A | 0xB1 ×1.39 | |
| func_8002398C | 0x0A | 0xB1 ×1.39 | |
| func_80023A84 | 0x35 | 0x7F ×1.00 | |
| func_80023D24 | 0x35 | 0x7F ×1.00 | |
| func_80026930 | 0x37 | 0x7F ×1.00 | gated on `a0 & 0x10` |
| func_80026968 | 0x37 | 0x7F ×1.00 | |
| func_8003F79C (main module) | 0x0B | 0x2D ×0.35 | **prog 0x0B is direct-fire only** |

The two direct-only programs carry the multiplier table's outlier
values (0xB1 and 0x2D) — the loudest and the quietest cues, both
unreachable through the command table. Conversely, programs
0x0C, 0x0F, 0x10..0x16 and 0x19 (10 ids, all mult 0x7F) have **no
call site found** — neither table-reachable nor direct-fired (dead
multiplier slots, or reached through an indirect path this sweep did
not cover; recorded as the open census remainder).

## Pass-12 corrections

1. The multiplier table D_80076CEC is the **per-program base volume**
   (the "rate scale" reading was wrong): its values scale the
   SsUtKeyOn/SsUtSetVVol L/R volumes, 0x7F = unity.
2. D_800ABB54/D_800ABB5C are the **global L/R volume scalers** (the
   "rate words" reading was wrong) — 0x7F = full.
3. The `t1 = 0x80016600` register load is the **vab-id word** (the
   "fixed string source" reading was wrong; the actual printf strings
   are the mapped D_80020830/D_8002083C).

## Evidence table (verified vs inferred)

| Claim | Level | Backing |
| --- | --- | --- |
| Volume chain + clamp shape | verified | func_80029FC0 body (both div/0x7F chains + 0x80 clamps) |
| Per-program tone bytes at D_800CFF88 (stride 0x20) | verified | both lbu reads; the table itself is runtime RAM |
| SsUtKeyOn / SsUtSetVVol identity | verified (4 legs) | sig-db 27/27 row alignment + LIBSND.H prototypes + error strings + single-caller census |
| "keyon err\n" / "set VVol err\n" strings | verified | data_80020000.data.s dlabels |
| Single note-on path campaign-wide | verified | callee caller census (1 caller each) |
| 10 direct-fire sites + fired progs | verified | the jal census + delay-slot ori ids |
| Progs 0x0A/0x0B direct-only; 10 progs unreachable | verified / open | table x call-site cross-reference |
| vab id = word at 0x80016600 (below-image RAM) | verified (read); store site open | the single lw reference |
| Note/fine byte VALUES | open | D_800CFF88 is runtime RAM — populated at sound init |
| The sound character of each program band | inferred | multiplier values + the volume arithmetic; no audio sample |

## Next R1 question

(1) Find the writer of the runtime tone tables — who fills
D_800CFF88 (note/fine per program) and D_800D0744 (voice handles),
and what writes the vab-id word at 0x80016600 (the VAB-open chain is
the prime suspect; the SsVabOpenHead/Sticky/WithMode placements sit
directly below the VMANAGER block). That closes the note VALUES and
turns the corpus decode into a literal "what plays when" score.
(2) The EU direct-fire twins (the EU aliases of the 10 direct
callers) to confirm the cue map is region-invariant. (3) The
SsSetSerialVol wrapper trio func_8002A23C/26C/29C (pass 12) still
belongs to a DIFFERENT consumer — trace who calls those and whether
serial volumes ride the same script path or a separate mixer lane.

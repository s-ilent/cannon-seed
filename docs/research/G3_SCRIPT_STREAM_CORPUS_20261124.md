# G3 R1 pass 13 — the script stream corpus and the two-channel dispatch

**R1 pass 13 — 2026-11-24 (window cron-20261124-1409, same window as
pass 12).** Bounded **JP-first read-only static decode** continuing
[G3_SCRIPT_INTERP_LANE_RANK_20261124.md](G3_SCRIPT_INTERP_LANE_RANK_20261124.md):
the pass-12 note left the script stream content undecoded; this pass
decodes the stream format, the dispatch tables, and the whole mapped
script corpus. Source-only: no retail SHA-1 comparison, no runtime
capture, no C conversion, no rename, no YAML or oracle change. Two
errors in the pass-12 note (the wait-gate halfword, the mode-gate
value) are corrected in that file by this window's commit.

## The two-channel architecture (all verified instruction-level)

The script machinery has **two independent cursors into the same
{frame-gate, payload} pair stream**, sharing one per-frame counter:

- **Reset** func_80044A90 (`func_80033C44.s`): zeroes the counter
  D_800AC384 and D_800ABEAC, sets BOTH cursors — the interpreter cursor
  D_800ABE14 and the ticker cursor D_800AC3B4 — to the stream base
  D_800ABA08.
- **Selector** func_80044AC0 (same file): for slot `a1` (bounds-checked
  `a1 == 0 || a1 >= 9` → bail; valid 1..8) picks
  `D_8008B1A8[(a0+v1)*4 + a1]` → the interpreter cursor, and
  `D_8008AF9C[a1]` → the ticker cursor; zeroes the counter; stores `a0`
  to D_800ABEAC.
- **Interpreter** (first channel) func_80044F60: per pair, when the
  counter reaches the frame gate, dispatches the payload halfword as a
  command through func_80045088/func_800450F4 → func_8002FA9C (the
  46-record command table D_800772F4) → func_80029FC0 (handler id, the
  D_80076CEC multiplier chain, the SsSetSerialVol sites). Commits the
  cursor only on the dispatch path.
- **Ticker** (second channel) func_80042BF0 (`func_80033C44.s`,
  0x80042BF0): per pair, when `stream[0] < counter`, commits BOTH
  halfwords (`v1 += 2` twice) and stores the cursor — the payload is
  consumed **blindly, with no dispatch**. This channel is a pure
  timeline tracker; what (if anything) reads the committed payloads is
  an open question (below).

## The pointer tables (mapped static data, inside data_80080048)

- **D_8008AF9C** — 12 word entries, the ticker-cursor table:
  `D_8008AF5C, D_800ABA0C, D_800ABA14, D_800ABA1C, D_800ABA24,
  D_800ABA28, D_800ABA30, D_800ABA38, D_800ABA40, D_8008AF6C,
  D_8008AF7C, D_8008AF8C`.
- **D_8008B1A8** — 24 word entries in 4-word groups (the selector's
  `<<4` stride), the interpreter-cursor table; entries point at the
  region-B scripts (D_8008B00C/54/9C/D4/E8/144/17C/190) and the empty
  stubs D_800ABA48/4C/50/54/58.

## The corpus (decoded halfword-by-halfword from the extracted blob)

Stream format per pair: `[frame_gate, payload]`; payload ≥ 0x8000 =
long command (3 more inline halfword args); −1 = terminator.

**Region A — 0x8008AF5C..0x8008AF9C (4 scripts, ticker table slots
0/9/10/11):**

| script | decoded |
| --- | --- |
| D_8008AF5C | (1, F3) (0x227, F4) (0x2FE, F5) END |
| D_8008AF6C | (1, FC) (0x25A, FE) (0x350, FF) END |
| D_8008AF7C | (1, FD) (0xA3, FE) (0x190, FF) END |
| D_8008AF8C | (1, FD) (0xA3, FE) (0x190, FF) END |

**Region B — 0x8008B00C..0x8008B1A8 (9 scripts, the interpreter's
region), per-script decodes:**

| script | decode ({frame, payload} pairs) |
| --- | --- |
| D_8008B00C | 7 long-form events: frames 0x8DE/0x8E8/0x8F2/0x8FC/0x906/0x910/0x91A, payload 0x800A each, arg triplets (0x4000/0x6000/0x7000/0x7800/0x7C00/0x7F00/0x0000, 0, 0x5000), then (0,0) (0x100) END |
| D_8008B054 | 7 long-form events: frames 2/0xC/0x16/0x2A/0x3E/0x52/0x66, payload 0x800A each, third arg 0x100/0x800/0x1000/0x2000/0x4000/0x7000/0x7000, END |
| D_8008B09C | 13 table-hit commands: frames 0x2E2..0x53A (13 gates), payloads 0x12..0x1D then 0x10 — the ladder (0x378/0x40E/0x42C/0x44A/0x468/0x486/0x4A4/0x4C2/0x4E0/0x4FE/0x51C/0x53A are the later gates) |
| D_8008B144 | 13 commands with THE SAME frame gates as D_8008B09C, payloads 0x28..0x34 — all absent from the table |
| D_8008B0D4 | (2, 0x0B) (0x60, 0x11) (0xD0, 0x0E) (0xE6, 0x0F) — all table hits, END |
| D_8008B0E8 | (1, long8009: 0,0,0x100) (5, long8009: 0,0,0x100) (0x10, 0x0B-hit) (0x16, long8009) (0x18, long8009) (0x1C, long8000: 0,0,0x100) (0x1E, 0x39-hit) (0x20, 0x39-hit) (0x30, 0x3A-hit) (0x39, 0x44-hit) (0x39, 0x8E-absent) (0xC, 0xC2-absent) (0xD, 0xDD-absent) (0xE, 0xF3-absent) then a terminal −1-payload event |
| D_8008B17C | (2, 0x26) (0x60, 0x27) (0xD0, 0x37) (0xFD, 0x38) — all absent |
| D_8008B190 | (2, 0x26) (0xAC, 0x35) (0xD3, 0x36) (0x10A, 0x37) (0x137, 0x38) — all absent |

Note how D_8008B09C/D_8008B144 are twin ladders over identical frame
gates with a present (0x12..0x1D/0x10) versus an absent (0x28..0x34)
payload set — the strongest single hint that the absent payloads mean
something the mapped table does not serve.

**Stub bank — 0x800ABA08..0x800ABA58 (the reset + selector defaults,
11 stubs):** mostly EMPTY scripts (bare −1 terminators:
D_800ABA08/24/48/4C/50/54/58) and single-pair one-shots
(1, F6) (1, F8) (1, F9) (1, FA) (1, F7) (1, F9) (1, FB) — payload
commands **absent from the 46-record table** (0xF6..0xFB).

**Not scripts:** the zero halfword dlabels from 0x800ABA5C onward
(D_800ABE14 the cursor, D_800ABEDC the mode bits, D_800ABF9C the mode,
D_800ABB54/B5C the rate words, …) are the game's **runtime state
globals** (static image zero; populated at boot/run) — the same
runtime-RAM law pass 12 banked; they sit in the same mapped blob but
are not script content.

## Findings

1. **The stream format is {frame-gate, payload} pairs, shared by both
   channels** — verified on both consumers (the interpreter's
   `counter < gate → no-commit wait`; the ticker's `gate < counter →
   commit`). The pass-12 mode-gate reading (operand-compare) was wrong:
   the comparison value is the literal 1 (mode-1 suppression of
   commands 0xC..0xF); corrected there.
2. **The corpus is small and concrete**: 4 ticker-timeline scripts
   (payloads 0xF3..0xFF, no dispatch), 9 interpreter scripts (the real
   command sequences — a 13-step ladder, an announce-style 19-command
   sequence, two 4-command ladders, one 6-command ladder), and 11
   default stubs. The whole system plays per-mode sequences through at
   most ~13 scripted commands per script.
3. **Absent commands are real, frequent, and structured** — the table
   covers opcodes 0x00..0x1D, 0x22, 0x23, 0x25, 0x39..0x45; the corpus
   additionally uses 0x1E..0x21, 0x24, 0x26..0x38, 0xF3..0xFB and the
   long-form 0x8009/0x800A (with 3 inline args each) — all of which
   walk the 46-record table to the sentinel and dispatch nothing. The
   D_8008B09C/D_8008B144 twin ladders (identical gates, present vs
   absent payload sets) show the absent band is deliberate stream
   content, not noise. Either a second command table exists at runtime
   (none found in the mapped image), the payloads are consumed by a
   third reader of the committed cursor region, or they are inert in
   retail. Open question; no mechanism invented.
4. **func_80044D2C decoded (bonus)**: zeroes D_800ABFB4 then, per the
   4 lanes (D_80147530 = D_801474FC + 0x34, stride 0x8C), when
   lane+0x2C is non-zero AND the 0x20 gate is set, copies
   {lane+0x0 word, lane+0x4 half, lane+0x52 half} into the rank-output
   record area D_801703A2 (stride 0x10) and accumulates into
   D_800ABFB4 — the metric collector that feeds pass 12's rank step.
5. The second channel's blind commits + the selector's separate
   pointer tables confirm the architecture: **one timeline, two
   consumers** — the dispatcher (sound/announce commands) and a
   tracker whose payload role is unresolved.

## Evidence table (verified vs inferred)

| Claim | Level | Backing |
| --- | --- | --- |
| Two-channel architecture, shared counter, reset + selector | verified | func_80044A90 / func_80044AC0 / func_80042BF0 / func_80044F60 asm |
| Ticker commits both halfwords blindly | verified | func_80042BF0 body |
| Pointer tables D_8008AF9C (12) / D_8008B1A8 (24×4-word) | verified | data_80080048.data.s dlabels |
| Corpus decode (regions A/B, stub bank) | verified | halfword decode of the extracted blob (this window's script) |
| Stub bank + region-B absent commands | verified | decode vs the pass-12 table |
| Absent-command mechanism (2nd table / third reader / inert) | open | none found in the mapped image |
| Payload role of the ticker's committed pairs | open | no reader found |

## Next R1 question

Label the nine region-B scripts' commands handler-by-handler (the
multiplier values + the SsSetSerialVol sites give the sound semantics),
then answer the absent-command question: sweep the full g3_jp image
for any second consumer of the committed pair region (the ticker
cursor's committed halfwords) before concluding inertness. The EU
ticker/selector twins (the EU aliases of func_80042BF0/func_80044AC0)
should be pinned to the EU script blob in the same pass.

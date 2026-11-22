# G3 four-gunner result ranking, score provenance, and mission counters

R1 bounded research pass **30**, 2026-11-23 (Australia/Adelaide). Source HEAD `8694f7bda46736b7a7dc4c1e3013bb3aaf31efc0` in PR #10. Continues [pass 29 GPU clears and ranking sprite tiers](G3_GPU_CLEAR_RANKING_LAYERS_20261123.md), [pass 9 hit/score ABI](G3_HIT_DAMAGE_SCORE_20261122.md), and [pass 4 FOBJ queue](G3_FOBJ_SPRITE_PATH_20261122.md). **Static tracked original retail EXEs** + game ASM only; no runtime frame, CHD extraction (container ClientError), changed C, new all-target hash/build oracle or image asset identification.

## Result

The `SLAVE_RANKING` columns are **one per the existing four gunner records**, not four unidentified decorative status cells. The game reads the same gunner `+0x34` 32-bit score accumulator previously proven to receive enemy hit awards; sorts the four scores descending with original gunner IDs; calculates **competition ranks** with ties (1,2,2,4), and stores each gunner's score/rank into a separate 16-byte render record. Two other numeric systems on the results display are **not per-gunner score**: a 0..100 percentage-style animated mission metric and a snapshotted global object terminal-event counter. The percentage's exact narrative label and the counter's full inclusion criteria need the TIM/STR or runtime evidence.

## 1. Game-owned score-to-ranking sorting algorithm

[JP display/control ASM](../../asm/g3_jp/nonmatchings/func_80044B4C.s) `80044B7C..80044D2C`, main gameplay [JP callback ASM](../../asm/g3_jp/nonmatchings/func_80033C44.s) `80042A80..80042AF4` (the latter >1 MB file cannot be retrieved whole via GitHub connector, so the instruction words were decoded directly from the tracked PS-X EXE). Recovered dataflow:

- Gunner array base `D_801474FC`, four records, **stride 0x8C**, with signed 32-bit score at `gunner+0x34`. The scalar award helper `80034D94` from pass 9 adds normalized packed-decimal deltas to this exact field.
- Mask `D_800AC17C` selects active gunner slots; the first four-pair work array `D_80144714` has **8-byte entries** `{s32 score, s16 original_gunner_index, padding}`. Inactive slots enter with score zero (but retain original index). Builder at `80044B98..80044BDC`.
- In-place 4-element adjacent swap sort at `80044BE0..80044C4C`. `slt` uses *signed comparison*: swap only when current score < next score. Scores tied in this comparison keep original order (**stable descending sorting**). Both score and gunner index travel together (2-word copy per swap).
- From highest to lowest, assign competition rank. The rank position advances regardless of whether scores tie, but tied scores retain previous rank: e.g. `100,90,90,80 → 1,2,2,4`. Map the score/rank into the second **8-byte** array `D_80144794 + originalIndex*8` at `80044C50..80044CBC`.
- Four final per-gunner records `D_80170394 + i*0x10` get **score at +4** and **rank at +8**, at `80044CE4..80044D20`. Non-participating slot rank forced to zero. Also write rank to gunner `+0x38`, identifying that field as **rank mirror** for subsequent game logic. Runtime call `80042AB8` invokes the sort routine after `80042A98` invokes metric update. The rank record is indexed by original gunner, *not* sorted display order.

### Partial ABI (16-byte entries)

```c
typedef struct {
    uint16_t gunner_field_3c;     // +0x00, from gunner+0x3c
    uint16_t unknown_02;         // +0x02
    int32_t  awarded_score;      // +0x04, from gunner+0x34, zero if inactive
    uint16_t competition_rank;   // +0x08, 0 if inactive
    uint16_t gunner_field_44;    // +0x0a, from gunner+0x44
    uint16_t unknown_0c;         // +0x0c
    uint16_t gunner_field_86;    // +0x0e, from gunner+0x86
} ResultGunnerRecord;            // sizeof=16 (provisional labels)
```

The other field copies are proved by `func_8004515C..800451B4` in [JP control ASM](../../asm/g3_jp/nonmatchings/func_80044B4C.s), invoked at `80042CB8`: it reads gunner `+0x3C/+0x44/+0x86`, writes result `+0x00/+0x0A/+0x0E`, strides source `0x8C` and destination `0x10` for exactly four slots. Independent display-state mask `D_800AC2F4` selects the four rank-indicator columns in `800471FC`, as documented pass29; do not assert it equals `D_800AC17C` without a writer proof.

## 2. Scores are rendered by actual decimal conversion, not an opaque bitmap

[Ranking source ASM](../../asm/g3_jp/nonmatchings/func_80046C30.s):
- `8004709C` labels the mode `SLAVE_RANKING` (table index 8); the mode dispatcher enters it via `800463C4`. It ORs the four result scores at `record+4` into `D_800ABC2C`, and invokes rank columns and numeric renderers.
- Per-column `func_800472DC..80047380` loads `resultRecord+4` and **multiplies score by 10** (`score*4+score`, then `*2`). It calls the formatting helper `func_8004803C` with the retail format string stored at `D_800ABA74` = ASCII **`%06d`**, a six-digit zero-padded decimal format. (This routine was referred to as an unknown formatting helper in earlier work; do not rename it `sprintf` until its own body/ABI is separately proven.)
- For each of six formatted characters, the renderer queues `0x1CB + ASCII_character`; ASCII '0' (0x30) becomes logical texture ID `0x1FB`; '9' -> `0x204`. It conditionally suppresses the **first** leading zero (not an arbitrary multi-zero left trim). Individual FOBJ command x advances 8 units; y=+65. Thus the same priority-12 digit texture bank from pass29 renders **actual per-gunner score**.
- Rank-related icon selection at `80047858..80047928` consumes result `+8` and uses `0x11F+(rank & 7)` in one HUD variant. Other glyph branches use `result+0xA` and need visual classification.

Example *illustrative scores*, not a runtime observation: original gunner scores (1250,1800,1250,700) produce ranks (2,1,2,4) and formatted values (`012500`,`018000`,`012500`,`007000`) before suppression of the first zero.

## 3. Distinguishing two other ranking-screen numerical metrics

### A. Mission percentage-style value

There are two 16-bit globals: `D_800AC2B4` (target/condition state) and `D_800AC394` (displayed smoothing value), distinct from every gunner `+0x34` score.

- Two initialization sites `80044840/44/48/4C` and `800449CC/D0/D4/D8` write literal **`0x2710 = 10,000`** to both target and displayed values.
- `func_80035348..80035418` (game-owned target update) checks state and, when allowed, computes a decrement using a table-selected halfword and a linked object/config halfword; subtracts it from `D_800AC2B4` at `800353D4..800353DC`. In a specified mode, clamps nonpositive target to 1 at `80035408..8003540C`. Other target writers exist, so this is **not a full mission-integrity formula**; exact story meaning still unproved. A writer also restores/snapshots another global into the target at `80041F60`.
- `func_800451B4..8004525C`, called `80042A98`, adjusts displayed `D_800AC394` toward nonnegative target by an adaptive signed step: if absolute difference 1..19 use ±1; 20..99 use ±20; >=100 use ±100. If target is negative it is treated as zero for the difference. No need to invent a seconds cadence.
- `func_800473BC..80047490` renders `displayValue/100`. It handles 100 as literal glyph IDs `0x1FC,0x1FB,0x1FB` (i.e. "100"), otherwise decomposes the quotient into tens and units, then adds sprite logical ID `0x65` at the end, plausibly a percent mark but artwork cannot be verified. The **0–100 percentage-like display** is established by the arithmetic and special 100 case, not by an extracted Japanese HUD label.

### B. Global object terminal-event count snapshot

- Another live 16-bit global, `D_800AC08C`, is explicitly incremented `+1` at **five separate game-owned object transition sites** in the JP original executable: `80030B44`, `8003379C`, `8003A050`, `8003B8A0`, `8003CAB8`. All show `lhu; addiu 1; sh`. The first case `80030B0C..80030B48` in [scene code](../../asm/g3_jp/nonmatchings/func_8002A2DC.s) clears object state, assigns object type `0x29`, disables collision mode `+0x28`, increments count, then calls object transition helper `80031C5C`. These are **terminal/event** increments; that the global equals every enemy kill/unique target is *not* proven.
- Before result display, `func_80044514..80044614` reads live `D_800AC08C` (`80044584/588`), and copies the halfword to **`D_800ABD9C`** (`80044600/604`) along with snapshots of multiple other game globals. It is called at `80042CB0`. It is **not** a score or per-player value.
- Rank screen `func_80047508..800475B0` reads the snapshot `D_800ABD9C` and displays decimal glyphs from the same `0x1FB+digit` bank. It caps its local input at **9999** before digit splitting and emits up to four glyph commands. This is a distinct counter on the results screen; exact wording, reset conditions, and whether it means destroyed enemy count require further event-classification/asset evidence.

## 4. Full four-target corroboration

Raw source: tracked original four PS-X EXEs, 0x800 header skipped, little-endian 32-bit MIPS, base VA `80020000`. Match unique best aligned windows using opcode+register/shift shapes with J/JAL targets and immediate fields ignored **for search**, then check critical source/stride instructions exactly. All six bounded JP code windows have 100% matching instruction shape at exactly one location in *each* target within scoped 0x8003/0x8004 address ranges; measured exact counts:

| Function (JP start..end exclusive) | Instructions | Dragoon EU VA / exact | Gourb JP VA / exact | Gourb EU VA / exact |
|---|---:|---|---|---|
| `44B7C..44D2C` descending sort + rank | 108 | `447E4` 97 | `42018` 87 | `41C38` 87 |
| `4515C..451B4` gunner field snapshot | 22 | `44DC4` 20 | `425F8` 18 | `42218` 18 |
| `451B4..4525C` adaptive metric smoothing | 42 | `44E1C` 37 | `42650` 33 | `42270` 33 |
| `472DC..47380` score-glyph preparation | 41 | `46F44` 38 | `44778` 37 | `44398` 37 |
| `4709C..4712C` ranking display handler | 36 | `46D04` 25 | `44538` 19 | `44158` 19 |
| `35348..35418` metric target decrement | 52 | `34FB0` 41 | `35FEC` 31 | `35C0C` 31 |
| **Total** | **301** | **258 identical** | **225 identical** | **225 identical** |

(All listed VA suffixes mean `0x80000000 + hex suffix`, not file offsets.) The score loader `lw v0,0x34(a1)`, stride `addiu a1,a1,0x8C`, rank score store `sw v0,4(a0)`, destination stride `0x10` and score formatting `score*10` arithmetic are **word-for-word identical in four executables**. Target absolute addresses and globals are relocated, not universal. Scoped SDK anchors show the inspected source routines are game-owned; the `func_8004803C` helper and LIBGS sprite sorter are separate.

**Verification boundary:** this is code-equivalence and dataflow, not a complete formal proof of all records or game states. Header/endian, branch target and data initialization assumptions are inherited from earlier verified inputs. No new byte-exact game compile or observed rank result.

## Next pass

Trace `D_800AC2F4` and source `D_800AC17C` participation-mask lifecycle to explain exactly when each column appears, including solo versus four-person and alternate scenario configurations. Classify all five `D_800AC08C` increment paths and reset sites before naming it a kill counter; map any four-column glyphs to actual TIM art when private CHD tooling works. Consider small game-owned rank-score sorting leaf for guarded matching C **only after** current compiler/8-target retail oracle is witnessed; do not convert the large ASM row speculatively.

# G3 attack variant follow-up: type 0x18 and cfg 0x74/0x76

**R1 pass 34 — 2026-11-23.** Continues [pass 33 attack-child provenance](G3_ATTACK_CHILD_PROVENANCE_20261123.md) on its dedicated research branch (base HEAD `f83aa4bdccb7472cc2698de19e1ffec4b1351aaf`). Bounded **read-only static research**: JP/EU generated code and data text, not new private-binary extraction, runtime play, model/texture inspection, matching build or C conversion. No visual name or active emission frequency inferred.

## Result

1. **Type 0x18 is a proximity-triggered attack handler, not a shootable enemy by this handler.** Parent type 0x81 / cfg 0x4A (37 authored mode-zero entries) uses attack case 1 to select child cfg 0x68 → runtime type 0x18. The child handler decrements its signed-tested halfword lifetime, integrates motion, measures squared distance and can invoke the angular shared-vehicle-health gate; no per-gunner hit routine, destruction credit, or global terminal-count increment occurs in this handler.
2. **Unexpected initial-lifetime negative:** the specific cfg 0x68 record is **short (0x30 bytes to the next label)**. Case-1 constructor `func_80035AA0` nevertheless reads `lhu (child_cfg+0xBE)` into child `+0x6C`. Both JP/EU **initial data images have zero** at that effective address (JP `0x80089D3A`, EU `0x8008A552`, the last halfword immediately before the 128-pointer config table). The type-0x18 handler decrements zero to `0xFFFF`, takes its signed-negative expiry branch and clears the type **before movement, proximity and rendering**. Therefore *this exact cfg 0x4A → 0x68 path cannot perform the later proximity contact on its first handler tick under unmodified initial data and object state*. A runtime mutation of that adjacent table-area word or of child `+0x6C`, or a different construction path, is not ruled out. Do **not** call this attack successfully observed or universally dead.
3. **Alternative cfg 0x74 is a type-0x13 data variant, not a demonstrated active attack.** It differs from cfg 0x76 at only six halfword positions in otherwise identical 0xBC-byte records. Its `+0xB4` parameter is **50 instead of 30**, and the case-8 constructor uses this to construct a larger squared contact-distance threshold if cfg 0x74 were ever selected. The normal parent cfg 0x4B selects **0x76**, not 0x74. None of the **125 statically decodable** parent `cfg+0x2C` halfwords in the 128-entry pointer table equals 0x74. The remaining three entries are intentionally short/aliased near-global records (indices 0x64/0x65/0x66), whose `+0x2C` position cannot be treated as an ordinary config field in the tracked word representation. The four mode-zero authored schedules also contain zero cfg 0x74 entries (pass 19). This does **not** exclude alternate-mode scripted/direct or runtime-computed selection.

## 1. Producer and type-0x18 handler: exact observations

| Site / object | Verified observation |
| --- | --- |
| Parent cfg 0x4A: JP `D_800893CC`; EU `D_80089BE4` | runtime type `0x81`, attack selector `cfg+0x2A = 1`, child selector `cfg+0x2C = 0x68`, case-1 angular predicate argument `cfg+0x2E = -1` |
| Child cfg 0x68: JP `D_80089C7C`; EU `D_8008A494` | runtime type `0x18`, resource `0xB9`, base vehicle damage `cfg+0x12 = 20` |
| `func_80035418` at JP `80035494` | case 1 calls `func_80035AA0`, subject to common `+0x32` and `+0x68` cooldown gates |
| `func_80035AA0` JP `80035AA0..80035C24` | allocates via `func_80031530` (74-slot prefix), calls angular filter `func_800365FC`, sets type/config via `func_80036704`, initializes child lifetime at `80035B08..80035B10`, copies parent pose/motion data, resets parent's cooldown with `func_800355C8` |
| `func_8003442C` JP `8003442C..800345A4` | type-0x18 active handler: `+0x6C -= 1` at `80034440..80034454`; `bltz → 8003458C` clears type, otherwise move and test proximity via `func_80034748` against `(+0x36)^2`; on proximity call `func_800352A0` at `800344F8`, then clear type at `80034504` |
| `func_800352A0` JP `800352A0..80035348` | angular gating around `func_80034EC0`; qualifying contact calls shared vehicle-health mutation `func_80035348` at `80035324`, subject to its further conditions |
| Initial lifetime backing word | JP: `child_cfg+0xBE = 80089D3A` lies inside word `80089D38 = 0`. EU: `8008A552` lies inside word `8008A550 = 0`. Both precede config pointer-table starts `80089D3C` / `8008A554` by two bytes |

**Important overlay issue:** `cfg 0x68` is only 0x30 bytes until the next labelled configuration, but the generic case-1 constructor reads `+0xB4` and `+0xBE`. These are physically valid addresses in the loaded image, *not fields demonstrated to belong to the short cfg record*. `cfg+0xB4` reads initial `0x000A0000` in both regions (low-32-bit square is zero); the derived child's `+0xA4` thus comes from the mode bias alone in that initial state. The `+0xBE` zero is the decisive expiry gate. A static code path is not proof that a successfully damaging type-0x18 attack actually occurs at runtime.

## 2. Side-by-side type-0x13 templates

Pointers: `D_80089D3C[0x74] = 80089774` and `[0x76] = 80089830` JP; EU `D_8008A554[0x74] = 80089F8C` and `[0x76] = 8008A048`. Exactly **94/94 halfwords** match JP↔EU for each complete 0xBC-byte template; cfg 0x68 also matches **24/24 halfwords** over its declared 0x30-byte span. Six locations differ between the two type-0x13 templates:

| Config-relative halfword(s) | cfg 0x74 | cfg 0x76 | Proven use / limit |
| --- | ---: | ---: | --- |
| `+0x02`, `+0x04` | `0x1B4`, `0x1B4` | `0x1B0`, `0x1B0` | model/resource selection; type-0x13 handler reads config `+0x02` for its render selector |
| `+0x06`, `+0x08` | 32, 32 | 21, 21 | distinct authored parameters; exact active use not proven here |
| `+0xA4` | `0x0800` | `0x8000` | stored record value; not demonstrated to drive this handler's collision decision |
| `+0xB4` | 50 | 30 | **case-8 constructor uses it as the offset of a mode-specific squared-contact bound** |

Both configs give **type 0x13**, `cfg+0x12=30` base vehicle damage, `cfg+0xB6=1500` time limit, `cfg+0xB8=30` secondary timer, and `cfg+0xBA=256` per-step rotation parameter. The constructor `func_80035E80` at `80035EC0..80035F0C` copies `+0xB6 → obj+0x6C`, `+0xB8 → obj+0x6E`, `+0xB4 → obj+0x46`, and sets `obj+0xA4 = (signed(cfg+0xB4)+mode_bias)^2`, where `mode_bias = 110` when `D_800ABF9C==0`, else 234. In the type-0x13 handler `func_8003DDC0`, `8003DE78..8003DE8C` compares squared distance against `obj+0xA4`. **Conditional outcomes if the alternate were selected:**

| Mode bias | cfg 0x74 contact-distance bound | cfg 0x76 bound |
| --- | ---: | ---: |
| 110 | `160² = 25,600` | `140² = 19,600` |
| 234 | `284² = 80,656` | `264² = 69,696` |

This is an increase of 20 world-distance units in the threshold radius, **not proof of a registered hit**: `func_800351D0` applies additional angular and mission-state gates. Neither template's existence establishes which on-screen attack effect corresponds to resource `0x1B0` versus `0x1B4`.

## 3. Selection and negative result

From the 128-entry `D_80089D3C` table, 40 distinct pointer destinations were decoded. For indices with a statically recoverable `cfg+0x2C` halfword, **0/125 equals 0x74**. Three short/global aliases (config indices `0x64/0x65/0x66` pointing to `D_800AB978/974/970`) do not expose a regular `+0x2C` field in the `.word`-based table read and are **not** counted as resolved. Pass 19 independently finds no cfg 0x74 in the 857 mode-zero scheduled entries, and cfg 0x4B's actual case-8 child selector equals 0x76. This is a bounded negative xref census; no claim that cfg 0x74 is unreachable in all modes, mutated tables, or computed scripts.

The two attack variants are *different mechanisms*, despite having the same type-0x81 parent family:
- **cfg 0x4A → method 1 → cfg 0x68 → type 0x18**: angular emitter filter, non-shot contact handler, **initial zero-lifetime anomaly**.
- **cfg 0x4B → method 8 → cfg 0x76 → type 0x13**: shootable object with `+0x2E` durability, 1500-frame/step timer, proximity collision threshold and type-0x31 death effect; its own fatal/expiry paths do not increment `D_800AC08C`.

## 4. JP/EU control-flow check

Source ASM: `asm/g3_jp/nonmatchings/func_80033C44.s`, `asm/g3_eu/nonmatchings/func_800338AC.s`; ROM data: `asm/g3_jp/nonmatchings/data/data_80080048.data.s`, `asm/g3_eu/nonmatchings/data/data_8008002C.data.s`. Each compared EU code VA is JP − `0x398`. Values below count instruction words, and *shape* masks I-type immediate and J/JAL target fields after correcting disassembly comment-byte endianness; R-type words are kept verbatim.

| JP code window (exclusive end) | EU start | Words | Identical words | Matching instruction shapes |
| --- | --- | ---: | ---: | ---: |
| `80035AA0..80035C24` method-1 producer | `80035708` | 97 | 88 | 97 |
| `8003442C..800345A4` type-0x18 handler | `80034094` | 94 | 85 | 94 |
| `8003DDC0..8003DFE4` type-0x13 handler | `8003DA28` | 137 | 116 | 137 |
| `80035E80..80035F70` method-8 producer | `80035AE8` | 60 | 50 | 60 |
| `800365FC..80036658` angular predicate | `80036264` | 23 | 20 | 23 |
| **Total** | | **411** | **359** | **411** |

Structural agreement supports mirrored behaviour; it is **not** a fresh retail hash oracle or runtime test. No assertion of SDK ownership or a matched semantic-C conversion.

## 5. Next bounded question

**Pass 35:** audit all potential writers of the **lifetime backing word** immediately before `D_80089D3C` (`80089D38` JP / `8008A550` EU) and any post-constructor mutation of type-0x18 object's `+0x6C`; distinguish an intentionally inert/one-tick emitter from mutable setup or an alternate valid child. Also trace if cfg 0x74 is sourced from a *different* configuration field/script, especially the unresolved mode-nonzero aliased encounter table. Only a targeted runtime watchpoint on child `+0x60/+0x6C/+0x0` plus `func_80035418` can prove it occurs in play. If no such source exists, preserve cfg 0x74 as **unassigned** rather than asserting universally unused. Results caption/art and the separate global terminal tally remain independent follow-ups.

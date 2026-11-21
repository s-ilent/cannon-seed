# G3 main-mode sequence controller atlas

**Investigation:** 2026-11-22; bounded third R1 pass on committed JP/EU MIPS source.
**Evidence:** tracked ASM/data literals, exact function-pointer relocation entries, decoded MIPS instruction shapes; no retail binary, runtime trace or rebuilt executable.
**Predecessor:** [HUD queue and frame-loop atlas](G3_HUD_QUEUE_FRAME_LOOP_20261122.md).

## Finding: the eight-entry table is a game sequence controller

The frame loop at JP `0x80042C6C..0x80042D4C` reads unsigned 16-bit `D_800AC5AC`, applies `& 7`, multiplies by four and calls the corresponding word through `jalr $v0` at `0x80042CE8`. EU uses `D_800ACDFC` and `D_8008B734` in the equivalent outer frame loop. All eight entries are present in committed data; slots 6 and 7 are the **same** no-op function, thus there are **seven unique targets**, six with behavior.

| Index | JP table slot → target | EU table slot → target | Evidence-backed role |
| ---: | --- | --- | --- |
| 0 | `8008AF1C → 800246B0` | `8008B734 → 80024710` | Increment sequence state |
| 1 | `8008AF20 → 800246D0` | `8008B738 → 80024730` | Call setup helpers, then increment sequence state |
| 2 | `8008AF24 → 80042E10` | `8008B73C → 80042A78` | `WAIT_FOR_START`; five-way inner switch |
| 3 | `8008AF28 → 800429B8` | `8008B740 → 80042620` | `INIT_SEQUENCE`; clear flag and increment state |
| 4 | `8008AF2C → 80042A20` | `8008B744 → 80042688` | `MAIN_SEQUENCE`; extended game-owned processing |
| 5 | `8008AF30 → 80043828` | `8008B748 → 80043490` | `WAIT_FOR_RESTART`; eight-way `STAR_MODE` switch |
| 6 | `8008AF34 → 80042E08` | `8008B74C → 80042A70` | Empty `jr $ra; nop` |
| 7 | `8008AF38 → 80042E08` | `8008B750 → 80042A70` | Same empty function as slot 6 |

**Direct sources:** [JP pointer table](../../asm/g3_jp/nonmatchings/data/data_80080048.data.s), [EU pointer table](../../asm/g3_eu/nonmatchings/data/data_8008002C.data.s), [JP large control ASM](../../asm/g3_jp/nonmatchings/func_80033C44.s), [EU control ASM](../../asm/g3_eu/nonmatchings/func_800338AC.s), and [JP early helper ASM](../../asm/g3_jp/nonmatchings/func_80022AFC.s).

The state names are not invented: JP [retained literal data](../../asm/g3_jp/nonmatchings/data/data_80020000.data.s) contains `INIT_SEQUENCE` at `0x80021340`, `MAIN_SEQUENCE` at `0x80021350`, `WAIT_FOR_START` at `0x80021360`, `WAIT_FOR_RESTART` at `0x80021400`. Each corresponding callback passes the literal address to `func_80022D9C`. That helper calls `strcat` to accumulate text in `D_800CD1E4`; therefore these are original diagnostic labels, **not proof that a named screen or menu is displayed**.

## Exact JP/EU structure checks

These windows were checked against *both* tracked source texts using the byte-order and opcode/register rules of [`tools/compare_asm_windows.py`](../../tools/compare_asm_windows.py). All listed windows have zero holes and matching opcode/register shapes. Identical words are not a claim of same retail executable.

| Paired window (JP ↔ EU) | Instructions | Identical words | Same shapes |
| --- | ---: | ---: | ---: |
| `246B0..246D0 ↔ 24710..24730` (slot 0) | 8 | 6 | 8 |
| `246D0..24718 ↔ 24730..24778` (slot 1) | 18 | 13 | 18 |
| `429B8..42A20 ↔ 42620..42688` (slot 3) | 26 | 18 | 26 |
| `42A20..42B70 ↔ 42688..427D8` (slot 4 prefix only) | 84 | 56 | 84 |
| `42E10..42E8C ↔ 42A78..42AF4` (slot 2 prefix only) | 31 | 21 | 31 |
| `43828..43920 ↔ 43490..43588` (slot 5 selector prefix) | 62 | 37 | 62 |

These are **bounded windows**, not complete function claims for slots 2, 4 or 5. Scanner labels after the entry are often internal branch blocks. For reproduction, supply each pair's first and ending VA to `tools/compare_asm_windows.py --left ... --right ... --require-shape` as in the preceding research atlas.

## Sequence-state producer and transition observations

The main sequence variable is an unsigned halfword at JP `D_800AC5AC` / EU `D_800ACDFC`. The loop **masks it to three bits on read**; this does not prove the stored value is always 0–7. A separate submode halfword is JP `D_800ABE94` / EU `D_800AC6E4`. The main-frame exit condition is **another** variable, JP `D_800AC4F4`: do not alias it to the mode state.

- `func_80044108` initializes the main state and submode to **zero**, along with other state. It is called before the loop's first iteration.
- In slot 0, `func_800246B0` reads/increments/stores the main state, so its direct effect is `0 → 1` modulo halfword arithmetic.
- In slot 1, `func_800246D0` calls `func_80044738`, `func_80044DD0` and `func_80030B68` before incrementing the main state, giving `1 → 2` when called with the expected state.
- Slot 2 (`WAIT_FOR_START`) decrements `D_800ABE7C`, checks other flags and switches on `D_800ABE94` through `jtbl_80021370`. The five entries call `func_80042F18`, `func_80043040`, `func_800430A4`, `func_80043130`, `func_8004323C`. Embedded labels include `WAIT_STEP0`, `WAIT_STEP1`, `WAIT_STEP2`, `WAIT_START_SW` and `WAIT_DEPARTURE`. A path at `0x80043328..0x80043340` zeros submode and increments main mode.
- Slot 3 (`INIT_SEQUENCE`) calls `func_80030B68` and `func_80046220`, clears bit `0x8` of `D_800ABEDC`, then **increments main mode** (`0x800429F8..0x80042A0C`). Thus its directly observed effect is `3 → 4` under the normal sequence.
- Slot 4 (`MAIN_SEQUENCE`) clears bit `0x10` of `D_800ABEDC`, selects `func_80040460` or `func_80024730` according to signed `D_800ABF9C`, sets `D_800AC29C=1`, calls multiple game-owned stage helpers (`func_8003E268`, `func_80044F60`, `func_80044D2C`, `func_800451B4`, `func_8003F198`, `func_8003E784`, `func_80044B7C`), and tests `D_800AB26C`, `D_800AC0DC` and additional state. Unlike slots 0/1/3, it does **not** unconditionally advance the mode: this is sustained active processing, with mode changes owned by other routines.
- Slot 5 (`WAIT_FOR_RESTART`) clears bit `0x20` of `D_800ABEDC`, copies two state halfwords to adjacent globals, and switches on **signed** `D_800ABE94` if its value is within `0..7`. The eight switch branches at JP `0x800438A8..0x80043918` call `func_80043930`, `func_80043B5C`, `func_80043BDC`, `func_80043C68`, `func_80043CFC`, `func_80043D90`, `func_80043E2C`, `func_80043EEC`. The literal strings `STAR_MODE0..STAR_MODE7` at `0x80021438..0x8002148C` independently corroborate their diagnostic names.

**Important multi-level distinction:** the frame dispatch has eight slots, WAIT_FOR_START has a *different* five-entry jump table, and WAIT_FOR_RESTART has a *different* eight-entry jump table. Neither inner table is the frame-level mode table.

## One game-owned callback traced further: restart submode zero

JP `func_80043930..0x80043B5C` (`STAR_MODE0`) is a substantive data-flow witness:

1. It sets `D_800ABE44` to -1 and `D_800ABFEC` to `0x308`, clears several consecutive fields at `D_8016AC18..0x8016AC28`, and scans **four** records beginning at `D_801474FC`, with a fixed `0x8C` byte stride.
2. In the scan, the halfword at record offset `+0x38` is copied to `+0x3A`; a signed comparison with `1` decides which records contribute. One selected record can seed several fields at `D_8016B218`, `D_8016B28C`, `D_8016B28E`, and `D_800AC57C`.
3. A later four-record loop copies selected values into a separate structure with **`0xAC` byte stride** (source stride remains `0x8C`), with an exclusion when a signed field equals 7.
4. It clears several unrelated halfwords, sets `D_800ABE7C=0xEF` (239), and **increments the restart submode** `D_800ABE94` at `0x80043B40..0x80043B48`.

These strides and copy conditions are observed. They are **not yet evidence** to call the records "players", "enemies", or "render objects"; ownership and structure layout remain open.

The next submode, `func_80043B5C` (`STAR_MODE1`), decrements the same `D_800ABE7C` timer. While nonnegative it calls `func_800440CC`; when it becomes negative it reloads **`0x1A4` (420)**, increments the submode and calls `STAR_MODE2` (`func_80043BDC`) immediately. This is a concrete timer-driven transition.

At the final restart-side control (`0x80043F4C..0x80043FEC`), the code tests a 32-bit `D_800AC294` against mode-specific thresholds and decrements that timer on one path. One exit writes **main mode 1**, resets submode and sets `D_800AC4F4=1` (the outer-loop exit flag); an adjacent entry `0x80043FD4` writes **main mode 2** and resets submode without setting that exit flag. The exact event ownership/incoming caller for the latter entry is not proven here.

## Relationship to the established renderer

The outer frame loop orders `func_800444B0` (font queue reset), **one mode callback**, then additional stage calls and `func_80022FE4` (render/HUD queue drain, swap and `GsDrawOt`). Separately, early graphics code reads the main state (`func_800233E8` tests for state 4 with submode 9–11; `func_8002377C` distinguishes states 2 and 5). This is real state-dependent rendering/control gating.

**Negative finding:** none of the *direct instructions* examined in the frame-level table targets calls `GsSortSprite` or `GsDrawOt` itself. Mode-dependent GPU packet ownership likely lies in transitive stage helpers or the separate render path. The calls above connect game states to the existing render lifecycle, but **do not prove that a particular callback enqueues a particular sprite or polygon**. Do not relabel those helpers as specific graphics components without another xref/calldata pass.

The string helpers `func_80022D9C/func_80022DE0` use `strcat` on two buffers; they are *diagnostic text accumulation*, not direct GPU work or proof of an on-screen log.

## Next R1 target and limitations

**Next bounded investigation:** trace one of the sustained `MAIN_SEQUENCE` helpers (start with `func_80044F60` and `func_80044B7C`), then follow its game-owned record writes into the shared object/font packet producers and the later render submission. Test the hypothesized `FOBJ` queue against the separately documented 10-entry text queue and retained `Over flow FOBJ packet!` string. Confirm actual OT sorter calls before giving object names.

Keep the unresolved resource `0x707`, `GsOT` allocation initialization and workbase allocation bounds in the research backlog. No C translation, SDK member rename, YAML edit, retail-image recheck, runtime trace or eight-target rebuild was done in this pass.
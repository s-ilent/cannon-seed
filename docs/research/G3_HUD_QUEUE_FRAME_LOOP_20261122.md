# G3 HUD sprite, font packet queue and frame-loop atlas

**Investigation:** 2026-11-22, source-only static analysis on main `f5f5e9ab`.
**Evidence level:** compared committed MIPS disassembly, YAML, SDK anchors,
retained data strings and independently documented Psy-Q ABI. **No
retail-image recheck, emulator trace, source conversion or symbol rename.**

Previous atlas: [G3 render preparation and presentation](G3_RENDER_PREP_ATLAS_20261122.md).
This second bounded investigation resolves that note's *first two
dispatch-callee* questions, **the incoming caller/order of both frame
routines**, and the **20-byte ordering-table header**. It also identifies
a complete font packet producer/consumer and the legal glyph alphabet.

## Executive findings

1. The array at `D_8016AF20` (EU `D_8016B044`), indexed by
   `GsGetActiveBuff() * 0x14`, holds **`GsOT` headers**, not a guessed
   custom render record. `GsOT` is five 32-bit words (20 bytes) in the
   Psy-Q ABI. The same pointer is passed unchanged to `GsClearOt`,
   nine local stage calls, `GsDrawOt` and the two HUD helpers.
2. **`func_8002F200`** (JP, 0x168 bytes) is a conditional, blinking
   **`GsSPRITE` HUD element**, not a general geometry dispatcher.
   EU: `func_8002EFD0`.
3. **`func_8002F660`** (JP, 0x98 bytes) drains a **ten-entry,
   eight-byte-per-record text queue**, centering each string and
   sorting one sprite per supported glyph into the active OT.
   EU: `func_8002F430`. The writer at JP `0x800446AC` accepts
   a non-null text pointer and signed 16-bit x/y; the initializer
   `0x800444B0` resets the queue count and write cursor.
4. The higher-level loop at **JP `0x80042C6C..0x80042D4C`**
   (EU `0x800428D4..0x800429B4`) calls frame preparation,
   resets the queue, dispatches a selected game-mode handler through
   a function pointer, then calls frame submission. It repeats while
   `D_800AC4F4 != 1`. This establishes the **actual caller and
   sequencing** that the previous atlas left open.
5. The preparation function also invokes **`DecDCTin` /
   `DecDCTout`** (confirmed by the committed SDK anchor catalog)
   on a conditional path; it has an MDEC video-decode aspect in
   addition to GPU/OT preparation.

**Important:** Most scanner `glabel` points in these functions are
branch/loop fragments, not true function boundaries. The complete
prologues and epilogues below determine the candidates.

## 1. Cross-region paired extents

All coordinates are RAM VAs, end-exclusive. The JP and EU files
for the two HUD functions are respectively
[JP scene ASM](../../asm/g3_jp/nonmatchings/func_8002A2DC.s)
and [EU scene ASM](../../asm/g3_eu/nonmatchings/func_8002A2CC.s);
the frame loop and queue helpers are in the large
[JP control ASM](../../asm/g3_jp/nonmatchings/func_80033C44.s) /
[EU control ASM](../../asm/g3_eu/nonmatchings/func_800338AC.s).
The glyph routines are in
[JP early ASM](../../asm/g3_jp/nonmatchings/func_80022AFC.s) /
[EU early ASM](../../asm/g3_eu/nonmatchings/func_80022B5C.s).

| Candidate, role | JP | EU | Size | Identical instructions | Identical opcode/register shapes |
| --- | --- | --- | ---: | ---: | ---: |
| Outer game loop | `42C6C..42D4C` | `428D4..429B4` | 0xE0 | 37/56 | **56/56** |
| Text queue initialization | `444B0..4450C` | `44118..44174` | 0x5C | 15/23 | **23/23** |
| Text queue append | `446AC..4471C` | `44314..44384` | 0x70 | 23/28 | **28/28** |
| Text queue count getter | `4471C..44728` | `44384..44390` | 0x0C | 3/3 | **3/3** |
| Text queue base getter | `44728..44738` | `44390..443A0` | 0x10 | 3/4 | **4/4** |
| Sprite-font single glyph | `25108..2515C` | `250E4..25138` | 0x54 | 19/21 | **21/21** |
| Centered string renderer | `251EC..252A0` | `251C8..2527C` | 0xB4 | 43/45 | **45/45** |
| Conditional HUD sprite | `2F200..2F368` | `2EFD0..2F138` | 0x168 | 82/90 | **90/90** |
| Queued text render | `2F660..2F6F8` | `2F430..2F4C8` | 0x98 | 35/38 | **38/38** |

The pair's VA offsets are **not globally constant**:
`-0x398` for the loop/queue family, `-0x24` for glyph helpers,
and `-0x230` for the two UI dispatch callees. These are
**structural mappings**, not byte-identical whole functions.
MIPS word comparisons decode spimdisasm's little-endian
annotation bytes before comparing opcode/register bits.

You can reproduce every comparison using the existing
[compare_asm_windows.py](../../tools/compare_asm_windows.py):

```sh
python3 tools/compare_asm_windows.py --left asm/g3_jp/nonmatchings/func_8002A2DC.s --left-start 0x8002F200 --left-end 0x8002F368 --right asm/g3_eu/nonmatchings/func_8002A2CC.s --right-start 0x8002EFD0 --require-shape
python3 tools/compare_asm_windows.py --left asm/g3_jp/nonmatchings/func_8002A2DC.s --left-start 0x8002F660 --left-end 0x8002F6F8 --right asm/g3_eu/nonmatchings/func_8002A2CC.s --right-start 0x8002F430 --require-shape
python3 tools/compare_asm_windows.py --left asm/g3_jp/nonmatchings/func_80033C44.s --left-start 0x80042C6C --left-end 0x80042D4C --right asm/g3_eu/nonmatchings/func_800338AC.s --right-start 0x800428D4 --require-shape
python3 tools/compare_asm_windows.py --left asm/g3_jp/nonmatchings/func_80033C44.s --left-start 0x800446AC --left-end 0x8004471C --right asm/g3_eu/nonmatchings/func_800338AC.s --right-start 0x80044314 --require-shape
```

All the paired windows have zero gaps in the tracked disassembly.
`--require-shape` checks *structure*, not retail hash or game semantics.

## 2. The 0x14-byte record really is `GsOT`

**Direct program evidence:** render preparation saves
`GsGetActiveBuff()` in JP `D_800ABA94` (EU
`D_800AC2D8`), then computes:

```text
ot = D_8016AF20 + 20 * D_800ABA94
GsClearOt(0, 0, ot)
...
func_8002F200(ot)    // HUD element, first dispatch callee
func_8002F660(ot)    // queued text, second dispatch callee
...
GsDrawOt(ot)
```

This 20-byte pointer stride and the *actual SDK function arguments*
match **Psy-Q `GsOT`**, whose documented 32-bit layout is:

| Offset | Type | Member |
| --- | --- | --- |
| +0x00 | 32-bit unsigned | `length` (OT bit length) |
| +0x04 | 32-bit pointer | `org` (OT tag array) |
| +0x08 | 32-bit unsigned | `offset` |
| +0x0C | 32-bit unsigned | `point` |
| +0x10 | 32-bit pointer | `tag` |

This ABI is described in the official [Psy-Q Run-Time Library
Reference, GsOT structure](https://psx.arthus.net/sdk/Psy-Q/DOCS/LibRef47.pdf)
and independently corroborated by
[PS1 debug-symbol type data showing `sizeof(GsOT)=0x14`](https://gist.github.com/mewmew/f4c94068e1462e40142b6cab112d43d2).
**Structure identity is high confidence.** A multi-element array is
indexed via the active buffer (normally two buffers); exact allocation
bounds and where its `length`/`org` are initialized still require
separate evidence. Do not merge the 0xE100-byte packet work buffers
with these 0x14-byte *headers*.

## 3. `func_8002F200` = state-driven sprite HUD path

**True JP function extent:** `0x8002F200..0x8002F368`.
The first scanner `glabel` is only `0x24` bytes long; the
`$sp -= 0x58` at `F204` is not restored until
`0x8002F358..F364`. All interior labels belong to this function.

- `0x108($gp)` is an enable state, with adjoining small functions
  `func_8002F1D8` (set 1), `func_8002F1E8` (clear) and
  `func_8002F1F4` (read). When disabled, the routine clears
  `0x104($gp)` and exits.
- When enabled it checks `func_80025944(8)` and reads the
  state `0x104($gp)`. Source-owned small accessors
  `func_8002F1C0`/`func_8002F1CC` read and write that word.
- It builds temporary halfwords at `$sp+0x38..0x44`,
  first setting `0x51, 0x1F8, 3, 1` followed by zeros.
  Depending on state `1` or `2`, one of the offsets
  `+0x42`/`+0x44` gets `0x7FFF`; otherwise `+0x40` does.
- A `0x110($gp)` timer reloads to `10` when zero, otherwise
  decrements; when its post-update value is at least `5`,
  it clears all three halfwords. These are **blink/phase-like
  state modulation**; no specific game UI label has been proven.
- It calls `func_8004B9F4(0)` and
  `func_8004BC1C($sp+0x38, $sp+0x40)`, then looks up
  resource key `0x707` using `func_8002F3D4`.
  If the lookup returns `-1`, it exits. Otherwise it
  copies **36 bytes** from the returned template onto the
  stack, zeros the copied sprite's `x`/`y` halfwords,
  and calls `GsSortSprite(sprite, ot, priority)`,
  taking priority from the lookup's output parameter.

**Likely typed object:** a standard 36-byte `GsSPRITE`, not
a game mesh or world geometry command.
The resource `0x707` and the temporary field group need
producer/asset analysis before naming the indicator
or interpreting its colors.

## 4. `func_8002F660` = queued centered-text renderer

**True JP extent:** `0x8002F660..0x8002F6F8`. The prologue
saves seven registers and builds a 0x40 stack frame;
`func_8002F6A4` is the body of a loop and
`func_8002F6D4` restores that frame. They are **not
independent functions**.

Its call chain is now determined:

```text
func_8002F660(GsOT *ot)
  count = func_8004471C()      // signed halfword at GP+0x79A
  records = func_80044728()    // &D_801443F4
  for i in [0, count):
    func_800251EC(records[i].text,
                  records[i].x, records[i].y, ot, 12)
```

The source records are **eight bytes** each:
`lw 0(s2)` -> text pointer, `lh 4(s2)` -> signed x,
`lh 6(s2)` -> signed y; the pointer increments by 8
per record. The fifth argument `12` is placed at
`0x10($sp)` per the MIPS calling convention.

The consumer is not a generic label guess: inspection of
`func_800251EC` (`JP 0x800251EC..0x800252A0`)
shows the implementation:
- Calls `strlen` on the text pointer.
- Centers around x by subtracting
  `((strlen(text) - 1) * advance) / 2`; integer rounding
  uses signed division-by-two correction.
- Walks the null-terminated string, draws one glyph per
  byte through `func_80025108`, incrementing x by
  `advance` (here 12 pixels).
- Passes the same OT pointer to each single-glyph helper. The
  **fifth argument 12 is character advance, not font priority**;
  `func_80025108` passes a separate constant **OT priority 0**
  when calling `GsSortSprite`.

`func_80025108` computes
`glyph = (unsigned_byte + 0xE0) & 0xFF`,
rejects glyph indices outside `[0,63]`, then selects
`D_800CF154 + 36 * glyph`. This maps the **ASCII interval
0x20..0x5F** (space through underscore) to exactly
64 **36-byte `GsSPRITE` glyph descriptors**, writes
the provided signed x/y into descriptor offsets `+4/+6`,
and calls `GsSortSprite(glyph_sprite, ot, 0)`.
Unsupported characters are skipped by the glyph helper
while the string renderer still advances the cursor.

The inferred 64 × 0x24 descriptor span occupies
`0x900` bytes at `D_800CF154`; this is a
**size/stride deduction**, not yet an allocation witness.
The original code modifies the glyph template's x/y
in place before sorting, which matters when preserving
exact runtime behavior.

## 5. The queue producer, cap, lifetime and error path

The queue initialization and append routines live in the
**large control ASM**: `JP 0x800444B0..0x8004450C`
and `JP 0x800446AC..0x8004471C`.

The initialization at `0x800444DC` (tail of the
`func_800444B0` flow) sets:
- `0x79A($gp)` (signed 16-bit count) to **0**;
- `D_800ABC1C` (mutable **write cursor**) to
  **`D_801443F4` (fixed base)**.
- A parallel queue at `0x798($gp)` and
  `D_8014419C` is also reset, but its purpose is
  outside this bounded atlas.

The append entry `func_800446AC(text, x, y)`:
- Returns if text pointer is null.
- If signed count `>= 10`, calls `printf` with the
  retained string **"Over flow FONT packet!\n"** at
  `D_800214D0` and declines to append.
- Else increments the count and writes the
  8-byte packet at the mutable cursor:
  `sw text,0(cursor); sh x,4(cursor); sh y,6(cursor)`.
- Advances `D_800ABC1C` by `8`.

A cautious *proposed 32-bit ABI view*, **not committed C**:

```c
typedef struct {
    uint32_t text_addr; // original MIPS pointer to a NUL-terminated string
    int16_t x;
    int16_t y;
} FontPacket32;        // exactly 8 bytes on a 32-bit PS1
// At most 10 entries, array base JP 0x801443F4 / EU 0x80144CDC
// Count in GP+0x79A, write cursor in a separate global.
```

Source-only check: `func_800468EC` is a direct caller of
the append entry and passes `&D_80144824` as text,
a sign-extended x position, and y = `0x28` (40).
Immediately prior, its function writes a zero terminator
into that buffer. This is one **real producer-to-queue
data flow**, not solely an API-shape inference.
Additional queue producers may be indirect or in C units;
this pass has not proved an exhaustive incoming-xref set.

## 6. Higher-level frame loop — caller/order now established

The main loop is **JP 0x80042C6C..0x80042D4C**:
the prologue begins at `0x80042C6C` (immediately
after a `jr $ra` within a scanner row labelled
`func_80042C64`), and the real epilogue is
`0x80042D3C..0x80042D48`. The scanner
`func_80042C90` label marks the **loop head,
not a separate function**.

**Ordered, independently observed direct call sites:**

1. `0x80042C90: jal func_80022E24` (graphics/MDEC prep).
2. `0x80042C98: jal func_80024718`;
   `0x80042CA0: jal func_80044294` (untyped support).
3. `0x80042CA8: jal func_800444B0`
   (**resets queue**).
4. `0x80042CB0 / 42CB8 / 42CC0`:
   three support stage helpers.
5. `0x80042CC8..42CE8`: loads
   `D_800AC5AC & 7`, indexes an eight-pointer
   dispatch table at **`D_8008AF1C`**, then
   **`jalr $v0`**. This is a strong game-mode
   or state-dispatch candidate. Table entries
   are not yet independently enumerated.
6. `0x80042CF0..42D10`: five additional stage
   calls, of currently untyped roles.
7. `0x80042D18: jal func_80022FE4`
   (**dispatch/render/sync/submit**), which
   itself calls the two HUD functions and
   `GsSwapDispBuff/GsDrawOt`.
8. `0x80042D20..42D30`: checks
   `D_800AC4F4 == 1`; if false, branches
   to `0x80042C90`. On true, calls
   `func_8002AD24` and returns.

EU `0x800428D4..0x800429B4` has 56/56
identical opcode/register shapes, with
**37/56 completely identical instruction words**.
The EU loop calls corresponding preparation
`0x80022E84` and submission `0x80023044`,
matching the entire stage order. This is
direct call-edge evidence for the previously
uncertain preparation→dispatch sequencing,
not merely physical source adjacency.

**Frame lifetime inference:** the text queue
is reset in the loop **before** the indirect
mode callback and drained in the later
submission function. As long as producers
run in between, enqueued text appears in
that same iteration. Runtime ordering and
frequency are supported by control flow,
not observed frame tracing; asynchronous
callbacks or indirect paths remain unexamined.

## 7. Video-decode side branch and remaining dependencies

The previous render-preparation atlas described
`func_8005E6C4` and `func_8005E740` as
unclassified helpers on the `0($gp)==0`
path. The current
[SDK anchor catalog](../../config/sdk_anchors.txt)
identifies those exact JP addresses as
**`DecDCTin`** and **`DecDCTout`** (LIBPRESS
3.3 fixed-window matches). The call site
reads an indexed input pointer and passes a
computed output size `(signed16A * signed16B)/2`.
This warrants a **video/MDEC input-output
stage** label; the media format, callback
scheduling and buffer ownership have not
been established in this pass.

Separately, `func_8005DBE0` receives
`D_8014773C + active_buffer * 0xE100`.
It sits next to recognised LIBGS routines but is not
currently named by the SDK-anchor file. Its complete
four-instruction body is available in
[func_8005DBE0.s](../../asm/g3_jp/nonmatchings/func_8005DBE0.s):
`sw $a0, D_8016AA40; jr $ra`.
That same global is loaded and updated by the
[SDK-identified `GsSortSprite` body](../../asm/g3_jp/nonmatchings/func_80051D14.s)
(`0x80051D78/7C` and `0x800521E4/E8`). Therefore
**the work-base setter behavior is directly verified**:
the 0xE100-stride buffer base is installed as the
LIBGS GPU packet allocation cursor consumed by
sprite sorting. The canonical SDK **name**
`GsSetWorkBase` is strongly supported but is
**not yet established from an archived member/signature**;
no shared symbol was renamed.

## 8. Recommended next bounded research

**High priority:** enumerate the eight mode dispatch-table
entries at `D_8008AF1C` (EU `D_8008B734`),
then trace a single nontrivial mode callback
that enqueues text or sorts objects into the OT.
This connects identified draw primitives to
actual gameplay state transitions and avoids
conflating SDK mechanisms with game design.

**Next smaller subtask:** map the producer of the
64 glyph-sprite descriptors at `D_800CF154`
and the owner of resource `0x707` used by
the conditional HUD sprite. Recover field
names only when the authoring/data and
initialization evidence supports them.

**Oracle-gated work only:** consider
`func_80025108`/`func_800251EC` plus the
font-queue getter/append family as unusually
clear semantic-C candidates. They are
not yet recompiled or byte matched. Any
migration would require an ASM split and
a witnessed eight-target build where shared
rows change.

## 9. Limits, negatives and decision status

- All byte-shape figures come from tracked
  disassembler comments and are structurally
  reproducible without game files.
- `GsOT` and `GsSPRITE` sizes are established by
  the documented ABI and observed strides,
  but the exact *local* SDK header version
  and array allocation sizes are not verified.
- The byte-exact interpretation of a third
  helper `func_8005DBE0` is still open.
- We **did** locate a direct frame-loop caller,
  queue initializer, queue writer and one
  text producer. We **did not** exhaust
  all direct/indirect callers, pointer tables
  or data-driven sprite resource owners.
- No code or matching files were changed,
  no oracle was present on this host,
  and **no new 8/8 retail verification
  was performed**.

# G3 render-path atlas, JP ↔ EU

**Static research window:** 2026-11-22. **Status:** new bounded analysis,
source-only; no new retail-image build or runtime trace.

Scope: Japanese main-game executable, ROM/file offsets
`0x32FC..0x3AD0`, runtime VAs `0x80022AFC..0x800232D0`.
Cross-region target: `g3_eu` at **JP VA + 0x60** over these sampled
windows. The range sits within the very large YAML `asm` row beginning
`func_80022AFC` (JP) / `func_80022B5C` (EU). It was chosen because the
assembled code contains graphics state setup, buffer-indexed dispatch,
display swap, and draw submission, not merely another Psy-Q wrapper.

## Source and evidence boundaries

- JP: [splat.g3_jp.yaml](../../config/splat.g3_jp.yaml),
  [func_80022AFC.s](../../asm/g3_jp/nonmatchings/func_80022AFC.s).
- EU: [splat.g3_eu.yaml](../../config/splat.g3_eu.yaml),
  [func_80022B5C.s](../../asm/g3_eu/nonmatchings/func_80022B5C.s).
- SDK ownership: [sdk_anchors.txt](../../config/sdk_anchors.txt).
  Neither region intersects an existing SDK anchor in either target;
  the earliest anchored functions are around `0x80027A40` JP and
  `0x80027A3C` EU. **Absence of an anchor is not positive proof of game
  ownership.** Use the direct graphics calls and state relationships
  below as *additional* behavioral evidence.
- Byte counts / shape comparison:
  [compare_asm_windows.py](../../tools/compare_asm_windows.py) parses the
  original spimdisasm instruction annotations with correct **little-endian
  word decoding** and refuses gaps. It does not rely on retail images.
- Prior research check: searched retained [TASKS.md](../TASKS.md) for
  `func_80022E24`, `func_80022FE4` and `func_80022B6C`: none had a
  preexisting targeted investigation under those exact labels. This
  is a first bounded atlas, **not** a claim that every adjacent code
  path has never been examined.

## A. Contiguous function candidates and cross-region evidence

| Role (provisional) | JP VA, end-exclusive | EU VA, end-exclusive | Bytes | Word-identical / total | Structural match |
| --- | --- | --- | ---: | ---: | --- |
| File/open-load helper | `22AFC..22B6C` | `22B5C..22BCC` | 0x70 | 23/28 | Same opcodes and registers |
| Conditional state/control gate | `22B6C..22D58` | `22BCC..22DB8` | 0x1EC | 90/123 | Same opcodes and registers |
| Three path/string append helpers | `22D58..22E24` | `22DB8..22E84` | 3 × 0x44 | Not compared in this pass | Independently bounded by return instructions |
| **Graphics preparation** | **`22E24..22FE4`** | **`22E84..23044`** | **0x1C0** | **80/112** | **Same opcodes and registers** |
| **Graphics dispatch, sync and draw submission** | **`22FE4..232D0`** | **`23044..23330`** | **0x2EC** | **128/187** | **Same opcodes and registers** |

All VAs in the table have the `0x80000000` prefix. In the two main
graphics windows together, **208/299 instruction words are byte-identical**;
the remaining **91/299 differ only in instruction operand/encoded
address fields** under the MIPS opcode+register comparison. Mnemonic
order, instruction count, branch placement, and register selections match
exactly. This is stronger than a vague similar-function hypothesis,
but it is not a symbolic relocation proof or a claim that the runtime
state values are equal.

**Important boundary correction:** spimdisasm has emitted many `glabel`
fragments inside these routines. The labels `func_800231B0`,
`func_800231D0`, `func_800231D8` and `func_800232C0` are **not four
independent C functions** here. `0x80022FE4` allocates 0x20 bytes of
stack and saves `$ra` and `$s0`; branches converge at
`0x800232C0`, whose `lw`/`jr`/stack-release instructions restore that
same frame. The next independent prologue starts at `0x800232D0`.
Similarly, `0x80022E24` creates a 0x28 frame and restores it at
`0x80022FD4`. Do **not** schedule isolated C conversion of interior
glabels as if each had an independent calling convention.

### Reproduce the paired instruction census

```sh
python3 tools/compare_asm_windows.py \
  --left asm/g3_jp/nonmatchings/func_80022AFC.s \
  --left-start 0x80022E24 --left-end 0x80022FE4 \
  --right asm/g3_eu/nonmatchings/func_80022B5C.s \
  --right-start 0x80022E84 --require-shape

python3 tools/compare_asm_windows.py \
  --left asm/g3_jp/nonmatchings/func_80022AFC.s \
  --left-start 0x80022FE4 --left-end 0x800232D0 \
  --right asm/g3_eu/nonmatchings/func_80022B5C.s \
  --right-start 0x80023044 --require-shape
```

The `--json` flag includes each window's distinct `jal` call targets for
a starting cross-region function map. **The raw 8-hex-digit instruction
annotations are little-endian byte sequences**: numerically parsing
them as big-endian MIPS words gives false opcode mismatches.

## B. Strongest subsystem inference: graphics-buffer ownership

### Preparation, `g3_jp:0x80022E24..0x80022FE4`

These observations come from direct loads/stores and call sites:

1. If `0($gp) == 0`, performs additional work: indexes
   `D_8016AEA8[D_8016AEB0]`, calls `func_8005E6C4` with
   `a1=2`, multiplies signed halfwords
   `D_8016AEC8 * D_8016AECA` and passes a
   sign-adjusted arithmetic halving of the product to
   `func_8005E740`. It invokes `func_8002ADA0` with
   `&D_8016AEA8`, `D_800ABA9C` and `2`, and can exit early
   after an error/sentinel result (`-1`).
2. The common path calls `func_8002B20C(&D_800AC294)`, doubles
   `D_800AC294`, and conditionally stores a two-times halfword
   field from a returned record into `D_800AC16C` (gated by
   `D_800AC494 == 1`).
3. Calls **`GsSetRefView2(&D_800CC5C4)`** (`0x80022F2C`).
4. Calls **`GsGetActiveBuff`** (`0x80022F34`), and writes
   its result into **`D_800ABA94`** (`0x80022F40`).
5. Passes **`D_8014773C + active_buffer × 0xE100`** to
   `func_8005DBE0` (`0x80022F60`): the shifts subtract
   the original index twice, producing `15 × 15 × 256 =
   57,600` bytes of stride. The allocation/base's meaning is
   **not yet verified**.
6. Calls **`GsClearOt(0, 0, D_8016AF20 + active_buffer × 0x14)`**
   (`0x80022F8C`). The 20-byte stride comes from
   `(buffer * 4 + buffer) * 4`. This makes the array a candidate
   per-buffer ordering-table descriptor; its **C structure and size
   have not been independently validated**.
7. Reads a mode-like helper `func_80025944(9)` and conditionally
   writes its result to `D_800AC164` if the value is in
   `[1, 6]` and `D_800AC5AC == 4`.

### Dispatch/presentation, `g3_jp:0x80022FE4..0x800232D0`

This is a *whole frame-owning routine* (not just the first 0x1CC bytes
before the next interior glabel). It:

1. Calls `func_80046304`, a setup helper, and a short series of
   unclassified state/update functions.
2. Reloads **`D_800ABA94`** and repeatedly computes the **same
   `D_8016AF20 + active_buffer × 0x14`**. It supplies that
   pointer to at least nine different callees, including
   `func_8002F200`, `func_8002F660`,
   `func_8002EF14`, `func_800232D0`,
   `func_8002EF84`, `func_8002F09C`,
   `func_8002DABC`, `func_8002E9F4`
   and `func_8002EC7C`. **Do not assume that all nine are
   drawing routines** until their bodies are audited.
3. Calls `func_8002F488`; clears the first byte of three
   0x200-spaced buffers (`D_800CCFE4`, `D_800CD1E4`,
   `D_800CD3E4`); then `func_8002334C`.
   Earlier functions at `0x80022D58`, `0x80022D9C` and
   `0x80022DE0` append source strings and a common suffix to these
   respective buffers via `strcat`. This gives a concrete
   **short-lived three-slot text/path workspace**; the final
   display purpose is still inferred.
4. Branches on `0($gp)` to **`VSync(4)`** or **`VSync(0)`**
   (`0x800231C0/0x800231D0`); decrements
   `D_800AC59C` when positive and conditionally updates
   additional GP-backed state.
5. Calls **`GsSwapDispBuff`** (`0x80023278`), passes
   `&D_8016AEA8` and active-buffer index to
   `func_8002AC04` (`0x80023290`), then calls
   **`GsDrawOt(D_8016AF20 + active_buffer × 0x14)`**
   (`0x800232B8`).
6. Finally restores the `0x20`-byte stack frame at
   `0x800232C0..0x800232CC`.

**Inference, not an observed runtime trace:** the repeated pointer
equivalence, explicit ordering-table API calls, VSync, buffer swap and
GsDrawOt strongly support the provisional name *frame render
preparation + rendering/presentation dispatcher*. The two routines
are **linked by shared state**, but their immediate **caller and call
order are not yet established**. Physical adjacency alone is not a
control-flow edge. A runtime trace or a complete cross-file xref index
would verify actual execution sequencing and frequency.

### EU correlation

EU `0x80022E84` and `0x80023044` have the **same instruction
and register skeletons** at every corresponding offset. Representative
state/site mappings:

| JP | EU | Evidence / role |
| --- | --- | --- |
| `D_800ABA94` | `D_800AC2D8` | active buffer saved in prepare, read by dispatch |
| `D_8016AF20` | `D_8016B044` | 20-byte-stride table passed to OT/render helpers |
| `D_8016AEA8` | `D_8016AFCC` | array or state object passed to update helpers |
| `D_8014773C` | `D_80158068` | 0xE100-stride base used by one prepare call |
| `GsSetRefView2` | `GsSetRefView2` | same SDK API |
| `GsGetActiveBuff` | `GsGetActiveBuff` | same SDK API |
| `GsClearOt` | `GsClearOt` | same SDK API |
| `GsSwapDispBuff` | `GsSwapDispBuff` | same SDK API |
| `GsDrawOt` | `GsDrawOt` | same SDK API |

**No global name migration** has been made; these mappings are scoped to
the compared instruction sites, not an automatic global-symbol equivalence
claim. The names used by the project are kept unchanged.

## C. A misleading SDK-negative area: format processing

One nearby `g3_jp` YAML region,
`func_8004803C` (`0x8004803C..0x80048DB4`, 0xD78 bytes),
is currently **origin-unattributed** by the SDK-anchor tool. It
lies directly between recognised libc veneers for `printf`/
`strncat` and `memchr`. Its code parses format bytes:
`0x25` ('%'), `0x2D` ('-'), `0x2B` ('+'), `0x23`
('#'), `0x30` ('0') and `0x2A` ('*'), while consuming
variable arguments from the stack.

Crucially, the game's `0x800232D0` helper explicitly passes
`D_800200CC = "MAP COUNTER = %d"` and a counter to
`func_8004803C` with output buffer `D_800CC5E4`.
See [data_80020000.data.s](../../asm/g3_jp/nonmatchings/data/data_80020000.data.s)
and the calling code in the root ASM file above.
The EU sibling `func_80047CA4` (`0xB3C bytes`) likewise parses
format flags, and is called with the EU counterpart of the same literal.
This is positive behavioral evidence for a **printf-family formatter
(e.g. sprintf-like)**, **not** a candidate game-state function.

**Decision:** keep this span as **SDK/standard-library-like,
unconfirmed origin**; do not relabel it an exact Psy-Q archive member or
remove it from the machine-readable unassigned metric until actual member
evidence exists. But *exclude it from the next gameplay-C priority list*.
The original rule was conservative enough to preserve this distinction.

## D. Ranked first-pass reconstruction targets

| Priority | Window | Why | Concrete blocker |
| --- | --- | --- | --- |
| **1** | JP `22FE4..232D0` / EU `23044..23330` | High-value original behavior: active-buffer dispatch, temporary text workspace, VSync, buffer swap and OT submission; independently measured same-form EU sibling | Establish **true external callers**, 20-byte record layout, and semantics/ABI of the nine dispatch callees; current row is one enormous YAML ASM segment, so a C conversion needs an evidence-backed split |
| **2** | JP `22E24..22FE4` / EU `22E84..23044` | Owns active-buffer selection, OT clear and render-state staging, shares buffer record with #1 | Establish `D_8014773C` 0xE100 object size, function input/output and exceptional return/control branch |
| **3** | JP `22B6C..22D58` / EU `22BCC..22DB8` | Distinct control/state gate (123-word cross-region skeleton); potential input/state machine | Explain the anonymous selector API and the state enum before assigning human-readable names |
| **4 (small first C experiment)** | JP `22D58..22D9C` and two 0x44-byte siblings | Simple two-`strcat` wrappers; three independent prologues/returns, trivial to model as semantic C, exercised by text/path code | Limited gameplay value; cannot land without toolchain and retail verifier; splitting existing 0x4F44-byte ASM row changes packaging |
| **Do not prioritize** | JP `4803C..48DB4` / EU `47CA4..487E0` | Likely libc formatting implementation, not gameplay; large false-positive in naive "unassigned code = game" analysis | Psy-Q member/signature attribution still missing |

The next bounded R1 experiment should **map the actual nine buffer
dispatch callees and the two function entry xrefs**. Start with
`func_8002F200` and `func_8002F660`, the first two stage calls
receiving the 20-byte-stride pointer, and classify their side effects
(including GTE/GPU commands). This is higher value than matching more
individual SDK veneers.

## E. Reproduction and limits

```sh
# Locate the two target segment owners and the relevant SDK evidence.
rg -n 'func_80022AFC|func_80022B5C' config/splat.g3_*.yaml
rg -n '^// target: g3_(jp|eu)' config/sdk_anchors.txt

# Locate shared-state and PSY-Q graphics operations in the two big rows.
rg -n 'Gs(GetActiveBuff|ClearOt|SwapDispBuff|DrawOt)|D_800ABA94|D_8016AF20' \
  asm/g3_jp/nonmatchings/func_80022AFC.s

# Find other syntactically direct references (many callers may be indirect).
rg -n 'jal +func_80022(E24|FE4|D58)|j +func_80022(E24|FE4|D58)' \
  asm/g3_jp/nonmatchings src
```

The second pair comparator in section A is a **structural**, not
semantic, test. Syntax/byte identity after masking immediate fields
does not prove that the called functions, global data or branch targets
have equal semantics.

**Not done / not claimed:** complete caller enumeration, runtime tracing,
SDK archive attribution for `func_8004803C`, typed structure recovery,
successful C compilation, unit object equality, or any new eight-target
retail SHA-1 verification. In particular, do not split the original ASM
row or change any source/addresses to force progress without the
owner's verified build environment.

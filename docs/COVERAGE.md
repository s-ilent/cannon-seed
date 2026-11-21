# Coverage metrics and evidence tiers

The historical [tools/progress.py](../tools/progress.py) census reports
target-specific C function definitions versus remaining assembly labels.
**It is not a percentage of semantically recovered game code.**

Run the new, independent source-only byte-span report:

```sh
python3 tools/coverage_report.py
python3 tools/coverage_report.py --target g3_jp --json --rows
python3 tools/coverage_report.py --strict --json --rows > coverage.json
```

GitHub Actions generates `coverage.json` alongside `progress.json` in the
existing `progress-report` artifact. The old report's numbers and
schema stay unchanged. **Neither file is a retail SHA-1 match witness.**

## Independent axes — read each separately

| Axis | Measurement | What the measurement does *not* imply |
| --- | --- | --- |
| **Per-executable C coverage** | Sum of bytes in `c` subsegments / sum in `c` + `asm` subsegments of the current YAML | Real executed instruction coverage; end-to-end game completeness |
| **SDK-evidenced C/assembly** | Union of overlapping exact VA/extent ranges from `config/sdk_anchors.txt` within the YAML's `c` and `asm` rows | A fully byte-verified SDK member at every site: some `window-fixed` identifications include relocation wildcards |
| **Origin-unattributed C/assembly** | Mapped code bytes **not** intersecting those SDK evidence spans | Definitively custom/game code; some SDK code is not in the currently indexed archives |
| **Source-unit assembly flag** | Resolved `src/<target>/<unit>.c` (target first) or `src/<unit>.c` contains inline `asm`/`__asm__` or `INCLUDE_ASM` after stripping comments | Amount of generated machine code from asm, or that assembly-free source has understandable semantics |
| **Reviewed semantic/hybrid/asm-preserved C** | Bytes in *specifically reviewed* C YAML rows listed in `config/coverage_reviews.json` | Every unreviewed C row is nonsemantic, or semantic review proves binary equality |
| **Original function census** | Definitions in C source files and `glabel` tokens in assembly | Distinct original functions or byte-level progress |

The two source axes are deliberately **not interchangeable**. A file may
contain one inline-assembly register shim and many readable C statements:
the automatic *source-unit* flag marks the entire C subsegment as
assembly-involved. A source without visible asm may still be a thin
wrapper, a copied stub, or a compiler-specific trick.

A review entry with `tier: "semantic_c"` is a **bounded qualitative
code-review claim**, not runtime validation or a fresh SHA-1 match. The
report explicitly refuses a semantic-C review if its source contains
inline assembly, but passing that check is **not sufficient** to grant
the label: a human must review the specific source and supply evidence.

## What is the denominator?

The current segment map labels spans `c`, `asm` or `data` under a
code segment. The report determines byte lengths from **successive YAML
offsets and the terminal segment boundary**, not from trailing `# 0x...`
comments (which can be stale). All eight executable payloads count
independently. The total is therefore **target instances**, not distinct
shared source functions.

`mapped_code_bytes = c_bytes + asm_bytes` is a **mapping convention**;
the scanner may still have classified executable code as data, or
included padding, tables or small data islands in an assembly row.
Consequently, these are **C-share-of-mapped-code** figures, not measured
CPU instruction coverage. The report separately exposes `mapped_data_bytes`.

For each mapped code category:

```text
mapped code = SDK-evidenced code + origin-unattributed code
C bytes     = SDK-evidenced C    + origin-unattributed C
SDK C share = SDK-evidenced C / SDK-evidenced code
Unassigned C share = origin-unattributed C / unattributed code
```

An `UNATTRIBUTED` label **must not be relabeled "game"** without
positive evidence (link records, cross-revision relocation, ownership,
control/data flow, etc.). The explicit unassigned group prevents an
incomplete SDK archive census from inflating gameplay progress.

## Manual review registry

`config/coverage_reviews.json` is a **small, source-inspected
demonstration set**, not an authoritative exhaustive list. Each record
is keyed by **target and YAML C row name**, identifies the resolved
source file and gives a narrow review rationale.

- `semantic_c`: behavior is expressed in intelligible C; can still have
  placeholder names or types. No inline asm allowed under this tier.
- `hybrid`: meaningful C mixed with register-pinned/manual assembly.
- `asm_preserved`: a C compilation wrapper whose actual algorithm is
  largely handwritten assembly; *not* recovered semantic C.

Unreviewed rows stay `unreviewed` regardless of automatic source style.
When extending the registry, inspect the source **and** its real target
YAML row. Do not mark a whole multi-function translation unit semantically
reviewed based on one readable function; annotate the unit only if the
entire row has been inspected. A stale review source, invalid quality,
nonexistent row or semantic/asm contradiction is a report error.

The initial narrow sample deliberately includes ordinary C wrappers
(game and menu), hybrid state-reset code, and SDK GTE asm-preserved
routines; it is **not** enough evidence to publish a global percentage
of semantically decompiled gameplay.

## Interpreting progress and prioritizing work

Use the SDK-evidenced vs unassigned **byte** split to identify where C
recovery is concentrated. Use the per-row JSON to choose large, likely
game-owned ASM spans for focused research. Then establish *positive*
game-code ownership through the [current research queue](WORK_QUEUE.md)
before trying an asm-to-C conversion.

A more ambitious future metric would divide proven game-owned functions
from unclassified code and measure typed, named semantic C **per
individually verified function**. This report does not pretend such an
ownership/semantic atlas already exists.

## Consistency and test gates

- The YAML parser fails closed on invalid, overlapping or noncontiguous
  subsegment offsets and missing end boundaries.
- SDK anchor intersections are unioned, so overlapping SDK windows do not
  double-count bytes.
- The strict mode refuses missing C sources or absent SDK evidence for
  any included target.
- The review registry is checked against actually compiled per-target
  rows, not filenames alone.
- `tests/test_coverage_report.py` covers arithmetic, false semantic
  promotions, source resolution, invalid evidence and review drift.
- CI runs both source-only reports and archives row-by-row JSON. **It
  does not build or verify any retail executable.**

Continue using [CI.md](CI.md) and [TOOLCHAIN.md](TOOLCHAIN.md) for the
actual complete-image verification contract.

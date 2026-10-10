# Contributing

This is a matching decompilation intended to remain workable for years. A
retail byte match is required, but it is only one part of accepting a
change. The rules live in [docs/RULES.md](docs/RULES.md); this file is the
contract for how a change moves through the tree.

## Daily loop

1. Keep experiments and non-matching reconstructions out of the tracked
   tree.
2. Add C to `src/` only together with the config entry that wires it in, so
   a fresh clone can never diverge from CI.
3. Keep functions within a file in ROM-address order; C89 only
   (`/* */` comments, declarations at block top).
4. Use subsystem headers for cross-unit declarations; do not add file-local
   `extern` debt.
5. Run the narrow per-function diff while iterating.
6. Run `make verify` before handing work off — and commit only on green.

For a shared header, compiler wrapper, Makefile, manifest, source move or
translation-unit boundary change, run `make clean verify` instead: structural
work must be proven without stale objects.

## State your claim

Every change declares which claim it makes, because the byte check validates
only the first of these:

| claim | meaning |
| --- | --- |
| **binary match** | the linked image is byte-identical to retail (`make verify` green) |
| **semantic recovery** | the C expresses the original logic, not just its bytes |
| **typing** | a struct/prototype is now typed from evidence |
| **naming** | a name is now backed by evidence (record the evidence) |
| **organization** | a boundary/ownership change follows the evidence order |

A green build proves only the first. Reviewers reject changes whose stated
claim outruns what was shown.

## Definition of done

A change is done when:

- the function is semantic C under the assembly policy (docs/RULES.md §3);
- its stock-compiler object diff is exact;
- `make verify` (or `make clean verify`) passes;
- any debt reduction is captured by lowering `config/ratchets.json` in the
  same PR;
- naming, typing or source-boundary claims have evidence, not only a byte
  match.

A file is **finished**, not only matched, when it is byte-matched *and*
fully named, typed, free of hidden fixed addresses, and placed in its
subsystem (docs/GUIDELINES.md).

## Ratchet discipline

`config/ratchets.json` baselines must equal the current tree. CI fails when
debt increases **and** when an improvement leaves a stale higher baseline —
every cleanup is therefore permanent: later work cannot silently spend it.
Baseline raises are policy changes and require explicit review in the PR
description; they are not a normal way to go green.

## Measurement over transcription

Progress lives in tools, not prose: `make progress`, `make nonmatchings`,
`make ratchets`. Do not paste numbers into documents — they are stale within
a round. Lessons go into `docs/` with evidence attached or into commit
messages.

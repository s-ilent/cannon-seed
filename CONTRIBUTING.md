# Contributing

This project reconstructs retail executables byte for byte while keeping the source maintainable. A retail byte match is required. Changes must also satisfy code structure rules. Core rules live in [docs/RULES.md](docs/RULES.md). This file describes the contribution workflow.

## Daily loop

1. Keep experiments and non-matching drafts out of the tracked tree.
2. Add C files to `src/` only when wired into the active build configuration.
3. Keep functions within a file in ROM-address order. Use C89 syntax (`/* */` comments, declarations at block tops).
4. Use subsystem headers for cross-unit declarations. Do not add file-scope `extern` definitions in C files.
5. Use narrow per-function diffs while iterating.
6. Run `make verify` before submitting work. Commit only on green builds.

Run `make clean verify` after you update shared headers, compiler wrappers, Makefiles, manifests, or translation boundaries.

## State your claim

Declare the claim for each change in your commit message:

| Claim | Meaning |
| --- | --- |
| **binary match** | The linked image matches the retail SHA-1 (`make verify` passes) |
| **semantic recovery** | The C code accurately expresses the original program logic |
| **typing** | A struct or prototype is defined with evidence |
| **naming** | An identifier is named based on evidence (cite the source) |
| **organization** | A file or boundary change follows layout evidence |

A passing build verifies binary equivalence only. Reviewers will reject patches if claims exceed what the author proved.

## Definition of done

A change is complete when:

- The function uses semantic C that follows the assembly policy (docs/RULES.md §3).
- The stock compiler produces an exact object match.
- `make verify` (or `make clean verify`) passes.
- The pull request lowers baselines in `config/ratchets.json` for any debt reduction.
- Naming, typing, or boundary claims include supporting evidence.

A file is finished when it matches byte for byte, uses typed structures, uses verified names, avoids hard-coded addresses, and resides in its target subsystem (docs/GUIDELINES.md).

## Ratchet discipline

Baselines in `config/ratchets.json` must match the current tree. CI fails if debt increases or if an improvement leaves behind an outdated higher baseline. Every cleanup is permanent. Raising a baseline requires an explicit review.

## Measurement over transcription

Track progress using tools: `make progress`, `make nonmatchings`, and `make ratchets`. Do not paste numbers into documentation. Record lessons in `docs/` with evidence or inside commit messages.

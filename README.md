# cannon-seed — Galaxian³ (PSX) matching decompilation

C source that compiles, with the game's original pinned toolchain, into
executables byte-for-byte identical to the retail Galaxian³: Project
Dragoon discs. Methodology distilled from tenchu-decomp, lsddecomp,
parasite-eve-decomp and rage-racer-decomp; the full survey is
[docs/PSX-Decompilation-Methodology-Report.pdf](docs/PSX-Decompilation-Methodology-Report.pdf).

> A paraphrase of a program can be subtly wrong without anyone noticing.
> A byte-exact rebuild can't be. — lsddecomp

**Targets (8 — this is a multi-EXE game):** the boot executables
SLPS-00270 (JP) / SCES-00269 (EU), plus three payloads per region:
`MAINMENU.EXE`, `DRAGOON/G3.EXE` (the main game) and `GOURB/G3ORG.EXE`.
All hashes, sizes and header facts are measured in
[docs/RECON.md](docs/RECON.md); the committed oracles live in
`config/sha1/`.

## What is and is not in this repository

**No game data and no Sony files.** No disc image, CHD, executable,
asset, SDK library or SDK header is committed, and none ever will be.
You bring your own legally obtained copies (this project started from the
owner's redump-style CHDs); the build reads them from git-ignored
directories.

| you provide | where | what the build does with it |
| --- | --- | --- |
| retail CHDs / exes | `baselines/` | split (splat) + whole-image verification |
| pinned toolchain | system / venv | compiles `src/` with the exact original compiler |
| Sony Psy-Q SDK | `sdk/` | converted to `lib/` + `include/psyq/` — generated and ignored |

What *is* committed: the reconstruction (`src/`, `include/`), splat
configs and symbol lists (`config/`), generated `asm/` (never edit it),
the tools — including `tools/chd_extract.py`, a self-contained CHD v5
CD-ROM reader (port of MAME's algorithms) so anyone can verify the
extraction from their own CHDs — and the docs.

## Status

The repo owns a byte-exact build machine: splat split → maspsx → mipsel
as → per-subsegment linker script → objcopy → generated PS-X EXE header.
The round-trip oracle is GREEN for **2 of 8 targets** — `slps_00270`
(Japan boot) and `sces_00269` (Europe boot) — i.e. `make verify
TARGET=<t>` reproduces those retail executables byte-for-byte from
committed asm. This is an asm round-trip, not decompiled source: every
function is still nonmatching, and the remaining six targets await their
scan configs. Next: compiler pinning (docs/TOOLCHAIN.md), GCC 2.6.3
acquisition, first C function match, then the remaining targets.
Live facts: [docs/RECON.md](docs/RECON.md). Measure, don't transcribe:
`make progress`, `make nonmatchings`, `make ratchets`.

## The one command that matters

```sh
make verify
```

Builds and compares the whole image with retail; ends
`OK: build matches retail ...` on success. It is the only build entrance —
a bare `make` is deliberately blocked, because a bare build says nothing
about whether the bytes are right.

| command | what it does |
| --- | --- |
| `make verify TARGET=<t>` | oracle gate: build + whole-image SHA-1 vs retail |
| `make extract TARGET=<t>` | split the target executable with [splat] |
| `make progress` | matched / nonmatching function report |
| `make nonmatchings` | list the functions that do not match yet |
| `make ratchets` | placeholder / debt ratchet audit |
| `make hooks` | install oracle-protecting git hooks |
| `make clean` | remove the build directory |

Targets: `slps_00270`, `sces_00269`, `mainmenu_jp`, `mainmenu_eu`,
`g3_jp`, `g3_eu`, `g3org_jp`, `g3org_eu`.

Extracting the executables from your own CHDs:

```sh
python3 tools/chd_extract.py Galaxian3_Japan.chd japan.bin      # 2352 B/sector
python3 tools/iso9660_extract.py japan.bin out/ 'SLPS_002.70;1' ...
```

## Methodology in the tree

| document | holds |
| --- | --- |
| [docs/RECON.md](docs/RECON.md) | measured facts: discs, executables, headers, fingerprints, open questions |
| [docs/WORKFLOW.md](docs/WORKFLOW.md) | the six-phase lifecycle, with the figure |
| [docs/RULES.md](docs/RULES.md) | the hard rules with rationale — oracle, toolchain, source, process |
| [docs/GUIDELINES.md](docs/GUIDELINES.md) | naming scheme, evidence order, shiftability, AI orchestration |
| [docs/MATCHING.md](docs/MATCHING.md) | the matching loop: ladder, parking policy, how a score lies |
| [docs/CHECKLIST.md](docs/CHECKLIST.md) | the starter checklist (steps 1-4 done — see RECON) |
| [CONTRIBUTING.md](CONTRIBUTING.md) | the review contract: state your claim, ratchets, definition of done |
| [CLAUDE.md](CLAUDE.md) | the short agent contract (rules + loop, never state) |

## Licence

The project's own work is MIT (see [LICENSE](LICENSE)) — covering the
reconstructed source, headers, configuration and tools *only*. Galaxian³,
its assets and Sony's Psy-Q SDK remain the property of Namco / Sony and
are not, and will not be, in this repository.

[splat]: https://github.com/ethteck/splat

# Galaxian³ (PSX) matching decompilation

A matching decompilation of Galaxian³: Project Dragoon for the PlayStation. The project reconstructs the original C source code to produce byte-identical binaries when compiled with the original toolchain.

The game uses eight executable targets across two regional releases:

* Boot executables: `slps_00270` (Japan) and `sces_00269` (Europe)
* Payloads: `mainmenu_jp` / `mainmenu_eu`, `g3_jp` / `g3_eu` (the main game), and `g3org_jp` / `g3org_eu`

Header details, memory maps, and SHA-1 checksums are documented in [docs/RECON.md](docs/RECON.md). Target hashes are stored in `config/sha1/`.

## Verification

```sh
make verify
```

`make verify` builds the image and checks its checksum against retail, printing `OK: build matches retail ...` on success. A bare `make` command is blocked intentionally to prevent unverified builds from running.

| Command | Action |
| --- | --- |
| `make verify TARGET=<t>` | Build and verify image SHA-1 against retail |
| `make extract TARGET=<t>` | Split target executable with [splat] |
| `make progress` | Report current matched function counts |
| `make nonmatchings` | List functions that do not match yet |
| `make ratchets` | Audit placeholder and debt ratchets |
| `make hooks` | Install git safety hooks |
| `make clean` | Remove build artifacts |

Targets: `slps_00270`, `sces_00269`, `mainmenu_jp`, `mainmenu_eu`, `g3_jp`, `g3_eu`, `g3org_jp`, `g3org_eu`.

Extracting executables from CHD disc images:

```sh
python3 tools/chd_extract.py Galaxian3_Japan.chd japan.bin      # 2352 B/sector
python3 tools/iso9660_extract.py japan.bin out/ 'SLPS_002.70;1' ...
```

## Documentation

Track ongoing progress, rules, and technical findings in the documentation tree:

| Document | Description |
| --- | --- |
| [docs/RECON.md](docs/RECON.md) | Measured facts: disc layouts, executables, headers, and toolchain fingerprints |
| [docs/TOOLCHAIN.md](docs/TOOLCHAIN.md) | Compiler version evidence, build pipeline, and assembly quirks |
| [docs/WORKFLOW.md](docs/WORKFLOW.md) | Six-phase decompilation lifecycle |
| [docs/RULES.md](docs/RULES.md) | Hard rules for oracle integrity, toolchains, source layout, and reviews |
| [docs/GUIDELINES.md](docs/GUIDELINES.md) | Naming conventions, evidence hierarchy, and shiftability |
| [docs/MATCHING.md](docs/MATCHING.md) | Matching loop ladder, non-matching parking policy, and false matches |
| [docs/CHECKLIST.md](docs/CHECKLIST.md) | Setup checklist from disc dump to matching build |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guide: stating claims, ratchets, and definition of done |
| [AGENTS.md](AGENTS.md) | Operational rules and loop for AI agents |

## License

Source code, headers, build scripts, and configurations are licensed under the MIT License ([LICENSE](LICENSE)). Galaxian³, game assets, and the Sony Psy-Q SDK are the property of Namco and Sony.

[splat]: https://github.com/ethteck/splat
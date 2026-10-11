# References

This template collects tools and methods from four reference projects. The comparative report is in [PSX-Decompilation-Methodology-Report.pdf](PSX-Decompilation-Methodology-Report.pdf).

## Source projects

* **[tenchu-decomp]**: Tenchu: Stealth Assassins (Fuuzetsu). Byte-exact rebuild with parallel exact and shiftable build lanes. Includes a matching cookbook (`docs/matching-cookbook.md`) and AI orchestration runbook (`docs/orchestration.md`).
* **[lsddecomp]**: LSD: Dream Emulator (brian-oblivion). Completed 1,446 of 1,446 functions with full retail byte matching. Provided the hook-enforced hard rules used in `.githooks/` and `AGENTS.md`.
* **[parasite-eve-decomp]**: Parasite Eve USA (khasinski). Systematic rules covering documentation, assembly, GTE policies, and debt ratchets.
* **[rage-racer-decomp]**: Rage Racer PAL/USA/JP (khasinski). Multi-region project covering 1,200 of 1,200 functions (423,420 code bytes on PAL) with structured naming evidence.

## Toolchain

| Tool | Role |
| --- | --- |
| [splat] | Splits retail executables into assembly, data, linker scripts, and symbol lists |
| [maspsx] | Translates Sony ASPSX assembly macros for GNU as |
| [m2c] | Decompiles MIPS assembly into C code drafts |
| [asm-differ] | Compares per-function assembly with retail binary |
| [decomp-permuter] | Searches for source variations to resolve register differences |
| [objdiff] / [decomp.dev] | Tracks project progress and displays per-function status |
| [decompme/compilers] | Stores historical compiler binaries |
| [decompals/old-gcc] | Stores historical GCC builds |

[tenchu-decomp]: https://github.com/Fuuzetsu/tenchu-decomp
[lsddecomp]: https://github.com/brian-oblivion/lsddecomp
[parasite-eve-decomp]: https://github.com/khasinski/parasite-eve-decomp
[rage-racer-decomp]: https://github.com/khasinski/rage-racer-decomp
[splat]: https://github.com/ethteck/splat
[maspsx]: https://github.com/mkst/maspsx
[m2c]: https://github.com/matt-kempster/m2c
[asm-differ]: https://github.com/simonlindholm/asm-differ
[decomp-permuter]: https://github.com/simonlindholm/decomp-permuter
[objdiff]: https://github.com/encounter/objdiff
[decomp.dev]: https://decomp.dev
[decompme/compilers]: https://github.com/decompme/compilers
[decompals/old-gcc]: https://github.com/decompals/old-gcc

# References

The projects and tools this template is distilled from. All accessed
October 2026. The full comparative survey is in
[PSX-Decompilation-Methodology-Report.pdf](PSX-Decompilation-Methodology-Report.pdf)
— the narrative behind every rule in this repository.

## Source projects

* **[tenchu-decomp]** — Tenchu: Stealth Assassins (Fuuzetsu).
  Byte-exact rebuild with a dual exact/shiftability lane; the matching
  cookbook (`docs/matching-cookbook.md`) and the AI orchestration runbook
  (`docs/orchestration.md`) are the deepest process docs in the field.
* **[lsddecomp]** — LSD: Dream Emulator (brian-oblivion). Completed:
  1,446/1,446 game functions, retail byte-identical, driven end-to-end by AI
  agents in 106 rounds. Its hook-enforced hard rules are the ancestor of
  this template's `.githooks/` and `CLAUDE.md`.
* **[parasite-eve-decomp]** — Parasite Eve USA (khasinski). The most
  systematic documentation contract: CONVENTIONS, CODE_ORGANIZATION,
  ASM_AND_GTE_POLICY, debt ratchets and the claim-stating review process
  behind `CONTRIBUTING.md` here.
* **[rage-racer-decomp]** — Rage Racer PAL/USA/JP (khasinski). Completion
  scale across regions: 1,200/1,200 functions, 423,420 code bytes on PAL,
  with the cleanest naming-evidence discipline.

## Toolchain

| Tool | Role |
| --- | --- |
| [splat] | splits the retail executable into per-function asm, data, linker script and symbol lists |
| [maspsx] | MIPS assembler translation layer reproducing Sony's ASPSX behaviour |
| [m2c] | MIPS assembly to C decompiler (first drafts) |
| [asm-differ] | per-function byte diffs against retail during iteration |
| [decomp-permuter] | automated source-shaping search for residual register-allocation ties (bounded runs, last resort) |
| [objdiff] / [decomp.dev] | whole-tree progress reports, badges and per-function status |
| [decompme/compilers] | prebuilt historical compiler collection |
| [decompals/old-gcc] | prebuilt old GCC toolchains |

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

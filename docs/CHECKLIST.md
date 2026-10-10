# Starter Checklist

Ten steps from "I have a disc" to a running matching decompilation —
compressing the [workflow](WORKFLOW.md), [rules](RULES.md) and
[guidelines](GUIDELINES.md) into the order the four source projects actually
followed. Tool names in parentheses are the community defaults.

- [ ] **1. Pick one retail revision** and record its executable name, SHA-1
      and entry point. Every address in every config is wrong for any other
      revision. (Put the executable in `baselines/`, hash in
      `config/sha1/<target>.sha1`, `git commit --no-verify` for that one
      setup commit.)

- [ ] **2. Confirm the source-only policy.** Disc dump, SDK files and all
      generated output stay git-ignored; document what contributors must
      supply. (This template ships the `.gitignore`, hook and licence scope
      note — adapt names, keep the posture.)

- [ ] **3. Identify the original compiler and Psy-Q library versions** and
      pin them exactly — old GCC cc1 plus [maspsx] and binutils. Prebuilt
      compilers exist in [decompme/compilers] and [decompals/old-gcc].

- [ ] **4. Configure splat and split the executable.** Commit the config and
      symbol lists, and the generated `asm/`; never the binary.

- [ ] **5. Prove the disassemble-to-reassemble round trip is byte-identical
      before writing any C.** Do not proceed until this gate is green. This
      is the foundation of the whole project.

- [ ] **6. Install the verification gate**: `make verify` (build + compare
      the whole image with retail) as the only build entrance, plus
      `make hooks` so the bypass routes are blocked.

- [ ] **7. Adopt the loop** (docs/MATCHING.md): pick easy targets with
      matched twins first, map a subsystem's structs before its functions,
      iterate length-first, park honest NON_MATCHING stubs.

- [ ] **8. Write the rules file early** — oracle, toolchain, source, process
      — and keep it short; move measurements into tools and lessons into
      commit messages. (`CLAUDE.md` and `docs/RULES.md` are the starting
      corpus, distilled from all four projects.)

- [ ] **9. Set up CI** that rebuilds, verifies the SHA-1 and publishes an
      objdiff report ([objdiff], [decomp.dev]); add debt ratchets the day
      the first placeholder name is introduced. (`.github/workflows/ci.yml`
      and `config/ratchets.json` are the skeleton.)

- [ ] **10. Plan the cleanup phase from the start.** Naming evidence, typed
      structures, subsystem organisation and shiftability are what turn a
      matched binary into a finished, readable reconstruction. Matched is
      not finished.

[maspsx]: https://github.com/mkst/maspsx
[decompme/compilers]: https://github.com/decompme/compilers
[decompals/old-gcc]: https://github.com/decompals/old-gcc
[objdiff]: https://github.com/encounter/objdiff
[decomp.dev]: https://decomp.dev

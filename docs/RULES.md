# Hard rules

Past errors established each rule in this document. Rules differ from guidelines by how the project enforces them. Tools, hooks, and build scripts enforce hard rules. Reviewers and ratchets enforce guidelines.

## 1. Oracle integrity

The build validates all results. Hash files stay immutable. Verification scripts provide the only build entrance. Diff outputs do not replace the full-image checksum.

1. **Never edit `config/sha1/**`.** These files contain retail SHA-1 hashes. Editing a hash file invalidates the oracle. Git hooks block edits (`make hooks`).
2. **Run all builds through `make verify`.** A bare `make` command does not verify output bytes. The default target blocks bare builds.
3. **Rebuild clean after structural changes.** Run `make clean verify` after you edit shared headers, the Makefile, manifests, or translation boundaries.
4. **Do not trust intermediate diff scores.** Stale object files, left-over `INCLUDE_ASM` stubs, and shifted addresses can show false matches. Only the final image validates a result (`docs/MATCHING.md` §5).

## 2. Toolchain rules

The original compiler output determines target bytes.

1. **Pin exact toolchain versions.** Keep compiler binaries, binutils, flags, and maspsx fixed.
2. **Use the attested effective toolchain for final builds.** The current byte-exact pipeline requires the specifically guarded GCC 2.6.3 build (guards 1–4), the pinned upstream maspsx revision with the committed delay-slot patch, and marker-gated `cc_post` rules. These are documented **project exceptions** to the historical stock-tool preference, not permission to add arbitrary patches. A full-image build must pass `tools/toolchain_preflight.py` and the retail SHA-1 oracle (`docs/TOOLCHAIN.md`, `docs/CI.md`).
3. **Declare per-file compiler options in file markers only.** Do not create ad-hoc build rules. Keep the build contract uniform so linker tools function correctly.
4. **Report toolchain problems directly.** Provide a minimal reproducer. Explore compiler variants in isolated standalone probes; do not use an experimental or un-attested toolchain for a claimed whole-image match.
5. **Keep unmatched code as assembly subsegments.** Do not patch the assembler wrapper to force a match from non-matching C.

## 3. Source and assembly rules

The original compiler requires strict historical standards.

| Rule | Reason | Enforcement |
| --- | --- | --- |
| Never edit generated disassembly (`asm/`) | Splat regenerates assembly. Edits get overwritten and invalidate tracking. | Git hook |
| Keep functions in ROM-address order | GCC emits code in source order. Reordering shifts later addresses. | Review; verify target |
| Use C89 syntax: declarations at block top, `/* */` comments | Historical compilers require C89. Modern syntax alters code generation. | Review |
| Define rodata strings once by name | Duplicate string literals emit multiple instances and shift image offsets. | Review; verify target |
| Do not introduce new register pinning or extended asm without an evidence-backed exception | These constructs obscure semantics and count as debt even when the image matches. | Review, documented exception, full-image verify |
| Restrict inline assembly to evidenced macros (GTE/COP2) | Non-standard instructions have no C form. Document each use. | Review |
| Reference code and data by symbol name | Fixed addresses break shiftability. Use macros for hardware registers and scratchpad memory. | Shift audit; review |
| Curate names in `config/symbols.curated.txt`; never hand-edit `asm/` or a yaml subsegment | The scanner rewrites the per-target symbols file and splat takes each output file's name from the yaml subsegment, which `tools/build.sh` then parses for the section address. | Review; `make extract` + `make verify` |
| Update structures globally | Changing a field without updating adjacent padding shifts offsets across files. | Clean rebuild |
| Mark matching anomalies with `/* MATCHING: */` | Prevents subsequent refactors from breaking matching output. | Review |

**Existing exceptions are not blanket approval.** Register-bound variables and inline-asm-heavy units already exist (for example, `src/MulMatrix.c` and `src/func_8002C478.c`). Retain them when necessary to preserve byte matching, classify them as hybrid/asm-backed rather than clean semantic C, and document why their exact instruction choices matter. A new such exception requires explicit review, narrowly bounded scope and full-image proof. Whole-function inline assembly is *assembly-preserved*, not a semantic-C decompilation result. Use generated `INCLUDE_ASM` stubs for unmatched routines.

## 4. Process and review rules

1. **Commit only on green builds.** Commit changes only after full-image verification succeeds. Do not commit broken trees.
2. **Keep experimental code out of the tracked tree.** Add C files to `src/` only when wired into the active build configuration.
3. **State the claim for each change.** Declare whether a patch asserts a *binary match*, *semantic recovery*, *typing*, *naming*, or *organization* (CONTRIBUTING.md).
4. **Keep ratchets synchronized with the tree.** Lower debt baselines as you fix issues. Raising a baseline requires explicit review.
5. **Store project knowledge in the repository.** Put architectural decisions and lessons in `docs/` with evidence. Track measurements with tools (`make progress`, `make ratchets`), not in prose.

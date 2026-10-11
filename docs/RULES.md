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
2. **Use stock tools for final builds.** Do not apply local patches, custom compilers, or post-build rewrite scripts.
3. **Declare per-file compiler options in file markers only.** Do not create ad-hoc build rules. Keep the build contract uniform so linker tools function correctly.
4. **Report toolchain problems directly.** Provide a minimal reproducer to the maintainer. Do not experiment on pinned tools.
5. **Keep unmatched code as assembly subsegments.** Do not patch the assembler wrapper to force a match from non-matching C.

## 3. Source and assembly rules

The original compiler requires strict historical standards.

| Rule | Reason | Enforcement |
| --- | --- | --- |
| Never edit generated disassembly (`asm/`) | Splat regenerates assembly. Edits get overwritten and invalidate tracking. | Git hook |
| Keep functions in ROM-address order | GCC emits code in source order. Reordering shifts later addresses. | Review; verify target |
| Use C89 syntax: declarations at block top, `/* */` comments | Historical compilers require C89. Modern syntax alters code generation. | Review |
| Define rodata strings once by name | Duplicate string literals emit multiple instances and shift image offsets. | Review; verify target |
| Do not use register pinning or extended asm | They hide program logic and add debt. | Ratchet (`make ratchets`) |
| Restrict inline assembly to evidenced macros (GTE/COP2) | Non-standard instructions have no C form. Document each use. | Review |
| Reference code and data by symbol name | Fixed addresses break shiftability. Use macros for hardware registers and scratchpad memory. | Shift audit; review |
| Curate names in `config/symbols.curated.txt`; never hand-edit `asm/` or a yaml subsegment | The scanner rewrites the per-target symbols file and splat takes each output file's name from the yaml subsegment, which `tools/build.sh` then parses for the section address. | Review; `make extract` + `make verify` |
| Update structures globally | Changing a field without updating adjacent padding shifts offsets across files. | Clean rebuild |
| Mark matching anomalies with `/* MATCHING: */` | Prevents subsequent refactors from breaking matching output. | Review |

Register pinning is debt. Use it only when it reproduces original register allocator choices while control flow stays in C. Whole-function inline assembly is not a decompilation result. Use generated `INCLUDE_ASM` stubs for unmatched routines.

## 4. Process and review rules

1. **Commit only on green builds.** Commit changes only after full-image verification succeeds. Do not commit broken trees.
2. **Keep experimental code out of the tracked tree.** Add C files to `src/` only when wired into the active build configuration.
3. **State the claim for each change.** Declare whether a patch asserts a *binary match*, *semantic recovery*, *typing*, *naming*, or *organization* (CONTRIBUTING.md).
4. **Keep ratchets synchronized with the tree.** Lower debt baselines as you fix issues. Raising a baseline requires explicit review.
5. **Store project knowledge in the repository.** Put architectural decisions and lessons in `docs/` with evidence. Track measurements with tools (`make progress`, `make ratchets`), not in prose.
6. **Commit under the agent identity, never the owner's.** Agent commits carry `Super Z <41898282+github-actions[bot]@users.noreply.github.com>`. The global git config holds the owner's personal identity, so an agent session that runs a plain `git commit` attributes the work to the owner. Commit through `tools/agent_git.sh`, which forces the agent identity. The pre-commit hook rejects the owner's identity in any session that carries a ZCode marker; a commit from the owner's own terminal is unaffected and records the owner, who can also opt in from inside a session with `ALLOW_OWNER_IDENT=1`.

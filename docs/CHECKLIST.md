# Starter checklist

Follow these ten steps to set up a matching decompilation project. The sequence reflects the workflow of the reference projects. Tool names in parentheses are community defaults.

- [ ] **1. Select one retail revision.** Record its executable name, SHA-1, and entry point. Addresses in configuration files do not match other revisions. Put the executable in `baselines/`. Write the hash to `config/sha1/<target>.sha1`. Use `git commit --no-verify` for this setup commit.

- [ ] **2. Enforce the source-only policy.** Keep disc dumps, SDK files, and generated files out of git. Document all files that contributors must supply. This repository supplies `.gitignore`, hook scripts, and license notes.

- [ ] **3. Identify original compiler and Psy-Q versions.** Pin the tools to exact versions. Use the GCC cc1 binary, [maspsx], and binutils. Find prebuilt compilers in [decompme/compilers] and [decompals/old-gcc].

- [ ] **4. Configure splat and split the executable.** Commit configuration files, symbol lists, and generated `asm/` files. Do not commit binary files.

- [ ] **5. Assemble the disassembly back into a binary.** Make sure the reassembled binary matches the retail binary byte for byte. Do not write C code before this check passes.

- [ ] **6. Add the verification gate.** Use `make verify` as the only build entrance. Run `make hooks` to block bypass paths.

- [ ] **7. Follow the matching loop.** Start with small functions that have matched twins. Map subsystem structures before you write function code. Match instruction count first. Record difficult functions with honest NON_MATCHING stubs.

- [ ] **8. Write the rules file early.** Document the oracle, toolchain, source policy, and process. Keep the file short. Record measurements with tools. Record lessons in commit messages.

- [ ] **9. Set up CI.** Configure CI to rebuild, check the SHA-1, and publish an objdiff report. Add debt ratchets when you add the first placeholder name.

- [ ] **10. Plan the cleanup phase.** Collect naming evidence. Create typed structures. Organize code by subsystem. Make the code shiftable. A matching build is only the start of the project.

[maspsx]: https://github.com/mkst/maspsx
[decompme/compilers]: https://github.com/decompme/compilers
[decompals/old-gcc]: https://github.com/decompals/old-gcc
[objdiff]: https://github.com/encounter/objdiff
[decomp.dev]: https://decomp.dev

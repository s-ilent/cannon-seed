# The matching loop

This document describes Phase 3 of the workflow (WORKFLOW.md). It summarizes matching practices from the reference projects.

## 1. Target selection

Use automated tools to select targets:

* Start with small functions with clear boundaries. Early matches validate the setup.
* Map shared subsystem structures before writing functions. Functions with unmapped structures take more time to match.
* Select functions with matched twin functions. Similar source code creates similar assembly output.
* Find recognizable assembly patterns such as dispatch tables, fixed loops, or structure copies.

## 2. Seeding the draft

Generate initial C drafts with Ghidra and [m2c]. Then adjust the code manually. Match the code against known idioms for the pinned compiler.

## 3. The iteration ladder

Fix differences in this order:

| Order | Priority | Reason |
| --- | --- | --- |
| 1 | Length: exact instruction count | Different counts show broken structure. Fix loop layout, dispatch forms, and temporary variables first. |
| 2 | Wrong, missing, or reordered instructions | Map differences to known compiler idioms. Inspect matched sibling functions for examples. |
| 3 | Register differences | Adjust statement order and temporary variables to fix register allocation. |
| 4 | Known compiler rules | Run rule tools on compiling code. Novel compiler behavior is rare. |
| 5 | Bounded permuter run | Use the permuter only for small register differences in right-length code. |
| 6 | Park non-matching code | Store residual mismatches under NON_MATCHING stubs. Do not spend excessive time on minor register differences. |

### 3a. Seeding the permuter: registers are not free

The permuter's MIPS scorer keeps `$a1` and `$v0` distinct. `$zero` and `$sp` are
normalized away, but the general-purpose registers are compared literally, so a
candidate that never materializes the retail register cannot be repaired by
mutation: no amount of statement shuffling changes which register the allocator
picks, because the base C already fixed that choice.

This bites in a common shape — a function whose retail body stores a parameter
through `$v0`. If the base C takes that value as an ordinary parameter, GCC 2.6.3
keeps it in the argument register (`$a1`) and every candidate scores a register
mismatch no matter how good its statement order is. Two idioms move the value
into `$v0`:

* an explicit `return` of the value, which copies it at entry — but that copy
  costs an instruction the retail body may not contain; or
* a local assigned *after* its uses, which lets the allocator settle on `$v0`
  without emitting a copy.

Establish which register the retail code uses before seeding. A base whose
disassembly already shows the right register and merely the wrong order
converges in minutes; a base with the wrong register plateaus.

`tools/permuter/` holds the project template and a runner — see
`tools/permuter/README.md`.

## 4. Parking: NON_MATCHING is a state, not a defeat

Some compiler patterns resist matching from C source. Put readable near-matches in `#ifdef NON_MATCHING` blocks. Put the `INCLUDE_ASM` stub in the `#else` block. The linked binary stays byte-identical. The source tracks progress clearly. Record attempted approaches in the header comment of the function.

## 5. How a score lies

Verify these failure modes before you trust a score:

* **Stale builds**: A failed build can leave an old binary in place. When in doubt, rebuild from clean.
* **Active `INCLUDE_ASM` stubs**: A stub compares retail bytes to retail bytes. Verify that the function compiles from real C code.
* **Address drift**: A length change in one function shifts all subsequent code. Check whether neighboring functions changed offset.
* **Incomplete merges**: Merge conflicts can stop compilation. Make sure git reports no active merge.
* **Skipped units**: Make can skip an object if a header error occurred earlier. Delete the target object and rebuild to verify.
* **Host-only code**: Code inside `#ifdef HOST_BUILD` does not run in the PS1 build.

If a build fails without compiler errors, locate the change with `cmp -l`. Convert the first differing byte offset to a VRAM address with `tools/verify.sh`.

## 6. Acceptance

The full-image checksum (`make verify`) is the only gate that confirms success. Diff tools ([asm-differ], `decomp.me`) help iteration. The linked SHA-1 is the final check.

[m2c]: https://github.com/matt-kempster/m2c
[asm-differ]: https://github.com/simonlindholm/asm-differ
[decomp-permuter]: https://github.com/simonlindholm/decomp-permuter

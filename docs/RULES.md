# Hard Rules

Every rule here was paid for: each exists because someone — or some agent —
broke it and the build or the tree suffered. Rules are separated from
[guidelines](GUIDELINES.md) by enforcement: a rule violation blocks a change
mechanically (hook, CI, or build failure); a guideline is applied by review
and ratchet.

## 1. Oracle integrity

> **The oracle is not negotiable.** Every claimed result is checked by the
> build, not by the author of the claim. Hash files are immutable, verify
> scripts are the only build entrance, and a green per-function diff never
> substitutes for the whole-image checksum.

1. **Never edit `config/sha1/**`.** The files hold the retail SHA-1.
   Changing one to make a build pass deletes the oracle. A git hook blocks
   it (`make hooks`).
2. **Every build goes through `make verify`.** A bare `make` says nothing
   about whether the bytes are right — and this repo's default target
   refuses to run for exactly that reason.
3. **Structural changes get a clean rebuild.** Shared headers, the compiler
   wrapper, the Makefile, manifests and translation-unit boundaries must
   pass `make clean verify`. Header dependencies protect incremental builds,
   but they do not replace a clean acceptance check.
4. **A score can lie.** Stale builds, leftover `INCLUDE_ASM` stubs and
   address drift have all made diffs look greener than they are. Only the
   linked image promotes a result. (`docs/MATCHING.md` §3 catalogues the
   known ways.)

## 2. Toolchain rules

The compiler is part of the retail bytes, not a knob to turn.

1. **The toolchain is pinned to exact revisions** — compiler, binutils,
   flags and maspsx. Byte matching is only possible against the exact
   original toolchain.
2. **Final builds use unmodified stock tools.** No local patches, no
   diagnostic compiler builds, no post-build rewrite passes, no build hacks.
3. **Per-file compiler options are stock flags declared in file markers
   only.** No per-source variants of the build contract: fixed layout and
   allocator policy have one authority so the linker tools can consume it.
4. **Suspected toolchain faults are reported, never experimented on.** A
   minimal reproducer goes to the operator; the pinned tools are not a
   playground.
5. **If stock C with allowed constraints does not match, the function stays
   an assembly subsegment** until its source reconstruction is corrected.
   Extending the assembler wrapper is not an acceptable matching technique.

## 3. Source and assembly rules

The original compiler re-runs on modern hardware and is intolerant of style.

| Rule | Rationale | Enforced by |
| --- | --- | --- |
| Never edit generated disassembly (`asm/`) | splat regenerates it; manual edits are silently overwritten and corrupt the oracle | git hook |
| Functions stay in ROM-address order within a file | GCC emits sections in source order; an out-of-order function shifts later bytes you didn't touch | review; the build fails the oracle |
| C89 discipline: declarations at block top, `/* */` comments only | the original compilers require it; later syntax changes code generation | review |
| A rodata string is defined once, by name | a literal written at a use emits a second copy and shifts the image | review; build |
| No register pins or extended-asm operands as matching shortcuts | they encode no recovered logic and hide real understanding; tracked as crutch debt | ratchet (`make ratchets`) |
| Inline assembly only via evidenced macros (GTE/COP2, proven-asm functions) | COP2 has no C spelling; everything else has one and must use it; every use listed in an evidence file | review |
| No program addresses in C; refer by symbol | fixed addresses break shiftability and hide layout knowledge (exceptions: hardware registers, scratchpad, loader contract — each behind a named macro) | shift audit / review |
| Renames go through rename tools, never by hand | tools update every reference and re-verify; hand edits miss sites | review |
| A struct edit is never local | an inserted field without shrinking adjacent padding moves every later offset, breaking functions in other files | clean rebuild |
| An odd spelling that exists to match gets one `MATCHING:` comment | future readers (human or agent) must not "fix" it | review |

Register pins deserve the full statement, since every project arrived at it
independently: they are debt, not tools. Allowed only when they reproduce the
original allocator's result while control flow stays in C; counted by the
debt ratchet; and removed after matching whenever the match survives without
them. Whole-function assembly is never a decompilation result — a generated
`INCLUDE_ASM` stub remains the correct representation of an unmatched
function, and inline instructions appear only through evidenced macros for
operations with no C spelling or for routines proven to have been assembly
originally.

## 4. Process and review rules

1. **Commit only on green.** A change is harvested only after a whole-image
   clean rebuild passes. Never commit a red tree, even to "save work".
2. **Keep experiments out of the tracked tree.** A C file enters `src/` only
   together with the config entry that wires its range in, so a fresh clone
   can never diverge from CI.
3. **State your claim.** Every change declares which of these it asserts:
   *binary match*, *semantic recovery*, *typing*, *naming*, or
   *organization* — because the byte check validates only the first
   (see CONTRIBUTING.md).
4. **Ratchets must equal the current tree.** A debt baseline that no longer
   matches reality is a bug; an improvement that leaves a stale higher
   baseline behind is rejected, so cleanups cannot be silently spent later.
   Raising a baseline is a policy change needing explicit review.
5. **Knowledge lives in the repository, not in private memory.** Durable
   lessons go into `docs/` with their evidence attached; measurements stay
   in tools (`make progress`, `make ratchets`), never in prose — a number
   written in a document is right for one session and wrong for every one
   after.

# The Matching Loop

The iteration detail behind Phase 3 of the [workflow](WORKFLOW.md),
synthesised from tenchu-decomp's matching cookbook and the rule files of the
other three projects. Every rule here is a hypothesis that has been paid for
at least once.

## 1. Target selection

Selection is a tool job, not a taste job. Tenchu's `triage` script rates
every unmatched function by difficulty and names the nearest already-matched
twins. The working heuristics:

* **Small, clean-seam functions first** — early wins validate the pipeline.
* **Map a subsystem's shared structs once** and whole families of functions
  become cheap; a function whose struct is unmapped is expensive.
* **Prefer functions with matched twins** — compilers are predictable, so
  similar source produces similar asm, and a sibling's idioms transfer.
* Look for known idiom families in the asm (dispatch tables, fixed-size
  loops, struct copy/clone shapes) — each maps to a C spelling you already
  know.

## 2. Seeding the draft

Seed mechanically, then shape by hand. The community default is Ghidra's
decompiler plus [m2c] for the first-draft C; Tenchu's pipeline generates the
draft and the matching context automatically. The draft is then shaped
against the compiler's *known idioms* — the cookbook records which source
spelling produces which asm pattern for the pinned compiler.

## 3. The iteration ladder

Fix diffs in this order. Fixing in the wrong order wastes enormous effort.

| Order | Fix first | Why |
| --- | --- | --- |
| 1 | Length — instruction count must match exactly | a different count means the structure (dispatch, loops, temps) is wrong; everything else is noise until length agrees |
| 2 | Wrong, missing or reordered instructions | map each difference to a known compiler idiom family; read the nearest matched siblings first |
| 3 | Register-only differences | usually fall out of steps 1–2; steer with statement order and temps before anything heavier |
| 4 | Mechanical rules via tools | run the rule sweeper on any compiling draft; if no known rule wins, the residual is something new |
| 5 | One bounded permuter run | only for right-length, small residuals; never as a decompiler, and never for GTE macro functions |
| 6 | Park it honestly | sub-C residuals are recorded NON_MATCHING with a status header instead of burning days |

## 4. Parking: NON_MATCHING is a state, not a defeat

Some residuals are below the obvious C level — the compiler did something no
plausible source spells. A close draft that resists matching is preserved
behind `#ifdef NON_MATCHING` with an `INCLUDE_ASM` fallback in its `#else`,
so the image stays byte-identical while the honest state of the function is
visible in the source. Parked functions keep a status header recording what
was tried. This is how the tree stays publishable while knowledge accumulates.

## 5. How a score lies

From lsddecomp's hard-won catalogue. Check these before believing any
per-function report:

* **Stale build** — a failed compile or link leaves the old image, and its
  score is plausible. Check mtimes; when in doubt, rebuild.
* **Still `INCLUDE_ASM`** — a stub compares retail with retail and reports a
  full match. Verify the function is really C.
* **Address drift** — C of a different length shifts everything after it, so
  later functions "differ" through no fault of their own. Watch for
  out-of-range differing bytes, and check no sibling lost its wrapper.
* **Half-finished merge** — a unit with conflict markers may not rebuild, so
  the build reads green against the old object. Check for `MERGE_HEAD`.
* **Skipped unit** — after a header edit breaks a unit once, the pipeline
  can leave a stale object that `make` then skips. A red build with no
  compile error means delete that unit's object and rebuild.
* **Host-only code** — `#ifdef HOST_BUILD` branches never reach the PS1
  build; a green hash says nothing about them.

To localise a red build with no compile error, diff the image against the
baseline (`cmp -l`) and translate the first differing file offset to a VRAM
address, then grep your linker map — `tools/verify.sh` prints the recipe for
the PS-X EXE layout.

## 6. Acceptance

The loop closes with the whole-image checksum — `make verify` — and nothing
else promotes work. Per-function diff tools ([asm-differ], `funcdiff`
helpers, decomp.me scores) are for *iteration*; [decomp-permuter] gets one
bounded run for residual register-allocation ties; the linked SHA-1 is the
verdict.

[m2c]: https://github.com/matt-kempster/m2c
[asm-differ]: https://github.com/simonlindholm/asm-differ
[decomp-permuter]: https://github.com/simonlindholm/decomp-permuter

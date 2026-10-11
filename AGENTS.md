# Galaxian^3 (PSX): matching decompilation

This project builds C source that compiles byte for byte to the retail executables in `config/sha1/`. Read README.md for setup instructions and layout.

Keep this file short. Focus on rules and the loop. Do not write project state or progress numbers here. Check state with `python3 tools/progress.py` and `python3 tools/check_ratchets.py`. Full conventions live in `docs/RULES.md`, `docs/GUIDELINES.md`, and `docs/MATCHING.md`.

## Hard rules

1. **Never edit `config/sha1/**`.** These files contain retail SHA-1 hashes. Editing a hash file invalidates the oracle. Git hooks block edits.
2. **Run all builds through `make verify`.** A bare `make` command does not check byte matching and is blocked. Permitted non-build targets: `extract`, `progress`, `nonmatchings`, `ratchets`, `hooks`, `clean`.
3. **Never commit game executables, disc images, or Sony files.** Keep `disk/`, `sdk/`, `lib/`, `include/psyq/`, `assets/`, and `baselines/` in `.gitignore`. Users supply these files locally.
4. **Never edit `asm/`.** Splat regenerates assembly files. Curate symbol names in `config/symbols.curated.txt` — the scanner rewrites the per-target symbols files, so only a curated name survives. Update segmentation in `config/splat.*.yaml`.
5. **Keep the toolchain pinned.** Use the exact compiler version, binutils, flags, and maspsx. Current baseline: Psy-Q GCC 2.6.3 (SDK strings dated 1995-10).
6. **No register pinning.** Do not use `register T v asm("$N")` or extended asm constraints to force register choices. Use `__asm__("")` only as a scheduling barrier. Place direct COP2/GTE assembly instructions in approved macro headers.

## Sandbox re-provision recovery

If the sandbox resets, restore configuration with this command:

```sh
sh tools/rehydrate.sh        # add --smoke for a full oracle check
```

This script restores git configuration, credentials, the virtual environment (`tools/make_wheelhouse.sh`), maspsx, and mipsel binutils. If the tree lags origin, run `git fetch origin && git reset --hard origin/main`. Push completed work regularly.

## The loop

1. Edit code in `src/` or `include/`. Keep functions in ROM-address order. Use C89 syntax (`/* */` comments, declarations at block tops). The target compiler treats `char` as unsigned; use `s8` for signed bytes.
2. Verify against the retail target:

   ```sh
   make verify TARGET=<t>   # t in slps_00270 sces_00269 mainmenu_jp
                            #    mainmenu_eu g3_jp g3_eu g3org_jp g3org_eu
   ```

   If the build fails without a compiler error, isolate differences:
   `cmp -l build/<target>.bin baselines/<target>.bin | head`
   Convert the byte offset to a VRAM address per instructions in `tools/verify.sh`. Verify each target touched.
3. Check progress and ratchets: `make progress`, `make ratchets`. Rename symbols by curating them in `config/symbols.curated.txt`, not by search and replace across the tree — `asm/` is regenerated and the per-target symbols file is rewritten by the scanner, so only a curated name survives (see "Naming what you find").
4. Non-matching C code must not remain active. Put near-matches in `#ifdef NON_MATCHING` with the `INCLUDE_ASM` stub in the `#else` block. Mark matching quirks with a `/* MATCHING: */` comment.

## Naming what you find

Names are recovered, not guessed, and they are authored in one place:
`config/symbols.curated.txt`, one line per name under a `// target: <name>`
header. `tools/scan_functions.py` reads it and writes the real
`config/symbols.<target>.txt`, so a curated name survives every re-scan
instead of reverting to `func_XXXXXXXX`. There is no rename command to run:
edit the curated file, then `make extract` and `make verify` the target.

* **PSY-Q library veneers** — a three-instruction body (`addiu $t2,$zero,0xA0|0xB0`, `jr $t2`, `addiu $t1,$zero,<index>`). SDK assembly the original build linked in; match as `INCLUDE_ASM`, never from C. `tools/sdk_symbols.py --libs <psyq lib dir>` reports every one with its SDK member; `docs/MATCHING.md` §3b has the SDK setup.
* **GTE and hand-written routines** — leave the assembly; curate a name when the evidence is clear.

Curate into `config/symbols.curated.txt`, never straight into
`config/symbols.<target>.txt` (the scanner overwrites it) and never into a
yaml subsegment (`tools/build.sh` reads each section's address out of the
file name, so a renamed subsegment breaks the link).

## How a score lies

Watch for stale objects, inactive `INCLUDE_ASM` stubs, address shifts, and unmerged files (`docs/MATCHING.md` §5). Code is accepted only when `make verify` produces a matching SHA-1.

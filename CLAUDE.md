# Galaxian^3 (PSX) — matching decompilation

C source that compiles byte-for-byte to the retail executables recorded in
`config/sha1/` (eight targets across two regions — see docs/RECON.md).
README.md covers the layout and the build; read it first.

**Keep this file short.** It holds rules and the loop, never project state,
counts or history. A number written here is right for one session and wrong
for every one after. Measure instead (`python3 tools/progress.py`,
`python3 tools/check_ratchets.py`). Lessons go in commit messages. The full
methodology lives in `docs/RULES.md`, `docs/GUIDELINES.md` and
`docs/MATCHING.md`.

## Hard rules

1. **Never edit `config/sha1/**`.** They hold the retail SHA-1. Changing one
   to make a build pass deletes the oracle. A hook blocks it.
2. **Every build goes through `make verify`.** A bare `make` says nothing
   about whether the bytes are right — and is blocked accordingly (allowed
   non-producing targets: `extract`, `progress`, `nonmatchings`,
   `ratchets`, `hooks`, `clean`).
3. **Never commit the executable, a disc image, or anything of Sony's.**
   `disk/`, `sdk/`, `lib/`, `include/psyq/`, `assets/` and `baselines/` are
   gitignored and read from the user's own files. A hook blocks it.
4. **Never edit `asm/`.** splat regenerates it. Rename symbols in
   `config/symbols.*.txt` (through a rename tool, never by hand) and change
   segmentation in `config/splat.*.yaml`. A hook blocks edits.
5. **The toolchain is pinned** (exact original compiler revision, binutils,
   flags, maspsx). A suspected toolchain problem is reported to the
   operator with a minimal reproducer, never experimented on. Current
   hypothesis: Psy-Q GCC 2.6.3 (SDK strings date to 1995-10) — hypothesis,
   not measurement, until the idiom pass pins it.
6. **No register pinning.** `register T v asm("$N")` and extended-asm
   operand constraints are banned as a way to fix which register holds a
   value. A bare `__asm__("")` barrier (order only) is allowed. The one
   exception is an instruction with no C spelling and no evidenced macro
   (COP2/GTE layer), and those constraints live in the sanctioned macro
   header.

## The loop

1. Edit `src/` or `include/`. Functions within a file stay in ROM-address
   order. C89 only (`/* */` comments, declarations at block top). `char`
   is unsigned on the original compilers, so a signed byte is `s8`.
2. Verify — only through the oracle gate, one target at a time:

   ```sh
   make verify TARGET=<t>   # t in slps_00270 sces_00269 mainmenu_jp
                            #    mainmenu_eu g3_jp g3_eu g3org_jp g3org_eu
   ```

   It builds and compares the whole image with retail. A red build with no
   compile error means the image differs; localise with
   `cmp -l build/<target>.bin baselines/<target>.bin | head` and translate
   the offset to a VRAM address (recipe in `tools/verify.sh`). The
   main-executable checksum does not verify the other targets; verify each
   target you touch.
3. Measure, don't transcribe: `make progress`, `make ratchets`. Renames go
   through a rename tool that updates every reference, never by hand.
4. Code that doesn't match never stays live. A readable near-miss goes in
   `#ifdef NON_MATCHING` with the `INCLUDE_ASM` in its `#else`. An odd
   spelling kept for matching gets one `MATCHING:` comment in the `.c`.

## How a score lies

Stale builds, leftover `INCLUDE_ASM` stubs, address drift, half-finished
merges, skipped units, host-only code — the catalogue lives in
`docs/MATCHING.md` §5. A per-function score never promotes work; only the
linked-image SHA-1 does.

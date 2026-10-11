# TASKS

Queued work for this repository, newest on top, with a record of what was done
below. Queued tasks are written for whoever picks them up next — usually the
sandbox agent, which is where the build toolchain lives.

## Queued

*(empty — the carve-pin application below landed as d683dc9; next queue items
live in the sandbox agent's shared worklog)*

## Log

**2026-10-12 — carve-type pins applied (d683dc9).**
- The queued `docs/carve-pin.patch` landed: 37 DATA-verdict rows re-typed to
  `pinned` data across the eight splat maps, `preserved_types()` taught to
  preserve them. The patch file stays for reference.
- Two round-trip gaps in `tools/scan_functions.py` had to close before the
  pins held; both are now regression-tested by the pin's own acceptance check
  (`code_data_screen --all` after every re-scan):
  1. *marker loss* — the generated-block writer never re-emitted the
     `pinned` comment, so the next scan read an unmarked data row and
     re-typed the range back to code. `preserved_types()` now returns the
     pinned set and the writer re-emits the marker; double scans are
     idempotent on all 8 targets.
  2. *pin-span enforcement* — `hard_stops` only blocked seeds AT the pinned
     start; a j-target strictly inside the span seeded a walk that swallowed
     the pin (witnessed: g3_eu `func_80022A1C` out of pinned
     `data_80022A18`). Pins are now no-walk zones: `walk()` refuses in-pin
     starts and stops before pin words; the v2/v4/v3 seed loops skip pin
     interiors.
- The no-walk rule exposed a third gap: kept rows fully inside a data gap
  were swallowed by the gap (mainmenu_jp `data_800253C4`). `main()` carves
  kept gap rows out as their own subsegment pieces now.
- Post-apply: all 8 targets `make verify` exit 0; stale pseudo-function rows
  removed via `clean_stale_asm.py`; re-audit = 0 DATA / 25 SUSPECT (25 is the
  documented human-call set); ratchets 317/12 and matched C count 80
  unchanged.

**2026-10-12 — static carve auditing.**
- `tools/code_data_screen.py` — flags code subsegments whose bytes are data. 37
  across the eight targets; calibrated against the known `0x80021800` =
  `CD_cachefile`.
- `tools/crossbuild_align.py` — aligns a JP/EU pair by unique-k-mer anchors plus
  LIS. Inside aligned regions the two sides are 88–93% byte-identical, against
  16–24% at fixed offset. Reports that ~35–44% of mappable boundaries disagree
  on code-vs-data.
- `tools/struct_infer.py` — clusters memory accesses into field maps with
  signedness (`lb`/`lbu`, `lh`/`lhu`); drops runs of identical non-nop words,
  which are data misdecoded as code.
- `tools/crossbuild_diff.py` — kept as a weak reference; its docstring records
  why fixed-offset byte-identity cannot validate boundaries here.
- `docs/TOOLCHAIN.md` — compiler-fingerprint table re-measured; the counts had
  drifted after the stale-asm cleanup.
- `docs/RUNTIME.md` — the PCSX-Redux runtime harness, plus its measured limits:
  exact-address Exec breakpoints fire, range breakpoints and watchpoints do not,
  the exe entry is not caught, and the GDB stub shares the same breakpoint
  store. It is not a carve oracle.

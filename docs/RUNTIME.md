# RUNTIME: emulator evidence for the split

Static analysis infers function boundaries. `tools/fragment_report.py`
classifies every prologue-less subsegment (ORPHAN / REF'D / SHARED-TAIL /
PTR-CALLED) from branch and pointer references, and `tools/prologue_hunt.py`
guesses where a prologue hides inside a data blob. Those are inferences. This
harness replaces them, where it can, with what the CPU actually executed.

It answers three questions per subsegment: was it reached at all, was it
entered through an indirect dispatch, and does the static class survive. An
`ORPHAN` the CPU reaches is refuted — the static scan missed an edge, often an
undiscovered jump table.

Coverage is only as good as the run. **"Not reached" means "no evidence",
never "dead".** The oracle for byte matching is still the retail binary.

## Prerequisites

* `pcsx-redux` on PATH (tested against `pcsx-redux-git r7505.d1bc093f`).
* A PSX BIOS matching the disc region, passed with `-bios`.
* The disc as a raw 2352-byte BIN plus a matching `.cue`. PCSX-Redux does not
  read CHD and reads the cue for the track layout; without the audio tracks the
  game rejects the TOC (`Too few TOC: please use CD-DA disc`). Generate both:

  ```sh
  python3 tools/chd_extract.py "/path/Galaxian^3 (Japan).chd" build/work/japan.bin --cue
  ```
* The git-ignored `baselines/<target>.bin`.

## The loop

```sh
# 1. Breakpoint list for one stage; --mark the next stage's entry so the log
#    splits by stage (its pc0 is in the EXE header / docs/LOADMAP.md).
python3 tools/gen_watchlist.py slps_00270 --mark 0x8005C530

# 2. Trace it. COV_AUTOPAD pulses START so the run advances unattended; drop it
#    when a human is driving. stdbuf keeps COV| lines flowing if it crashes.
COV_AUTOPAD=1 stdbuf -oL -eL pcsx-redux -run -interpreter -debugger -lua_stdout \
    -bios "/path/PSX - SCPH5500.BIN" -iso build/work/japan.cue \
    -dofile build/cov.slps_00270.lua > /tmp/trace.log 2>&1

# 3. Split at the handoff and diff each phase against its own stage.
awk '/^COV\|MARK/{m=1;next} m==0 && /^COV\|(ENTERED|ITARGET)/' /tmp/trace.log \
    > build/coverage.slps_00270.txt
python3 tools/coverage_vs_fragments.py slps_00270
```

`--stop <addr>` ends the run at a handoff (instead of marking it) when only one
stage is wanted. `gen_watchlist.py --merge a,b,c` builds a play-session probe:
the union of several stages' entries plus a marker at each entry.

## Interactive gdb sessions

The Lua tracer is a batch probe. To stop the game and inspect it directly,
drive the stub with a real gdb through the rewrite shim:

```sh
# disc sessions must run headed (see Constraints below)
SDL_AUDIODRIVER=dummy pcsx-redux -run -interpreter -gdb-port 3333 \
    -bios <BIOS.bin> -iso build/work/japan.cue > /tmp/emu.log 2>&1 &
python3 tools/gdb_stub_proxy.py &        # 127.0.0.1:3334 -> 127.0.0.1:3333
gdb -ex "target remote localhost:3334"   # break *0x8005C530, continue, ...
```

gdb 18.1 aborts at connect without the shim (`invalid remote ptid: p1.t1`):
the stub reports its thread as `p1.t1` in the `qC` reply and as the
`qXfer:threads` XML id, and gdb parses remote thread ids strictly as
`p<pid>.<tid>` with numeric fields. `set remote threads-packet off` only
removes the XML instance — `qC` still kills the session, so the knob is not
enough. The shim rewrites the id in text replies only (hex payloads cannot
contain the literal; binary/console `x`/`X`/`O` packets pass through
untouched). Upstream `gdb-server.cc` still emits `p1.t1` (checked
2026-10-13), and the stub serves `target.xml` over `qXfer:features`, so gdb
sets `mips:3000` and the register layout itself; `Z0` exec breakpoints
answer `OK`.

Verified on `r7505.d1bc093f` (BIOS-only headless run): connect, `info
threads` (`Thread 1.1 "MainThread"`), registers, `x/4i $pc`, memory reads,
and `break *0xbfc0d950` + `continue` stopping with `T05`. The stub accepts
one client at a time; `detach` is unimplemented ("Remote doesn't know how
to detach") — use `disconnect`.

## Constraints (all of these cost real debugging time)

* **`-debugger` is required.** Exec breakpoints run only on the interpreter's
  debug path, gated on `DebugSettings::Debug` (`src/core/psxinterpreter.cc`),
  off by default. Without it nothing fires.
* **Keep every native wrapper in a global.** A breakpoint or event listener
  whose Lua wrapper is collected has its native side torn down mid-run, so a
  local table is not enough: the chunk's locals become collectible when it
  finishes, silently dropping every breakpoint after the first seconds. The
  tracer anchors them in `PCSXCOV`. (tenchu-decomp documents the same trap.)
* **Run headed (`GUI`), not `-no-ui`, for disc sessions.** The title dies
  mid-init headless — reproduced 3×, with and without `-debugger` and with
  no gdb client attached, always right after the `PS-X Control PAD Driver`
  banner. BIOS-only headless runs are stable; the GUI path is the one the
  play sessions use. A window opens — expected.
* **Do not depend on `GPU::Vsync`** for output; it does not fire headless.
  Emit on first hit instead.
* **Read jump registers with `r.GPR.r[rs]`**; `r.GPR.n[name]` fails on `$zero`.
* A `jr`/`jalr` site may be an SDK veneer (`$t2 = 0xA0`) or a library dispatcher,
  not a dispatch table; the consumer filters targets to the payload range.

## Measured limits (pcsx-redux-git r7505.d1bc093f)

Probed directly; these bound what runtime evidence can do here:

* **Only exact-address Exec breakpoints fire.** A range Exec breakpoint
  (`addBreakpoint(base, "Exec", size)`) never fires; only a 4-byte address does.
* **Read/Write watchpoints barely fire.** A 0x46800-wide Write window over the
  image fired once in 60 s; a Read window never fired, and neither did a 0x100
  window on the live stack region. The memory-check path is largely bypassed,
  so watchpoints cannot supply field-width or signedness evidence.
* **The exe entry is not caught.** The loader sets PC directly, so an Exec
  breakpoint on pc0 does not fire at the handoff; the first hit at that PC
  arrives later, when another stage occupies the same RAM.
* **The GDB stub is usable through a shim.** gdb 18.1 cannot connect to it
  directly (see "Interactive gdb sessions"), but with
  `tools/gdb_stub_proxy.py` in between an interactive session works, and
  stub exec breakpoints fire **without** `-debugger` — the gate the Lua path
  needs does not apply here (measured on a no-flag run).

Net: this build can log exact-address Exec hits (auto-pad reaches MAINMENU),
but it is not a trustworthy carve oracle. The static checks
(`tools/code_data_screen.py`, `tools/fragment_report.py`) are the reliable route.

## Reading the output

`!!` marks a real refutation (`REFUTED`); everything else is `not reached`:

* `ORPHAN` reached at runtime → the scan missed a reference; add the edge or
  re-carve.
* `+ indirect-entry`: the subsegment start is an indirect jump target.

**Attribution needs the image-word check, and that check is not yet trusted.**
Every stage loads at the same base, so an address hit while another stage is
resident is not evidence for the target. The tracer reads the live instruction
word and tags a hit with the stage whose image word matches, dropping hits that
match none — but the live read has not been validated against a known address,
and observed hits did not match their own stage's carve bytes. Until the read
primitive is confirmed, treat every `REFUTED` line as provisional. Use the
`MISS` diagnostic (`COV_DEBUG=1`) to see live-vs-expected words.

## Files

| File | Role |
| --- | --- |
| `tools/gen_watchlist.py` | emits the per-target (or merged) breakpoint driver |
| `tools/pcsx_coverage.lua` | the tracer; one `COV|` line per first hit |
| `tools/coverage_vs_fragments.py` | diffs a trace against `fragment_report` |
| `tools/fragment_report.py` | static classifier (`--json` / `build_rows`) |
| `tools/chd_extract.py` | extracts the disc BIN and writes the `.cue` |
| `tools/gdb_stub_proxy.py` | RSP shim: gdb on 3334 -> stub on 3333 (`p1.t1` rewrite) |

`Fuuzetsu/tenchu-decomp` (`tools/pcsx-*.lua` + `tools/pcsx_*.py`) is the same
Lua-probe-plus-Python-driver pattern, and is worth copying further: it verifies
the instruction word at an address against the expected image before counting a
hit, which removes cross-stage false positives without marker splitting.

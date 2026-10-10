# Toolchain

How the bytes of this repository are reproduced, what is proven, and
what is still hypothesis. Everything in the **Proven** table is load-
bearing for `make verify` — do not bump versions casually.

## Proven — the oracle is green with this exact stack

| component | version / source | role |
| --- | --- | --- |
| splat | 0.50 (PyPI `splat64`) | split the retail EXE per config |
| spimdisasm | 1.42.4 (splat dependency) | disassembly used by the split |
| maspsx | pinned clone, `tools-src/maspsx` | Sony ASPSX semantics for GNU as |
| GNU as / ld / objcopy | **2.31.1** (Debian buster `binutils-mipsel-linux-gnu 2.31.1-16`, amd64 host) | assemble + link + extract |
| Python | 3.12 venv (`pyyaml`, `capstone` for `make map`) | pipeline tooling |

Bring-up, no root required:

```sh
tools/get_binutils.sh                      # downloads + dpkg -x into tools-local/mipsel-root
python3 -m pip install splat64==0.50 spimdisasm==1.42.4 capstone pyyaml n64img pygfxd crunch64 intervaltree
make verify TARGET=slps_00270              # must end: OK: build matches retail
```

The assemble flags (`tools/build.sh`): `-march=mips64 -mabi=32 -EL`.
mips64 is deliberate: gas expands macro-prone 64-bit mnemonics (`ld`,
`sd`, ...) under o32, so `build.sh` rewrites those instruction words to
`.word` from the comment encodings — the bytes are the retail bytes, not
gas's macro expansion. The linker script is generated per subsegment by
`tools/gen_ld.py` (splat 0.50's own script reorders an interleaved
image); the PS-X EXE header is rebuilt by `tools/mkpsxexe.py` from
`config/exe.json`.

## Compiler fingerprint — measured on the matched asm

Evidence is reproducible with grep against `asm/nonmatchings/`
(slps_00270); counts are of the committed split.

| signal | measurement | interpretation |
| --- | --- | --- |
| Psy-Q kernel RCS strings | `intr.c` 1995-08-29, `sys.c` 1995-10-26 (docs/RECON.md) | SDK stamped **October 1995** — proven |
| ISA | `mult` 61, `multu` 35, `mflo` 93, `mfhi` 22; no MIPS32 `mul` | **MIPS1** code; multiply = mult+mflo pairs |
| division guard | `div` 13, `break` 33; e.g. `0x80028D74`: `bnez $a3,+7; nop; break 7` then `addiu $at,$zero,-1; bne/lui 0x80000000; break 6` | inline divide-by-zero **and** INT_MIN/-1 overflow traps — the classic GCC MIPS1 idiom |
| libgcc arithmetic calls | 0 `jal` to `__divsi3/__mulsi3/...` | arithmetic fully inlined by the compiler |
| char signedness | `lbu` 184 vs `lb` 13 | **unsigned char is the default** (`-funsigned-char` convention), with a minority of genuinely signed char fields |
| gp-relative addressing | `0` occurrences of `%gp_rel` | **no small-data use** — working assumption `-G0`; *revises* the earlier small-data guess in docs/RECON.md. %hi/%lo pairs carry all data addressing |
| delay slots | `.set noreorder` + explicit `nop` scheduling | compiler-scheduled delay slots, not assembler-reordered |

## Working hypothesis (until pinned per-function)

**GCC 2.6.3 + Psy-Q October-1995**, starting flag set for C rebuilds:
`-mips1 -O2 -G0 -funsigned-char -fno-builtin` (FILL: prove or replace
each flag individually). The `break`-based division guards and the
delay-slot scheduling match GCC 2.6.x-era MIPS output; they do not
uniquely pin the minor revision — only a byte-comparison against the
real compiler can.

## Pinning the exact GCC revision (next step)

1. Acquire candidates: `decompme/compilers` or `decompals/old-gcc`
   prebuilt mips GCC 2.6.3 (and 2.7.x as a control).
2. Compile probe functions exercising each fingerprint row above:
   signed/unsigned division, INT_MIN edge, 64-bit products, unsigned
   char arrays, switch tables (`jtbl` jumps), struct passing.
3. Pass criterion: probe idioms byte-identical to the matched asm
   (guard structure, register allocation, scheduling), not merely
   similar. Record the winning revision + flags here.
4. Only then start C matches; every one is gated by `make verify`.

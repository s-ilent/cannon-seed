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

## Pinned — GCC 2.6.3, Sony Playstation build (2026-10-10)

The compiler of record is **GCC 2.6.3 [AL 1.1, MM 40] Sony Playstation**
— the Psy-Q compiler. Its banner identifies itself on every cc1 run;
the Psy-Q kernel RCS dates (1995-10) agree. Acquired as prebuilt Linux
binaries from `decompals/old-gcc` release 0.12 (`gcc-2.6.3-psx.tar.gz`,
the same artifact decomp.me builds its PSX images from) via
`tools/get_gcc.sh`. The binaries are 32-bit i386; this sandbox's
seccomp allowlist rejects i386 syscall numbers (SIGSYS on first
syscall), so cc1 runs under `qemu-i386` (static, from Debian bullseye's
qemu-user-static — trixie's package only ships symlinks, and this
sandbox refuses symlinks). qemu itself is an amd64 binary making
ordinary syscalls and translates the guest syscalls in userspace.
Everything lands in `tools-local/` (git-ignored, outside the repo,
survives re-provisions); `tools/get_gcc.sh` re-acquires it idempotently.

Pipeline (`tools/cc.sh`, one .c per invocation):

```sh
tools/cc.sh -o out.o file.c        # .c -> .o for standalone checks
tools/cc.sh -S -o out.o file.c     # stop at the maspsx .s (build.sh path)
```

cpp (bundled) -> cc1 -> maspsx `--expand-div` -> mipsel as 2.31.1.
Two non-obvious details: the Psy-Q cc1 rejects comments/#-directives in
raw source (the original driver ran cpp first, so cc.sh does too), and
`--expand-div` is what reproduces the ASPSX assembler's div/divu macro
expansion — the break 7 / break 6 trap guards in the retail bytes come
from that expansion, not from the compiler emitting them.

Flag set: `-mips1 -O2 -G0 -funsigned-char -fno-builtin` (the earlier
working hypothesis, now exercised by probes and the first match).

Probe evidence (`probes/gcc263/idioms.c`, compare against
`asm/nonmatchings/`):

| probe | retail idiom | result |
| --- | --- | --- |
| `a / b` (signed) | `func_80028B8C.s` guard chain | **instruction-for-instruction identical**: `div $zero` + `bnez/nop/break 7` + `addiu $at,-1/bne/lui 0x8000/bne/nop/break 6` + `mflo` |
| `a / b` (unsigned) | divu row | `divu` + `bnez/nop/break 7` + `mflo`, as measured |
| `a * b` | mult row | `mult` + `mflo`, no MIPS32 `mul` |
| `p[i]` plain char | char signedness row | `lbu` (default unsigned char) |
| `p[i]` signed char | minority row | `lb` |

cc1 defaults confirmed on the banner: `-mgas -msoft-float`,
`-G value = 8` (overridden to `-G0`, matching the %gp_rel=0
measurement), `Cpu = 3000, ISA = 1`.

Gotcha for the linker path: gas pads the default `.text` section to 16
bytes on MIPS regardless of content, while the asm staging path's fresh
`.section .r_<rom>, "awx", @progbits` carries no default padding. C
objects therefore go through the same in-source section rewrite
(`tools/build.sh` compiles with `cc.sh -S`, rewrites `.text` in the
.mas.s, assembles with `$ASFLAGS`); renaming with
`objcopy --rename-section` after assembly would keep the padding.

First C match through the round-trip oracle: `src/func_80036CFC.c`
(empty function; retail body `jr $ra; nop`),
`make verify TARGET=slps_00270` green with the C object in place of the
generated disassembly (2026-10-10). Per-function byte-matching
continues to validate the flag set; switch tables (`jtbl`) and struct
passing probes are still open rows.

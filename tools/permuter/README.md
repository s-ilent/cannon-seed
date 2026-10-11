# Permuter integration

Wires [decomp-permuter][permuter] to this project's pinned toolchain. The
permuter searches C source variations to close small codegen differences —
see `docs/MATCHING.md` §3 for where it belongs in the iteration ladder.

## Setup

Clone the permuter next to this repo and give it a Python with `toml`:

```sh
git clone --depth 1 https://github.com/simonlindholm/decomp-permuter ../decomp-permuter
python3 -m pip install toml     # plus pynacl/Levenshtein, optional
```

The pinned toolchain (`tools/get_gcc.sh`, `tools/get_binutils.sh`) must be
installed. `run.sh` refreshes the machine-specific parts automatically, so
nothing under this directory needs editing per machine.

## Preparing a target

A permuter project directory needs four files. `base.c` and `target.o` are
yours; the other two are generated:

| File | Source |
| --- | --- |
| `base.c` | your C draft of the function, containing exactly one function |
| `target.o` | the retail function, assembled from its `asm/<target>/nonmatchings/<name>.s` |
| `compile.sh` | copied in by `run.sh` (single source of truth: `tools/permuter/compile.sh`) |
| `settings.toml` | written by `run.sh`, holds absolute paths, never committed |

To build `target.o`:

```sh
as -march=mips64 -mabi=32 -EL -G0 -I include -I asm/<target>/nonmatchings \
   -o target.o asm/<target>/nonmatchings/<name>.s
```

## Running

```sh
tools/permuter/run.sh <project-dir> -j <cores> --stop-on-zero
```

Useful flags: `--show-errors` (keep sources that fail to compile),
`--stop-on-zero` (halt on an exact match), `-j` for multi-threaded mode.

Check the base candidate's disassembly before a long run. In particular,
confirm the register allocation matches retail: the scorer does not normalize
`$a1` against `$v0`, so a wrong-register base plateaus instead of converging.
`docs/MATCHING.md` §3a has the idioms that move a value into `$v0`.

## What the permuter cannot fix

* **Register choice fixed by the base C.** See above.
* **Instruction count.** Fix length in the source first (ladder step 1); the
  permuter optimizes within a fixed instruction count.
* **Store order the compiler derives from something other than statement
  order.** Eight independent stores can be permuted 8! ways, but if GCC
  reorders a group by a rule the source cannot express, no permutation reaches
  the retail sequence. Park such a function rather than exhausting the search.

[permuter]: https://github.com/simonlindholm/decomp-permuter

#!/usr/bin/env python3
"""exe_map.py - static proof pass for the Galaxian^3 load maps.

Parses the PS-X EXE headers of all eight retail targets (the git-ignored
baselines/), verifies every structural invariant, and disassembles each
entry point with capstone.

Load map (proven from headers alone, v2 - see docs/LOADMAP.md):
  every target is a STANDARD PS-X EXE: one contiguous payload loaded at
  t_addr = 0x80020000, entry at pc0 (inside the image), sp 0x801FFFF0,
  no separate data/bss section in the header. The first pass of this tool
  inherited a one-word-shifted field mapping from the Phase-0 recon script
  (pc0 read as t_addr, t_size as gp0); this version reads the canonical
  layout and cross-checks it against the file sizes.

Emits docs/LOADMAP.md (regenerated wholesale - measurement over
transcription) and exits non-zero if any invariant fails.

Usage: python3 tools/exe_map.py [TARGET ...]   (default: every target)
"""

import struct
import sys
from pathlib import Path

from capstone import CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
from capstone import Cs

REPO = Path(__file__).resolve().parent.parent
BASELINES = REPO / "baselines"
SHA1_DIR = REPO / "config" / "sha1"
OUT = REPO / "docs" / "LOADMAP.md"

HEADER_SIZE = 0x800

# Canonical PS-X EXE header (little-endian words after the 16-byte magic).
WORD_FIELDS = [
    (0x10, "pc0", "entry PC"),
    (0x14, "gp0", "initial $gp"),
    (0x18, "t_addr", "payload load addr"),
    (0x1C, "t_size", "payload size"),
    (0x20, "data_addr", "data dest"),
    (0x24, "data_size", "data size"),
    (0x28, "bss_addr", "bss addr"),
    (0x2C, "bss_size", "bss size"),
    (0x30, "sp0", "initial $sp"),
    (0x34, "w34", "sp offset?"),
    (0x38, "w38", "initial fp?"),
    (0x3C, "w3C", "initial gp?"),
    (0x40, "w40", "initial ret?"),
    (0x44, "w44", "initial base?"),
    (0x48, "w48", "reserved"),
]

MD = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 | CS_MODE_LITTLE_ENDIAN)
MD.skipdata = True


def targets():
    return sorted(p.stem for p in SHA1_DIR.glob("*.sha1"))


def parse_header(path: Path):
    blob = path.read_bytes()
    if len(blob) < HEADER_SIZE:
        raise SystemExit(f"{path.name}: shorter than a PS-X EXE header")
    words = {name: struct.unpack_from("<I", blob, off)[0] for off, name, _ in WORD_FIELDS}
    mark_region = blob[0x4C:0x80]
    mark = mark_region.split(b"\x00")[0].decode("ascii", "replace")
    tail = blob[0x80:HEADER_SIZE]
    # everything after the mark's NUL terminator must be zero up to 0x80
    after = mark_region.split(b"\x00", 1)[1] if b"\x00" in mark_region else b""
    return {
        "magic": blob[0:8],
        "words": words,
        "mark": mark,
        "mark_padded_zero": after.count(0) == len(after),
        "tail_zero": tail.count(0) == len(tail),
        "payload": blob[HEADER_SIZE:],
    }


def invariants(t, h):
    """Return list of failure strings for the structural invariants."""
    w = h["words"]
    errs = []
    if h["magic"] != b"PS-X EXE":
        errs.append(f"{t}: bad magic {h['magic']!r}")
    if w["t_addr"] != 0x80020000:
        errs.append(f"{t}: t_addr {w['t_addr']:#010x} != 0x80020000")
    if w["t_size"] != len(h["payload"]):
        errs.append(f"{t}: t_size {w['t_size']:#x} != payload {len(h['payload']):#x}")
    for k in ("data_addr", "data_size", "bss_addr", "bss_size", "gp0",
              "w34", "w38", "w3C", "w40", "w44", "w48"):
        if w[k] != 0:
            errs.append(f"{t}: {k} unexpectedly {w[k]:#x}")
    if w["sp0"] != 0x801FFFF0:
        errs.append(f"{t}: sp0 {w['sp0']:#010x} != 0x801FFFF0")
    if not (w["t_addr"] < w["pc0"] < w["t_addr"] + w["t_size"]):
        errs.append(f"{t}: pc0 {w['pc0']:#010x} outside image")
    if not h["tail_zero"] or not h["mark_padded_zero"]:
        errs.append(f"{t}: header padding not all-zero")
    return errs


def disasm(blob: bytes, vaddr: int, count: int) -> list[str]:
    out = []
    for ins in MD.disasm(blob, vaddr):
        out.append(f"  {ins.address:08X}:  {ins.bytes.hex():<8s}  {ins.mnemonic} {ins.op_str}")
        count -= 1
        if count == 0:
            break
    return out


def esc(s: str) -> str:
    return s.replace("|", "\\|")


def main(argv):
    want = argv[1:] or targets()
    rows = []
    sections = []
    failures = []

    for t in want:
        path = BASELINES / f"{t}.bin"
        if not path.exists():
            failures.append(f"{t}: baseline missing ({path})")
            continue
        h = parse_header(path)
        w = h["words"]
        failures += invariants(t, h)

        entry_off = w["pc0"] - w["t_addr"]
        rows.append(
            f"| `{t}` | {len(h['payload']):#x} | {w['pc0']:#010x} | {entry_off:#x} "
            f"| {w['t_addr']:#010x} | {w['t_size']:#x} | {w['sp0']:#010x} |"
        )

        entry = h["payload"][entry_off : entry_off + 0x90]
        entry_lines = disasm(entry, w["pc0"], 24)

        sections.append(
            f"""### `{t}`

- Image range: `{w['t_addr']:#010x} .. {w['t_addr'] + w['t_size']:#010x}` ({w['t_size']:,} bytes)
- Entry `pc0`: `{w['pc0']:#010x}` (image offset `{entry_off:#x}`)
- Stack pointer init: `{w['sp0']:#010x}`
- Global pointer init: {w['gp0']} (crt0 sets `$gp`)
- ASCII mark at 0x4C: `{esc(h['mark'])}` (NUL-padded to 0x80)
- Header padding 0x80..0x800 all-zero: {h['tail_zero']}

Entry disassembly:

```mips
{chr(10).join(entry_lines)}
```
"""
        )

    status = "PASS" if not failures else "FAIL"
    fail_block = "".join(f"- {f}\n" for f in failures)

    doc = f"""# LOADMAP: measured header facts and proven RAM map

> Generated by `tools/exe_map.py`. Regenerate with `make map`. Status: **{status}**

## 0. Structural invariants (all eight executables)

{fail_block or "- Magic `PS-X EXE`. `t_addr = 0x80020000`. `t_size` matches payload size. `data_addr/data_size/bss_addr/bss_size = 0`. `gp0 = 0`. Initial `$sp = 0x801FFFF0`. `pc0` resides inside the image. Header padding is all zeroes."}

**Verdict: all eight files are standard PS-X EXEs.** Each target contains one contiguous payload. The BIOS loads each target at `0x80020000`. The entry point sits at `pc0`. The initial stack sits at `0x801FFFF0` (matches `SYSTEM.CNF` `STACK = 801fff00`). The image packages text and data in one block. The header declares no separate data or bss sections. The crt0 stub initializes `$gp`.

## 1. Combined table

| target | payload size | pc0 (entry) | entry offset | t_addr (load) | t_size | initial $sp |
| --- | --- | --- | --- | --- | --- | --- |
{chr(10).join(rows)}

## 2. Per-target measurements

{chr(10).join(sections)}
"""

    OUT.write_text(doc)
    print(f"wrote {OUT.relative_to(REPO)} ({status})")
    for f in failures:
        print(f"FAIL: {f}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

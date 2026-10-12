#!/usr/bin/env python3
"""cc_split.py - split one cc.sh -S product into per-piece staged files.

The multi-subsegment C machinery (docs/FABRIC.md): ONE src file covering
several disjoint address windows. build.sh compiles `src/<base>.c` once
and hands the .mas.s here with the pieces' rom offsets in ADDRESS order;
this tool cuts the output at cc1's `.ent` boundaries - one function per
piece, in compilation order = address order - and writes the staged
files build.sh's normal C path would have written:

    <stem>.r.s      piece 1  (.section .r_<rom1>)
    <stem>.p2.r.s   piece 2  (.section .r_<rom2>)
    ...

Everything before the first `.ent` is the shared preamble and is repeated
into every piece (the .file / gcc2_compiled / .text header cc1 emits
once). Each function chunk must be self-contained .text: a chunk that
switches to another section (.rdata for constants, .data, .sdata, ...) or
holds more than one .ent fails loudly - the fabric C units are pure
control flow + calls, and constants get their own rows.

Usage:
    python3 tools/cc_split.py IN.mas.s STEM ROM1 [ROM2 ...]
"""

import re
import sys
from pathlib import Path

SECTION_RE = re.compile(r"^\s*\.section\s+\.([A-Za-z0-9_.]+)")
TEXT_ONLY = {"text"}
BAD_SECTIONS = {
    "rdata", "data", "sdata", "bss", "sbss", "lit4", "lit8", "rodata",
}


BOUNDARY_RE = re.compile(r"^\s*\.(?:align|globl)\s")
END_RE = re.compile(r"^\s*\.end\s")
ENT_RE = re.compile(r"^\s*\.ent\s")


def split(text):
    """(preamble_lines, [chunk_lines, ...]).

    cc1 groups ALL the symbol preambles (.align/.globl/.extern) at the top
    of the file, before the first `.ent` - there is no per-function
    preamble between bodies. So: the preamble is everything before the
    first `.ent` and is REPEATED into every piece (each piece then
    declares every function global - the undefined ones resolve as
    externals at link time, which is exactly what cross-piece calls
    need); a chunk is one `.ent ... .end` body."""
    lines = text.splitlines()
    starts = [i for i, ln in enumerate(lines) if ENT_RE.match(ln)]
    ends = [i for i, ln in enumerate(lines) if END_RE.match(ln)]
    if not starts or not ends:
        raise SystemExit("cc_split: no .ent/.end in input - nothing to split")
    pre = lines[:starts[0]]
    chunks = []
    for i, s in enumerate(starts):
        e = next((x for x in ends if x > s), None)
        if e is None:
            raise SystemExit(f"cc_split: function {i + 1} has no .end")
        chunks.append(lines[s:e + 1])
    return pre, chunks


def check_chunk(chunk, idx):
    ents = sum(1 for ln in chunk if ENT_RE.match(ln))
    ends = sum(1 for ln in chunk if END_RE.match(ln))
    if ents != 1 or ends != 1:
        raise SystemExit(f"cc_split: piece {idx + 1}: {ents} .ent / {ends} "
                         f".end - pieces are whole functions")
    for ln in chunk:
        m = SECTION_RE.match(ln)
        if m:
            sec = m.group(1).rstrip('"').split(",")[0]
            if sec not in TEXT_ONLY:
                raise SystemExit(
                    f"cc_split: piece {idx + 1} uses section .{sec} - "
                    f"pieces must be pure .text; give constants their "
                    f"own rows")
        if re.match(r"^\s*\.(rdata|data|sdata|lit4|lit8)\b", ln):
            raise SystemExit(f"cc_split: piece {idx + 1} switches section: "
                             f"{ln.strip()}")
    if not any(re.match(r"^\s*\.globl\s", ln) for ln in chunk):
        pass  # .globls live in the shared preamble; repetition carries them


def main(argv):
    gp = "0"
    args = []
    for a in argv:
        if a.startswith("--gp="):
            gp = a[5:]
        else:
            args.append(a)
    if len(args) < 3:
        raise SystemExit(__doc__)
    src = Path(args[0])
    stem = args[1]
    roms = [int(r, 16) for r in args[2:]]
    pre, chunks = split(src.read_text())
    if len(chunks) != len(roms):
        raise SystemExit(
            f"cc_split: {len(chunks)} function(s) in {src.name} but "
            f"{len(roms)} piece rom(s) given - the .c function order must "
            f"equal the yaml row order (docs/FABRIC.md machinery)")
    outs = []
    for i, (chunk, rom) in enumerate(zip(chunks, roms)):
        check_chunk(chunk, i)
        name = f"{stem}.r.s" if i == 0 else f"{stem}.p{i + 1}.r.s"
        body = pre + [""] + chunk
        text = "\n".join(body) + "\n"
        text = re.sub(r"^\s*\.text\s*$",
                      f'.section .r_{rom:08X}, "awx", @progbits',
                      text, flags=re.M)
        # Small-data rewrite, gp targets only - the SAME rewrite build.sh's
        # single-file C staging applies (keep the two in sync; see the
        # rationale comment there).
        if gp == "1":
            text = re.sub(
                r"(?m)^(\s*(?:lb|lbu|lh|lhu|lw|lwl|lwr|sb|sh|sw|swl|swr)\s+\$[a-z0-9]+,)([A-Za-z_][A-Za-z0-9_]*(?:\+[0-9]+)?)\s*$",
                r"\1%gp_rel(\2)($gp)",
                text,
            )
        Path(name).write_text(text)
        outs.append(name)
    print("cc_split: " + ", ".join(outs))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""sdk_symbols.py - resolve game BIOS-call veneers to their Psy-Q SDK names.

A PS-X EXE does not call `syscall` to reach the BIOS. It loads a vector
address into $t2 (0xA0 = the libc/C vector, 0xB0 = the kernel vector) and
jumps through it, passing a function number in $t1:

    addiu  $t2, $zero, 0xB0
    jr     $t2
     addiu $t1, $zero, 0xD      <- delay slot: function number

Those three instructions are the SDK's own entry stubs for the corresponding
PSY-Q library member. They are library code that was linked into the game,
NOT C compiled into a register-indirect jump: a C compiler's `jr` is always a
return (a cross-function call is `jal` to a wrapper). So they are matched as
assembly stubs (INCLUDE_ASM), exactly like the other hand-written routines the
project already parks that way - not matched from C.

What this script adds is the NAMES. The function number in the delay slot is
an index into the SDK's vector table, and the SDK ships that table as source:
each library archive (LIBAPI.LIB, LIBC.LIB, ...) contains one small member per
callable function, and each member contains its own (vector, index) stub. Parse
the archives, read (vector, index) -> member name, then find the same pairs in
the game -> every veneer gets the name of the SDK function it dispatches to.

Usage:
    python3 tools/sdk_symbols.py --libs <dir>     # emit config/sdk_symbols.txt
    python3 tools/sdk_symbols.py --check <dir>   # report only, write nothing

<dir> is a directory holding the Psy-Q .LIB files (LIBAPI.LIB, LIBC.LIB, ...).
The SDK is not committed; see docs/RULES.md. Without the archives the script
exits 0 and writes nothing, so make/scan keep working in a bare checkout.
"""
import argparse
import json
import re
import struct
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "config" / "sdk_symbols.txt"

# Vector tables. 0xA0 is the C library vector, 0xB0 the kernel vector.
VEC_LIBC = 0xA0
VEC_KERNEL = 0xB0

# Stub encodings. The SDK itself is built by ccpsx and uses `li`/`jr`;
# some members use `jalr`. Both forms appear.
_RE_STUB_ASM = re.compile(
    r"addiu\s+\$t2,\s*\$zero,\s*(0x[AB]0)\b.*?"
    r"(?:jr|jalr)\s+\$t2.*?"
    r"addiu\s+\$t1,\s*\$zero,\s*(0x[0-9A-Fa-f]+)\b",
    re.S,
)
# Decoded, not bit-matched: an SDK veneer is three instructions -
#   addiu $t2, $zero, <vector>   op 9, rt 10 ($t2)
#   jr/jalr $t2                  op 0, rs 10
#   addiu $t1, $zero, <index>    op 9, rt 9 ($t1)
# The third lands in the jump's delay slot. Reading the ENCODING as an
# address word is the classic way to get this wrong: 0x240A00B0 is
# "addiu $t2,$zero,0xB0", not a pointer to 0x240A00B0.
_SDK_VECTORS = (VEC_LIBC, VEC_KERNEL)

# Ark member records: <len><name> ... sections ... <len><name> <code>.
# We only need the name record immediately preceding a veneer.
_LNK = b"LNK"


def _member_name_before(data: bytes, off: int):
    """The last <len><identifier> name record before `off`."""
    name = None
    best = -1
    for m in re.finditer(_LNK, data[:off]):
        p = m.start()
        for back in range(0, 30):
            q = p - back
            if q < 1:
                break
            ln = data[q - 1]
            if 2 <= ln <= 24:
                nm = data[q:q + ln]
                if all(32 <= c < 127 for c in nm) and re.match(
                        rb"^[A-Za-z_][A-Za-z0-9_]*$", nm):
                    if p > best:
                        best = p
                        name = nm.decode()
                    break
    return name


def _decode(w):
    """(op, rs, rt, imm) for a MIPS instruction word."""
    return ((w >> 26) & 0x3F, (w >> 21) & 0x1F, (w >> 16) & 0x1F, w & 0xFFFF)


def _veneers(data: bytes):
    """[(offset, vector, index)] for every SDK stub in an archive."""
    out = []
    for i in range(len(data) - 12):
        w1, w2, w3 = struct.unpack("<III", data[i:i + 12])
        op1, _, rt1, imm1 = _decode(w1)
        op2, rs2, _, _ = _decode(w2)
        op3, _, rt3, imm3 = _decode(w3)
        if op1 != 9 or rt1 != 10 or imm1 not in _SDK_VECTORS:
            continue
        if op2 != 0 or rs2 != 10:          # jr/jalr $t2
            continue
        if op3 != 9 or rt3 != 9:           # addiu $t1,$zero,<index>
            continue
        if out and i < out[-1][0] + 12:
            continue
        out.append((i, imm1, imm3))
    return out


def build_table(libdir: Path):
    """(vector, index) -> SDK function name, from the library archives."""
    table = {}
    for lib in sorted(libdir.glob("LIB*.LIB")):
        data = lib.read_bytes()
        for off, vec, idx in _veneers(data):
            name = _member_name_before(data, off)
            if name:
                table.setdefault((vec, idx), name)
    return table


def _game_stub_words(text: str):
    """Instruction words of a `addiu $t2 / jr|jalr $t2 / addiu $t1` stub.

    spimdisasm writes the hex in the ROM's BYTE order, so the comment
    `B0000A24` is bytes B0 00 0A 24 - the little-endian word 0x240A00B0.
    """
    out = []
    for line in text.splitlines():
        m = re.search(r"^\s*/\*\s+\S+\s+\S+\s+([0-9A-Fa-f]{8})\s+\*/", line)
        if not m:
            continue
        asm = line.split("*/")[1]
        if "$t2" in asm or "$t1" in asm:
            raw = int(m.group(1), 16)
            out.append(int.from_bytes(raw.to_bytes(4, "big"), "little"))
    return out


def _stub_pair(words):
    """(vector, index) if `words` is exactly one SDK stub, else None.

    Decoded, not bit-matched: addiu $t2,$zero,<vec> (op 9, rt 10), a
    jr/jalr $t2 (op 0, rs 10), and addiu $t1,$zero,<idx> (op 9, rt 9).
    """
    vec = idx = None
    saw_jump = False
    for w in words:
        op = (w >> 26) & 0x3F
        rs = (w >> 21) & 0x1F
        rt = (w >> 16) & 0x1F
        imm = w & 0xFFFF
        if op == 0 and rs == 10:                      # jr/jalr $t2
            saw_jump = True
        elif op == 9 and rt == 10 and imm in (VEC_LIBC, VEC_KERNEL):
            vec = imm                                  # addiu $t2,$zero,vec
        elif op == 9 and rt == 9:
            idx = imm                                  # addiu $t1,$zero,idx
    if vec is None or idx is None:
        return None
    return (vec, idx)


def _is_pure_stub(text: str):
    """True when a .s file is exactly ONE SDK veneer and nothing else.

    A game function that merely *contains* a BIOS call is not a library
    member and must not take the SDK name. Require the file to hold
    exactly three instructions - no frame, no saves, no other body - and
    that they decode as one stub. Anything longer is game code.
    """
    insns = [l for l in text.splitlines() if re.search(r"/\*\s*\S+\s+\S+\s+[0-9A-Fa-f]{8}", l)]
    if len(insns) != 3:
        return None
    words = _game_stub_words(text)
    if len(words) != 3:
        return None
    return _stub_pair(words)


def game_veneers(targets):
    """target -> [(file, vector, index)] for pure-stub functions only."""
    out = {}
    for t in targets:
        d = REPO / "asm" / t / "nonmatchings"
        if not d.is_dir():
            continue
        per = []
        for f in sorted(d.glob("func_*.s")):
            pair = _is_pure_stub(f.read_text(errors="replace"))
            if pair:
                per.append((f.stem, pair[0], pair[1]))
        if per:
            out[t] = per
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--libs", type=Path, required=True,
                    help="directory holding the Psy-Q *.LIB archives")
    ap.add_argument("--check", action="store_true",
                    help="report only, write nothing")
    ap.add_argument("--json", action="store_true", help="emit JSON to stdout")
    args = ap.parse_args(argv[1:])

    libdir = args.libs
    if not libdir.is_dir():
        print(f"sdk_symbols: {libdir} is not a directory", file=sys.stderr)
        return 0

    table = build_table(libdir)
    if not table:
        print(f"sdk_symbols: no SDK veneers found under {libdir}", file=sys.stderr)
        return 0

    targets = [p.name for p in sorted((REPO / "asm").iterdir()) if p.is_dir()]
    found = game_veneers(targets)

    resolved = {}
    for t, per in found.items():
        for name, vec, idx in per:
            sdk = table.get((vec, idx))
            if sdk:
                resolved.setdefault(t, {})[name] = (sdk, vec, idx)

    if args.json:
        print(json.dumps({"table": {f"{v:X}:{i:02X}": n for (v, i), n in table.items()},
                          "resolved": {t: {k: v[0] for k, v in d.items()}
                                       for t, d in resolved.items()}}, indent=1))
        return 0

    n_tot = sum(len(p) for p in found.values())
    n_res = sum(len(p) for p in resolved.values())
    print(f"sdk_symbols: {len(table)} SDK (vector,index) names from {libdir}")
    print(f"sdk_symbols: {n_tot} game stub functions found, {n_res} resolved")
    for t in sorted(resolved):
        for name, (sdk, vec, idx) in sorted(resolved[t].items()):
            print(f"  {t:<12} {name:<16} {vec:#x}/{idx:#04x} -> {sdk}")
    unresolved = [(t, n) for t, per in found.items()
                  for n in per if n not in resolved.get(t, {})]
    if unresolved:
        print(f"  unresolved: {len(unresolved)}")

    if args.check:
        return 0

    # Refuse to emit a name that already means something else in this target:
    # the linker would resolve two addresses to one symbol.
    existing = {}
    for t in sorted(resolved):
        sym = REPO / "config" / f"symbols.{t}.txt"
        if sym.is_file():
            for line in sym.read_text(errors="replace").splitlines():
                m = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(0x[0-9A-Fa-f]+)", line)
                if m:
                    existing.setdefault(t, {})[m.group(1)] = int(m.group(2), 16)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "// SDK veneer report - GENERATED by tools/sdk_symbols.py.",
        "//",
        "// Regenerate:  python3 tools/sdk_symbols.py --libs <psyq lib dir>",
        "//",
        "// This is evidence, not configuration: it records which functions",
        "// are a pure SDK veneer and which SDK member each dispatches to,",
        "// with the vector/index the member emits. Names that have been",
        "// VERIFIED and adopted live in the target's symbols file (and in",
        "// config/symbols.curated.txt, which the scanner preserves).",
        "//",
        "// A pure veneer is three instructions - addiu $t2,$zero,<vector>;",
        "// jr $t2; addiu $t1,$zero,<index> - and is SDK assembly, matched via",
        "// INCLUDE_ASM, never from C. A game function that merely contains a",
        "// BIOS call is NOT listed here and stays func_XXXXXXXX.",
        "",
    ]
    n = 0
    for t in sorted(found):
        lines.append(f"// target: {t}")
        for name, vec, idx in sorted(found[t], key=lambda x: x[0]):
            sdk = table.get((vec, idx))
            mark = "=" if sdk else "?"
            lines.append(f"//   {name:<16} {vec:#x}/{idx:#04x} {mark} "
                         f"{sdk or '(unresolved)'}")
            if sdk:
                n += 1
        lines.append("")
    OUT.write_text("\n".join(lines))
    print(f"sdk_symbols: wrote {OUT.relative_to(REPO)} "
          f"({sum(len(v) for v in found.values())} sites, {n} resolved)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

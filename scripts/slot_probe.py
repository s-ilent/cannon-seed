#!/usr/bin/env python3
"""slot_probe.py - word-level slot probe of a compiled .mas.s against the
committed retail listing.

Usage: slot_probe.py <compiled.mas.s> <retail_listing.s> [function_name]

Normalizes both sides to (mnemonic, operands) word tuples: ABI register
names -> numbers, hex/decimal immediates -> canonical int, whitespace
collapsed. difflib aligns the sequences; prints matched/total slots and
the hunk regions with retail addresses so a ladder iteration can see
exactly which shapes remain. Exit 0 when every slot matches.
"""
import difflib
import re
import sys

ABI = {
    "$zero": "$0", "$at": "$1", "$v0": "$2", "$v1": "$3",
    "$a0": "$4", "$a1": "$5", "$a2": "$6", "$a3": "$7",
    "$t0": "$8", "$t1": "$9", "$t2": "$10", "$t3": "$11",
    "$t4": "$12", "$t5": "$13", "$t6": "$14", "$t7": "$15",
    "$s0": "$16", "$s1": "$17", "$s2": "$18", "$s3": "$19",
    "$s4": "$20", "$s5": "$21", "$s6": "$22", "$s7": "$23",
    "$t8": "$24", "$t9": "$25", "$k0": "$26", "$k1": "$27",
    "$gp": "$28", "$sp": "$29", "$fp": "$30", "$s8": "$30", "$ra": "$31",
}

INSN_RE = re.compile(
    r"^\s*(?:[a-z][a-z0-9]*)\s+(.*)$"  # mnemonic + rest
)


def norm_reg(tok: str) -> str:
    tok = tok.strip().lower()
    return ABI.get(tok, tok)


def norm_operands(rest: str) -> str:
    parts = []
    for p in rest.split(","):
        p = p.strip()
        # branch/jump target: opaque (labels differ between the two sides)
        if p.lower().startswith((".l", "$l")):
            parts.append("L")
            continue
        # register
        if p.startswith("$"):
            parts.append(norm_reg(p))
            continue
        # mem operand: off($reg) or sym($reg) or %lo(sym)($reg)
        m = re.match(r"^(.*)\(\s*(\$[a-z0-9]+)\s*\)$", p)
        if m:
            off = m.group(1).strip()
            reg = norm_reg(m.group(2))
            try:
                off = str(int(off, 0))
            except ValueError:
                pass
            parts.append(f"{off}({reg})")
            continue
        # immediate
        try:
            parts.append(str(int(p, 0)))
            continue
        except ValueError:
            pass
        parts.append(p)
    return ",".join(parts)


def words_from_mas(path: str):
    """Expand the assembler pseudos the same way gas does at assembly time:
    bare-symbol loads take the dest as base (lui d,%hi; lw d,%lo(d)),
    bare-symbol stores take $at (lui $at,%hi; sw d,%lo($at)), la splits to
    lui+addiu, subu-imm canonicalizes to addiu-negative, j $reg is jr."""
    out = []

    def emit(mnem: str, rest: str):
        out.append((mnem, norm_operands(rest)))

    for ln in open(path, encoding="utf-8", errors="replace"):
        ln = ln.split("#")[0].strip()
        if not ln or ln.startswith("."):
            continue
        if ln.endswith(":"):
            continue
        toks = ln.split(None, 1)
        mnem = toks[0]
        rest = toks[1].strip() if len(toks) > 1 else ""
        # immediate forms of register-named ALU ops assemble as the imm ops
        if mnem in ("addu", "addiu", "slt", "sltu") and "," in rest:
            parts = [p.strip() for p in rest.split(",")]
            if len(parts) == 3:
                try:
                    int(parts[2], 0)
                    if mnem == "addu":
                        mnem = "addiu"
                    elif mnem == "slt":
                        mnem = "slti"
                    elif mnem == "sltu":
                        mnem = "sltiu"
                except ValueError:
                    pass
        if mnem == "nop":
            out.append(("nop", ""))
            continue
        _op = rest.strip().lower()
        if mnem == "j" and (
            re.match(r"^\$\d+$", _op) or _op in ABI
        ):
            # j $reg assembles as jr; j <label> stays j
            emit("jr", rest)
            continue
        if mnem == "subu" and "," in rest:
            parts = [p.strip() for p in rest.split(",")]
            if len(parts) == 3 and parts[0] == parts[1]:
                try:
                    n = int(parts[2], 0)
                    if 0 < n < 0x8000:
                        emit("addiu", f"{parts[0]},{parts[1]},-{n}")
                        continue
                except ValueError:
                    pass
        # bare-symbol (or sym+off / sym.idx) load/store/la: expand
        m = re.match(r"^(l[a-z]+|la)\s+(\$\w+),\s*([A-Za-z_][A-Za-z0-9_.+]*)$", ln)
        if m:
            op, dest, sym = m.group(1), m.group(2), m.group(3)
            if op == "la":
                emit("lui", f"{dest},%hi({sym})")
                emit("addiu", f"{dest},{dest},%lo({sym})")
            else:
                emit("lui", f"{dest},%hi({sym})")
                emit(op, f"{dest},%lo({sym})({dest})")
            continue
        m = re.match(r"^(s[a-z]+)\s+(\$\w+),\s*([A-Za-z_][A-Za-z0-9_.+]*)$", ln)
        if m:
            op, data, sym = m.group(1), m.group(2), m.group(3)
            emit("lui", f"$at,%hi({sym})")
            emit(op, f"{data},%lo({sym})($at)")
            continue
        emit(mnem, rest)
    return out


def words_from_listing(path: str, func: str):
    out = []
    addr_of = []
    in_func = False
    for ln in open(path, encoding="utf-8", errors="replace"):
        if func:
            if ln.startswith(f"glabel {func}"):
                in_func = True
                continue
            if in_func and ln.startswith("endlabel"):
                break
            if not in_func:
                continue
        m = re.match(r"\s*/\*\s*[0-9A-Fa-f]+\s+([0-9A-Fa-f]+)\s+[0-9A-Fa-f]+\s*\*/\s*(.*)$", ln)
        if not m:
            continue
        addr, insn = m.group(1), m.group(2).strip()
        insn = insn.split("#")[0].strip()
        if not insn:
            continue
        toks = insn.split(None, 1)
        mnem = toks[0]
        rest = toks[1].strip() if len(toks) > 1 else ""
        # beqz/bnez are the canonical retail spellings of beq/bne $0
        if mnem == "beqz":
            mnem, rest = "beq", f"{rest.split(',')[0].strip()},$0,{rest.split(',')[1].strip()}"
        elif mnem == "bnez":
            mnem, rest = "bne", f"{rest.split(',')[0].strip()},$0,{rest.split(',')[1].strip()}"
        out.append((mnem, norm_operands(rest)))
        addr_of.append(addr)
    return out, addr_of


def main():
    mas, listing = sys.argv[1], sys.argv[2]
    func = sys.argv[3] if len(sys.argv) > 3 else ""
    A = words_from_mas(mas)
    B, addrs = words_from_listing(listing, func)
    sm = difflib.SequenceMatcher(a=A, b=B, autojunk=False)
    matched = sum(b.size for b in sm.get_matching_blocks())
    print(f"probe {matched}/{len(B)} slots (compiled {len(A)})")
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        print(f"-- {tag}: compiled[{i1}:{i2}] vs retail[{j1}:{j2}] @{addrs[j1] if j1 < len(addrs) else '?'}")
        for k in range(i1, i2):
            print(f"   C  {A[k][0]} {A[k][1]}")
        for k in range(j1, j2):
            print(f"   R@{addrs[k]}  {B[k][0]} {B[k][1]}")
    sys.exit(0 if matched == len(B) == len(A) else 1)


if __name__ == "__main__":
    main()

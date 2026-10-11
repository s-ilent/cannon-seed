#!/usr/bin/env python3
"""rank_cmatch.py - rank asm subsegs (function clusters) as C-match candidates.

A yaml asm subseg's .s file usually contains SEVERAL tiny functions
(one glabel each). Matching converts the WHOLE cluster to one C file
(splittable later via re-scan, as done for func_8004D704).

Criteria (worklog cron-20261011-0156/0400):
  - cluster size <= 0x140
  - every function: no `invalid instruction`, no handwritten marks, no GTE
  - every function: either clean prologue'd frame (addiu $sp,-N with an
    $ra/$s* save nearby) or frameless leaf
  - NO live-frame j tail (worklog 0400: live-frame `j` = asm origin)
  - fewer jal / data refs / gp refs = better; small = better

Usage: python3 tools/rank_cmatch.py [TARGET ...]   (default: all 8)
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

YAML_RE = re.compile(r"\s*-\s*\[(0x[0-9A-Fa-f]+),\s*(asm|c|data),\s*(\w+)\]\s*#\s*(0x[0-9A-Fa-f]+)")
GLABEL_RE = re.compile(r"^glabel\s+(\S+)", re.M)
SP_ALLOC_RE = re.compile(r"^addiu\s+\$sp,\s*\$sp,\s*-0x")
SP_FREE_RE = re.compile(r"^(?:addiu|addu)\s+\$sp,\s*\$sp,\s*(?!-)")
GTE_OPS = {"mfc2", "mtc2", "cfc2", "ctc2", "lwc2", "swc2", "cop2"}
LOADS = {"lw", "lb", "lbu", "lh", "lhu", "lwl", "lwr", "lwc2", "ll"}
STORES = {"sw", "sb", "sh", "swl", "swr", "swc2", "sc"}
REG_RE = re.compile(r"\$(\w+)")
ARG_REGS = {"a0", "a1", "a2", "a3", "zero"}
# defined at function entry by the ABI/calling convention
ENTRY_REGS = {"sp", "ra", "gp", "fp", "k0", "k1"} | ARG_REGS


def reads_writes(mnem, rest):
    """Return (read_reg_names, write_reg_name|None) - MIPS1-ish."""
    ops = [o.strip() for o in rest.split(",")] if rest else []
    regs = [REG_RE.match(o).group(1) for o in ops if REG_RE.match(o)]
    bases = re.findall(r"\((\$\w+)\)", rest)
    bases = [b[1:] for b in bases]
    if mnem in LOADS:
        dest = regs[0] if regs else None
        reads = set(bases) | (set(regs[1:]) if len(regs) > 1 else set())
        return reads, dest
    if mnem in STORES:
        reads = set(regs) | set(bases)
        return reads, None
    if mnem in ("mflo", "mfhi"):
        return set(), regs[0] if regs else None
    if mnem in ("mtlo", "mthi"):
        return set(regs), None
    if mnem in ("mult", "multu", "div", "divu"):
        return set(regs), None
    if mnem.startswith("b") or mnem.startswith("j"):
        # branch: bXX $rs, $rt, label / j label / jr $rs
        return set(regs), None
    if mnem in ("nop", "syscall", "break"):
        return set(), None
    # generic arith/logic: op1 = dest, rest = sources
    dest = regs[0] if regs else None
    return set(regs[1:]) | set(bases), dest


def parse_subsegs(target):
    out = []
    yaml = REPO / "config" / f"splat.{target}.yaml"
    for ln in yaml.read_text().splitlines():
        m = YAML_RE.match(ln)
        if m:
            out.append((int(m.group(1), 16), m.group(2), m.group(3), int(m.group(4), 16)))
    return out


def instructions(text):
    """Yield (mnemonic, rest) for real instruction lines."""
    for raw in text.splitlines():
        l = raw.strip()
        if not l or l.startswith(("#", "*")):
            continue
        if l.startswith("/*"):
            end = l.find("*/")
            if end < 0:
                continue
            l = l[end + 2:].strip()
            if not l:
                continue
        if l.startswith(".") or l.startswith(("glabel", "enddlabel", "endlabel", "alabel")) or l.endswith(":"):
            continue
        parts = l.split(None, 1)
        mnem = parts[0]
        rest = parts[1].strip() if len(parts) > 1 else ""
        if "/*" in rest:
            rest = rest.split("/*")[0].strip()
        yield mnem, rest


def eval_function(name, code):
    """Return (ok, flags_dict, reason)."""
    flags = {}
    if not code:
        return False, flags, "empty"
    for mnem, _ in code:
        if mnem in GTE_OPS:
            return False, flags, "GTE"

    n_alloc = sum(1 for m, r in code if SP_ALLOC_RE.match(m + " " + r))
    if n_alloc > 1:
        return False, flags, "multi-frame"
    if n_alloc == 0:
        # frameless leaf is fine ONLY if it is a true entry: every register
        # read before being written must be an argument register. Reading
        # $t*/$s*/$v*/$gp first = continuation of a split function.
        live = set(ENTRY_REGS)
        for m, r in code:
            reads, writes = reads_writes(m, r)
            bad = {x for x in reads if x not in live and x not in ENTRY_REGS}
            if bad:
                return False, flags, f"continuation (reads {sorted(bad)[0]} first)"
            if writes:
                live.add(writes)
    if n_alloc == 1:
        calls = any(m in ("jal", "jalr") for m, _ in code)
        saves_ra = any(re.match(r"^sw\s+\$ra,", r) for _, r in code)
        if calls and not saves_ra:
            return False, flags, "calls but never saves $ra"

    # tail = last control-flow instruction (delay-slot instrs follow it)
    cf_idx = [i for i, (m, _) in enumerate(code) if m in ("jr", "j", "jalr", "jal")]
    tail_m, tail_r = code[cf_idx[-1]] if cf_idx else ("", "")
    if tail_m == "jr" and tail_r.split(",")[0].strip() != "$ra":
        return False, flags, f"computed dispatch (jr {tail_r.split(',')[0].strip()})"
    if tail_m not in ("jr", "j"):
        return False, flags, f"tail is {tail_m or 'none'}"
    if tail_m == "j":
        if n_alloc == 0:
            pass  # frameless j tail = compiler tail call (return g();)
        else:
            ra_reload = any(re.match(r"^lw\s+\$ra,", r) for _, r in code)
            sp_freed_tail = any(SP_FREE_RE.match(m + " " + r) for m, r in code[-3:])
            if not (ra_reload and sp_freed_tail):
                return False, flags, "live-frame j tail"

    flags["jal"] = sum(1 for m, _ in code if m == "jal")
    flags["jalr"] = sum(1 for m, _ in code if m == "jalr")
    flags["j"] = sum(1 for m, _ in code if m == "j")
    flags["data"] = sum(1 for m, r in code if "%hi(D_" in r or "%lo(D_" in r)
    flags["gp"] = sum(1 for m, r in code if "$gp" in r)
    return True, flags, ""


def inspect(target, name):
    asmfile = REPO / "asm" / target / "nonmatchings" / f"{name}.s"
    if not asmfile.exists():
        return None, "no .s file"
    text = asmfile.read_text()

    if text.count("invalid instruction"):
        return None, "has invalid"
    if "handwritten" in text:
        return None, "handwritten"

    glabels = GLABEL_RE.findall(text)
    if not glabels:
        return None, "no glabel"

    # split into per-glabel sections
    starts = [m.start() for m in GLABEL_RE.finditer(text)]
    sections = [text[starts[i]:starts[i + 1] if i + 1 < len(starts) else len(text)]
                for i in range(len(starts))]

    tot = {"jal": 0, "jalr": 0, "j": 0, "data": 0, "gp": 0, "nfuncs": len(glabels),
           "frameless": 0, "framed": 0}
    for gname, sec in zip(glabels, sections):
        code = list(instructions(sec))
        ok, flags, why = eval_function(gname, code)
        if not ok:
            return None, f"{gname}: {why}"
        for k in ("jal", "jalr", "j", "data", "gp"):
            tot[k] += flags[k]
        tot["frameless" if not any(SP_ALLOC_RE.match(m + " " + r) for m, r in code) else "framed"] += 1
    return tot, ""


def main(argv):
    cap = 0x140
    if len(argv) > 1 and argv[1].startswith("0x"):
        cap = int(argv[1], 0)
        argv = argv[:1] + argv[2:]
    targets = argv[1:] or ["slps_00270", "sces_00269", "mainmenu_jp", "mainmenu_eu",
                           "g3_jp", "g3_eu", "g3org_jp", "g3org_eu"]
    rows, rejects = [], {}
    for target in targets:
        for start, typ, name, size in parse_subsegs(target):
            if typ != "asm" or size == 0 or size > cap:
                continue
            stats, why = inspect(target, name)
            if stats is None:
                rejects[why] = rejects.get(why, 0) + 1
                continue
            rows.append((size, stats["jal"], stats["jalr"], stats["j"],
                         stats["data"], stats["gp"], stats["nfuncs"],
                         target, name, start))

    rows.sort(key=lambda r: (r[0] + 16 * r[1] + 16 * r[3] + 8 * r[4], r[1], r[0]))
    print(f"{'size':>5} {'jal':>4} {'jr':>3} {'j':>3} {'dat':>4} {'gp':>3} {'fn':>3}  target       name")
    for size, njal, njalr, nj, ndata, ngp, nfn, target, name, start in rows:
        print(f"{size:>5} {njal:>4} {njalr:>3} {nj:>3} {ndata:>4} {ngp:>3} {nfn:>3}  {target:<12} {name:<15} 0x{start + 0x80020000:08X}")
    print(f"\n{len(rows)} candidates; rejects: {sum(rejects.values())} in {len(rejects)} classes")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

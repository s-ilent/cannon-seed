#!/usr/bin/env python3
"""second_compiler_census - the second-compiler discriminator census as its own screen.

Windows 29/31 proved by probe (cc1 2.6.3-PSX, the in-repo compiler): it never
emits
  (1) `sltu $at, ...` for a single compare - retail's func_8005BB94/5B270/
      5A714/59EF0/80047844 chain and parked func_800487F4 carry them, and
  (2) `multu` on provably sign-extended operands - seven source shapes (the
      cast form, the unsigned-declared form, the volatile-load form, the
      ternary-corrected form, ...) all fold the unsigned multiply into
      `mult`; retail's func_80049DA0 matrix builder carries 14 such multu.

Rows carrying either artifact cannot match under the in-repo cc1: they are
the SECOND-COMPILER CLASS (a different psyq gcc built those objects), parked
pending a 2.7.x cc1 in tools-local (scripts/deferred_func_800487F4.c and
scripts/deferred_func_80049DA0.c are the banked precedents). This census
screens the committed asm for both discriminators so the real-C reading list
spends decode-windows on matchable rows first.

Screens (conservative, function-granular evidence - never verdicts; every
hit quotes the defining insn for hand verification):

  sltu-at     every `sltu $at, ...`; classified range-idiom when an
              `addiu $at, <reg>, <imm>` sits within 4 upstream insns (the
              two-compare bounds fold - whose provenance is NOT yet probed,
              so range hits do NOT count toward the verdict), else
              single-compare (the probed discriminator).

  multu-sext  for every `multu`, a backward def-scan of both operand
              registers over fall-through instruction flow: piece markers
              (nonmatching/glabel/endlabel) are transparent ONLY across an
              exact VA fall-through (prev last-insn VA + 4 == next VA;
              branch-target piece starts are barriers), a branch/jump stops
              the walk (defs above it do not dominate), and the FIRST def
              found decides - sra/lh/lb is sign-extending (HIT), lhu/srl/
              andi/slt/sltu are zero-or-non-negative (clean stop), anything
              else is unknown width (stop, no claim).

Usage: python3 tools/second_compiler_census.py [target] [--top N] [--detail]
Calibration (hard, exit 2 on failure): func_800487F4 must surface as
sltu-at single-compare; func_80049DA0 must surface as multu-sext.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pick_game_candidates as pgc  # noqa: E402

ROOT = pgc.ROOT

INSN_RE = re.compile(
    r"^\s*/\*\s*[0-9A-Fa-f]+\s+([0-9A-Fa-f]+)\s+[0-9A-Fa-f]+\s*\*/\s*(.*)$")
NONMATCHING_RE = re.compile(r"^\s*nonmatching\s+([A-Za-z_][A-Za-z0-9_]*)")
GLABEL_RE = re.compile(r"^\s*glabel\s+([A-Za-z_][A-Za-z0-9_]*)")

CONTROL = {"b", "beq", "bne", "blez", "bgtz", "bltz", "bgez", "bltzal", "bgezal",
           "beqz", "bnez", "beql", "bnel", "blezl", "bgtzl", "j", "jal", "jr",
           "jalr"}
DEF_MINOR = {"li", "la", "lw", "lh", "lhu", "lb", "lbu", "lwl", "lwr", "move",
             "addiu", "addi", "addu", "add", "subiu", "subu", "sub", "negu",
             "neg", "not", "and", "or", "xor", "nor", "ori", "xori", "andi",
             "slti", "sltiu", "slt", "sltu", "sll", "srl", "sra", "sllv",
             "srlv", "srav", "mflo", "mfhi", "mfc0", "mfc1", "mfc2", "lwc1",
             "lwc2"}
SEXT = {"sra", "lh", "lb"}
CLEAN = {"lhu", "srl", "andi", "slt", "sltu"}
# every MIPS I GPR writer is in DEF_MINOR or CONTROL (loads, ALU, mflo/mfhi,
# jal/jalr/bltzal/bgezal->ra). everything else writes memory, hi/lo or cop
# registers only, so the backward walk treats it as transparent - stopping
# at a previous multu or a nop killed the calibration recall (2/14).
TRANSPARENT = {"nop", "mult", "multu", "div", "divu", "mthi", "mtlo",
               "sw", "sb", "sh", "swc1", "swc2", "sd", "mtc0", "mtc1", "mtc2",
               "ctc0", "ctc1", "ctc2", "cop0", "cop1", "cop2", "rfe", "break",
               "syscall", "sync", "lwc1", "lwc2", "cache", "eret"}

MEM_RE = re.compile(r"[(%]")


def parse_ops(rest):
    return [o.strip().lstrip("$") for o in rest.split(",")] if rest else []


def dest_of(mnem, ops):
    """the GPR an insn writes, or None. stores/mults/cop-store never do."""
    if mnem in CONTROL or not ops:
        return None
    if mnem in ("sw", "sb", "sh", "swc1", "swc2", "sd", "mult", "multu",
                "div", "divu", "mtc0", "mtc1", "mtc2", "ctc0", "ctc1", "ctc2",
                "break", "syscall", "nop", "sync"):
        return None
    d = ops[0]
    if not d or MEM_RE.search(d):
        return None
    return d


def parse_file(path):
    """-> list of insn dicts {mnem, ops, va, raw, barrier} in file order."""
    insns = []
    prev_va = None
    piece_started = False
    for ln in path.read_text(errors="replace").splitlines():
        s = ln.strip()
        if NONMATCHING_RE.match(s) or GLABEL_RE.match(s):
            piece_started = True
            continue
        m = INSN_RE.match(ln)
        if not m:
            continue
        va = int(m.group(1), 16)
        body = m.group(2).strip()
        body = re.sub(r"\s+", " ", body)
        parts = body.split(None, 1)
        if not parts:
            continue
        mnem = parts[0].lower()
        ops = parse_ops(parts[1] if len(parts) > 1 else "")
        barrier = piece_started and (prev_va is None or prev_va + 4 != va)
        insns.append({"mnem": mnem, "ops": ops, "va": va, "raw": body,
                      "barrier": barrier})
        prev_va = va
        piece_started = False
    return insns


def sext_def(insns, i, reg, max_back=64):
    """the first def of `reg` walking backward from just before insn i.
    returns (verdict, insn_or_None): 'sext' | 'clean' | 'unknown' | 'none'."""
    if reg in ("zero", "at", "ra", "sp", "gp", "fp"):
        return "none", None
    for j in range(i - 1, max(-1, i - 1 - max_back), -1):
        ins = insns[j]
        if ins["barrier"]:
            return "none", None
        if ins["mnem"] in CONTROL:
            return "none", None
        if ins["mnem"] in TRANSPARENT:
            continue
        if ins["mnem"] not in DEF_MINOR:
            return "unknown", None
        d = dest_of(ins["mnem"], ins["ops"])
        if d != reg:
            continue
        if ins["mnem"] in SEXT:
            return "sext", ins
        if ins["mnem"] in CLEAN:
            return "clean", ins
        return "unknown", ins
    return "none", None


def screen_file(path):
    """-> {"sltu_single": [...], "sltu_range": [...], "multu_sext": [...]}"""
    insns = parse_file(path)
    out = {"sltu_single": [], "sltu_range": [], "multu_sext": []}
    for i, ins in enumerate(insns):
        if ins["mnem"] == "sltu" and ins["ops"] and ins["ops"][0] == "at":
            cls = "sltu_range"
            for j in range(max(0, i - 4), i):
                p = insns[j]
                if p["barrier"]:
                    break
                if p["mnem"] == "addiu" and p["ops"] and p["ops"][0] == "at":
                    cls = "sltu_range"
                    break
            else:
                cls = "sltu_single"
            out[cls].append(ins["raw"])
        if ins["mnem"] == "multu":
            regs = [o for o in ins["ops"][:2]
                    if o and not MEM_RE.search(o) and o != "zero"]
            hits = []
            for r in regs:
                v, d = sext_def(insns, i, r)
                if v == "sext":
                    hits.append((r, d["raw"] if d else "?"))
            if hits:
                out["multu_sext"].append((ins["raw"], hits))
    return out


def census_target(target):
    """-> {func_name: screen_dict} for every nonmatchings .s of the target."""
    d = ROOT / "asm" / target / "nonmatchings"
    res = {}
    if not d.is_dir():
        return res
    for p in sorted(d.glob("*.s")):
        sc = screen_file(p)
        if any(sc.values()):
            res[p.stem] = sc
    return res


def candidates_for(target):
    """the pick_game_candidates filter loop, imported verbatim."""
    rows = pgc.parse_yaml_rows(target)
    spans = pgc.parse_windows(target)
    curated = pgc.parse_curated(target)
    kind_map = pgc.row_kind_map(target, rows)
    cands = []
    for r in rows:
        if r["kind"] != "asm" or r["sdk"] or not r["size"]:
            continue
        if r["name"] in curated:
            continue
        va, end = r["va"], r["va"] + r["size"]
        if any(s <= va < e or (va < s < end) for s, e in spans):
            continue
        sh = pgc.shape(target, r["name"])
        if sh is None or sh["thunk"] or sh["split"] or sh["n_blocks"] > 48:
            continue
        game, sdk = pgc.callers_of(target, r["name"], kind_map)
        score = r["size"] + 8 * sh["n_br"] + 16 * sh["n_jal"]
        cands.append({"name": r["name"], "va": r["va"], "size": r["size"],
                      "score": score, "game_callers": game,
                      "sdk_callers": sdk, **sh})
    cands.sort(key=lambda c: -c["score"])
    return cands


def main():
    args = sys.argv[1:]
    target = "g3_eu"
    top = 20
    detail = False
    if args and not args[0].startswith("-"):
        target = args.pop(0)
    if "--top" in args:
        top = int(args[args.index("--top") + 1])
    detail = "--detail" in args

    all_targets = sorted({p.parent.parent.name
                          for p in ROOT.glob("asm/*/nonmatchings/*.s")})

    # ---- per-target totals -------------------------------------------------
    print("=== second-compiler discriminator census (committed asm) ===")
    totals = {}
    for t in all_targets:
        res = census_target(t)
        n_single = sum(len(v["sltu_single"]) for v in res.values())
        n_range = sum(len(v["sltu_range"]) for v in res.values())
        n_multu = sum(len(v["multu_sext"]) for v in res.values())
        totals[t] = (res, n_single, n_range, n_multu)
        n_func = len(list((ROOT / "asm" / t / "nonmatchings").glob("*.s")))
        print(f"{t:<14} funcs={n_func:<4} sltu-at:single={n_single:<3} "
              f"range={n_range:<3} multu-sext funcs={len([1 for v in res.values() if v['multu_sext']]):<3} "
              f"hits={n_multu}")

    # ---- calibration -------------------------------------------------------
    print("\n=== calibration (banked second-compiler rows must surface) ===")
    res_eu = totals.get(target, ({}, 0, 0, 0))[0]
    ok1 = "func_800487F4" in res_eu and res_eu["func_800487F4"]["sltu_single"]
    ok2 = "func_80049DA0" in res_eu and res_eu["func_80049DA0"]["multu_sext"]
    n49 = len(res_eu.get("func_80049DA0", {}).get("multu_sext", [])) if ok2 else 0
    print(f"func_800487F4 sltu-at single-compare: "
          f"{'SURFACED' if ok1 else 'MISSED'}")
    print(f"func_80049DA0 multu-on-sext: {'SURFACED' if ok2 else 'MISSED'} "
          f"({n49} multu hits vs 14 banked)")
    if not (ok1 and ok2):
        print("CALIBRATION FAILED - the screen disagrees with the banked "
              "probes; do not trust the census this run.")
        sys.exit(2)

    # ---- candidate join ----------------------------------------------------
    print(f"\n=== {target} ranked candidates x discriminators ===")
    cands = candidates_for(target)
    flagged = 0
    hdr = (f"{'name':<18}{'sz':>6}{'score':>7}  {'sltu1':>5}{'sltur':>5}"
           f"{'multu':>6}  verdict")
    print(hdr)
    print("-" * len(hdr))
    for c in cands[:top]:
        sc = res_eu.get(c["name"], {})
        n1 = len(sc.get("sltu_single", []))
        nr = len(sc.get("sltu_range", []))
        nm = len(sc.get("multu_sext", []))
        verdict = "second-compiler class" if (n1 or nm) else "clean"
        flagged += bool(n1 or nm)
        print(f"{c['name']:<18}{c['size']:>6}{c['score']:>7}  {n1:>5}{nr:>5}"
              f"{nm:>6}  {verdict}")
    print(f"\n{flagged} of {min(top, len(cands))} listed candidates flagged "
          f"(second-compiler class: decode-priority deprioritized, park "
          f"pending a 2.7.x cc1; range-idiom sltu-at alone is NOT a verdict).")

    # ---- detail ------------------------------------------------------------
    if detail:
        print("\n=== detail (every flagged function, quotes) ===")
        for t, (res, _, _, _) in sorted(totals.items()):
            for name in sorted(res):
                sc = res[name]
                lines = []
                if sc["sltu_single"]:
                    lines.append(f"sltu-at single x{len(sc['sltu_single'])}: "
                                 + " | ".join(sc["sltu_single"][:2]))
                if sc["sltu_range"]:
                    lines.append(f"sltu-at range x{len(sc['sltu_range'])}")
                if sc["multu_sext"]:
                    ex = sc["multu_sext"][0]
                    lines.append(f"multu-sext x{len(sc['multu_sext'])}: "
                                 f"{ex[0]} <- " + "; ".join(
                                     f"{r}:{d}" for r, d in ex[1]))
                print(f"{t:<12} {name:<20} " + " ; ".join(lines))

    # ---- reading-list verdicts --------------------------------------------
    reading = ["func_80052038", "func_8006AF70", "func_80027B00",
               "func_8006923C", "func_8007068C", "func_80047844",
               "func_8006D09C"]
    print(f"\n=== reading-list verdicts ({target}) ===")
    byname = {c["name"]: c for c in cands}
    for r in reading:
        if r in res_eu:
            sc = res_eu[r]
            n1 = len(sc["sltu_single"])
            nm = len(sc["multu_sext"])
            rank = next((i + 1 for i, c in enumerate(cands)
                         if c["name"] == r), None)
            print(f"{r:<18} rank={rank} sltu1={n1} multu-sext={nm} -> "
                  f"{'SECOND-COMPILER: park, next candidate' if (n1 or nm) else 'clean: decode-eligible'}")
        elif r in byname:
            print(f"{r:<18} rank={byname[r] and [i+1 for i,c in enumerate(cands) if c['name']==r][0]} clean (no .s hits)")
        else:
            print(f"{r:<18} not a live candidate (landed/curated/filtered)")


if __name__ == "__main__":
    main()

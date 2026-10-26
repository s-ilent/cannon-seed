#!/usr/bin/env python3
"""str_chain.py - mechanize the str->a1 prologue hoist (judge-delta (ii)).

The final-asm delta: ours binds str's pseudo into a1 IN THE PROLOGUE
(move a1,a2 right after the code bind); retail keeps str in a2 and does
the a1<-a2 copy AT THE STRCPY CALL SITE (delay slot).  Both compile from
the same C, so the divergence is a pass-level decision on str's pseudo.

This tool compiles a variant with -da, finds the strcpy call and str's
pseudo number in the expansion dump, then windows the call region in
every -da pass and prints local-alloc's own dump lines that mention that
pseudo, so the pass that fixes str's hard reg can be read directly.

Usage: python3 scripts/bm_unit_decode/str_chain.py <variant.c> [cc1-extra]
"""
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLROOT = os.environ.get("TOOLROOT", "/home/z/my-project/tools-local/mipsel-root")
OBJDUMP = os.path.join(TOOLROOT, "usr/bin/mipsel-linux-gnu-objdump")
PASSES = ["rtl", "jump", "cse", "loop", "cse2", "flow", "combine",
          "sched", "lreg", "greg", "sched2", "jump2", "dbr"]
HEAD = re.compile(r"^\((?:insn|jump_insn|call_insn|code_label|barrier|note)\s+(\d+)\s")


def parse(path):
    text = open(path, errors="replace").read()
    out, i, n = [], 0, len(text)
    while i < n:
        nl = text.find("\n", i)
        line = text[i:nl if nl >= 0 else n]
        m = HEAD.match(line)
        if m:
            depth, j = 0, i
            while j < n:
                c = text[j]
                if c == "(":
                    depth += 1
                elif c == ")":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            out.append((int(m.group(1)), line[1:line.find(" ", 1)], text[i:j + 1]))
            i = j + 1
        else:
            i = nl + 1 if nl >= 0 else n
    return out


def compact(rec):
    rec = re.sub(r"^\((insn|jump_insn|call_insn|code_label|barrier|note)\s+(\d+)\s+(\d+)\s+(\d+)",
                 r"[\2]", rec)
    rec = re.sub(r"\((reg|mem):/\w+ ", r"(\1 ", rec)
    rec = rec.replace("\n", " ")
    rec = re.sub(r"\s+", " ", rec)
    return rec.strip()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    cand = os.path.abspath(sys.argv[1])
    extra = (sys.argv[2] if len(sys.argv) > 2 else "") + " -da"
    base = os.path.splitext(os.path.basename(cand))[0]
    stem = f"build/judge/str_{base}"
    os.makedirs(os.path.join(REPO, "build/judge"), exist_ok=True)
    env = dict(os.environ, CC1FLAGS_EXTRA=extra,
               LD_LIBRARY_PATH=f"{TOOLROOT}/usr/lib/x86_64-linux-gnu")
    r = subprocess.run([f"{REPO}/tools/cc.sh", "-o", stem + ".o", cand],
                       cwd=REPO, capture_output=True, text=True, env=env)
    if r.returncode:
        print(f"COMPILE-FAIL:\n{r.stderr[-800:]}")
        return 1
    prefix = stem + ".i"
    dumps = {p: f"{prefix}.{p}" for p in PASSES
             if os.path.exists(f"{prefix}.{p}")}
    if "rtl" not in dumps:
        print(f"no rtl dump at {prefix}.rtl; dumps found: {sorted(dumps)}")
        return 1

    # 1. str's pseudo = the source of the (set (reg 5) ...) that feeds the
    #    strcpy call (a1 = hard reg 5 in o32), read from the expansion dump.
    insns0 = parse(dumps["rtl"])
    call_no, str_pseudo = None, None
    for no, kind, rec in insns0:
        if kind == "call_insn" and "symbol_ref" in rec and re.search(r'symbol_ref[^)]*"strcpy"', rec):
            call_no = no
            # the arg-use block: find (use (reg:SI 5 ...)) and the set feeding it
            m = re.search(r"\(set\s*\(reg:SI 5(?: \w+)?\)\s*\(reg[^)]*SI (\d+)\)", rec) \
                or re.search(r"\(use\s*\(reg:SI 5", rec)
            # str's pseudo: the insn immediately before the call that sets reg 5
            for no2, kind2, rec2 in reversed(insns0[:insns0.index((no, kind, rec))]):
                m2 = re.search(r"\(set\s*\(reg:SI 5(?: \w+)?\)\s*\(reg[^)]*SI (\d+)\)", compact(rec2))
                if m2 and kind2 == "insn":
                    str_pseudo = m2.group(1)
                    break
            break
    print(f"strcpy call insn {call_no}; str pseudo = {str_pseudo}")
    if str_pseudo is None:
        return 1

    # 2. per pass: the entry binds (first 12 insns) + the pre-call window
    for p, path in dumps.items():
        insns = parse(path)
        head = [compact(rec) for _, kind, rec in insns[:14] if kind in ("insn", "call_insn")]
        has_head_bind = any(re.search(rf"\(set\s*\(reg:SI 5(?: \w+)?\)\s*\(reg[^)]*SI {str_pseudo}\)", h) for h in head)
        pre = [(no, compact(rec)) for no, kind, rec in insns
               if kind == "insn" and no < (call_no or 0) + 1
               and re.search(rf"\(set\s*\(reg:SI 5(?: \w+)?\)\s*\(reg[^)]*SI {str_pseudo}\)", compact(rec))]
        # pseudo -> hard reg in this pass's dump text (post-lreg prints hard regs in brackets)
        hardcoded = re.findall(rf"reg:?/?\w*\s*{str_pseudo}\b", open(path, errors='replace').read()[:200000])
        print(f"== {p:7s} insns={len(insns):4d} head-bind(str->a1 in first 14)={has_head_bind}"
              f"  set-a1-str-pseudo sites={len(pre)}")
        if p == "lreg":
            # local-alloc's own commentary about this pseudo
            txt = open(path, errors="replace").read()
            for ln in txt.splitlines():
                if re.search(rf"\b{str_pseudo}\b", ln) and ("reg" in ln or "pref" in ln or "allocat" in ln):
                    print("   LREG:", ln.strip()[:160])
    return 0


if __name__ == "__main__":
    sys.exit(main())

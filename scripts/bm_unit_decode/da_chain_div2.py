#!/usr/bin/env python3
"""da_chain_div2.py - track the div2 region across the -da pass chain.

cron-20261026-1349 NEXT WINDOW item (1) (banked lead of cron-202610261919):
compile a variant with -da at -fno-cse-skip-blocks, then for every pass dump
print the insn window from div1's branch to the fill-loop entry, so the
div2 operand's class membership at its SET and the pass that rewrites the
correction can be read directly.

Usage: python3 /home/z/my-project/scripts/da_chain_div2.py <dump-prefix>
       (dump-prefix e.g. build/judge/div2_v21_expr_on_t.i)
"""
import re
import sys

PASSES = ["rtl", "jump", "cse", "loop", "cse2", "flow", "combine",
          "sched", "lreg", "greg", "sched2", "jump2", "dbr"]

# an insn record in a 2.6.3 dump: starts with "(insn NN" / "(jump_insn NN" /
# "(call_insn NN" / "(code_label NN" / "(barrier NN" / "(note NN"
HEAD = re.compile(r"^\((?:insn|jump_insn|call_insn|code_label|barrier|note)"
                  r"\s+(\d+)\s")


def parse(path):
    """Yield (insn_no, kind, oneline_text) for each top-level insn record."""
    with open(path) as f:
        text = f.read()
    out = []
    i = 0
    n = len(text)
    while i < n:
        nl = text.find("\n", i)
        line = text[i:nl if nl >= 0 else n]
        m = HEAD.match(line)
        if m:
            no = int(m.group(1))
            kind = line[1:line.find(" ", 1)]
            # consume until parens balance
            depth = 0
            j = i
            while j < n:
                c = text[j]
                if c == "(":
                    depth += 1
                elif c == ")":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            rec = text[i:j + 1]
            out.append((no, kind, rec))
            i = j + 1
        else:
            i = nl + 1 if nl >= 0 else n
    return out


def compact(rec):
    """One-line rendering: strip locations/notes, keep the SET/jump expr."""
    rec = re.sub(r"^\((insn|jump_insn|call_insn|code_label|barrier|note)"
                 r"\s+(\d+)\s+(\d+)\s+(\d+)", r"[\2]", rec)
    rec = re.sub(r"\(\(reg:/\w+ ", "(", rec)
    rec = re.sub(r"\(reg:/\w+ ", "(reg ", rec)
    rec = re.sub(r"\(mem:/\w+ ", "(mem ", rec)
    rec = re.sub(r"\(/bin/rel:", "", rec)
    rec = rec.replace("\n", " ")
    rec = re.sub(r"\s+", " ", rec)
    # drop trailing insn-address/location annotations
    rec = re.sub(r"-?\d+ \*?-\d*", "", rec)
    return rec.strip()


def main():
    prefix = sys.argv[1].rstrip(".")
    # anchor: div2's copy (the second "set X (reg Y)" copy of t before the
    # second bgez) - find via the SECOND branchy div: two (ge ...) jumps.
    for p in PASSES:
        path = f"{prefix}.{p}"
        try:
            insns = parse(path)
        except FileNotFoundError:
            continue
        # find jump insns whose pattern is (ge ...) - the branchy signed divs
        ge_jumps = [(no, rec) for no, kind, rec in insns
                    if kind == "jump_insn" and "(ge:" in rec]
        if not ge_jumps:
            print(f"== {p}: no (ge) jumps found")
            continue
        # div1 = first ge jump, div2 = second
        d1, d2 = ge_jumps[0][0], ge_jumps[1][0]
        # window: 4 insns before div2's copy to 6 after div2's product sra/sll
        # print from the insn after div1's sll (the product store) - simpler:
        # print insns from div1's jump through div2's jump + 5
        lo = d1
        d2_idx = next(k for k, (no, _, _) in enumerate(insns) if no == d2)
        window = insns[max(0, d2_idx - 6): d2_idx + 8]
        print(f"== {p}: div1=insn {d1}, div2=insn {d2}; div2 window:")
        for no, kind, rec in window:
            print(f"   {no:4d} {kind:10s} {compact(rec)[:150]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

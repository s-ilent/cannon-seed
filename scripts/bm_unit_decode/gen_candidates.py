#!/usr/bin/env python3
"""gen_candidates.py - generate div2-hunt candidate .c forms from the staged
unit and screen each through div2_screen.py.

The staged file scripts/bm_unit_decode/func_8002ADA0.c carries the current
best modulo block:
    total = t / 0x2000 * 0x2000;
    if (t % 0x2000 != 0)
        total += 0x2000;
Each candidate swaps ONLY that block (everything else byte-identical).
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STAGED = os.path.join(HERE, "func_8002ADA0.c")

BASE_MOD = """    t = size + 0x200;
    total = t / 0x2000 * 0x2000;
    if (t % 0x2000 != 0)
        total += 0x2000;
"""

CANDIDATES = {
    # reproduce the falsified one-div result (harness sanity)
    "e1_v4": """    t = size + 0x200;
    total = t / 0x2000 * 0x2000;
    if (t != t / 0x2000 * 0x2000)
        total += 0x2000;
""",
    # remainder variable kept, division expressions separate
    "e2_remvar": """    t = size + 0x200;
    rem = t % 0x2000;
    total = t / 0x2000 * 0x2000;
    if (rem != 0)
        total += 0x2000;
""",
    # two quotient variables, both kept live
    "e3_qvars": """    t = size + 0x200;
    q1 = t / 0x2000;
    total = q1 * 0x2000;
    q2 = t / 0x2000;
    if (t != q2 * 0x2000)
        total += 0x2000;
""",
    # total starts as a copy of t, divided in place
    "e4_total_copy": """    t = size + 0x200;
    total = t;
    total = total / 0x2000 * 0x2000;
    if (t != total)
        total += 0x2000;
""",
    # re-division inside the if body (across the join label)
    "e5_body_rediv": """    t = size + 0x200;
    total = t / 0x2000 * 0x2000;
    if (t != t / 0x2000 * 0x2000)
        total = t / 0x2000 * 0x2000 + 0x2000;
""",
}

# extra declarations some candidates need
EXTRA_DECLS = {
    "e2_remvar": "    int rem;\n",
    "e3_qvars": "    int q1;\n    int q2;\n",
}


def main():
    src = open(STAGED).read()
    if BASE_MOD not in src:
        print("staged file does not carry the expected modulo block", file=sys.stderr)
        return 2
    want = sys.argv[1:] or list(CANDIDATES)
    for name in want:
        if name not in CANDIDATES:
            print(f"unknown candidate {name}", file=sys.stderr)
            return 2
        body = src.replace(BASE_MOD, CANDIDATES[name])
        if name in EXTRA_DECLS:
            body = body.replace("    int total;\n",
                                "    int total;\n" + EXTRA_DECLS[name])
        out = os.path.join(HERE, f"cand_{name}.c")
        open(out, "w").write(body)
        print(f"\n########## {name} ##########")
        r = subprocess.run([sys.executable, os.path.join(HERE, "div2_screen.py"),
                            out], cwd=os.path.dirname(HERE))
        if r.returncode:
            print(f"({name} screen failed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

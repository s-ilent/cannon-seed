"""sibling_probe.py - word-level distance from every unmatched named unit
to its landed same-name copies in the sibling targets.

twin_probe only reports byte-EXACT twins (0 tree-wide since the 0313b
re-derivation); the near_twin_census only compares unmatched-vs-unmatched.
The missing measurement for the shape-transfer lane (the 34 named
cross-target re-scopes: the landed sibling's C source is the draft, the
question is HOW FAR the local copy sits from it) is this: diff the local
retail bytes against every landed same-name sibling's retail bytes at
word granularity. diffwords 0 is twin_probe's report (already
exhausted); small counts are the landed C source adapting by that many
word edits - relocation hi/lo pairs pointing at per-target VAs are the
expected flavor and cost nothing in a real landing.

Usage: sibling_probe.py [target ...]     (default: all eight)
Output: stdout summary + build/sibling_probe.txt, one row per
(target, name, sibling) triple, sorted by diffwords.
Gated (cron-20261022-0928): each target must pass pair_report.input_gates
(witnessed baseline + build ELF consistent with the committed yaml) or it
is skipped as unwitnessed - retail bytes off a woven baseline are
artifacts.
Exit: 0 report produced (possibly partial); 2 every requested target
refused.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pair_report import (REPO, baseline_bytes, elf_funcs,  # noqa: E402
                         input_gates, is_matched)

TARGETS = ["slps_00270", "sces_00269", "mainmenu_jp", "mainmenu_eu",
           "g3_jp", "g3_eu", "g3org_jp", "g3org_eu"]
MIN_SIZE = 0x10   # the AverageSZ3/SZ4 class lives at 0x10; leaves below
UNNAMED = re.compile(r"^(func_|D_)")


def word_diff(a, b):
    """(#differing words, total words compared, [first offsets])."""
    n = min(len(a), len(b)) // 4
    off = []
    for i in range(n):
        if a[i * 4:i * 4 + 4] != b[i * 4:i * 4 + 4]:
            off.append(i * 4)
    return len(off), n, off


def main():
    want = sys.argv[1:] or TARGETS
    refused = []
    fresh = []
    for t in want:
        ok, problems = input_gates(t)
        if not ok:
            refused.append(t)
            print(f"{t}: REFUSED - {'; '.join(problems)}")
            continue
        fresh.append(t)
    if not fresh:
        print("\nall requested targets REFUSED - no sibling report. Run the "
              "disc-return sequence first (witness 8/8 STRICT).",
              file=sys.stderr)
        return 2

    # the landed registry: every same-name unit that renders as C in its
    # own target (the shape-transfer draft pool)
    landed = {}
    for t in TARGETS:
        elf = os.path.join(REPO, f"build/{t}.elf")
        if not os.path.exists(elf):
            continue
        for name, (va, size) in elf_funcs(elf).items():
            if is_matched(t, name, va):
                landed.setdefault(name, []).append((t, va, size))

    rows = []
    for t in fresh:
        elf = os.path.join(REPO, f"build/{t}.elf")
        for name, (va, size) in elf_funcs(elf).items():
            if is_matched(t, name, va) or UNNAMED.match(name):
                continue
            if size < MIN_SIZE:
                continue
            a = baseline_bytes(t, va, size)
            if a is None:
                continue
            for st, sva, ssize in landed.get(name, []):
                b = baseline_bytes(st, sva, min(ssize, size))
                if b is None:
                    continue
                dw, n, off = word_diff(a, b)
                rows.append((dw, n, t, name, va, size, st, sva, ssize,
                             off[:6]))

    rows.sort(key=lambda r: (r[0], r[2], r[3]))
    for dw, n, t, name, va, size, st, sva, ssize, off in rows:
        o = " ".join(f"{x:#x}" for x in off)
        print(f"{t:12s} {name:28s} {va:08X} sz={size:#05x}  "
              f"vs {st:12s} dw={dw:3d}/{n}  {o}")
    print(f"\n{len(rows)} unmatched-named-vs-landed-sibling rows; "
          f"dw=0 means byte-identical (twin_probe's class)")
    with open(os.path.join(REPO, "build/sibling_probe.txt"), "w") as f:
        for dw, n, t, name, va, size, st, sva, ssize, off in rows:
            f.write(f"{t} {name} {va:08X} {size} {st} {sva:08X} {ssize} "
                    f"dw={dw} {n} "
                    + " ".join(f"{x:x}" for x in off) + "\n")
    if refused:
        print(f"\n({len(refused)} target(s) refused: {', '.join(refused)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""audit_flip_clashes.py - the woven-name/true-position clash census.

Post-extract instrument (the precise one; a yaml-side census over-counts
because it cannot see which context symbols spimdisasm actually emits).

Mechanism (docs/TASKS.md, window cron-20261018-2219): the de-frame flip
moved every row to its TRUE file offset while the row names keep their
woven-era spelling. splat exports each asm row's name as a glabel at the
row's true VMA; spimdisasm additionally emits a dlabel for every context
symbol inside a row's span (auto-created entries from the retail bytes'
own jal/j/branch encodings at TRUE runtime addresses, plus identity-true
symbols-file entries passed through verbatim). In the woven view row name
== row position, so the row label and the same-address context symbol
merged into one definition. In the true view, a row whose woven-era name
encodes an address that now falls inside a DIFFERENT row's span gets its
name emitted TWICE at two VMAs - the row's glabel and the owning row's
dlabel - and ld fails with "multiple definition" (glabel first-defined,
dlabel the duplicate).

Rule: a name clashes iff it is BOTH exported as a glabel by one .s file
AND placed as a dlabel inside a DIFFERENT .s file of the same target.
Same-file glabel+dlabel pairs are splat extract-time duplicates and are
reported as errors (the extract should be clean before this tool runs).

Usage:
    python3 tools/audit_flip_clashes.py <target> [target ...]

Targets: slps_00270 sces_00269 mainmenu_jp mainmenu_eu g3_jp g3_eu
         g3org_jp g3org_eu.  Reads the git-ignored split output only;
         writes nothing.  Run `make extract TARGET=<t>` first.
"""

import re
import sys
from pathlib import Path

GLABEL = re.compile(r"^\s*glabel\s+(\S+)")
# alabel (macro.inc) = .global + .type + label + .aent: a real global
# definition emitted for functions spimdisasm finds inside another row's
# true span (the func_800253F8 class the first census missed - the link
# witnessed it as a multiple definition the glabel/dlabel regex never saw).
# glabel-class for census purposes.
ALABEL = re.compile(r"^\s*alabel\s+(\S+)")
DLABEL = re.compile(r"^\s*dlabel\s+(\S+)")


def source_dirs(target: str):
    """The .s source dirs for a target (repo-root asm/, NOT build/asm/)."""
    if target == "slps_00270":
        # primary target: asm/nonmatchings + asm/data (siblings of the
        # per-target dirs, which belong to the other seven targets)
        return [Path("asm/nonmatchings"), Path("asm/data")]
    t = Path("asm") / target
    return [t / "nonmatchings", t / "data"]


def collect(roots):
    """Return (glabels, dlabels): name -> set of .s files (relative to asm/)."""
    glabels: dict[str, set] = {}
    dlabels: dict[str, set] = {}
    files = 0
    paths = []
    for root in roots:
        paths.extend(root.rglob("*.s"))
    for p in sorted(paths):
        # rglob("*.s") already skips .s.err/.s.aserr/.s.o (different suffixes)
        rel = str(p.relative_to("asm"))
        files += 1
        with p.open(errors="replace") as fh:
            for line in fh:
                m = GLABEL.match(line)
                if m:
                    glabels.setdefault(m.group(1), set()).add(rel)
                    continue
                m = ALABEL.match(line)
                if m:
                    glabels.setdefault(m.group(1), set()).add(rel)
                    continue
                m = DLABEL.match(line)
                if m:
                    dlabels.setdefault(m.group(1), set()).add(rel)
    return glabels, dlabels, files


def audit(target: str) -> int:
    dirs = [d for d in source_dirs(target) if d.is_dir()]
    if not dirs:
        print(f"== {target}: NO SOURCE DIRS under asm/ (run make extract TARGET={target}) ==")
        return 0
    glabels, dlabels, files = collect(dirs)
    errors = 0
    clashes = []
    for name in sorted(set(glabels) & set(dlabels)):
        gf, df = glabels[name], dlabels[name]
        if gf & df:
            print(f"[{target}] ERROR same-file glabel+dlabel: {name} in {sorted(gf & df)}")
            errors += 1
        if df - gf:
            clashes.append((name, sorted(gf), sorted(df - gf)))
    # secondary sanity: cross-file duplicate glabels (two rows same name)
    for name, gf in sorted(glabels.items()):
        if len(gf) > 1:
            print(f"[{target}] ERROR cross-file glabel dupe: {name} in {sorted(gf)}")
            errors += 1
    print(f"== {target}: {len(clashes)} clashes over {files} .s files"
          + (f" ({errors} ERRORS)" if errors else "") + " ==")
    for name, gf, df in clashes:
        print(f"  {name}: glabel in {gf[0]} ; dlabel in {', '.join(df)}")
    return len(clashes)


def main() -> None:
    targets = sys.argv[1:]
    if not targets:
        print(__doc__)
        sys.exit(1)
    total = 0
    for t in targets:
        total += audit(t)
    print(f"TOTAL {total} clashes")


if __name__ == "__main__":
    main()

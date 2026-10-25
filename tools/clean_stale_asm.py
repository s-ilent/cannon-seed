#!/usr/bin/env python3
"""clean_stale_asm.py - remove .s files no longer listed in any yaml.

Every `make extract` writes the current target's split; layouts shrink
and rename across scans, so files the CURRENT yamls no longer reference
would still sit in asm/ and get compiled (build.sh assembles the whole
directory) - stale objects break the build or, worse, silently pollute
it. This tool deletes every tracked-or-untracked .s file under each
yaml's asm_path that no yaml row of the file's consuming type names
(union rule: a name shared by two targets in the same directory
survives; the row-type law below).

ROW-TYPE LAW (cron-202610251904): the reference must be of the row type
that consumes the file - a plain .s is alive iff an ASM row names it, a
.data.s iff a DATA row names it. The pre-law rule was type-blind: a
name referenced only by a c ROW (the landed-flip class - g3_eu's
func_8004D704 flipped to src/func_8004D704.c while its whole-row
disassembly stayed behind) kept its dead .s forever, and the
glabel_collision_pass renamed it on every extract - the standing
restore-to-HEAD dance. Type-aware, the flip's leftover dies with the
sweep like every other stale file.

Usage: python3 tools/clean_stale_asm.py
       python3 tools/clean_stale_asm.py --filter-status   (pre-commit mode:
           reads `git diff --cached --name-status` lines on stdin, passes
           through every line except deletions of stale paths, which are
           dropped so the hook can allow legitimate cleanups)
"""
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTRY = re.compile(r"-\s*\[(0x[0-9A-Fa-f]+),\s*(\w+),\s*([\w.]+)\]")
SUFFIXES = (".data.s", ".s")


def stem(path: str) -> str:
    name = os.path.basename(path)
    for suf in SUFFIXES:
        if name.endswith(suf):
            return name[: -len(suf)]
    return name


def yaml_ref_dirs() -> dict:
    """{asm_path: {'asm': names, 'data': names, 'any': names}} by yaml.

    'asm' collects every ASM-row label (the consumers of plain .s
    files), 'data' every DATA-row label (the consumers of .data.s
    files), 'any' both plus the c rows (kept for the union-rule
    reporting and any future consumer). Comment lines never reference:
    the MIGRATE-DROPPED rows are commented out of the yamls and their
    stale files are exactly what this tool exists to remove
    (cron-20261019-0319 fix).
    """
    dirs = {}
    for y in sorted(REPO.glob("config/splat.*.yaml")):
        text = y.read_text()
        m = re.search(r"^\s*asm_path:\s*(\S+)", text, re.M)
        if not m:
            continue
        d = m.group(1).rstrip("/")
        names = dirs.setdefault(d, {"asm": set(), "data": set(),
                                    "any": set()})
        for ln in text.splitlines():
            if ln.lstrip().startswith("#"):
                continue
            em = ENTRY.search(ln)
            if em:
                typ, lbl = em.group(2), em.group(3)
                names["any"].add(lbl)
                if typ == "asm":
                    names["asm"].add(lbl)
                elif typ == "data":
                    names["data"].add(lbl)
    return dirs


def file_kind(rel: str) -> str:
    """The row type that consumes this .s path: 'data' or 'asm'."""
    return "data" if rel.endswith(".data.s") else "asm"


def is_stale(rel: str, dirs: dict) -> bool:
    """The type-aware union rule for one asm/-relative path."""
    d = next((k for k in dirs if rel.startswith(k.rstrip("/") + "/")), None)
    if d is None:
        return False
    return stem(rel) not in dirs[d][file_kind(rel)]


def stale_names() -> set:
    """Union rule: every .s file under any yaml asm_path that no yaml
    lists with the file's consuming row type."""
    dirs = yaml_ref_dirs()
    stale = set()
    for d in sorted(dirs):
        base = REPO / d
        if not base.exists():
            continue
        for p in base.rglob("*.s"):
            rel = p.relative_to(REPO).as_posix()
            if is_stale(rel, dirs):
                stale.add(rel)
    return stale


def filter_status() -> int:
    """Pass through name-status lines except stale-path deletions.

    Staged deletions are already gone from the working tree, so the
    check compares each deleted path's stem against its directory's
    yaml references directly (the type-aware union rule) instead of
    enumerating files on disk.
    """
    dirs = yaml_ref_dirs()
    for ln in sys.stdin.read().splitlines():
        parts = ln.split("\t", 1)
        if len(parts) == 2 and parts[0] == "D":
            if is_stale(parts[1], dirs):
                continue
        print(ln)
    return 0


def main() -> int:
    if "--filter-status" in sys.argv:
        return filter_status()
    dirs = yaml_ref_dirs()
    stale = []
    for d in sorted(dirs):
        base = REPO / d
        if not base.exists():
            continue
        for p in base.rglob("*.s"):
            rel = p.relative_to(REPO).as_posix()
            if is_stale(rel, dirs):
                stale.append(rel)
    if not stale:
        print("clean_stale_asm: nothing stale")
        return 0
    for rel in sorted(stale):
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", rel],
            cwd=REPO, capture_output=True).returncode == 0
        if tracked:
            subprocess.run(["git", "rm", "-qf", rel], cwd=REPO, check=True)
        else:
            (REPO / rel).unlink()
    print(f"clean_stale_asm: removed {len(stale)} stale .s files")
    return 0


if __name__ == "__main__":
    sys.exit(main())

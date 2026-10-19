#!/usr/bin/env python3
"""clean_stale_asm.py - remove .s files no longer listed in any yaml.

Every `make extract` writes the current target's split; layouts shrink
and rename across scans, so files the CURRENT yamls no longer reference
would still sit in asm/ and get compiled (build.sh assembles the whole
directory) - stale objects break the build or, worse, silently pollute
it. This tool deletes every tracked-or-untracked .s file under each
yaml's asm_path whose name is not listed in ANY target yaml (union rule:
a name shared by two targets in the same directory survives).

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
    """{asm_path: set of segment names referenced by any yaml}."""
    dirs = {}
    for y in sorted(REPO.glob("config/splat.*.yaml")):
        text = y.read_text()
        m = re.search(r"^\s*asm_path:\s*(\S+)", text, re.M)
        if not m:
            continue
        d = m.group(1).rstrip("/")
        names = dirs.setdefault(d, set())
        for ln in text.splitlines():
            # comment lines never reference: the MIGRATE-DROPPED rows are
            # commented out of the yamls and their stale files are exactly
            # what this tool exists to remove (cron-20261019-0319 fix).
            if ln.lstrip().startswith("#"):
                continue
            em = ENTRY.search(ln)
            if em:
                names.add(em.group(3))
    return dirs


def stale_names() -> set:
    """Union rule: every .s file under any yaml asm_path that no yaml lists."""
    dirs = yaml_ref_dirs()
    stale = set()
    for d, names in sorted(dirs.items()):
        base = REPO / d
        if not base.exists():
            continue
        for p in base.rglob("*.s"):
            rel = p.relative_to(REPO).as_posix()
            if stem(rel) not in names:
                stale.add(rel)
    return stale


def filter_status() -> int:
    """Pass through name-status lines except stale-path deletions.

    Staged deletions are already gone from the working tree, so the
    check compares each deleted path's stem against its directory's
    yaml references directly (the union rule) instead of enumerating
    files on disk.
    """
    dirs = yaml_ref_dirs()
    for ln in sys.stdin.read().splitlines():
        parts = ln.split("\t", 1)
        if len(parts) == 2 and parts[0] == "D":
            p = parts[1]
            d = next((k for k in dirs if p.startswith(k.rstrip("/") + "/")), None)
            if d is not None and stem(p) not in dirs[d]:
                continue
        print(ln)
    return 0


def main() -> int:
    if "--filter-status" in sys.argv:
        return filter_status()
    dirs = {}  # asm_path -> set of names referenced by any yaml
    for y in sorted(REPO.glob("config/splat.*.yaml")):
        text = y.read_text()
        m = re.search(r"^\s*asm_path:\s*(\S+)", text, re.M)
        if not m:
            continue
        d = m.group(1).rstrip("/")
        names = dirs.setdefault(d, set())
        for ln in text.splitlines():
            if ln.lstrip().startswith("#"):
                continue
            em = ENTRY.search(ln)
            if em:
                names.add(em.group(3))
    stale = []
    for d, names in sorted(dirs.items()):
        base = REPO / d
        if not base.exists():
            continue
        for p in base.rglob("*.s"):
            rel = p.relative_to(REPO).as_posix()
            if stem(rel) not in names:
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

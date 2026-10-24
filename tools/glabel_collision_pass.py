#!/usr/bin/env python3
"""glabel_collision_pass.py - rename interior-default glabels that collide
with linked C symbols (the interior-default-glabel class).

THE CLASS (witnessed on the scan-verified campaign, parked targets
g3org_jp / mainmenu_eu / mainmenu_jp): spimdisasm default-names an interior
block start `func_<linear-vram>` when no symbols entry claims that vram,
and the spelled name can equal a symbol a preserved C file defines
(g3org_jp func_800258F4 inside func_800250FC.s vs src/func_800258F4.c;
mainmenu_eu func_80037A0C + func_80037C1C inside func_80034EBC.s vs the
functions in src/func_800379E4.c). The row-start name-uniqueness registry
does not cover interior labels; the link dies with `multiple definition`.

THE FIX SHAPE (documented in TASKS.md, "the window carve campaign"):
"extract needs a post-pass renaming interior default glabels that collide
with linked symbols." This tool is that post-pass. It runs AFTER
`make extract` (wired into the Makefile's extract target) and is a strict
no-op on clean trees - proven against the five scan-verified targets'
committed asm before it was trusted.

CLAIM PRIORITY (mirrors the row-start law "preserved rows claim their
names first"):
  1. The C side owns the name: the c row's own name (by yaml
     construction) plus every identifier the row's src file DEFINES -
     column-0 declarations of the census name shapes (func_/D_ + 8 hex).
     `extern` lines and column-0 function PROTOTYPES (`... name(...);`)
     are references, not definitions, and are excluded: renaming the asm
     side of a mere reference would dangle it.
  2. Every asm glabel carrying a C-owned name is a loser and takes the
     first free dotted-suffix name `<name>_2`, `_3`, ... - checked
     against every asm glabel, the whole C-side set and the symbols
     file, so the new name is unique in the link.

SCOPE LAW (evidence-driven, see the no-op proof): asm-asm duplicate
glabels are TOLERATED by the pipeline - the verified g3_eu tree links
GREEN byte-exact with hundreds of them (interior sub-block labels
spelled identically to a standalone row's label; the live build's
ld.err carries zero `multiple definition`). Renaming there would CHANGE
verified trees. Only the C-collision class is witnessed-broken (the
campaign's parked targets died on it), so it is the only class this
pass fires on.

REWRITE SEMANTICS: a rename rewrites the loser file's own text only -
its `glabel`/`endlabel` pair, its operands, its comments - via one
combined word-boundary regex per file. References from OTHER files stay
on the plain name, which now binds to the surviving definition (the C
symbol for class 1, the keeper for class 2) - exactly what those
references always meant. A cross-file reference that truly targeted a
renamed interior block was already a broken link (multiple definition);
the oracle will surface any such case loudly. The `nonmatching <name>,
<size>` metadata headers are tool-owned report input and are never
touched.

USAGE:
    python3 tools/glabel_collision_pass.py TARGET [--dry-run]

Exit codes: 0 = clean or renamed (tree consistent); 1 = usage/IO error.
Idempotent: a second run over a passed tree reports zero collisions.
"""

import argparse
import re
import sys
from pathlib import Path

# A C-side definition: column-0 declaration of a shaped identifier, not an
# extern, not a prototype. `void func_80037A0C(void) {`,
# `static s32 D_8004A2B0[4] = {...}`.
C_DEF = re.compile(
    r"^(?:static\s+)?[A-Za-z_][\w\s\*]*?\b((?:func|D)_[0-9A-Fa-f]{8})\b\s*(\(|\[|=|,|;)"
)
# yaml subsegment row: - [0xROM, type, name]  # optional comment
YAML_ROW = re.compile(r"^\s*-\s*\[0x([0-9A-Fa-f]+),\s*(\w+),\s*([^\]\s]+)\]")


def parse_yaml_rows(yaml_path):
    """Ordered (name, type) list from the splat config's subsegments."""
    rows = []
    for line in yaml_path.read_text(errors="replace").splitlines():
        m = YAML_ROW.match(line)
        if m:
            rows.append((m.group(3), m.group(2)))
    return rows


def is_prototype(line):
    """Column-0 `... name(...);` - a declaration, not a definition."""
    stripped = line.rstrip()
    return stripped.endswith(";") and "=" not in stripped


def c_side_symbols(repo, target, c_rows):
    """Every symbol a preserved C file defines (never renamed)."""
    claimed = set(c_rows)
    for name in c_rows:
        src = repo / "src" / f"{name}.c"
        if not src.exists():
            continue
        for line in src.read_text(errors="replace").splitlines():
            if line.lstrip().startswith("extern"):
                continue  # a reference, not a definition
            if is_prototype(line):
                continue  # a declaration, not a definition
            m = C_DEF.match(line)
            if m:
                claimed.add(m.group(1))
    return claimed


def asm_files(repo, target, asm_path):
    """The target's asm tree, from the yaml's own asm_path (the build's
    source of truth - the primary target splits to asm/nonmatchings,
    the others to asm/<t>/nonmatchings)."""
    base = repo / asm_path
    files = []
    if base.name == "nonmatchings":
        data = base.parent / "data"
        if data.exists():
            files.extend(sorted(p for p in data.rglob("*.s") if p.is_file()))
    else:
        data = base.parent / "data"
        if data.exists():
            files.extend(sorted(p for p in data.rglob("*.s") if p.is_file()))
    if base.exists():
        files.extend(sorted(p for p in base.rglob("*.s") if p.is_file()))
    return files


def collect_glabels(files):
    """name -> [(path, stem), ...] for every `glabel N`; caches texts."""
    defs = {}
    texts = {}
    for path in files:
        text = path.read_text(errors="replace")
        texts[path] = text
        for line in text.splitlines():
            s = line.strip()
            if s.startswith("glabel "):
                name = s.split()[1]
                defs.setdefault(name, []).append(path)
    return defs, texts


def symbols_file_names(repo, target):
    """Identifiers already claimed by config/symbols.<t>.txt."""
    path = repo / "config" / f"symbols.{target}.txt"
    names = set()
    if path.exists():
        for m in re.finditer(
            r"\b([A-Za-z_][A-Za-z0-9_]*)\b", path.read_text(errors="replace")
        ):
            names.add(m.group(1))
    return names


def choose_suffix(base, taken):
    k = 2
    while f"{base}_{k}" in taken:
        k += 1
    return f"{base}_{k}"


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("target")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    repo = Path(__file__).resolve().parent.parent
    yaml_path = repo / "config" / f"splat.{args.target}.yaml"
    if not yaml_path.exists():
        print(f"glabel_pass: no splat config at {yaml_path}", file=sys.stderr)
        return 1

    import yaml as yaml_mod

    opts = yaml_mod.safe_load(yaml_path.read_text())["options"]
    asm_path = str(opts["asm_path"]).rstrip("/")
    rows = parse_yaml_rows(yaml_path)
    c_rows = [name for name, typ in rows if typ == "c"]
    claimed = c_side_symbols(repo, args.target, c_rows)
    files = asm_files(repo, args.target, asm_path)
    if not files:
        print(f"glabel_pass: no asm tree at {asm_path}; nothing to pass.")
        return 0

    defs, texts = collect_glabels(files)
    taken = set(defs) | claimed | symbols_file_names(repo, args.target)

    # The one collision class: an asm-defined glabel the C side defines
    # (the witnessed link-killer). per_file: path -> {old: new}.
    per_file = {}
    report = []
    for name in sorted(defs):
        if name not in claimed:
            continue
        for path in defs[name]:
            new = choose_suffix(name, taken)
            taken.add(new)
            per_file.setdefault(path, {})[name] = new
            report.append((name, new, path, "collides with a linked C symbol"))

    if not report:
        print(f"glabel_pass: {args.target} clean - 0 collisions.")
        return 0

    # Apply: one combined regex per loser file, word-boundary exact.
    changed = 0
    for path, mapping in per_file.items():
        pattern = re.compile(
            r"\b(" + "|".join(re.escape(o) for o in sorted(mapping, key=len, reverse=True)) + r")\b"
        )
        out_lines = []
        touched = False
        for line in texts[path].splitlines():
            if line.strip().startswith("nonmatching "):
                out_lines.append(line)
                continue
            new_line = pattern.sub(lambda m: mapping[m.group(1)], line)
            if new_line != line:
                touched = True
            out_lines.append(new_line)
        if touched:
            changed += 1
            if not args.dry_run:
                path.write_text("\n".join(out_lines) + "\n")

    for old, new, path, reason in report:
        print(f"glabel_pass: {args.target} {old} -> {new} ({reason})")
    print(
        f"glabel_pass: {args.target} {len(report)} rename(s) across "
        f"{changed} file(s){' [dry-run]' if args.dry_run else ''}."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

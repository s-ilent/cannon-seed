#!/usr/bin/env python3
"""Generic curated port: restore every committed-symbols claim the fresh
scan regen drops, into symbols.curated.txt.

For each target: diff the committed (git HEAD) symbols file's generated
function+data blocks against the fresh regen; every (name, addr) pair the
committed file carries and the fresh file lacks is a port candidate -
provided the target's curated section does not already carry the name (at
any address) or the address (under any name). Collisions are reported and
skipped (the curated placement supersedes), everything else is inserted
verbatim at the end of the target's curated section with a provenance
note.

Usage: python3 scripts/port_symbols_to_curated.py <target> [<target>...]
"""
import re
import subprocess
import sys

PATH = "config/symbols.curated.txt"
NOTE = ("ported verbatim from the committed symbols file "
        "(cron-202611062346 scan-drift unit, the 2adb7d81 port class)")
ROW_RE = re.compile(r"^([A-Za-z_][\w.]*)\s*=\s*(0x[0-9A-Fa-f]+)$")
# Auto names (the walk's own func_XXXXXXXX / dotted-row spellings) die with
# their rows legitimately - only semantic (hand-attested) names port.
AUTO_NAME = re.compile(r"^(func|data)_[0-9A-Fa-f]{8}(\.\d+)?$")


def block_pairs(text, begin_marker):
    out = set()
    in_block = False
    for ln in text.splitlines():
        if begin_marker in ln:
            in_block = True
            continue
        if in_block and "// END GENERATED" in ln:
            break
        if in_block:
            body = ln.strip().split(";")[0].strip()
            m = ROW_RE.match(body)
            if m:
                out.add((m.group(1), m.group(2).replace("X", "x")))
    return out


def committed(target):
    txt = subprocess.run(
        ["git", "show", f"HEAD:config/symbols.{target}.txt"],
        capture_output=True, text=True, check=True).stdout
    return block_pairs(txt, "// BEGIN GENERATED FUNCTION SYMBOLS") | \
        block_pairs(txt, "// BEGIN GENERATED DATA SYMBOLS")


def fresh(target):
    txt = open(f"config/symbols.{target}.txt").read()
    return block_pairs(txt, "// BEGIN GENERATED FUNCTION SYMBOLS") | \
        block_pairs(txt, "// BEGIN GENERATED DATA SYMBOLS")


def main(argv):
    targets = argv[1:]
    lines = open(PATH).read().splitlines(keepends=True)
    scope = None
    names, addrs = {}, {}
    for ln in lines:
        mt = re.match(r"\s*//\s*target:\s*(\w+)", ln)
        if mt:
            scope = mt.group(1)
            continue
        m = re.match(r"\s*([A-Za-z_]\w*)\s*=\s*(0x[0-9A-Fa-f]+)", ln)
        if m and scope and not ln.lstrip().startswith("//"):
            names.setdefault(scope, set()).add(m.group(1))
            addrs.setdefault(scope, set()).add(m.group(2).replace("X", "x"))

    total = 0
    ins = {}
    for t in targets:
        cset, fset = committed(t), fresh(t)
        ports = sorted(cset - fset)
        skipped = 0
        for n, a in ports:
            if AUTO_NAME.match(n):
                skipped += 1
                continue
            if n in names.get(t, set()):
                print(f"SKIP {t} {n} {a}: name already in curated")
                skipped += 1
                continue
            if a in addrs.get(t, set()):
                print(f"SKIP {t} {n} {a}: address already named in curated")
                skipped += 1
                continue
            ins.setdefault(t, []).append(f"{n} = {a.lower()[:2] + a[2:]}; // {NOTE}\n")
            names.setdefault(t, set()).add(n)
            addrs.setdefault(t, set()).add(a)
            total += 1
        print(f"{t}: {len(ports)} missing, {skipped} skipped")

    if not total:
        print("nothing to port")
        return 0

    out = []
    scope = None
    for ln in lines:
        mt = re.match(r"\s*//\s*target:\s*(\w+)", ln)
        if mt and scope is not None:
            out.extend(ins.pop(scope, []))
            out.append("\n")
        scope = mt.group(1) if mt else scope
        out.append(ln)
    if scope is not None:
        out.extend(ins.pop(scope, []))
    open(PATH, "w").write("".join(out))
    print(f"ported {total} curated entries")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

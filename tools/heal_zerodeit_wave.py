#!/usr/bin/env python3
"""Zero-edit heal wave executor (the motion behind preflight_heal_wave's ZEROEDIT class).

For every row the machine pre-flight classifies ZEROEDIT, execute the heal:

  asm/data rows  git mv the drifted-named file to the pin name; the yaml row
                 re-spells to the pin. Zero content edits (the committed file
                 already spells the pin in its glabel/definition).
  c rows         two sub-cases, decided by destination collision:
                 - pin-named file absent: same git mv + yaml re-spell motion.
                 - pin-named file exists (a shared top-level src/ copy another
                   target's yaml already uses): NOT a rename - that is the
                   ddc7702d shared-copy merge class (diff-gate, git rm the
                   drifted duplicate, yaml-only re-spell). Routed to a report,
                   never renamed here.

Every row is re-asserted from the tree before any mutation (the pre-flight
verdict is recomputed, not trusted): file exists, content spells the pin and
not the drifted name, the drifted token appears exactly once in the target's
own yaml and nowhere in any other yaml, and the destination is free. Any
failed assertion aborts the whole run BEFORE the first mutation.

Usage: python3 tools/heal_zerodeit_wave.py TARGET [--apply]
Without --apply: dry-run, assertions only, no tree change.
"""
import re
import subprocess
import sys
from pathlib import Path

REPO = Path("/home/z/my-project/cannon-seed")
sys.path.insert(0, str(REPO / "tools"))
import preflight_heal_wave as pf  # noqa: E402

PIN_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def sh(*args):
    return subprocess.run(args, cwd=REPO, capture_output=True, text=True)


def yaml_token_count(target, token):
    hits = sh("git", "grep", "-c", "--", token, f"config/splat.{target}.yaml").stdout.strip()
    return int(hits.split(":")[1]) if hits else 0


def foreign_yaml_hits(target, token):
    """FOREIGN splat yamls spelling the token: for a c row at shared top-level
    src/ this means the file is genuinely shared - never rename it."""
    out = sh("git", "grep", "-l", "--", token, "config/").stdout.splitlines()
    own = f"config/splat.{target}.yaml"
    sym = f"config/symbols.{target}.txt"
    return [
        h
        for h in out
        if h != own
        and h != sym
        and h.startswith("config/splat.")
    ]


def row_pattern(off, kind, name):
    return re.compile(rf"^(\s*-\s*\[0x{off:X},\s*{kind},\s*){re.escape(name)}(\s*\].*)$")


def main():
    args = sys.argv[1:]
    apply = "--apply" in args
    excludes = set()
    for a in args:
        if a.startswith("--exclude="):
            excludes.add(int(a.split("=", 1)[1], 16))
    targets = [a for a in args if not a.startswith("--")]
    if not targets:
        print("usage: heal_zerodeit_wave.py TARGET [--apply]")
        return 2
    failures = []
    renames, merges = [], []
    for target in targets:
        rows = pf.load(target)
        for off, kind, name, tva, pin in rows:
            verdict, why = pf.classify(target, off, kind, name, tva, pin)
            if verdict != "ZEROEDIT":
                continue
            if off in excludes:
                print(f"  EXCLUDED (by flag): {target} 0x{off:05X} {kind} {name} -> {pin}")
                continue
            tag = f"{target} 0x{off:05X} {kind} {name} -> {pin}"
            if not PIN_NAME.match(pin):
                failures.append(f"{tag}: pin name not a sane identifier")
                continue
            fpath = next((c for c in pf.file_candidates(target, kind, name, pin) if c.exists()), None)
            if fpath is None:
                failures.append(f"{tag}: drifted file vanished since pre-flight")
                continue
            # destination free at EVERY candidate location (rename collision guard)
            dest_pin_file = None
            for dest in pf.file_candidates(target, kind, pin, pin):  # noqa: E501
                if dest.exists():
                    dest_pin_file = dest
            if dest_pin_file is not None:
                if kind == "c" and dest_pin_file == REPO / "src" / f"{pin}.c":
                    merges.append(f"{tag}: shared-copy merge candidate ({dest_pin_file.name} exists)")
                else:
                    failures.append(f"{tag}: destination exists {dest_pin_file}")
                continue
            text = fpath.read_text()
            if kind == "asm":
                g = re.search(r"^glabel\s+(\S+)", text, re.M)
                if g is None or g.group(1) != pin:
                    failures.append(f"{tag}: glabel mismatch since pre-flight")
                    continue
            if re.search(rf"\b{re.escape(name)}\b", text):
                failures.append(f"{tag}: drifted token appeared in content")
                continue
            if not re.search(rf"\b{re.escape(pin)}\b", text):
                failures.append(f"{tag}: pin missing from content")
                continue
            if yaml_token_count(target, name) != 1:
                failures.append(f"{tag}: yaml token count != 1 (fragment sibling or rider; own pass)")
                continue
            fyh = foreign_yaml_hits(target, name)
            if fyh and kind == "c":
                # shared top-level src/ file another target's yaml also names:
                # never rename; merge if the pin-named shared file exists, else own pass
                if dest_pin_file is not None:
                    merges.append(f"{tag}: shared-copy merge candidate (foreign yaml names it: {fyh})")
                else:
                    failures.append(f"{tag}: foreign yaml names the shared file, no pin file: {fyh}")
                continue
            # asm foreign-config hits are the same-spelled-neighbor law: each
            # target's own row at its own VA, untouched by this target's rename
            ytext = (REPO / "config" / f"splat.{target}.yaml").read_text()
            if not any(row_pattern(off, kind, name).match(l) for l in ytext.splitlines()):
                failures.append(f"{tag}: yaml row line does not match the expected shape")
                continue
            renames.append((target, off, kind, name, pin, fpath))

    if failures:
        print(f"ABORT - {len(failures)} assertion failure(s), no mutation performed:")
        for f in failures:
            print("  FAIL:", f)
        return 1

    print(f"assertions clean: {len(renames)} rename(s), {len(merges)} merge candidate(s)")
    for m in merges:
        print("  MERGE:", m)
    if not apply:
        print("dry-run complete (no --apply)")
        return 0

    for target, off, kind, name, pin, fpath in renames:
        r = sh("git", "mv", str(fpath), str(fpath.parent / (pin + fpath.suffix)))
        if r.returncode != 0:
            print(f"MID-RUN git mv failure at {name}: {r.stderr}")
            return 1
        ypath = REPO / "config" / f"splat.{target}.yaml"
        lines = ypath.read_text().splitlines(keepends=True)
        pat = row_pattern(off, kind, name)
        hit = False
        for i, line in enumerate(lines):
            if pat.match(line):
                lines[i] = pat.sub(rf"\g<1>{pin}\g<2>", line)
                hit = True
        if not hit:
            print(f"MID-RUN yaml row not found for 0x{off:X} {name}")
            return 1
        ypath.write_text("".join(lines))
        print(f"  healed {target} 0x{off:05X} {kind} {name} -> {pin}")
    print(f"applied {len(renames)} rename heal(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

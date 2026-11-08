#!/usr/bin/env python3
"""Machine pre-flight for a pin-first heal wave (generalized; cron-202611082317).

The sces_00269 zero-edit campaign's pre-flight instrument, rebuilt in-repo
and generalized to any target after the all-target census sweep found the
same drifted-row classes on the seven non-sces targets (~1,325 healable).

For each HEALABLE row (drifted auto-name + pin at the true VA, per
tools/pin_first_census.py), classify:

  ZEROEDIT   file exists @drifted-name, content already spells the pin
             (asm/data glabel; c content mention), and the drifted token
             appears ONLY in the target's own yaml row + the file's path
             (+ the target's generated symbols layer). The wave is one
             git mv + one yaml row re-spell; nothing else.
  RIDER      like ZEROEDIT but the drifted token has N extra reference
             hits inside the TARGET'S OWN layers (caller jals, comments):
             the wave re-spells those hits in the same motion (they are
             enumerated in the manifest).
  RESPELL    the file content spells the drifted name (definition/glabel):
             the wave re-spells content + renames (the 0118aa35 shape).
  NOFILE     no per-target file layer (the shared-copy class): the wave
             is a yaml-only re-spell; extract-stability must be watched.
  EXCLUDE    anything else (unexpected state) - never touch without a
             human look.

SELF-class rows (the pin echoes the drifted name) always come back
EXCLUDE here: their heal shape is the 820679b9 true-VA re-spell, a
different motion needing its own pass.

Usage: python3 tools/preflight_heal_wave.py TARGET [TARGET...]
Emits a machine-readable manifest per target to stdout.
"""
import re
import sys
from pathlib import Path

REPO = Path("/home/z/my-project/cannon-seed")
AUTO = re.compile(r"^(func|data)_([0-9A-Fa-f]{8})$")
PIN = re.compile(r"^(\S+)\s*=\s*0x([0-9A-Fa-f]+)\s*;")
COUNTED_LAYERS = ("*.c", "*.h", "*.inc")  # the ratchet's counted layers


def load(target):
    import yaml

    cfg = yaml.safe_load((REPO / "config" / f"splat.{target}.yaml").read_text())
    seg = cfg["segments"][0]
    delta = seg["vram"] - seg["start"]
    pins = {}
    for line in (REPO / "config" / f"symbols.{target}.txt").read_text().splitlines():
        m = PIN.match(line)
        if m:
            pins.setdefault(m.group(2).upper(), []).append(m.group(1))
    rows = []
    for entry in seg["subsegments"]:
        if not isinstance(entry, list) or len(entry) != 3:
            continue
        off, kind, name = entry
        m = AUTO.match(str(name))
        if not m or kind not in ("asm", "c", "data"):
            continue
        name_va = int(m.group(2), 16)
        true_va = off + delta
        if name_va != true_va and f"{true_va:X}" in {p.upper() for p in pins}:
            pin_names = pins.get(f"{true_va:X}", [])
            rows.append((off, kind, name, true_va, pin_names[0]))
    return rows


def file_candidates(target, kind, name, pin):
    if kind == "asm":
        return [REPO / "asm" / target / "nonmatchings" / f"{name}.s"]
    if kind == "c":
        return [REPO / "src" / target / f"{name}.c", REPO / "src" / f"{name}.c"]
    if kind == "data":
        return [REPO / "data" / target / f"{name}.data.s", REPO / "data" / target / f"{name}.s"]
    return []


def classify(target, off, kind, name, tva, pin):
    if pin == name:
        return "EXCLUDE", "SELF-class (pin echoes drifted name; 820679b9 motion)"
    fpath = next((c for c in file_candidates(target, kind, name, pin) if c.exists()), None)
    if fpath is None:
        # any pin-named file already? (pre-renamed layer)
        pin_path = next((c for c in file_candidates(target, kind, pin, pin) if c.exists()), None)
        if pin_path is not None:
            return "NOFILE", f"no drifted-named file; pin-named file exists ({pin_path.name})"
        return "NOFILE", "no per-target file layer (shared-copy class; yaml-only)"
    text = fpath.read_text()
    if kind == "c":
        content_ok = re.search(rf"\b{re.escape(pin)}\b", text) is not None
        drifted_content = re.search(rf"\b{re.escape(name)}\b", text) is not None
    else:
        g = re.search(r"^glabel\s+(\S+)", text, re.M)
        content_ok = g is not None and g.group(1) == pin
        drifted_content = re.search(rf"\b{re.escape(name)}\b", text) is not None
    # reference graph: repo-wide hits for the drifted token
    import subprocess

    out = subprocess.run(
        ["git", "grep", "-l", "--", name], cwd=REPO, capture_output=True, text=True
    ).stdout.splitlines()
    own_yaml = f"config/splat.{target}.yaml"
    own_sym = f"config/symbols.{target}.txt"
    prefix_own = (f"asm/{target}/", f"src/{target}/", f"data/{target}/")
    riders, foreign = [], 0
    for hit in out:
        if hit == own_yaml or hit == str(fpath.relative_to(REPO)) or hit == own_sym:
            continue
        if hit.startswith(prefix_own):
            riders.append(hit)
        else:
            foreign += 1  # other targets' same-spelled rows: untouched neighbors
    if drifted_content:
        return "RESPELL", f"content spells the drifted name; riders={len(riders)} foreign={foreign}"
    if riders:
        return "RIDER", f"content PIN-SPELLED; {len(riders)} own-layer rider file(s): {riders[:3]}"
    if content_ok:
        return "ZEROEDIT", f"content PIN-SPELLED @drifted-name; foreign={foreign}"
    return "EXCLUDE", f"content neutral/mismatched (glabel neither pin nor drifted); foreign={foreign}"


def main():
    targets = sys.argv[1:]
    if not targets:
        print("usage: preflight_heal_wave.py TARGET [TARGET...]")
        return 2
    tally = {}
    for t in targets:
        rows = load(t)
        print(f"### {t}: {len(rows)} healable rows")
        for off, kind, name, tva, pin in rows:
            verdict, why = classify(t, off, kind, name, tva, pin)
            tally[verdict] = tally.get(verdict, 0) + 1
            print(f"{t}\t0x{off:05X}\t{kind}\t{name}\t{pin}\t{verdict}\t{why}")
    print("\n### TALLY:", " ".join(f"{k}={v}" for k, v in sorted(tally.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())

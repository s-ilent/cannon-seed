#!/usr/bin/env python3
"""Machine pre-flight for a pin-first heal wave (generalized; cron-202611082317).

The sces_00269 zero-edit campaign's pre-flight instrument, rebuilt in-repo
and generalized to any target after the all-target census sweep found the
same drifted-row classes on the seven non-sces targets (~1,325 healable).

For each HEALABLE row (drifted auto-name + pin at the true VA, per
tools/pin_first_census.py), classify:

  ZEROEDIT   file exists @drifted-name, content already spells the pin
             (asm/data glabel; c content mention), the drifted token appears
             ONLY in the target's own yaml row + the file's path (+ the
             target's generated symbols layer), the own-yaml mention count
             is exactly 1, and the pin-named destination is free (v2: the
             g3_eu batch's three blind-spot guards). The wave is one git mv
             + one yaml row re-spell; nothing else.
  SHAREDMERGE  a c row whose pin-named shared top-level src/ file already
             exists: the ddc7702d motion - body diff-gate, git rm the
             drifted duplicate, yaml-only re-spell. v2 class (the g3_eu
             batch routed 8 rows here that v1 called ZEROEDIT).
  RIDER      like ZEROEDIT but the drifted token has N extra reference
             hits inside the TARGET'S OWN layers (caller jals, comments):
             the wave re-spells those hits in the same motion (they are
             enumerated in the manifest). v3: hits are enumerated
             WHOLE-TOKEN (a .N fragment sibling's name and a same-spelled
             real function at another VA are NOT riders - the cron-
             202611091532 pass proved all six RIDER rows' hits were those
             two false-positive shapes), and every enumerated hit must
             still be checked to bind to the row's true VA before the
             wave re-spells it (branch/jal target resolution; hits that
             bind to the drift-name's own VA are the real same-named
             function and STAY).
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


def whole_token(name):
    """Regex for the bare token: not preceded/followed by a word char, and
    NOT followed by '.' - so func_X.2 fragment names never match func_X.
    (cron-202611091532: the substring collision that made every .2-sibling
    row look like a RIDER)."""
    return rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_.])"


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
    """v4: consult the yaml's options.asm_path (cron-202611091647: slps_00270's
    asm layer lives at the top-level asm/nonmatchings tree - the hardcoded
    asm/<target>/nonmatchings guess manufactured the whole NOFILE class and
    hid five SELF rows' own files during the SELF pass). The per-target dir
    stays as the fallback; data rows live under <asm_path>/data/."""
    import yaml

    cfg = yaml.safe_load((REPO / "config" / f"splat.{target}.yaml").read_text())
    ap = Path(
        REPO / cfg["options"].get("asm_path", f"asm/{target}/nonmatchings").rstrip("/")
    )
    dp = REPO / "asm" / target / "nonmatchings"
    if kind == "asm":
        return [ap / f"{name}.s", dp / f"{name}.s"]
    if kind == "c":
        return [REPO / "src" / target / f"{name}.c", REPO / "src" / f"{name}.c"]
    if kind == "data":
        return [
            ap / "data" / f"{name}.data.s",
            ap / f"{name}.data.s",
            dp / "data" / f"{name}.data.s",
            REPO / "data" / target / f"{name}.data.s",
            REPO / "data" / target / f"{name}.s",
        ]
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
        drifted_content = re.search(whole_token(name), text) is not None
    else:
        g = re.search(r"^glabel\s+(\S+)", text, re.M)
        content_ok = g is not None and g.group(1) == pin
        drifted_content = re.search(whole_token(name), text) is not None
    # reference graph: repo-wide hits for the drifted token
    import subprocess

    out = subprocess.run(
        ["git", "grep", "-l", "-P", "--", whole_token(name)],
        cwd=REPO,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    own_yaml = f"config/splat.{target}.yaml"
    own_sym = f"config/symbols.{target}.txt"
    prefix_own = (f"asm/{target}/", f"src/{target}/", f"data/{target}/")
    riders, foreign_yaml, foreign_other = [], [], 0
    for hit in out:
        if hit == own_yaml or hit == str(fpath.relative_to(REPO)) or hit == own_sym:
            continue
        if hit.startswith(prefix_own):
            riders.append(hit)
        elif hit.startswith("config/splat."):
            foreign_yaml.append(hit)  # another target's yaml spells the token
        else:
            foreign_other += 1  # symbols layers, docs: untouched neighbors
    own_yaml_hits = subprocess.run(
        ["git", "grep", "-c", "--", name, own_yaml],
        cwd=REPO,
        capture_output=True,
        text=True,
    ).stdout.strip()
    own_yaml_count = int(own_yaml_hits.split(":")[1]) if own_yaml_hits else 0
    if drifted_content:
        return "RESPELL", f"content spells the drifted name; riders={len(riders)} foreign={foreign_other}"
    if riders:
        return "RIDER", f"content PIN-SPELLED; {len(riders)} own-layer rider file(s): {riders[:3]}"
    if content_ok:
        # v2 guards (cron-202611090647): the g3_eu batch found three v1 blind
        # spots - a second own-yaml mention (fragment sibling like .2 rows),
        # the pin-named shared file already at top-level src/, and foreign
        # yamls naming a shared top-level c file
        if own_yaml_count != 1:
            return "EXCLUDE", f"own-yaml token count {own_yaml_count} != 1 (fragment sibling or rider; own pass)"
        pin_file = next((c for c in file_candidates(target, kind, pin, pin) if c.exists()), None)
        if pin_file is not None:
            if kind == "c" and pin_file == REPO / "src" / f"{pin}.c":
                return "SHAREDMERGE", "pin-named shared file exists (ddc7702d motion; body diff-gated)"
            return "EXCLUDE", f"destination exists {pin_file.name}"
        if foreign_yaml and kind == "c":
            return "EXCLUDE", f"shared-file naming conflict (foreign yaml names the drifted copy: {foreign_yaml}; coordinated multi-row heal)"
        # asm foreign-config hits are the same-spelled-neighbor law: each
        # target's own row at its own VA, untouched by this target's heal
        return "ZEROEDIT", f"content PIN-SPELLED @drifted-name; foreign={foreign_other + len(foreign_yaml)}"
    return "EXCLUDE", f"content neutral/mismatched (glabel neither pin nor drifted); foreign={foreign_other}"


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

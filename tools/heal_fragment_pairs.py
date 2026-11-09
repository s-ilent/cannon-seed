#!/usr/bin/env python3
"""Fragment-sibling pair heal (the 'own pass' the v2 guard routes EXCLUDE rows to).

The v2/v4 preflight classifies a drifted row EXCLUDE when its own-yaml token
count is 2. The cron-202611091802 inspection proved the shape: the second
mention is a `.N` FRAGMENT SIBLING row - a separate yaml row whose name is
`<drifted>.N`, whose TRUE VA equals the drifted name's own VA (the fragment
sits at the address the drift name encodes; the `.N` suffix is a dedup
artifact from when the drifted main row squatted the base name).

The pair heals in ONE motion (per-row inspection FIRST, then assert-everything
before the first mutation):

  main row      the ZEROEDIT motion: git mv <name>.s -> <pin>.s (glabel
                already spells the pin) + one yaml row re-spell.
  fragment row  three sub-shapes, decided by the pin at the fragment's true VA:
    (a) curated pin (file glabel already spells it):
        git mv <name>.N.s -> <fpin>.s + yaml row re-spell. Zero content edits.
    (b) pin echoes the fragment row name (the '(row name)' pin - SELF-class
        law at the fragment): the true-VA auto name is the base name, freed
        by the main row's mv. git mv + WHOLE-TOKEN content re-spell + yaml
        row re-spell + the '(row name)' pin line re-spell.
    (c) no pin at the fragment VA: NEVER TOUCHED (routed back to a report).

The shape-b content re-spell is WHOLE-TOKEN across the moved fragment file:
the token lives in the glabel, the 'nonmatching' header line AND the
'endlabel' directive (the first 1802 apply re-spelled only the glabel and
the assembler died on the endlabel .size binding - the SELF pass's
'glabel/header re-spells' law).

Usage: python3 tools/heal_fragment_pairs.py TARGET [TARGET ...] [--apply]
Without --apply: dry-run, assertions only, no tree change.
"""
import re
import subprocess
import sys
from pathlib import Path

REPO = Path("/home/z/my-project/cannon-seed")
sys.path.insert(0, str(REPO / "tools"))
import preflight_heal_wave as pf  # noqa: E402

FRAG = re.compile(r"^(\d+)$")
YAML_ROW = re.compile(r"^(\s*-\s*\[0x([0-9A-Fa-f]+),\s*(asm|c|data),\s*)(\S+)(\s*\].*)$")
PIN = re.compile(r"^(\S+)\s*=\s*0x([0-9A-Fa-f]+)\s*;")
LEAVE_PREFIX = ("docs/",)


def sh(*args):
    return subprocess.run(args, cwd=REPO, capture_output=True, text=True)


def whole_token(name):
    return rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_.])"


def yaml_lines(target):
    return (REPO / "config" / f"splat.{target}.yaml").read_text().splitlines(keepends=True)


def find_fragment_rows(target, base_name):
    """All yaml rows spelling <base_name>.N (N = dedup suffix >= 2)."""
    out = []
    for i, line in enumerate(yaml_lines(target)):
        m = YAML_ROW.match(line)
        if not m:
            continue
        row_name = m.group(4)
        if row_name.startswith(base_name + "."):
            suffix = row_name[len(base_name) + 1:]
            if FRAG.match(suffix):
                out.append((i, line, row_name, int(suffix)))
    return out


def pin_at(target, va):
    for line in (REPO / "config" / f"symbols.{target}.txt").read_text().splitlines():
        m = PIN.match(line)
        if m and int(m.group(2), 16) == va:
            return m.group(1), line
    return None, None


def glabel_of(path):
    m = re.search(r"^glabel\s+(\S+)", path.read_text(), re.M)
    return m.group(1) if m else None


def mentions_outside(target, token, own_paths):
    """Whole-token repo-wide mentions minus the pair's own layers.
    docs/ mentions are banked no-touch neighbors; anything else fails."""
    out = sh("git", "grep", "-l", "-P", "--", whole_token(token)).stdout.splitlines()
    bad = []
    for h in out:
        if h in own_paths or h == f"config/symbols.{target}.txt" or h.startswith(LEAVE_PREFIX):
            continue
        bad.append(h)
    return bad


def plan_target(target, failures, plans):
    import yaml as Y

    cfg = Y.safe_load((REPO / "config" / f"splat.{target}.yaml").read_text())
    seg = cfg["segments"][0]
    delta = seg["vram"] - seg["start"]
    ap = Path(REPO / cfg["options"].get("asm_path", f"asm/{target}/nonmatchings").rstrip("/"))
    rows = pf.load(target)
    n_pairs = 0
    for off, kind, name, tva, pin in rows:
        verdict, why = pf.classify(target, off, kind, name, tva, pin)
        if not (verdict == "EXCLUDE" and why.startswith("own-yaml token count 2")):
            continue
        tag = f"{target} 0x{off:05X} {kind} {name} -> {pin}"
        frags = find_fragment_rows(target, name)
        if len(frags) != 1:
            failures.append(f"{tag}: expected exactly 1 fragment row, found {len(frags)}")
            continue
        fi, fline, frag_name, suffix = frags[0]
        fm = YAML_ROW.match(fline)
        foff = int(fm.group(2), 16)
        ftva = foff + delta
        base_va = int(name[5:], 16)
        if kind != "asm":
            failures.append(f"{tag}: non-asm pair (kind {kind}) - not covered by this motion")
            continue
        if ftva != base_va:
            failures.append(
                f"{tag}: fragment true VA 0x{ftva:08X} != name-base VA 0x{base_va:08X} - different shape, own pass"
            )
            continue
        main_file = ap / f"{name}.s"
        frag_file = ap / f"{frag_name}.s"
        if not main_file.exists():
            failures.append(f"{tag}: main file missing {main_file}")
            continue
        if not frag_file.exists():
            failures.append(f"{tag}: fragment file missing {frag_file}")
            continue
        if glabel_of(main_file) != pin:
            failures.append(f"{tag}: main glabel mismatch (want {pin})")
            continue
        fg = glabel_of(frag_file)
        fpin, fpinline = pin_at(target, ftva)
        if fpin is None:
            failures.append(f"{tag}: no pin at fragment VA 0x{ftva:08X} - shape (c), untouched")
            continue
        if fpin == frag_name:
            # shape (b): the '(row name)' SELF-class echo; true-VA auto name is
            # the base, freed by the main row's mv
            fdest = name
            fshape = "b"
            if fg != frag_name:
                failures.append(f"{tag}: shape b but fragment glabel is {fg}, want {frag_name}")
                continue
        else:
            # shape (a): curated pin; the file's glabel must already spell it
            fdest = fpin
            fshape = "a"
            if fg != fpin:
                failures.append(
                    f"{tag}: shape a but fragment glabel {fg} != pin {fpin} - not zero-edit, own pass"
                )
                continue
        # destinations free
        if (ap / f"{pin}.s").exists():
            failures.append(f"{tag}: main destination exists {ap / (pin + '.s')}")
            continue
        if (ap / f"{fdest}.s").exists() and not (
            fshape == "b" and (ap / f"{fdest}.s") == main_file
        ):
            failures.append(f"{tag}: fragment destination exists {ap / (fdest + '.s')}")
            continue
        # mention surface: nothing outside the pair's own layers + docs
        own = {str(main_file.relative_to(REPO)), str(frag_file.relative_to(REPO)),
               f"config/splat.{target}.yaml"}
        bad = mentions_outside(target, name, own) + mentions_outside(target, frag_name, own)
        if bad:
            failures.append(f"{tag}: unexpected mention surface: {bad}")
            continue
        # yaml row shapes
        if not YAML_ROW.match(fline):
            failures.append(f"{tag}: fragment yaml row shape mismatch")
            continue
        plans.append({
            "target": target, "tag": tag, "off": off, "kind": kind, "name": name,
            "pin": pin, "main_file": main_file, "frag_file": frag_file,
            "frag_name": frag_name, "fdest": fdest, "fshape": fshape, "fg": fg,
            "fpin": fpin, "fpinline": fpinline, "ftva": ftva, "ap": ap,
        })
        n_pairs += 1
    return n_pairs


def apply_plans(plans):
    for p in plans:
        # 1. main mv (frees the base name for shape b)
        r = sh("git", "mv", str(p["main_file"]), str(p["ap"] / (p["pin"] + ".s")))
        if r.returncode != 0:
            print(f"MID-RUN main mv failure {p['tag']}: {r.stderr}")
            return 1
        # 2. fragment mv
        r = sh("git", "mv", str(p["frag_file"]), str(p["ap"] / (p["fdest"] + ".s")))
        if r.returncode != 0:
            print(f"MID-RUN fragment mv failure {p['tag']}: {r.stderr}")
            return 1
        # 3. shape b: whole-token re-spell inside the moved fragment file -
        # the token lives in the glabel, the 'nonmatching' header line AND
        # the 'endlabel' directive (cron-202611091802: the first apply
        # re-spelled only the glabel and the assembler died on the endlabel
        # .size binding - the SELF pass's 'glabel/header re-spells' law)
        if p["fshape"] == "b":
            fpath = p["ap"] / (p["fdest"] + ".s")
            text = fpath.read_text()
            pat = re.compile(pf.whole_token(p["frag_name"]))
            hits = len(pat.findall(text))
            if hits == 0:
                print(f"MID-RUN shape-b re-spell: no token occurrences in {fpath} ({p['tag']})")
                return 1
            new = pat.sub(p["fdest"], text)
            fpath.write_text(new)
            print(f"    shape-b re-spell: {hits} token occurrence(s) in {fpath.name}")
        # 4. yaml row re-spells (main + fragment)
        ypath = REPO / "config" / f"splat.{p['target']}.yaml"
        lines = ypath.read_text().splitlines(keepends=True)
        for old, new_dest in ((p["name"], p["pin"]), (p["frag_name"], p["fdest"])):
            hit = False
            for i, line in enumerate(lines):
                m = YAML_ROW.match(line)
                if m and m.group(4) == old:
                    lines[i] = YAML_ROW.sub(rf"\g<1>{new_dest}\g<5>", line)
                    hit = True
            if not hit:
                print(f"MID-RUN yaml row not found for {old} ({p['tag']})")
                return 1
        ypath.write_text("".join(lines))
        # 5. shape b: the '(row name)' pin line re-spell
        if p["fshape"] == "b":
            spath = REPO / "config" / f"symbols.{p['target']}.txt"
            stext = spath.read_text()
            old_line = p["fpinline"]
            new_line = re.sub(
                rf"^{re.escape(p['frag_name'])}(\s*=\s*0x[0-9A-Fa-f]+;\s*.*)$",
                rf"{p['fdest']}\g<1>",
                old_line,
                count=1,
            )
            if new_line == old_line:
                print(f"MID-RUN pin line re-spell failure {p['tag']}")
                return 1
            if old_line not in stext:
                print(f"MID-RUN pin line vanished {p['tag']}")
                return 1
            spath.write_text(stext.replace(old_line, new_line, 1))
        print(
            f"  healed {p['tag']} | frag {p['frag_name']} -> {p['fdest']} "
            f"(shape {p['fshape']})"
        )
    print(f"applied {len(plans)} pair heal(s)")
    return 0


def main():
    args = sys.argv[1:]
    apply = "--apply" in args
    targets = [a for a in args if not a.startswith("--")]
    if not targets:
        print("usage: heal_fragment_pairs.py TARGET [TARGET ...] [--apply]")
        return 2
    failures, plans = [], []
    for t in targets:
        n = plan_target(t, failures, plans)
        print(f"### {t}: {n} pair(s) planned")
    if failures:
        print(f"ABORT - {len(failures)} assertion failure(s), no mutation performed:")
        for f in failures:
            print("  FAIL:", f)
        return 1
    if not apply:
        print("dry-run complete (no --apply)")
        return 0
    return apply_plans(plans)


if __name__ == "__main__":
    sys.exit(main())

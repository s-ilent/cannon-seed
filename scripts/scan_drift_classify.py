#!/usr/bin/env python3
"""scan_drift_classify.py - classify the committed-vs-fresh-scan yaml drift.

Reads two yaml files (committed via git show, fresh from the working tree)
and pairs their generated subsegment rows by (vram, name) / (vram, type).

Classes:
  W  spacing-only        same type/name/size/markers, only column padding differs
  C  comment-enrichment  same row fields, committed carries extra comment text
                         (sdk tag placement, hand notes) the walk cannot rederive
  T  type change         row type differs (asm <-> data)
  E  extent change       row size differs
  R  rename              same vram, different name
  N  new row             fresh only
  D  dropped row         committed only

Usage: python3 scripts/scan_drift_classify.py <target>   # uses git show for committed
"""
import re
import subprocess
import sys

ROW = re.compile(
    r"\s*- \[(0x[0-9A-Fa-f]+),\s*(\w+),\s*(\w+)\]\s*#\s*(0x[0-9A-Fa-f]+)(.*)$"
)


def parse_rows(text):
    rows = []
    in_block = False
    for ln in text.splitlines():
        if "# BEGIN GENERATED SUBSEGMENTS" in ln:
            in_block = True
            continue
        if "# END GENERATED SUBSEGMENTS" in ln:
            break
        if not in_block:
            continue
        m = ROW.match(ln)
        if not m:
            continue
        vram = int(m.group(1), 16)
        size = int(m.group(4), 16)
        rest = m.group(5) or ""
        markers = set(re.findall(r"\b(pinned|sdk|noseed|absolute)\b", rest))
        note = re.sub(r"\b(pinned|sdk|noseed|absolute)\b", "", rest).strip()
        rows.append(
            {
                "vram": vram,
                "type": m.group(2),
                "name": m.group(3),
                "size": size,
                "markers": markers,
                "note": note,
                "line": ln,
            }
        )
    return rows


def classify(committed, fresh):
    out = {"W": [], "C": [], "T": [], "E": [], "R": [], "N": [], "D": []}
    by_vram_c = {}
    for r in committed:
        by_vram_c.setdefault(r["vram"], []).append(r)
    by_vram_f = {}
    for r in fresh:
        by_vram_f.setdefault(r["vram"], []).append(r)

    consumed_f = set()
    for vram, crows in by_vram_c.items():
        frows = by_vram_f.get(vram, [])
        fkeys = {(r["type"], r["name"], r["size"]) for r in frows}
        for c in crows:
            match = None
            for f in frows:
                if f["name"] == c["name"] and f["size"] == c["size"]:
                    match = f
                    break
            if match is None:
                for f in frows:
                    if f["name"] == c["name"]:
                        match = f
                        break
            if match is None:
                # renamed row: vram carries a different name set
                out["D"].append(c)
                continue
            consumed_f.add(id(match))
            if match["type"] != c["type"]:
                out["T"].append((c, match))
            elif match["size"] != c["size"]:
                out["E"].append((c, match))
            elif match["markers"] != c["markers"]:
                out["C"].append((c, match))
            elif (match["note"] or "") != (c["note"] or ""):
                out["C"].append((c, match))
            else:
                out["W"].append((c, match))
    for frows in by_vram_f.values():
        for f in frows:
            if id(f) not in consumed_f:
                out["N"].append(f)
    return out


def main(argv):
    target = argv[1]
    committed = subprocess.run(
        ["git", "show", f"HEAD:config/splat.{target}.yaml"],
        capture_output=True, text=True, check=True,
    ).stdout
    fresh = open(f"config/splat.{target}.yaml").read()
    res = classify(parse_rows(committed), parse_rows(fresh))
    print(f"== {target}: W={len(res['W'])} C={len(res['C'])} T={len(res['T'])} "
          f"E={len(res['E'])} D={len(res['D'])} N={len(res['N'])}")
    for c, f in res["T"]:
        print(f"  T {c['vram']:08X} {c['type']}/{c['name']}/{c['size']:#x} -> "
              f"{f['type']}/{f['name']}/{f['size']:#x}")
    for c, f in res["E"]:
        print(f"  E {c['vram']:08X} {c['type']}/{c['name']} {c['size']:#x} -> "
              f"{f['name']}/{f['size']:#x}")
    for c, f in res["C"]:
        print(f"  C {c['vram']:08X} {c['name']} markers {sorted(c['markers'])} -> "
              f"{sorted(f['markers'])} note_c={c['note']!r} note_f={f['note']!r}")
    for c in res["D"]:
        print(f"  D {c['vram']:08X} {c['type']}/{c['name']}/{c['size']:#x} {c['note']!r}")
    for f in res["N"]:
        print(f"  N {f['vram']:08X} {f['type']}/{f['name']}/{f['size']:#x} {f['note']!r}")


if __name__ == "__main__":
    main(sys.argv)

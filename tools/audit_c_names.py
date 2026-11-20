#!/usr/bin/env python3
"""audit_c_names.py — the carve-name law census (name==VMA) for splat yamls.

The carve-name law (banked 2026-10-20 in the func_800598C0 completion): a
subsegment row whose NAME encodes a VA must encode the row's own placement
VA (vram + (offset - start)).  Stale names encode a different address — a
nested dump row's VA, a woven-era VA — and hoard the name the two-pass
link's auto-alias fallback needs for the real owner.  The proven repair
shape is the regen-coupled re-spell (9388aca7 g3org_jp func_800250F4,
3ccee159 mainmenu_eu): git mv + content re-spell + both-region yaml lines +
the dump's collision-pass _2 units reclaim plain.

Primary census: c rows — the actionable repair class.
Secondary census (--types c,data,asm,...): every VA-encoding row, reported
for visibility only.  Data rows include the documented "pinned" provenance
class (dump-derived names that predate the de-framing flip and carry their
analysis provenance in the row comment); asm rows carry the glabel law and
are adjudicated separately.

Read-only; ALWAYS exits 0 (convention: tools/baseline_audit.py).
"""

import argparse
import glob
import os
import re
import sys

import yaml

NAME_VA_RE = re.compile(r"^(func|data)_([0-9A-Fa-f]{8})(?:_(\w+))?$")
ROW_COMMENT_RE = re.compile(
    r"^\s+-\s+\[(?P<off>0x[0-9A-Fa-f]+),\s*(?P<typ>[a-z0-9_]+),\s*"
    r"(?P<name>[^\]]+)\]\s*(?:#\s*(?P<cmt>.*))?\s*$"
)


def comment_map(path):
    """(offset_hex, type, name) -> comment text, from the raw subsegment lines."""
    out = {}
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            m = ROW_COMMENT_RE.match(line.rstrip("\n"))
            if m:
                out[(m.group("off").lower(), m.group("typ"), m.group("name"))] = (
                    m.group("cmt") or ""
                ).strip()
    return out


def fmt(v):
    return "0x%08X" % v


def census_target(path, types, all_rows=None):
    name = os.path.basename(path)[len("splat."):-len(".yaml")]
    with open(path, "r", encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    cmap = comment_map(path)
    stats = {}
    for t in types:
        stats[t] = {"rows": 0, "va_named": 0, "match": 0, "mismatch": 0, "curated": 0}
    mismatches = []
    for seg in doc.get("segments") or []:
        if not isinstance(seg, dict):
            continue  # flat pad/list entries carry no rows
        vram = seg.get("vram")
        start = seg.get("start")
        if vram is None or start is None:
            continue
        for row in seg.get("subsegments") or []:
            if not isinstance(row, (list, tuple)) or len(row) < 3:
                continue
            off, typ, rname = row[0], row[1], row[2]
            if typ not in stats:
                continue
            st = stats[typ]
            st["rows"] += 1
            m = NAME_VA_RE.match(rname)
            if not m:
                st["curated"] += 1
                continue
            st["va_named"] += 1
            name_va = int(m.group(2), 16)
            if len(row) >= 4 and isinstance(row[3], int):
                placement = row[3]  # explicit per-row vram override
            else:
                placement = vram + (off - start)
            status = "match" if name_va == placement else "mismatch"
            if status == "match":
                st["match"] += 1
            else:
                st["mismatch"] += 1
            if all_rows is not None:
                all_rows.append(
                    {
                        "target": name,
                        "off": off,
                        "typ": typ,
                        "name": rname,
                        "name_va": name_va,
                        "placement": placement,
                        "status": status,
                        "cmt": cmap.get(("%08x" % off, typ, rname), ""),
                    }
                )
            if status == "match":
                continue
            delta = name_va - placement
            sign = "+" if delta >= 0 else "-"
            mismatches.append(
                {
                    "seg": seg.get("name") or "?",
                    "off": off,
                    "typ": typ,
                    "name": rname,
                    "name_va": name_va,
                    "placement": placement,
                    "delta": "%s0x%X" % (sign, abs(delta)),
                    "cmt": cmap.get(("%08x" % off, typ, rname), ""),
                }
            )
    return name, stats, mismatches


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--types", default="c",
                    help="comma-separated row types to census (default: c)")
    ap.add_argument("--all", action="store_true",
                    help="census every VA-encodable type (c,data,asm,...)")
    ap.add_argument("--target", default=None, help="census one target only")
    ap.add_argument("--quiet", action="store_true", help="summary only")
    ap.add_argument("--cross", action="store_true",
                    help="report names used by more than one target "
                         "(the shared cross-target name convention vs "
                         "target-unique stale names)")
    args = ap.parse_args()

    cfg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config")
    if args.all:
        types = ["c", "data", "asm"]
    else:
        types = [t.strip() for t in args.types.split(",") if t.strip()]

    paths = sorted(glob.glob(os.path.join(cfg, "splat.*.yaml")))
    if args.target:
        paths = [p for p in paths if args.target in os.path.basename(p)]
    if not paths:
        print("no targets matched", file=sys.stderr)
        return 0

    totals = {t: {"rows": 0, "va_named": 0, "match": 0, "mismatch": 0, "curated": 0}
              for t in types}
    all_mm = []
    all_rows = []
    for path in paths:
        name, stats, mm = census_target(path, types, all_rows)
        line = "== %s:" % name
        for t in types:
            st = stats[t]
            line += ("  %s[rows=%d va=%d match=%d MISMATCH=%d curated=%d]"
                     % (t, st["rows"], st["va_named"], st["match"],
                        st["mismatch"], st["curated"]))
            for k in totals[t]:
                totals[t][k] += st[k]
        print(line)
        for r in mm:
            all_mm.append((name, r))
            if not args.quiet:
                print("   MISMATCH [%s] off=0x%X name=%s name_va=%s placement=%s "
                      "delta=%s seg=%s%s"
                      % (r["typ"], r["off"], r["name"], fmt(r["name_va"]),
                         fmt(r["placement"]), r["delta"], r["seg"],
                         ("  # " + r["cmt"]) if r["cmt"] else ""))

    if args.cross:
        by_name = {}
        for r in all_rows:
            by_name.setdefault(r["name"], []).append(r)
        shared = {n: rows for n, rows in by_name.items() if len(rows) > 1}
        print("== CROSS-TARGET NAMES (used by >1 target): %d names"
              % len(shared))
        for n in sorted(shared):
            rows = sorted(shared[n], key=lambda r: r["target"])
            hosts = ["%s:%s" % (r["target"], r["status"]) for r in rows]
            canon = [r["target"] for r in rows if r["status"] == "match"]
            tag = "canonical=%s" % canon[0] if canon else "NO-MATCH-HOST"
            print("   %s  %s  %s" % (n, tag, " ".join(hosts)))
        stale = [r for r in all_rows if r["status"] == "mismatch"
                 and len(by_name.get(r["name"], [])) == 1]
        print("== TARGET-UNIQUE MISMATCHES (single-target stale names): %d"
              % len(stale))

    print("== TOTAL:")
    for t in types:
        st = totals[t]
        print("   %s: rows=%d va_named=%d match=%d MISMATCH=%d curated=%d"
              % (t, st["rows"], st["va_named"], st["match"], st["mismatch"],
                 st["curated"]))
    print("== census complete (read-only, exit 0)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Region-aware B-class filter for the data-typed-sdk census (v3, linear).

The 2101 window's handoff queue: the B-class (census members strictly
INSIDE data rows) counts 300+ hits per target, "mostly the psyq veneer
spans, needs the walk-name collision filter before any row-level
conclusion".

v3 uses the ONE map that is above suspicion: the retail EXE's own
linear load. docs/LOADMAP.md's header audit shows every target loads
as a single linear image at t_addr 0x80020000 (payload off 0 = VA
0x80020000; the yaml's offsets include the 0x800 header, so the
linear delta is 0x8001F800 universally). Verify is byte-exact against
the retail payload, so file order IS runtime order - no name anchors
are involved.

Why the name anchors cannot be trusted for containment: the walk
named rows in CARVE space, and the framing pockets (docs/TASKS.md
"Witness A") skew carve-vs-runtime by ~304 B/sector, unbounded with
depth - mainmenu_jp's deep region carries +0x9df0-class drifts while
its game region is linear. v2 trusted the anchors and re-created the
skew's echo as 152 false "inside-data" hits. v3 annotates the owning
row's anchor drift instead, turning the hazard into the measurement.

Classes (per census member VA, mapped linearly into the yaml rows):
  start-data    off == row start of a data row        (the A class)
  inside-data   off strictly inside a data row        (the TRUE B class)
  claimed-code  off inside an asm/c row               (the walk owns it)
  unmapped      off beyond the payload

Each hit carries the owning row's anchor drift (name VA minus linear
VA): 0x0 = linearly named; anything else = carve-space name, and the
value is the pocket skew at that depth.

Run: python3 scripts/check_b_class_filter.py
"""

import bisect
import collections
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from tools.sdk_members import yaml_anchors  # noqa: E402

sys.path.insert(0, str(REPO / "scripts"))
from check_data_typed_sdk import CODE_KINDS, parse_census  # noqa: E402

LINEAR_BASE = 0x8001F800  # t_addr 0x80020000 minus the 0x800 EXE header


def classify_target(target, members):
    rows = sorted(yaml_anchors(target, with_kind=True), key=lambda r: r[0])
    offs = [r[0] for r in rows]
    payload_end = None  # from the last row's off; containment open-ended

    cls = collections.defaultdict(list)
    for addr, names in sorted(members.items()):
        off_m = addr - LINEAR_BASE
        if off_m < 0:
            cls["unmapped"].append((addr, names, None))
            continue
        i = bisect.bisect_right(offs, off_m) - 1
        if i < 0:
            cls["unmapped"].append((addr, names, None))
            continue
        off_i, kind_i, name_i, nv_i = rows[i]
        ext_i = (rows[i + 1][0] - off_i) if i + 1 < len(rows) else None
        if ext_i is not None and off_m >= off_i + ext_i:
            # row extents run to the next row; a miss here means the
            # address sits past the last row's start without a next
            # row - treat as payload tail, owned by nothing typed
            cls["unmapped"].append((addr, names, None))
            continue
        drift = (nv_i - (off_i + LINEAR_BASE)) if nv_i is not None else None
        if kind_i in CODE_KINDS:
            cls["claimed-code"].append((addr, names, (off_i, kind_i, name_i, drift)))
        elif off_m == off_i:
            cls["start-data"].append((addr, names, (off_i, kind_i, name_i, drift)))
        else:
            cls["inside-data"].append((addr, names, (off_i, kind_i, name_i, drift)))
    return cls, len(rows)


def main():
    census = parse_census()
    grand = collections.Counter()
    for target in sorted(census):
        members = census[target]
        cls, nrows = classify_target(target, members)
        for k, v in cls.items():
            grand[k] += len(v)
        print(f"== {target}: {len(members)} member addrs / {nrows} rows")
        for k in ("start-data", "inside-data", "claimed-code", "unmapped"):
            hits = cls.get(k, [])
            print(f"   {k:13s} {len(hits):4d}")
        # drift census over all owned hits (the pocket-skew measurement)
        drifts = collections.Counter()
        for k in ("claimed-code", "start-data", "inside-data"):
            for _, _, r in cls.get(k, []):
                drifts[r[3]] += 1
        if drifts:
            def dtxt(d):
                if d is None:
                    return "no-anchor"
                return "linear" if d == 0 else f"+0x{d:X}"
            top = ", ".join(f"{dtxt(d)} x{n}" for d, n in drifts.most_common(6))
            print(f"   owning-row anchor drift: {top}")
        residue = cls.get("inside-data", [])
        if residue:
            byrow = collections.defaultdict(list)
            for addr, names, r in residue:
                byrow[(r[0], r[2], r[3])].append((addr, names))
            for (off_i, name, drift), hits in sorted(byrow.items()):
                addrs = ", ".join(f"0x{a:08X}" for a, _ in hits)
                allnames = sorted({n for _, ns in hits for n in ns})
                dtxt = "linear" if drift == 0 else f"drift +0x{drift:X}"
                print(f"     TRUE-B row {name} (off 0x{off_i:X}, {dtxt}) "
                      f"x{len(hits)}: {addrs}")
                print(f"       names: {allnames}")
    print(f"\nGRAND TOTALS: {dict(grand)}")


if __name__ == "__main__":
    main()

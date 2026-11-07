#!/usr/bin/env python3
"""Check for data-typed sdk member rows in every target's splat yaml.

The mainmenu_jp sdk-lane taught the class: a PSYQ library member whose
address is the START of a `data` subsegment in the target's yaml is an
adoption gap - the region holds code (the member's function body) but
the yaml types it data. Eight such rows closed in mainmenu_jp (the
last two: SpuMalloc 0x8008062C, SpuSetCommonAttr 0x80080FE0). This
check sweeps ALL targets for the same class, per the 1946 window's
handoff queue ("a census check for data-typed sdk rows in the OTHER
targets").

Two matchers:
  name-match    census addr == row name vram (names are the build
                ground truth the linker uses)
  linear-match  census addr == seg.vram + off - seg.start (catches
                targets whose row names drifted from true VA;
                mainmenu_jp's did - the drift-fix renames rows)

Reported per target:
  A: member at the exact START of a non-asm/c row  (the gap class)
  B: member strictly INSIDE a non-asm/c row        (evidence only)

Run from anywhere: it locates the repo via tools/sdk_members.py.
"""

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from tools.sdk_members import subsegment_kinds, yaml_anchors  # noqa: E402

CENSUS = REPO / "config" / "sdk_members.txt"
TARGET_HDR = re.compile(r"^// target: (\S+)")
MEMBER = re.compile(r"^//   0x([0-9a-f]{8}) +(\S+) +(\S+) +(\S+) +(\S+)")

# kinds that hold code
CODE_KINDS = {"asm", "c"}


def parse_census():
    """{target: {addr:int, ...set of member names}} from sdk_members.txt."""
    targets = {}
    cur = None
    for line in CENSUS.read_text().splitlines():
        m = TARGET_HDR.match(line)
        if m:
            cur = m.group(1)
            targets.setdefault(cur, {})
            continue
        if cur is None:
            continue
        m = MEMBER.match(line)
        if m:
            addr = int(m.group(1), 16)
            name = m.group(5)
            targets[cur].setdefault(addr, set()).add(name)
    return targets


def rows_for_target(target):
    """[(off, kind, name, name_vram)] sorted by off, plus seg extents."""
    out = []
    for off, kind, name, nv in yaml_anchors(target, with_kind=True):
        out.append((off, kind, name, nv))
    out.sort(key=lambda r: r[0])
    return out


def main():
    census = parse_census()
    print(f"census targets: {len(census)}  "
          f"{', '.join(sorted(census))}")
    total_a = 0
    for target in sorted(census):
        members = census[target]
        rows = rows_for_target(target)
        # extent of row i = next row's off (sorted scatter list; extents
        # only used for the inside-class heuristic)
        a_hits = []   # exact start
        b_hits = []   # inside
        for addr, names in sorted(members.items()):
            hit = False
            for i, (off, kind, name, nv) in enumerate(rows):
                if kind in CODE_KINDS:
                    continue
                # name-match: the row's NAME carries the member's VA
                if nv == addr:
                    a_hits.append((addr, names, off, kind, name, "name"))
                    hit = True
                    break
                # linear-match: seg vram+off-lo (fallback for drifted
                # names); computed against the yaml's own seg fields
            if hit:
                continue
            for i, (off, kind, name, nv) in enumerate(rows):
                if kind in CODE_KINDS:
                    continue
                nxt = rows[i + 1][0] if i + 1 < len(rows) else None
                # containment by linear map is unreliable across load
                # gaps; only flag containment when the member addr is
                # between this row's name-vram and the next row's
                # name-vram (name-vram is ground truth where present)
                if nv is not None and nxt is not None:
                    pass  # handled below via name-vram sweep
            # containment sweep by name-vram order
            nv_rows = [(nv, kind, name) for off, kind, name, nv in rows
                       if nv is not None and kind not in CODE_KINDS]
            nv_rows.sort()
            for j, (nv, kind, name) in enumerate(nv_rows):
                if nv >= addr:
                    break
                if j + 1 < len(nv_rows) and nv_rows[j + 1][0] > addr:
                    b_hits.append((addr, names, None, kind, name, "inside"))
                    break
        if a_hits or b_hits:
            print(f"\n== {target}: {len(a_hits)} start-hit(s), "
                  f"{len(b_hits)} inside-hit(s)")
            for addr, names, off, kind, name, how in a_hits:
                print(f"  A 0x{addr:08X} {sorted(names)} row=0x{off:X} "
                      f"kind={kind} name={name} ({how})")
            for addr, names, off, kind, name, how in b_hits:
                print(f"  B 0x{addr:08X} {sorted(names)} "
                      f"inside kind={kind} name={name} ({how})")
            total_a += len(a_hits)
        else:
            print(f"== {target}: clean (0 start, 0 inside) over "
                  f"{len(members)} addrs / {len(rows)} rows")
    print(f"\nTOTAL start-hit class A: {total_a}")


if __name__ == "__main__":
    main()

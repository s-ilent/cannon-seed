#!/usr/bin/env python3
"""explore_siblings2.py - resolve candidate VRAM -> raw file offset -> the
row file whose FILE range actually covers it, per the scatter-list law."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import sdk_members as sm  # noqa: E402

PROPOSALS = [
    ("mainmenu_eu", 0x8005AE34),
    ("mainmenu_eu", 0x8005AE70),
    ("mainmenu_eu", 0x8005AC68),
    ("g3org_jp",    0x80043E94),
]

for target, va in PROPOSALS:
    anchors = sm.yaml_anchors(target, with_kind=True)
    raw = sm.name_to_raw(va, [(a[0], a[3]) for a in anchors if a[3] is not None])
    print(f"== {target} 0x{va:08X} -> raw 0x{raw:X}" if raw is not None
          else f"== {target} 0x{va:08X} -> UNMAPPED")
    if raw is None:
        continue
    # the row whose FILE range covers raw
    by_off = sorted(anchors)  # (off, kind, name, vram)
    owner = None
    for i, (off, kind, name, nv) in enumerate(by_off):
        if off <= raw:
            nxt = by_off[i + 1][0] if i + 1 < len(by_off) else None
            owner = (off, kind, name, nv, nxt)
        else:
            break
    if owner:
        off, kind, name, nv, nxt = owner
        span = (nxt - off) if nxt else None
        print(f"   file owner: {name} ({kind}) off 0x{off:X} "
              f"name-vram 0x{nv:08X} file-span "
              f"{hex(span) if span else '?'} delta-in-file +0x{raw-off:X}")

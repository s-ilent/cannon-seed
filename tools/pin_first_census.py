#!/usr/bin/env python3
"""Pin-first census for sces_00269: every yaml auto-name row vs the pins.

For each splat.sces_00269.yaml row whose name is a true-VA-class auto-name
(func_XXXXXXXX / data_XXXXXXXX):
  true_va = row_offset + (vram - start)
  name_va = the VA encoded in the auto-name
  drifted = name_va != true_va
  pinned  = symbols.sces_00269.txt carries a pin at the true VA

Reports:
  HEALABLE  drifted AND pinned at the true VA (yaml/file layer may catch up)
  DRIFTED   drifted, no pin at the true VA (waits for evidence)
  CLEAN     auto-name with name_va == true_va (no drift)
"""
import re
import sys
from pathlib import Path

REPO = Path("/home/z/my-project/cannon-seed")
TARGET = "sces_00269"
AUTO = re.compile(r"^(func|data)_([0-9A-Fa-f]{8})$")


def main() -> int:
    import yaml

    cfg = yaml.safe_load((REPO / "config" / f"splat.{TARGET}.yaml").read_text())
    seg = cfg["segments"][0]
    delta = seg["vram"] - seg["start"]

    pins = {}
    for line in (REPO / "config" / f"symbols.{TARGET}.txt").read_text().splitlines():
        m = re.match(r"^(\S+)\s*=\s*0x([0-9A-Fa-f]+)\s*;", line)
        if m:
            pins.setdefault(m.group(2).upper(), []).append(m.group(1))

    healable, drifted, clean = [], [], []
    for entry in seg["subsegments"]:
        if not isinstance(entry, list) or len(entry) != 3:
            continue
        off, kind, name = entry
        m = AUTO.match(str(name))
        if not m or kind not in ("asm", "c", "data"):
            continue
        name_va = int(m.group(2), 16)
        true_va = off + delta
        row = (off, kind, name, true_va)
        if name_va == true_va:
            clean.append(row)
        elif f"{true_va:X}" in {p.upper() for p in pins}:
            healable.append(row)
        else:
            drifted.append(row)

    print(f"clean auto-name rows : {len(clean)}")
    print(f"drifted, unpinned    : {len(drifted)}")
    print(f"HEALABLE (drifted+pinned at true VA): {len(healable)}")
    for off, kind, name, tva in healable:
        pin = "; ".join(pins.get(f"{tva:X}", ["?"]))
        print(f"  0x{off:05X} {kind:<4} {name} -> true VA 0x{tva:08X} pin: {pin}")
    print("\ndrifted rows (evidence wanted, name stays):")
    for off, kind, name, tva in drifted:
        nv = int(name.split("_")[1], 16)
        print(f"  0x{off:05X} {kind:<4} {name} true VA 0x{tva:08X} drift {nv - tva:+#x}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Report duplicate curated names per target scope in config/symbols.curated.txt,
mimicking tools/scan_functions.py load_curated semantics (live rows only)."""
import re
from collections import defaultdict
from pathlib import Path

C = Path("/home/z/my-project/cannon-seed/config/symbols.curated.txt")
scope = None
by_addr = defaultdict(lambda: defaultdict(list))  # scope -> addr -> [(name, line)]
by_name = defaultdict(lambda: defaultdict(list))
for i, line in enumerate(C.read_text(errors="replace").splitlines(), 1):
    mt = re.match(r"\s*//\s*target:\s*(\w+)", line)
    if mt:
        scope = mt.group(1)
        continue
    m = re.match(r"\s*([A-Za-z_]\w*)\s*=\s*(0x[0-9A-Fa-f]+)", line)
    if m and scope:
        name, addr = m.group(1), int(m.group(2), 16)
        by_addr[scope][addr].append((name, i))
        by_name[scope][name].append((addr, i))

bad = 0
for t in sorted(by_addr):
    for addr, rows in sorted(by_addr[t].items()):
        if len(rows) > 1:
            bad += 1
            names = ", ".join(f"{n}(L{ln})" for n, ln in rows)
            print(f"ADDR-DUP {t} 0x{addr:08X}: {names}")
    for name, rows in sorted(by_name[t].items()):
        if len(rows) > 1:
            bad += 1
            addrs = ", ".join(f"0x{a:08X}(L{ln})" for a, ln in rows)
            print(f"NAME-DUP {t} {name}: {addrs}")
print(f"\n{bad} duplicate(s) across {len(by_addr)} scopes")

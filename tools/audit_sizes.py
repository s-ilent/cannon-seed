#!/usr/bin/env python3
"""Audit: for every slps yaml row, the object's section size vs the row span.
Overruns force ld LMA adjustments (the second-pass link failure)."""
import re
import subprocess
import sys

OD = "/home/z/my-project/tools-local/mipsel-root/usr/bin/mipsel-linux-gnu-objdump"
env = {"LD_LIBRARY_PATH": "/home/z/my-project/tools-local/mipsel-root/usr/lib/x86_64-linux-gnu",
       "PATH": "/usr/bin:/bin"}

txt = open("config/splat.slps_00270.yaml").read()
rows = [(int(a, 16), t, n, int(s, 16))
        for a, t, n, s in re.findall(
            r"- \[(0x[0-9A-Fa-f]+), (\w+), (\w+)\]\s+# (0x[0-9A-Fa-f]+)", txt)]

bad = 0
for i, (off, typ, name, size) in enumerate(rows):
    if typ == "c":
        obj = f"build/src/{name}.o"
        sec = f".r_{off:08X}"
    elif typ == "data":
        obj = f"build/asm/nonmatchings/data/{name}.data.s.o"
        sec = f".r_{off:08X}"
    else:
        obj = f"build/asm/nonmatchings/{name}.s.o"
        sec = f".r_{off:08X}"
    try:
        out = subprocess.run([OD, "-h", obj], capture_output=True,
                             text=True, env=env, check=True).stdout
    except Exception as e:
        print(f"0x{off:X} {name}: OBJ MISSING ({e.__class__.__name__})")
        bad += 1
        continue
    m = re.search(rf"^\s*\d+\s+{re.escape(sec)}\s+([0-9a-fA-F]+)", out, re.M)
    if not m:
        print(f"0x{off:X} {name}: section {sec} ABSENT")
        bad += 1
        continue
    got = int(m.group(1), 16)
    if got != size:
        print(f"0x{off:X} {name}: yaml 0x{size:X} obj 0x{got:X} "
              f"({'OVERFLOW +0x%X' % (got - size) if got > size else 'short'})")
        bad += 1
print(f"{bad} mismatches / {len(rows)} rows")

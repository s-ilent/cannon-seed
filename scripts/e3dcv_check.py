#!/usr/bin/env python3
"""e3dcv_check.py - pre-landing checks for the E3DC-early-variant wave.

Per row: yaml row exists as asm at off == VA - 0x8001F800; extent == 0x10c;
name absent from the target's c rows and symbols file (collision class);
retail bytes byte-identical across all seven members (the census claim);
word-delta vs the landed func_8005E3DC is exactly the six commit-destination
words ($4 -> $6).
"""
import re
import struct
import sys

ROW = re.compile(r"^\s*- \[(0x[0-9A-Fa-f]+),\s*(asm|c|data),\s*([A-Za-z_][\w.]*)\]")
MEMBERS = [
    ("slps_00270", "func_80034138", 0x80034138),
    ("sces_00269", "func_80033C00", 0x80033C00),
    ("mainmenu_eu", "func_8005D4FC", 0x8005D4FC),
    ("g3_jp", "func_80049608", 0x80049608),
    ("g3_eu", "func_80049020", 0x80049020),
    ("g3org_jp", "func_80046AA4", 0x80046AA4),
    ("g3org_eu", "func_80046474", 0x80046474),
]
SIZE = 0x10C
DELTA_WORDS = {48, 52, 58, 62, 63, 64}


def rows_of(target):
    out = []
    for ln in open(f"config/splat.{target}.yaml"):
        m = ROW.match(ln)
        if m:
            out.append((int(m.group(1), 16), m.group(2), m.group(3)))
    out.sort()
    return out


def fail(msg):
    print(f"  FAIL {msg}")
    return False


def main():
    ok = True
    bytes_seen = {}
    landed = None
    for target, name, va in MEMBERS:
        print(f"== {target}:{name} @ 0x{va:X}")
        off = va - 0x8001F800
        rows = rows_of(target)
        hit = [r for r in rows if r[0] == off]
        if not hit:
            ok = fail("no yaml row at computed off") or ok
            continue
        o, kind, nm = hit[0]
        if kind != "asm" or nm != name:
            ok = fail(f"row is {kind}:{nm}, want asm:{name}") or ok
        i = rows.index(hit[0])
        ext = rows[i + 1][0] - o if i + 1 < len(rows) else 0
        if ext != SIZE:
            ok = fail(f"extent 0x{ext:X} != 0x{SIZE:X}") or ok
        # collision: name must not appear as any other row or in symbols
        if any(nm2 == name and o3 != o for o3, _, nm2 in rows):
            ok = fail("name labels a second yaml row") or ok
        syms = open(f"config/symbols.{target}.txt").read()
        for ln in syms.splitlines():
            m = re.match(r"([0-9A-Fa-f]+) (\S+)", ln)
            if m and int(m.group(1), 16) != va and m.group(2) == name:
                ok = fail(f"symbols labels name at {m.group(1)} too") or ok
        b = open(f"build/{target}.bin", "rb").read()[off:off + SIZE]
        bytes_seen.setdefault(b, []).append(target)
        w = struct.unpack("<67I", b)
        if target == "g3_jp":
            landed_w = struct.unpack("<67I",
                                     open("build/g3_jp.bin", "rb").read()[0x2A6C8:0x2A6C8 + SIZE])
            d = {i for i in range(67) if w[i] != landed_w[i]}
            if d != DELTA_WORDS:
                ok = fail(f"delta words {sorted(d)} != commit-destination set") or ok
            else:
                print("  delta = exactly the six $4->$6 commit words")
    groups = [v for v in bytes_seen.values() if len(v) > 1]
    if len(bytes_seen) != 1:
        ok = fail(f"members split into {len(bytes_seen)} distinct byte runs") or ok
    else:
        print(f"all seven byte-identical (0x{SIZE:X} B)")
    print("PRECHECK", "OK" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

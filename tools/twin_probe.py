#!/usr/bin/env python3
"""twin_probe.py - cross-target byte-twin candidates for landed sources.

The four region-pair lists are name-keyed and region-scoped; a function
landed for one executable can reappear byte-identical in another image
under a different name. Hash every function's retail bytes across all
eight targets, and report each unmatched copy whose bytes equal a
matched function's bytes (a C source or c row on the matched side).

Usage: twin_probe.py [target ...]     (default: all eight)
Output: stdout summary + build/twin_probe.txt, one candidate per line.
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pair_report import (REPO, baseline_bytes, elf_funcs,  # noqa: E402
                         fn_class, is_matched)

TARGETS = ["slps_00270", "sces_00269", "mainmenu_jp", "mainmenu_eu",
           "g3_jp", "g3_eu", "g3org_jp", "g3org_eu"]
MIN_SIZE = 0x18   # below this, leaves collide on jr ra; nop


def main():
    want = sys.argv[1:] or TARGETS
    groups = {}
    for t in want:
        elf = os.path.join(REPO, f"build/{t}.elf")
        if not os.path.exists(elf):
            print(f"{t}: no build ELF, skipped")
            continue
        for name, (va, size) in elf_funcs(elf).items():
            if size < MIN_SIZE:
                continue
            b = baseline_bytes(t, va, size)
            if b is None:
                continue
            groups.setdefault(hashlib.blake2b(b, digest_size=16).digest(),
                              []).append((t, name, va, size,
                                          is_matched(t, name, va)))
    rows = []
    for entries in groups.values():
        if len(entries) < 2:
            continue
        src = [e for e in entries if e[4]
               and fn_class(e[0], e[2], e[3], e[1]) == "compiler"]
        dst = [e for e in entries if not e[4]]
        if not src or not dst:
            continue
        for t, name, va, size, _ in dst:
            s = src[0]
            rows.append((t, name, va, size, s[0], s[1], s[2]))
    rows.sort()
    for t, name, va, size, st, sname, sva in rows:
        print(f"{t:12s} {name:32s} {va:08X} sz={size:#05x}  "
              f"<= {st}:{sname} {sva:08X}")
    print(f"\n{len(rows)} unmatched byte-twins of matched functions")
    with open(os.path.join(REPO, "build/twin_probe.txt"), "w") as f:
        for r in rows:
            f.write(f"{r[0]} {r[1]} {r[2]:08X} {r[3]} "
                    f"{r[4]} {r[5]} {r[6]:08X}\n")


if __name__ == "__main__":
    main()

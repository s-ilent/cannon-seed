#!/usr/bin/env python3
"""judge_fulldiff.py - full word-by-word diff of a judged unit vs retail.

Companion to tools/judge_unit.py (which prints only the first 8 diffs).
Run AFTER judge_unit has built build/judge/<unit>.bin: slices retail at
the unit's yaml row (same VA/offset law as judge_unit: va = 0x80020000 +
rom - 0x800), disassembles both sides with capstone and prints every
differing word as built|retail pairs, with the last matching word before
each gap (alignment anchors) and a run-length summary.

Usage: python3 scripts/bm_unit_decode/judge_fulldiff.py <target> <unit>
"""
import os
import struct
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "tools"))

try:
    import capstone
except ImportError:
    capstone = None

BASE_VA = 0x80020000
HDR = 0x800


def c_rows(target):
    import yaml
    cfg = yaml.safe_load(open(f"{REPO}/config/splat.{target}.yaml"))
    allsubs, cs = [], []
    for seg in cfg["segments"]:
        if isinstance(seg, dict) and seg.get("type") == "code":
            for e in seg.get("subsegments", []):
                if isinstance(e, list) and len(e) >= 2:
                    allsubs.append(e)
                    if len(e) >= 3 and e[1] == "c":
                        cs.append(e)
    out = []
    for e in cs:
        i = allsubs.index(e)
        end = allsubs[i + 1][0] if i + 1 < len(allsubs) else e[0] + 0x10
        out.append((e[2], e[0], end - e[0]))
    return out


def disasm(words, va):
    if capstone is None:
        return ""
    md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32 |
                     capstone.CS_MODE_LITTLE_ENDIAN)
    md.skipdata = True
    out = []
    for ins in md.disasm(bytes(words), va):
        out.append(f"{ins.mnemonic} {ins.op_str}")
    return " | ".join(out)


def main():
    target, unit = sys.argv[1], sys.argv[2]
    rows = {n: (n, r, x) for n, r, x in c_rows(target)}
    if unit not in rows:
        print(f"{unit}: no c row", file=sys.stderr)
        return 2
    _, rom, extent = rows[unit]
    va = BASE_VA + rom - HDR
    built = open(f"{REPO}/build/judge/{unit}.bin", "rb").read()
    base = open(f"{REPO}/baselines/{target}.bin", "rb")
    base.seek(rom)
    retail = base.read(extent)
    print(f"unit {unit}: va 0x{va:08X} rom 0x{rom:X} extent {extent} "
          f"built {len(built)}")
    n = min(len(built), len(retail))
    bad = [i for i in range(0, n, 4) if built[i:i+4] != retail[i:i+4]]
    print(f"diff words: {len(bad)}/{n//4}")

    # group into runs separated by >=2 matching words
    runs = []
    for i in bad:
        if runs and i - runs[-1][1] <= 8:
            runs[-1][1] = i
            runs[-1][2].append(i)
        else:
            runs.append([i, i, [i]])
    for start, end, idxs in runs:
        a0 = max(0, start - 4)
        anchor = f"anchor@0x{va+a0:08X}: {disasm(retail[a0:a0+4], va+a0)}"
        print(f"\n== run 0x{va+start:08X}..0x{va+end:08X} "
              f"({len(idxs)} words) {anchor}")
        for i in idxs[:40]:
            bw, rw = built[i:i+4], retail[i:i+4]
            print(f"  0x{va+i:08X}  B {bw.hex().upper()}  "
                  f"{disasm(bw, va+i):<28} | R {rw.hex().upper()}  "
                  f"{disasm(rw, va+i)}")
        if len(idxs) > 40:
            print(f"  ... {len(idxs)-40} more")
    if len(built) != len(retail):
        print(f"\nSIZE delta: built-retail = {len(built)-len(retail)} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())

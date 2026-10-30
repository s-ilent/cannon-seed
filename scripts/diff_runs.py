#!/usr/bin/env python3
"""diff-run analyzer for judge bins: group word diffs into runs."""
import struct
import sys

BASE_VA = 0x80020000
HDR = 0x800

def load_retail_slice(target, va, size):
    path = f"baselines/{target}.bin"
    data = open(path, "rb").read()
    off = va - BASE_VA + HDR
    return data[off:off + size]

def words(b):
    return [struct.unpack_from(">I", b, i)[0] for i in range(0, len(b) - 3, 4)]

def main():
    target, va_s, size_s, built_path = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    va = int(va_s, 16)
    size = int(size_s, 16)
    retail = load_retail_slice(target, va, size)
    built = open(built_path, "rb").read()
    rw, bw = words(retail), words(built)
    n = max(len(rw), len(bw))
    runs = []
    i = 0
    while i < n:
        r = rw[i] if i < len(rw) else None
        b = bw[i] if i < len(bw) else None
        if r != b:
            j = i
            while j < n:
                r2 = rw[j] if j < len(rw) else None
                b2 = bw[j] if j < len(bw) else None
                if r2 != b2:
                    j += 1
                else:
                    break
            runs.append((i, j))
            i = j
        else:
            i += 1
    print(f"{len(runs)} diff run(s), retail {len(rw)}w built {len(bw)}w")
    for (a, bnd) in runs:
        print(f"--- run 0x{va + a*4:06x}..0x{va + bnd*4:06x} ({bnd-a} words)")
        for k in range(a, min(bnd, a + 8)):
            r = f"{rw[k]:08x}" if k < len(rw) else "________"
            b = f"{bw[k]:08x}" if k < len(bw) else "________"
            mark = "R" if k >= len(bw) else ("B" if k >= len(rw) else " ")
            print(f"  0x{va + k*4:06x} {mark} retail {r}  built {b}")
        if bnd - a > 8:
            print(f"  ... {bnd - a - 8} more")

main()

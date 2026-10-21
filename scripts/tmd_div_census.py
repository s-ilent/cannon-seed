#!/usr/bin/env python3
"""Masked byte census for the GsTMDdiv* divider bodies across all 8 baselines.

Usage: tmd_div_census.py <target> <file_off_hex> <size_hex> <off1,off2,...>
Masks the given word-offsets (relative to row start, 4-byte words) then
searches every baseline .bin for the masked pattern. Reports hit target +
file offset. Baseline file offset law: off = VA - 0x80020000 + 0x800.
"""
import sys, os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGETS = ["slps_00270", "sces_00269", "mainmenu_jp", "mainmenu_eu",
           "g3_jp", "g3_eu", "g3org_jp", "g3org_eu"]


def main():
    src_t, off_s, size_s = sys.argv[1], int(sys.argv[2], 0), int(sys.argv[3], 0)
    mask_offs = [int(x, 0) for x in sys.argv[4].split(",")]
    with open(os.path.join(REPO, f"baselines/{src_t}.bin"), "rb") as f:
        data = f.read()
    pat = bytearray(data[off_s:off_s + size_s])
    for o in mask_offs:
        pat[o:o + 4] = b"\x00\x00\x00\x00"
    print(f"pattern from {src_t} @ {off_s:#x} size {size_s:#x}, "
          f"masked word offs {[hex(o) for o in mask_offs]}")
    # stage-1 anchor: the contiguous run of words BEFORE the first masked
    # slot (relocations never sit before the first jal in these bodies)
    first = min(mask_offs) if mask_offs else size_s
    anchor = bytes(pat[:first])
    for t in TARGETS:
        with open(os.path.join(REPO, f"baselines/{t}.bin"), "rb") as f:
            blob = f.read()
        hits, i = [], 0
        while True:
            i = blob.find(anchor, i)
            if i < 0:
                break
            ok = True
            for o in range(0, size_s, 4):
                if o in mask_offs:
                    continue
                if blob[i + o:i + o + 4] != bytes(pat[o:o + 4]):
                    ok = False
                    break
            if ok and i + size_s <= len(blob):
                hits.append(i)
            i += 4
        if hits:
            print(f"  {t}: {len(hits)} hit(s) " +
                  " ".join(f"{h:#x}" for h in hits))
        else:
            print(f"  {t}: -")


if __name__ == "__main__":
    main()

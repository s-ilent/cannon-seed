#!/usr/bin/env python3
"""bm_family_map.py - map the gcc movstrsi block-move family across targets.

The family: out-of-line chunks emitted for 0x80-byte struct assignments
(mips.c expand_block_move loop form). Chunk rhythm per copy:
  0x1c head (or/andi/beqz dispatch + end setup)  [copy 1's head lives in
      the owning function's body]
  0x54 unaligned loop  (lwl/lwr x4 + swl/swr x4, 16-stride, bne back,
      j out to next chunk)
  0x4  aligned-path end setup (addiu t0, src, 0x80)
  0x2c aligned loop    (lw x4 + sw x4, 16-stride, bne back, falls through)

Signature: the unaligned loop's first eight words (register binding
identical to the probe's a2-cursor binding):
  88C20003 98C20000 88C30007 98C30004 88C4000B 98C40008 88C5000F 98C5000C

For every hit, report VA, and walk forward to locate the 0x4 + 0x2c
chunks (the aligned loop's last word + the bne-back) to confirm the
rhythm. Baselines only - no build, no oracle.
"""
import glob
import os
import struct
import sys

# spimdisasm comments print MEMORY byte order (little-endian dwords) -
# the signature is the raw bytes exactly as they sit in the payload.
SIG = bytes.fromhex(
    "0300C288 0000C298 0700C388 0400C398"
    " 0B00C488 0800C498 0F00C588 0C00C598".replace(" ", "")
)
# aligned loop's lw run (a2 cursor) first four words
ALIGNED = bytes.fromhex(
    "0000C28C 0400C38C 0800C48C 0C00C58C".replace(" ", "")
)

BASE = os.environ.get("REPO", "/home/z/my-project/cannon-seed")


def scan(path):
    with open(path, "rb") as f:
        data = f.read()
    hits = []
    off = 0
    while True:
        i = data.find(SIG, off)
        if i < 0:
            break
        if i % 4:
            off = i + 1
            continue
        va = 0x80010000 + i  # payload file offset == VA - 0x80010000 (all 8 targets load 0x80020000 at file 0x800/0x10000? no - report both)
        # the boots' payload starts at file 0x800 (vram 0x80020000);
        # the six modules start at file 0x0 (vram 0x80020000/0x80010000).
        # report the file offset; the caller maps it.
        hits.append((i, ALIGNED in data[i + 0x54 : i + 0x74]))
        off = i + 4
    return hits


def main():
    for path in sorted(glob.glob(os.path.join(BASE, "baselines", "*.bin"))):
        name = os.path.basename(path)[:-4]
        hits = scan(path)
        if not hits:
            print(f"{name}: 0 hits")
            continue
        parts = []
        for off, aligned in hits:
            parts.append(f"file {off:#x} (VA~{off + 0x80020000 - 0x800:#x} boot / {off + 0x80020000:#x} module) aligned={'Y' if aligned else 'N'}")
        print(f"{name}: {len(hits)} unaligned-loop hit(s)")
        for p in parts:
            print(f"   {p}")


if __name__ == "__main__":
    sys.exit(main())

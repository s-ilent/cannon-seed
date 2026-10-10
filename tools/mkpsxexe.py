#!/usr/bin/env python3
"""mkpsxexe.py - regenerate the 2048-byte PS-X EXE header from committed
config and prepend it to the linked payload, producing the full image that
`make verify` compares against retail.

The header fields (entry pc0, load t_addr, initial sp, regional Sony mark)
are build configuration measured once in Phase 1 (docs/LOADMAP.md,
tools/exe_map.py) and committed in config/exe.json. Nothing is read from
the retail baseline here: the SHA-1 oracle (config/sha1/) is the judge.

Header layout (standard PS-X EXE, little-endian):
  0x00  "PS-X EXE"            0x08  zeros (8)
  0x10  pc0                   0x14  gp0 (0 - crt0 sets $gp)
  0x18  t_addr (0x80020000)   0x1C  t_size (payload size)
  0x20  data_addr/size = 0    0x28  bss_addr/size = 0
  0x30  initial sp (0x801FFFF0)     0x34..0x4B zeros
  0x4C  ASCII mark, NUL-padded to 0x80
  0x80  zeros through 0x800

Usage: python3 tools/mkpsxexe.py TARGET
  reads  build/<TARGET>.payload.bin
  writes build/<TARGET>.bin
"""

import json
import struct
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HEADER_SIZE = 0x800


def main(argv):
    if len(argv) < 2:
        raise SystemExit("usage: mkpsxexe.py TARGET")
    target = argv[1]
    cfg = json.loads((REPO / "config" / "exe.json").read_text())
    if target not in cfg:
        raise SystemExit(f"{target} not in config/exe.json")
    t = cfg[target]

    payload_path = REPO / "build" / f"{target}.payload.bin"
    payload = payload_path.read_bytes()

    h = bytearray(HEADER_SIZE)
    h[0:8] = b"PS-X EXE"
    struct.pack_into("<I", h, 0x10, int(t["pc0"], 16))
    struct.pack_into("<I", h, 0x14, int(t.get("gp0", "0"), 16))
    struct.pack_into("<I", h, 0x18, int(t["t_addr"], 16))
    struct.pack_into("<I", h, 0x1C, len(payload))
    struct.pack_into("<I", h, 0x30, int(t["sp0"], 16))
    mark = t["mark"].encode("ascii")
    h[0x4C : 0x4C + len(mark)] = mark  # rest stays NUL

    out = REPO / "build" / f"{target}.bin"
    out.write_bytes(bytes(h) + payload)
    print(f"mkpsxexe: {out.relative_to(REPO)} ({HEADER_SIZE + len(payload)} bytes, "
          f"pc0={t['pc0']})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

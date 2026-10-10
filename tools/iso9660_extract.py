#!/usr/bin/env python3
"""iso9660_extract.py — extract files from a mode2 form1/form2 raw image.

Works on the 2352-byte/sector main-channel .bin produced by chd_extract.py.
Plain ISO9660 (PSX discs don't use Joliet/RockRidge extensions for their
boot files). Usage:

    python3 iso9660_extract.py IMAGE.BIN /lba/out/dir [path/in/iso ...]

With no iso paths, lists the whole tree. Paths are like SYSTEM.CNF;1 or
DRAGOON/FILE.DAT;1 (directory separator '/').
"""

import struct
import sys
from pathlib import Path

SEC = 2352
USER_OFF = 24          # mode2: 12 sync + 4 header + 8 subheader
USER_LEN = 2048        # form1 user data


class Iso:
    def __init__(self, path: Path):
        self.f = open(path, "rb")
        self.f.seek(16 * SEC + USER_OFF)
        pvd = self.f.read(USER_LEN)
        if pvd[1:6] != b"CD001":
            raise ValueError("no ISO9660 PVD at sector 16")
        self.volume_id = pvd[40:72].decode("ascii", "replace").strip()
        self.root = self._dirrec(pvd[156:156+34])

    def _dirrec(self, r: bytes) -> dict:
        lba = int.from_bytes(r[2:6], "little")
        size = int.from_bytes(r[10:14], "little")
        flags = r[25]
        name_len = r[32]
        name = r[33:33 + name_len]
        return {"lba": lba, "size": size, "flags": flags, "name": name}

    def _read_dir(self, lba: int, size: int):
        self.f.seek(lba * SEC + USER_OFF)
        data = self.f.read(size)
        out = []
        pos = 0
        while pos < len(data):
            ln = data[pos]
            if ln == 0:
                # rest of sector
                pos = ((pos // USER_LEN) + 1) * USER_LEN
                continue
            out.append(self._dirrec(data[pos:pos + ln]))
            pos += ln
        return out

    def lookup(self, path: str) -> dict:
        node = self.root
        for part in path.split("/"):
            part = part.upper()
            node = next((e for e in self._read_dir(node["lba"], node["size"])
                         if e["name"].decode("ascii", "replace").upper()
                         in (part, part + ";1")), None)
            if node is None:
                raise FileNotFoundError(path)
        return node

    def read(self, node: dict) -> bytes:
        if node["flags"] & 2:
            raise ValueError("is a directory")
        self.f.seek(node["lba"] * SEC + USER_OFF)
        return self.f.read(node["size"])

    def walk(self, node=None, prefix=""):
        node = node or self.root
        for e in self._read_dir(node["lba"], node["size"]):
            name = e["name"].decode("ascii", "replace")
            if name in ("\x00", "\x01"):
                continue
            if e["flags"] & 2:
                yield from self.walk(e, prefix + name + "/")
            else:
                yield prefix + name, e


def main():
    iso = Iso(Path(sys.argv[1]))
    outdir = Path(sys.argv[2])
    paths = sys.argv[3:]
    print(f"volume: {iso.volume_id!r}")
    if not paths:
        for name, e in iso.walk():
            kind = "DIR " if e["flags"] & 2 else "file"
            print(f"  {kind} {name:40} lba={e['lba']:7d} size={e['size']}")
        return
    outdir.mkdir(parents=True, exist_ok=True)
    for p in paths:
        node = iso.lookup(p)
        data = iso.read(node)
        dest = outdir / p.replace("/", "_")
        dest.write_bytes(data)
        print(f"extracted {p} -> {dest} ({len(data)} bytes)")


if __name__ == "__main__":
    main()

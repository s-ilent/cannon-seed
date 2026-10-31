#!/usr/bin/env python3
"""probe_psyq_blobs2 - systematic grammar walk of the pre-table blob layer.

Tests the ALIAS? hypothesis: the def rows for the module's own publics live
in the 06/02 chunk layer between the LNK table and the symbol table, as
ANONYMOUS rows (name supplied by the publics list order).

Grammar attempts, per module, over data[LNK_end .. table_start]:
  - path region after the last LNK entry: 0x1c ... scan to a stable anchor
  - records of form: [u8 kind] ...
Track: counts of 0x06/0x02 chunk headers, trailing anonymous kind rows.
"""
import re
import struct
import sys

sys.path.insert(0, "tools")
from omf_pubsyms import PsyqLib  # noqa: E402

KIND_PAYLOAD = {0x0C: 8, 0x0E: 2, 0x12: 6}


def lnk_end(data, mod):
    """Return offset just past the last LNK entry name+0x1c marker."""
    end = mod.offset + mod.size
    o = mod.offset + 20
    while o < end and data[o] != 0x00:
        ln = data[o]
        o += 1 + ln
    if o < end and data[o] == 0x00:
        o += 1
    o += 3  # LNK
    last = o
    while o < end:
        ln = data[o]
        p = o + 1 + ln
        if p >= end or data[p] == 0x1C:
            last = o
            break
        o = p + 6
    # from last entry name: name, then 0x1c, then path region
    p = last + 1 + data[last]
    return p  # points at the 0x1c byte


def main():
    lib = PsyqLib(sys.argv[1])
    rx = re.compile(sys.argv[2]) if len(sys.argv) > 2 else None
    for mod in lib.modules:
        if rx and not rx.search(mod.name):
            continue
        data = lib.data
        end = mod.offset + mod.size
        p = lnk_end(data, mod)
        # skip the debug-path region: [0x1c][u16?][len][path]... find where
        # printable-ascii path ends
        q = p
        while q < end and data[q] != 0x06 and data[q] != 0x02:
            q += 1
        print(f"{mod.name:8s} pubs={len(mod.publics):2d} "
              f"path@{p:#x} chunks@{q:#x} table@{mod.table_start:#x} "
              f"blob={mod.table_start - q:#x}B")
        # walk chunks from q
        o = q
        kinds = []
        while o < end:
            k = data[o]
            if k == 0x06:
                # guess: 06 + u16 + 00?
                kinds.append(f"06@{o - mod.offset:x}:{data[o + 1]:02x}")
                o += 3
                continue
            if k == 0x02:
                sz = struct.unpack_from("<H", data, o + 1)[0]
                kinds.append(f"02@{o - mod.offset:x}:sz{sz:#x}")
                o += 4 + sz
                continue
            break
        # remaining bytes to table_start: dump structure summary
        rest = data[o:mod.table_start] if mod.table_start else b""
        if mod.table_start is None:
            rest = data[o:end]
        n0a = rest.count(0x0A)
        # find trailing anonymous kind rows: from the end, try the
        # [0x00-terminated tail] then preceding kind rows
        print(f"    chunks: {kinds}")
        if rest:
            print(f"    post-chunk rest ({len(rest)}B): {rest[:40].hex(' ')}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""probe_psyq_blobs - dump the unparsed 06/02 section-blob layer of a psyq module.

The omf_pubsyms container walk parses publics -> LNK -> symbol table and
leaves the region between the LNK table and the discovered table start
unparsed ("06 xx 00 / 02 yy 00 chunk headers"). The ALIAS? hypothesis
(cron-20261101-0151 NEXT (2)): the def rows for the own-public-0x0e
publics live there.

This probe dumps that region byte-exactly for chosen modules, plus a
structured guess at the chunk grammar (u8 0x06/0x02 header + payload?).

Usage:
  python3 scripts/probe_psyq_blobs.py <lib> <modregex> [--max N]
"""
import re
import struct
import sys

sys.path.insert(0, "tools")
from omf_pubsyms import PsyqLib  # noqa: E402


def hexdump(data, base=0, width=16):
    lines = []
    for i in range(0, len(data), width):
        chunk = data[i:i + width]
        hx = " ".join(f"{b:02x}" for b in chunk)
        asc = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        lines.append(f"  {base + i:06x}  {hx:<{width * 3}}  {asc}")
    return "\n".join(lines)


def main():
    lib = PsyqLib(sys.argv[1])
    rx = re.compile(sys.argv[2])
    mods = [m for m in lib.modules if rx.search(m.name)]
    for mod in mods:
        print(f"module {mod.name!r} @{mod.offset:#x} size={mod.size:#x} "
              f"hdr_x={mod.hdr_x}")
        print(f"  publics: {mod.publics}")
        print(f"  sections: {sorted(mod.sections.items())}")
        print(f"  table_start={mod.table_start:#x} tail={mod.tail_name!r}")
        # walk region: from LNK end to table start
        # recompute LNK end: after publics terminator, parse LNK again
        data = lib.data
        end = mod.offset + mod.size
        o = mod.offset + 20
        while o < end and data[o] != 0x00:
            ln = data[o]
            o += 1 + ln
        if o < end and data[o] == 0x00:
            o += 1
        assert data[o:o + 3] == b"LNK", f"LNK not at {o:#x}"
        o += 3
        while o < end:
            ln = data[o]
            p = o + 1 + ln
            if p >= end or data[p] == 0x1C:
                # last entry + debug path region start
                break
            o = p + 6
        print(f"  LNK ends, last entry at {o:#x}")
        # the 0x1c debug-path region: [0x1c][len][path]... find where it
        # ends - scan for the 06/02 chunk run start candidates
        print(f"  debug-path region from {o:#x}:")
        q = o
        print(hexdump(data[q:min(q + 0x60, end)], q))
        # find first 06/02-ish byte after the path region
        # heuristic: path region is [len][ascii path] 00 maybe repeated?
        # dump up to table_start instead - full blob region
        blob = data[o:mod.table_start]
        print(f"  --- full pre-table region {o:#x}..{mod.table_start:#x} "
              f"({len(blob)} bytes):")
        print(hexdump(blob, o))
        print(f"  --- symbol table @{mod.table_start:#x}:")
        tbl = data[mod.table_start:min(mod.table_start + 0x100, end)]
        print(hexdump(tbl, mod.table_start))
        print()


if __name__ == "__main__":
    main()

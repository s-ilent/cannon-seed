#!/usr/bin/env python3
"""probe_psyq_rows - forward-parse the row stream with extended kinds.

Finds, for each module, the earliest start from which a continuous
[len][name][kind][payload] walk (kinds 0x0c/0x0e/0x12/0x30) reaches the
module-end tail exactly. Reports row counts, unnamed-row candidates, and
kind histogram.
"""
import struct
import sys

sys.path.insert(0, "tools")
from omf_pubsyms import PsyqLib  # noqa: E402

KIND_PAYLOAD = {0x0C: 8, 0x0E: 2, 0x12: 6, 0x30: 8}


def try_parse(data, start, end):
    """Parse named rows from start; return (rows, stop) - stop = offset
    where the walk broke (should be the tail start on success)."""
    rows = []
    q = start
    while q < end:
        ln = data[q]
        if not (1 <= ln <= 128):
            return rows, q
        nm = data[q + 1:q + 1 + ln]
        if len(nm) != ln or not all(32 <= c < 127 for c in nm):
            return rows, q
        p = q + 1 + ln
        if p >= end:
            return rows, q
        kind = data[p]
        psz = KIND_PAYLOAD.get(kind)
        if psz is None or p + 1 + psz > end:
            return rows, q
        rows.append((nm.decode("ascii"), kind,
                     data[p + 1:p + 1 + psz]))
        q = p + 1 + psz
    return rows, q


def main():
    lib = PsyqLib(sys.argv[1])
    total_bad = 0
    for mod in lib.modules:
        data = lib.data
        end = mod.offset + mod.size
        # find the tail: last [len][name] 00 ending at module end
        tail_start = None
        for s in range(max(mod.offset + 20, end - 130), end - 2):
            ln = data[s]
            nm = data[s + 1:s + 1 + ln]
            if (1 <= ln <= 128 and len(nm) == ln
                    and all(32 <= c < 127 for c in nm)
                    and s + 1 + ln < end and data[s + 1 + ln] == 0x00
                    and s + 1 + ln + 1 == end):
                tail_start = s
                break
        if tail_start is None:
            print(f"{mod.name:10s} NO TAIL")
            total_bad += 1
            continue
        # earliest start that reaches the tail exactly
        best = None
        for s in range(mod.offset + 20, tail_start):
            rows, stop = try_parse(data, s, end)
            if stop == tail_start and rows:
                best = (s, rows)
                break
        if best is None:
            print(f"{mod.name:10s} NO FULL STREAM (tail@{tail_start:#x})")
            total_bad += 1
            continue
        s, rows = best
        kinds = {}
        for _, k, _p in rows:
            kinds[k] = kinds.get(k, 0) + 1
        # def rows: kind 0x0c/0x30
        defs = [(nm, struct.unpack("<HHI", p)) for nm, k, p in rows
                if k in (0x0C, 0x30) and len(p) == 8]
        pubs = set(mod.publics)
        pub_defs = [(nm, b, off) for nm, (a, b, off) in defs if nm in pubs]
        print(f"{mod.name:10s} stream@{s:#x} rows={len(rows):3d} "
              f"kinds={ {hex(k): v for k, v in sorted(kinds.items())} } "
              f"pubs={len(mod.publics)} pub_defs={len(pub_defs)}")
    print(f"# modules with issues: {total_bad}/{len(lib.modules)}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""probe_psylib_reczone - the PSYLIB record-zone law probe (cron-20261101-0806).

The banked cron-20261101-0651 NEXT item (1): the 02-record chain law (what
bounds a run of 0a/2c records) + the per-object base-derivation formula
(SEQREAD's second cluster at +0x10ea is the anchor case). This probe walks
the FULL post-path zone of every module byte-exactly, classifies every
record shape (06 marker / 02 chunk / 0a / 2c / other), and cross-references:

  - the 0a-record u16 offsets against the module's def rows and against
    addiu-sp prologue positions;
  - the 2c records against the 0a run (bounds/terminators?);
  - where each 02-chunk starts relative to 06 markers and to the 0a/2c
    runs (the inter-record law).

POST-HOC CORRECTION (same window): the zone is NOT a pure record stream.
VMANAGER's defs land as real code (base 0x10668, all 38 valid MIPS heads)
at file positions that map THROUGH the zone, and the walk's '?' blobs are
the classifier misreading record-zone CODE clusters (code resumes at
0x11820 without a header) plus short fixup-target forms ([02][u8][00])
that this probe does not model. The classify walk is kept as a ZONE MAP
tool, not a law: every '?' position is a place where the zone grammar
still has an unparsed shape. The def-base answer banked this window is
the all-landings-valid constraint (tools/omf_pubsyms.py:
solve_def_base_valid) - the base itself stays underivable from the
record structure so far.

Usage:
    python3 scripts/probe_psylib_reczone.py [lib ...] [module-regex]
"""
import glob
import os
import re
import struct
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import omf_pubsyms as op  # noqa: E402

DEFAULT_LIBS = sorted(glob.glob("/home/z/my-project/psyq/3.3/PSX/LIB/*.LIB"))


def classify_zone(d, o, end):
    """Walk [o, end) classifying records. Returns a list of
    (off, kind, size, detail) tuples covering every byte (unknown runs are
    emitted as ('?', n) blobs)."""
    out = []
    while o < end:
        b = d[o]
        if b == 0x06 and o + 3 <= end and d[o + 2] == 0x00:
            out.append((o, "06", 3, f"seg={d[o+1]:#04x}"))
            o += 3
        elif b == 0x02 and o + 3 <= end:
            size = struct.unpack_from("<H", d, o + 1)[0]
            out.append((o, "02", 3 + size, f"size={size:#06x}"))
            if size == 0:
                out.append((o, "02-size0", 3, ""))
                o += 3
            else:
                o += 3 + size
        elif b == 0x0A and o + 4 <= end:
            t = d[o + 1]
            off = struct.unpack_from("<H", d, o + 2)[0]
            out.append((o, "0a", 4, f"t={t:#04x} off={off:#06x}"))
            o += 4
        elif b == 0x2C and o + 6 <= end and d[o + 1] == 0x00:
            v = struct.unpack_from("<I", d, o + 2)[0]
            out.append((o, "2c0", 6, f"v={v:#010x}"))
            o += 6
        elif b == 0x2C and o + 9 <= end and d[o + 1] == 0x04:
            w = struct.unpack_from("<H", d, o + 2)[0]
            v = struct.unpack_from("<I", d, o + 4)[0]
            out.append((o, "2c4", 9, f"w={w} v={v:#010x}"))
            o += 9
        else:
            # unknown byte: coalesce into a blob
            start = o
            while o < end:
                bb = d[o]
                if bb == 0x06 and o + 3 <= end and d[o + 2] == 0x00:
                    break
                if bb == 0x02 and o + 3 <= end:
                    break
                if bb == 0x0A and o + 4 <= end:
                    break
                if bb == 0x2C and o + 6 <= end and d[o + 1] in (0x00, 0x04):
                    break
                o += 1
            out.append((start, "?", o - start, d[start:o].hex()[:64]))
    return out


def main(argv):
    libs = [a for a in argv[1:] if not a.startswith("-") and a.endswith(".LIB")]
    rx = None
    for a in argv[1:]:
        if not a.endswith(".LIB"):
            rx = re.compile(a)
    libs = libs or DEFAULT_LIBS
    for path in libs:
        try:
            lib = op.PsyqLib(path)
        except (OSError, ValueError) as e:
            print(f"# {path}: {e}")
            continue
        d = lib.data
        for m in lib.modules:
            if rx and not rx.search(m.name):
                continue
            blob, pe, np_ = op.first_code_chunk(d, m)
            if blob is None:
                continue
            end = m.offset + m.size
            ts = m.table_start or end
            zone = classify_zone(d, pe, min(ts, len(d)))
            defs = [(n, off) for n, k, a, b, off in op.def_map(m)
                    if k == 0x0C and b == 2]
            print(f"\n=== {os.path.basename(path)} {m.name} "
                  f"mod={m.offset:#x} size={m.size:#x} paths_end={pe:#x} "
                  f"blob1={blob:#x} table_start={ts:#x} defs={len(defs)}")
            kinds = {}
            for _o, k, sz, _det in zone:
                kinds[k] = kinds.get(k, 0) + 1
            print(f"  zone records: {kinds}")
            for off, k, sz, det in zone:
                if k in ("06", "0a", "2c0", "2c4") or k.startswith("02-size0") \
                        or k == "?":
                    print(f"  {off:#010x} {k:8s} sz={sz:<6} {det}")
                elif k == "02" and sz <= 3 + 32:
                    print(f"  {off:#010x} {k:8s} sz={sz:<6} {det}")
            if defs:
                print("  defs (b=2): " + ", ".join(
                    f"{n}@{off:#x}" for n, off in defs[:40]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

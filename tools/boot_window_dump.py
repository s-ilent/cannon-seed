#!/usr/bin/env python3
"""Contiguous-view dump of the boots' .sdata window offsets.

The queue item (2026-10-15 disc re-provision follow-ups) names two windows
inside the boot executables' payloads:

    slps_00270  payload 0x4632C..0x463FC  (VA 0x8006632C..0x800663FC, 0xD0 B)
    sces_00269  payload 0x45FC4..0x46098  (VA 0x80065FC4..0x80066098, 0xD4 B)

Payload offsets are VA - 0x80020000; offsets into the PS-X EXE baseline
files are payload + 0x800. Both views share these payload offsets.

VIEW CAVEAT: this tool reads baselines/ - the CONTIGUOUS raw-read views
(the woven re-layout). At these offsets the contiguous bytes present
8-byte records {u32 0xFE000002, u32 0}, not .sdata content. The TRUE user
data at the same offsets is the gameinfo slot map decoded in
docs/TASKS.md (window cron-20261017-0842 entry); dumping it needs the
--per-sector true-EXE trees, i.e. disc access. This tool's job is to
preserve the window offsets in-repo and to cross-check the JP/EU shift
relation in the contiguous view, where sces window == zero word + slps
window byte-exactly - the same +4 shift the true view shows.

Both boots must verify GREEN (`make verify TARGET=<t>`) for a dump to be
trustworthy.

Usage:
    python3 tools/boot_window_dump.py
            # analyze and print the report
    python3 tools/boot_window_dump.py --witness-dir DIR
            # additionally write per-target window/stream hexdumps and a
            # sha256 manifest into DIR. Keep DIR OUTSIDE the repo -
            # extracted asset bytes are never committed.
"""

import argparse
import hashlib
import struct
import sys

VRAM = 0x80020000
HDR = 0x800  # PS-X EXE header size: file offset = payload + HDR

# (target, window payload start, window payload end) - payload coordinates
WINDOWS = [
    ("slps_00270", 0x4632C, 0x463FC),
    ("sces_00269", 0x45FC4, 0x46098),
]

RECORD = bytes.fromhex("020000fe00000000")  # {0xFE000002, 0x00000000}
RECORD_INV = bytes.fromhex("00000000020000fe")  # the other 4-byte phase


def load(target):
    path = "baselines/%s.bin" % target
    with open(path, "rb") as f:
        return f.read()


def rec_ok(d, o, limit):
    """8-byte record at payload offset o matches the FE/0 shape."""
    if o < 0 or o + 8 > limit:
        return False
    w = d[o + HDR:o + HDR + 8]
    return w == RECORD or w == RECORD_INV


def strict_extent(d, anchor, limit):
    """Maximal [s, e) around anchor where bytes have period 8
    (d[i] == d[i+8] for all i in [s, e-8)). Phase-agnostic."""
    s = anchor
    while s - 8 >= 0 and d[s - 8 + HDR:s + HDR] == d[s + HDR:s + 8 + HDR]:
        s -= 8
    e = anchor
    while e + 8 <= limit and d[e + HDR:e + 8 + HDR] == d[e + 8 + HDR:e + 16 + HDR]:
        e += 8
    return s, e


def tolerant_extent(d, anchor, limit):
    """Like strict_extent but walks through up to one consecutive
    non-record 8-byte span on each side (record-shaped walk)."""
    s, bad = anchor, 0
    while s - 8 >= 0:
        if rec_ok(d, s - 8, limit):
            s -= 8
            bad = 0
        elif bad < 1:
            s -= 8
            bad += 1
        else:
            break
    e, bad = anchor, 0
    while e + 8 <= limit:
        if rec_ok(d, e, limit):
            e += 8
            bad = 0
        elif bad < 1:
            e += 8
            bad += 1
        else:
            break
    return s, e


def hexdump(d, payload_lo, payload_hi, va_base=VRAM):
    lines = []
    for o in range(payload_lo, payload_hi, 16):
        row = d[o + HDR:min(o + HDR + 16, payload_hi + HDR)]
        lines.append("%08X: %s" % (va_base + o,
                     " ".join("%02x" % b for b in row)))
    return "\n".join(lines)


def analyze(target, wlo, whi, dumps=None):
    d = load(target)
    limit = len(d) - HDR  # payload size
    win = d[wlo + HDR:whi + HDR]
    print("== %s window: payload 0x%X..0x%X (0x%X B) VA 0x%08X..0x%08X" %
          (target, wlo, whi, whi - wlo, VRAM + wlo, VRAM + whi))
    print("   sha256 %s" % hashlib.sha256(win).hexdigest())

    # record decomposition: optional zero lead word, then FE/0 records
    lead = win[:4] if win[:4] == b"\x00\x00\x00\x00" else b""
    off = len(lead)
    n_rec = 0
    while off + 8 <= len(win) and win[off:off + 8] in (RECORD, RECORD_INV):
        n_rec += 1
        off += 8
    trail = win[off:]
    print("   content: %s + %d x {0xFE000002, 0} records + trail 0x%X B"
          % ("zero lead word" if lead else "no lead word", n_rec, len(trail)))

    # extents of the host record region
    ss, se = strict_extent(d, wlo, limit)
    ts, te = tolerant_extent(d, wlo, limit)
    print("   host region strict  : payload 0x%X..0x%X (0x%X B) VA 0x%08X..0x%08X"
          % (ss, se, se - ss, VRAM + ss, VRAM + se))
    print("   host region tolerant: payload 0x%X..0x%X (0x%X B)"
          % (ts, te, te - ts))
    hdr_words = struct.unpack_from("<II", d, ts - 8 + HDR)
    print("   pre-stream u32 (ts-8, ts-4): 0x%08X 0x%08X"
          % (hdr_words[0], hdr_words[1]))
    print("   pre-stream 16B: %s"
          % " ".join("%02x" % b for b in d[ts - 16 + HDR:ts + HDR]))
    print("   post-stream 16B: %s"
          % " ".join("%02x" % b for b in d[te + HDR:te + 16 + HDR]))
    print("   payload tail 16B: %s"
          % " ".join("%02x" % b for b in d[limit - 16 + HDR:limit + HDR]))

    if dumps is not None:
        with open("%s/%s.window.hex" % (dumps, target), "w") as f:
            f.write(hexdump(d, wlo, whi) + "\n")
        with open("%s/%s.stream.hex" % (dumps, target), "w") as f:
            f.write(hexdump(d, ts, te) + "\n")
        print("   witness: %s/%s.{window,stream}.hex" % (dumps, target))
    return win


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--witness-dir", metavar="DIR", default=None,
                    help="write hexdumps + sha256 manifest here (repo-external)")
    args = ap.parse_args()

    wins = {}
    for target, wlo, whi in WINDOWS:
        wins[target] = analyze(target, wlo, whi, args.witness_dir)

    # JP/EU relation: the Europe window is a zero word followed by the
    # Japan window, byte-exact.
    jp, eu = wins["slps_00270"], wins["sces_00269"]
    rel = (b"\x00" * 4 + jp) == eu
    print("== JP/EU relation: sces window == zero word + slps window: %s"
          % ("BYTE-EXACT" if rel else "NO - investigate"))
    if args.witness_dir is not None:
        lines = []
        for target, wlo, whi in WINDOWS:
            d = load(target)
            win = d[wlo + HDR:whi + HDR]
            lines.append("%s window payload 0x%X..0x%X size 0x%X sha256 %s"
                         % (target, wlo, whi, len(win),
                            hashlib.sha256(win).hexdigest()))
        with open("%s/manifest.txt" % args.witness_dir, "w") as f:
            f.write("\n".join(lines) + "\n")
        print("   manifest: %s/manifest.txt" % args.witness_dir)
    return 0 if rel else 1


if __name__ == "__main__":
    sys.exit(main())

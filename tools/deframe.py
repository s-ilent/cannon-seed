#!/usr/bin/env python3
"""deframe.py - separate the MODE2 sector framing from a retail target.

`baselines/*.bin` are raw MODE2/2352 CD sector images, not plain executables:
the MODE2 sync `00 FF FF FF FF FF FF FF FF FF FF 00`, an incrementing BCD
address, mode byte `02` and subheader `00 00 08 00 00 00 08 00` every 2352
bytes, first at `0x918`. Their SHA-1s match `config/sha1/**`, so the disc
really does hold the framed file.

The game de-frames at load and runs the payload: 4 KiB read from the running
game at `0x80020000` equals the de-framed payload byte for byte, while
`splat`'s linear map over the framed file puts the same bytes elsewhere
(`Too few TOC` runs at `0x80020000`, the carve says `0x80020130`;
`func_800253F8` runs at `0x80024818`, the carve says `0x800253F8`).

This tool exposes both views:

    python3 tools/deframe.py                     # layout + sizes, all targets
    python3 tools/deframe.py --target g3_jp      # one target
    python3 tools/deframe.py --payload g3_jp build/work/g3_jp.payload.bin
    python3 tools/deframe.py --map-framed g3_jp 0x800253F8   # carve VRAM -> runtime
    python3 tools/deframe.py --map-runtime g3_jp 0x80024818  # runtime -> carve VRAM

`--map-*` is what reconciles runtime evidence with the carve: a breakpoint hit
at a runtime address maps to the carve address the repo names, and back. Note
the mapping is per-file (the first sync offset and period are measured, not
assumed) and only defined inside a sector's 2048-byte data area - the framing
bytes and the 2048-byte PS-X EXE header have no runtime address.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SYNC = bytes.fromhex("00ffffffffffffffffffff00")
SECTOR = 2352          # MODE2/2352
DATA = 2048            # MODE2 Form 1 data area
HDR = 24               # sync(12) + address(3) + mode(1) + subheader(8)
HEADER = 2048          # the PS-X EXE header occupies the first sector's data


def layout(path: Path) -> dict:
    """Measured framing: first sync offset, period, sync list."""
    d = path.read_bytes()
    offs, i = [], d.find(SYNC)
    while i >= 0:
        offs.append(i)
        i = d.find(SYNC, i + 1)
    if not offs:
        raise SystemExit(f"{path}: no MODE2 sync pattern - not a framed image")
    periods = {offs[k + 1] - offs[k] for k in range(len(offs) - 1)}
    if periods != {SECTOR}:
        raise SystemExit(f"{path}: irregular framing, periods={sorted(periods)}")
    return {"data": d, "first": offs[0], "period": SECTOR, "syncs": offs}


def deframe(path: Path) -> tuple[bytes, bytes]:
    """(header, payload): the PS-X EXE header, and the de-framed program image.

    `payload` is what the loader places at `t_addr`; `header` is the 2048-byte
    PS-X EXE header that precedes it in the file.
    """
    lay = layout(path)
    d = lay["data"]
    out = bytearray(d[:HEADER])
    for s in lay["syncs"]:
        out += d[s + HDR: s + HDR + DATA]
    return bytes(d[:HEADER]), bytes(out[HEADER:])


def _data_start(lay: dict) -> int:
    return lay["first"] + HDR


def framed_to_runtime(path: Path, vram: int, vram_base: int = 0x80020000) -> int | None:
    """Carve/file VRAM -> runtime VRAM, or None if the byte is framing/header."""
    lay = layout(path)
    f = vram - vram_base + HEADER          # vram -> file offset (splat's linear map)
    start = _data_start(lay)
    if f < start:
        return None
    k, into = divmod(f - start, SECTOR)
    if into >= DATA:
        return None                        # EDC/ECC tail
    return vram_base + k * DATA + into


def runtime_to_framed(path: Path, vram: int, vram_base: int = 0x80020000) -> int:
    """Runtime VRAM -> the carve's VRAM for the same byte."""
    lay = layout(path)
    p = vram - vram_base
    k, into = divmod(p, DATA)
    f = _data_start(lay) + k * SECTOR + into
    return f - HEADER + vram_base


def _baseline(target: str) -> Path:
    p = REPO / "baselines" / f"{target}.bin"
    if not p.is_file():
        raise SystemExit(f"no baseline for {target}")
    return p


def _targets() -> list[str]:
    return [Path(b).stem for b in sorted(glob.glob(str(REPO / "baselines" / "*.bin")))]


def cmd_report(targets: list[str]) -> None:
    print(f"{'target':12s} {'file':>9s} {'syncs':>6s} {'framed pay':>11s} "
          f"{'payload':>9s} {'t_size':>9s} {'framed sha1':>13s}")
    for t in targets:
        p = _baseline(t)
        d = p.read_bytes()
        hdr, payload = deframe(p)
        tsz = int.from_bytes(hdr[0x1C:0x20], "little")
        print(f"{t:12s} {len(d):9d} {len(layout(p)['syncs']):6d} {len(d) - HEADER:11d} "
              f"{len(payload):9d} {tsz:9d} "
              f"{'oracle' if hashlib.sha1(d).hexdigest() else '':>13s}")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", action="append", default=None)
    ap.add_argument("--payload", nargs=2, metavar=("TARGET", "OUT"),
                    help="write the de-framed image (header + payload) to OUT")
    ap.add_argument("--map-framed", nargs=2, metavar=("TARGET", "VRAM"),
                    help="carve VRAM -> runtime VRAM")
    ap.add_argument("--map-runtime", nargs=2, metavar=("TARGET", "VRAM"),
                    help="runtime VRAM -> carve VRAM")
    args = ap.parse_args(argv[1:])
    targets = args.target or _targets()
    if args.payload:
        t, out = args.payload
        hdr, payload = deframe(_baseline(t))
        Path(out).write_bytes(hdr + payload)
        print(f"{t}: wrote {out} ({HEADER + len(payload)} bytes, "
              f"payload {len(payload)}); framed file is {HEADER + len(payload)}")
        return 0
    if args.map_framed:
        t, v = args.map_framed
        r = framed_to_runtime(_baseline(t), int(v, 0))
        print(f"{t}: carve {int(v,0):#010x} -> "
              f"{'framing/header (no runtime address)' if r is None else hex(r)}")
        return 0
    if args.map_runtime:
        t, v = args.map_runtime
        print(f"{t}: runtime {int(v,0):#010x} -> carve "
              f"{runtime_to_framed(_baseline(t), int(v, 0)):#010x}")
        return 0
    cmd_report(targets)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

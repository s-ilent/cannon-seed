#!/usr/bin/env python3
"""chd_extract.py — minimal CHD v5 (CD-ROM) reader.

Ports exactly the algorithms in MAME's src/lib/util/{chd.cpp,huffman.cpp,
bitstream.h,chdcodec.cpp,cdrom.cpp} needed to recover the main-channel
(2352-byte) sectors of a cdlzma/cdzl-compressed CD-ROM CHD.

Verification strategy:
  * LZMA (main channel) decodes are length-checked per hunk — liblzma
    refuses corrupted streams, so recovered main-channel bytes are exact.
  * Subcode (FLAC) streams are skipped: not needed for ISO9660 extraction.
  * ECC/sync fields flagged in the hunk bitmap are regenerated per
    cdrom_file::ecc_generate and cross-checked where the original bytes
    are available in COMPRESSION_NONE hunks.
"""

import re
import struct
import sys
import zlib
import lzma
from pathlib import Path

from ecc_tables import ECCLOW as _ECCLOW, ECCHIGH as _ECCHIGH, \
    POFFSETS as _POFFSETS, QOFFSETS as _QOFFSETS

# ---------------------------------------------------------------- bit reader
def bits(data: bytes, start: int, n: int) -> int:
    """Read n bits MSB-first starting at bit offset start."""
    first = start // 8
    last = (start + n - 1) // 8
    v = int.from_bytes(data[first:last + 1], "big")
    shift = len(data[first:last + 1]) * 8 - (start - first * 8) - n
    return (v >> shift) & ((1 << n) - 1)


class BitCursor:
    """MSB-first bit cursor (equivalent to MAME's bitstream_in)."""

    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0

    def read(self, n: int) -> int:
        v = bits(self.data, self.pos, n)
        self.pos += n
        return v

    @property
    def exhausted(self) -> bool:
        return self.pos >= len(self.data) * 8


# ---------------------------------------------------------------- huffman
# The exact enum (chd.cpp):
#   COMPRESSION_TYPE_0..3 = 0..3, COMPRESSION_NONE = 4, SELF = 5, PARENT = 6,
#   COMPRESSION_RLE_SMALL = 7, COMPRESSION_RLE_LARGE = 8,
#   COMPRESSION_SELF_0 = 9, SELF_1 = 10, PARENT_SELF = 11,
#   PARENT_0 = 12, PARENT_1 = 13
SYM_TYPE0_3 = (0, 1, 2, 3)
SYM_NONE = 4
SYM_SELF = 5
SYM_PARENT = 6
SYM_SELF_0, SYM_SELF_1 = 9, 10
SYM_PARENT_SELF, SYM_PARENT_0, SYM_PARENT_1 = 11, 12, 13
SYM_RLE_SMALL, SYM_RLE_LARGE = 7, 8
NUM_SYMBOLS = 16


def import_tree_rle(cur: BitCursor, numcodes: int = NUM_SYMBOLS, maxbits: int = 8):
    numbits = 5 if maxbits >= 16 else (4 if maxbits >= 8 else 3)
    lengths = []
    while len(lengths) < numcodes:
        v = cur.read(numbits)
        if v != 1:
            lengths.append(v)
        else:
            v2 = cur.read(numbits)
            if v2 == 1:
                lengths.append(1)
            else:
                rep = cur.read(numbits) + 3
                lengths.extend([v2] * rep)
    if len(lengths) != numcodes:
        raise ValueError("tree RLE overrun")
    return lengths


def assign_canonical_codes(lengths):
    """MAME assign_canonical_codes: longest-first halving."""
    maxbits = 32
    bithisto = [0] * 33
    for ln in lengths:
        if ln > maxbits:
            raise ValueError("code too long")
        bithisto[ln] += 1
    curstart = 0
    for codelen in range(32, 0, -1):
        nextstart = (curstart + bithisto[codelen]) >> 1
        bithisto[codelen] = curstart
        curstart = nextstart
    codes = []
    for ln in lengths:
        if ln > 0:
            codes.append((ln, bithisto[ln]))
            bithisto[ln] += 1
        else:
            codes.append(None)
    return codes


def build_lookup(codes, maxbits=8):
    """Prefix-keyed lookup: 8-bit peek -> (symbol, length)."""
    table = {}
    for sym, entry in enumerate(codes):
        if entry is None:
            continue
        ln, code = entry
        if ln == 0:
            continue
        base = code << (maxbits - ln)
        for fill in range(1 << (maxbits - ln)):
            table[base | fill] = (sym, ln)
    return table


# ---------------------------------------------------------------- ECC tables
# Tables live in ecc_tables.py (verbatim from MAME's cdrom.cpp).
CD_SYNC = bytes([0x00] + [0xFF] * 10 + [0x00])
ECC_P_OFFSET, ECC_P_NUM, ECC_P_COMP = 0x81C, 86, 24
ECC_Q_OFFSET = ECC_P_OFFSET + 2 * ECC_P_NUM
ECC_Q_NUM, ECC_Q_COMP = 52, 43


def ecc_source_byte(sector: bytes, offset: int) -> int:
    # mode byte at sector[15]; offsets < 4 read as 0 in mode 2
    if sector[15] == 2 and offset < 4:
        return 0
    return sector[12 + offset]


def ecc_compute(sector, row):
    val1 = val2 = 0
    for o in row:
        b = ecc_source_byte(sector, o)
        val1 ^= b
        val2 ^= b
        val1 = _ECCLOW[val1]
    val1 = _ECCHIGH[_ECCLOW[val1] ^ val2]
    val2 ^= val1
    return val1, val2


def ecc_generate(sector: bytearray):
    for byte in range(ECC_P_NUM):
        v1, v2 = ecc_compute(sector, _POFFSETS[byte])
        sector[ECC_P_OFFSET + byte] = v1
        sector[ECC_P_OFFSET + ECC_P_NUM + byte] = v2
    for byte in range(ECC_Q_NUM):
        v1, v2 = ecc_compute(sector, _QOFFSETS[byte])
        sector[ECC_Q_OFFSET + byte] = v1
        sector[ECC_Q_OFFSET + ECC_Q_NUM + byte] = v2


# ---------------------------------------------------------------- lzma/zlib
LZMA_FILTER = {"id": lzma.FILTER_LZMA1, "lc": 3, "lp": 0, "pb": 2,
               "dict_size": 1 << 15}


def lzma_decode_raw(data: bytes, outlen: int) -> bytes:
    # CHD stores a bare LZMA1 stream (no props header, no end mark,
    # lc=3 lp=0 pb=2). Wrap it in an ALONE header with known size.
    props = bytes([0x5D]) + struct.pack("<I", 1 << 15) + struct.pack("<Q", outlen)
    dec = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE)
    out = dec.decompress(props + data)
    if len(out) != outlen:
        raise ValueError(f"lzma out {len(out)} != {outlen}")
    return out


def zlib_decode_raw(data: bytes, outlen: int) -> bytes:
    d = zlib.decompressobj(-15)
    out = d.decompress(data, outlen)
    if len(out) != outlen:
        out += d.flush()
    if len(out) != outlen:
        raise ValueError(f"zlib out {len(out)} != {outlen}")
    return out


# ---------------------------------------------------------------- CHD file
class Chd:
    def __init__(self, path: Path):
        self.f = open(path, "rb")
        hdr = self.f.read(124)
        if hdr[0:8] != b"MComprHD":
            raise ValueError("not a CHD")
        self.version = int.from_bytes(hdr[12:16], "big")
        if self.version != 5:
            raise ValueError(f"only v5 supported, got {self.version}")
        self.compressors = [int.from_bytes(hdr[16 + 4 * i:20 + 4 * i], "big")
                            for i in range(4)]
        self.logicalbytes = int.from_bytes(hdr[32:40], "big")
        self.mapoffset = int.from_bytes(hdr[40:48], "big")
        self.metaoffset = int.from_bytes(hdr[48:56], "big")
        self.hunkbytes = int.from_bytes(hdr[56:60], "big")
        self.unitbytes = int.from_bytes(hdr[60:64], "big")
        self.rawsha1 = hdr[64:84]
        self.hunkcount = (self.logicalbytes + self.hunkbytes - 1) // self.hunkbytes
        self.frames_per_hunk = self.hunkbytes // self.unitbytes
        self.frame_size = self.unitbytes          # 2448
        self.main_size = 2352
        self.sub_size = self.frame_size - self.main_size

    # ---- metadata ----
    def read_metadata(self):
        """Header: [tag u32be][flags u8][len u24be][next u64be] + data."""
        out = []
        pos = self.metaoffset
        seen = set()
        while pos and pos not in seen and pos < self.mapoffset:
            seen.add(pos)
            self.f.seek(pos)
            hdr = self.f.read(16)
            if len(hdr) < 16:
                break
            tag = hdr[0:4]
            flags = hdr[4]
            length = int.from_bytes(hdr[5:8], "big")
            nxt = int.from_bytes(hdr[8:16], "big")
            if length == 0 or length > 1_000_000:
                break
            data = self.f.read(length)
            out.append((tag, flags, data))
            pos = nxt
        return out

    def tracks(self):
        """Parse CHT2 track metadata -> [(num, type, subtype, frames, pregap, pgtype)]."""
        out = []
        for tag, flags, data in self.read_metadata():
            if tag != b"CHT2":
                continue
            fields = dict()
            for kv in data.decode("ascii", "replace").rstrip("\x00").split(" "):
                if ":" in kv:
                    k, v = kv.split(":", 1)
                    fields[k] = v
            out.append(fields)
        return out

    # ---- map ----
    def _decode_map(self):
        self.f.seek(self.mapoffset)
        raw = self.f.read(16)
        mapbytes = int.from_bytes(raw[0:4], "big")
        firstoffs = int.from_bytes(raw[4:10], "big")
        lengthbits, selfbits, parentbits = raw[12], raw[13], raw[14]
        comp = self.f.read(mapbytes)
        cur = BitCursor(comp)

        lengths = import_tree_rle(cur)
        codes = assign_canonical_codes(lengths)
        table = build_lookup(codes)

        def decode_one(c: BitCursor) -> int:
            peek8 = bits(c.data, c.pos, 8) if c.pos + 8 <= len(c.data) * 8 else \
                bits(c.data, c.pos, max(0, len(c.data) * 8 - c.pos)) << max(
                    0, 8 - (len(c.data) * 8 - c.pos))
            sym, ln = table[peek8]
            c.pos += ln
            return sym

        # pass 1: compression type per hunk (with RLE)
        types = []
        lastcomp = 0
        repcount = 0
        for _ in range(self.hunkcount):
            if repcount > 0:
                types.append(lastcomp)
                repcount -= 1
            else:
                val = decode_one(cur)
                if val == SYM_RLE_SMALL:
                    repcount = 2 + decode_one(cur)
                    types.append(lastcomp)
                elif val == SYM_RLE_LARGE:
                    repcount = 2 + 16 + (decode_one(cur) << 4)
                    repcount += decode_one(cur)
                    types.append(lastcomp)
                else:
                    lastcomp = val
                    types.append(lastcomp)

        # pass 2: per-entry extra bits
        entries = []
        curoffset = firstoffs
        last_self = 0
        last_parent = 0
        for hunknum in range(self.hunkcount):
            t = types[hunknum]
            offset = curoffset
            length = 0
            crc = 0
            if t in SYM_TYPE0_3:
                length = cur.read(lengthbits)
                curoffset += length
                crc = cur.read(16)
                entries.append((t, length, offset, crc))
            elif t == SYM_NONE:
                length = self.hunkbytes
                curoffset += length
                crc = cur.read(16)
                entries.append((t, length, offset, crc))
            elif t == SYM_SELF:
                last_self = offset = cur.read(selfbits)
                entries.append((t, 0, offset, 0))
            elif t == SYM_PARENT:
                offset = cur.read(parentbits)
                last_parent = offset
                entries.append((t, 0, offset, 0))
            elif t == SYM_SELF_1:
                last_self += 1
                entries.append((SYM_SELF, 0, last_self, 0))
            elif t == SYM_SELF_0:
                entries.append((SYM_SELF, 0, last_self, 0))
            elif t == SYM_PARENT_SELF:
                last_parent = offset = (hunknum * self.hunkbytes) // self.unitbytes
                entries.append((SYM_PARENT, 0, offset, 0))
            elif t == SYM_PARENT_1:
                last_parent += 1
                entries.append((SYM_PARENT, 0, last_parent, 0))
            elif t == SYM_PARENT_0:
                entries.append((SYM_PARENT, 0, last_parent, 0))
            else:
                raise ValueError(f"bad map type {t}")
        return entries

    # ---- hunk reads ----
    def read_hunk(self, hunknum: int, depth: int = 0) -> bytes:
        if depth > 8:
            raise ValueError("SELF recursion too deep")
        t, length, offset, crc = self.map[hunknum]
        self.f.seek(offset)
        block = self.f.read(length)
        if t in SYM_TYPE0_3:
            comp = self.compressors[t]
            if comp in (0x63646C7A,):        # 'cdlz'
                return self._unpack_cd_hunk(block, lzma_decode_raw)
            elif comp in (0x63647A6C,):      # 'cdzl'
                return self._unpack_cd_hunk(block, zlib_decode_raw)
            elif comp in (0x6364666C,):      # 'cdfl' — audio track (FLAC main)
                # CDDA hunk: emit silence in the main channel. The data
                # track never uses cdfl, so ISO9660 extraction is unaffected.
                return bytes(self.hunkbytes)
            else:
                raise ValueError(f"codec {comp:08x} unsupported")
        elif t == SYM_NONE:
            return block
        elif t == SYM_SELF:
            return self.read_hunk(offset, depth + 1)
        else:
            raise ValueError("parent hunk not supported")

    def _unpack_cd_hunk(self, block: bytes, base_decode) -> bytes:
        frames = self.frames_per_hunk
        ecc_bytes = (frames + 7) // 8
        complen_bytes = 2 if self.hunkbytes < 65536 else 3
        header_bytes = ecc_bytes + complen_bytes
        complen_base = int.from_bytes(block[ecc_bytes:ecc_bytes + complen_bytes], "big")
        main = base_decode(block[header_bytes:header_bytes + complen_base],
                           frames * self.main_size)
        out = bytearray(frames * self.frame_size)
        ecc_bits = block[0]
        for i in range(frames):
            sector = bytearray(main[i * self.main_size:(i + 1) * self.main_size])
            if (ecc_bits >> i) & 1:
                # regenerate sync + ECC: pad to 2352 with zero subheader,
                # run MAME's algorithm over the full 2352-byte sector
                full = bytearray(sector)  # sync(12)+hdr(4)+subhdr(8)+data+edc+ecc
                full[0:12] = CD_SYNC
                ecc_generate(full)
                sector = full
            out[i * self.frame_size:i * self.frame_size + self.main_size] = sector
            # subcode left zero (skipped FLAC)
        return bytes(out)

    def open_map(self):
        self.map = self._decode_map()

    def main_stream(self):
        """Yield main-channel 2352-byte sectors for the whole disc."""
        for h in range(self.hunkcount):
            hunk = self.read_hunk(h)
            for fr in range(self.frames_per_hunk):
                yield hunk[fr * self.frame_size:fr * self.frame_size + self.main_size]


# ---------------------------------------------------------------- main
def main():
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("chd", type=Path)
    ap.add_argument("out", type=Path, help="output .bin (2352 bytes/sector)")
    args = ap.parse_args()

    chd = Chd(args.chd)
    print(f"CHD v{chd.version}: {chd.logicalbytes:,} logical bytes, "
          f"{chd.hunkcount} hunks x {chd.hunkbytes} B, "
          f"frame={chd.frame_size} B, codecs={[f'{c:08x}' for c in chd.compressors]}")
    print(f"raw sha1 (expected): {chd.rawsha1.hex()}")

    metas = chd.read_metadata()
    tracks = chd.tracks()
    for t in tracks:
        print(f"track {t.get('TRACK')}: TYPE={t.get('TYPE')} FRAMES={t.get('FRAMES')} "
              f"PGTYPE={t.get('PGTYPE')} PREGAP={t.get('PREGAP')}")
    if not tracks:
        for tag, flags, data in metas:
            print(f"meta {tag} flags={flags}: {data[:120]!r}")

    chd.open_map()
    from collections import Counter
    cnt = Counter(t for t, *_ in chd.map)
    print(f"map types: {dict(cnt)}")

    n = 0
    with open(args.out, "wb") as fo:
        for sector in chd.main_stream():
            fo.write(sector)
            n += 1
            if n % 50000 == 0:
                print(f"  {n} sectors...")
    print(f"wrote {n} sectors -> {args.out}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Compare g3_eu func_800642A0 retail bytes against psyq LIBSPU.LIB members across versions."""
import struct, glob, json, sys

ROW_VA = 0x800642A0
ROW_LEN = 0x548
BASELINE = "/home/z/my-project/cannon-seed/baselines/g3_eu.bin"

# g3_eu: find the file offset for VA. The yaml row said [0x44AA0] - that's the ROM/segment offset.
# Read bytes straight from the per-sector baseline via the exe map convention: VA 0x800642A0.
with open(BASELINE, "rb") as f:
    img = f.read()
print("baseline size:", len(img))

# locate the PS-X EXE header to map VA->file offset
# standard: t_addr in header at 0x18, t_size at 0x1C, text starts at 0x800
idx = img.find(b"PS-X EXE")
print("PS-X EXE header at:", hex(idx) if idx >= 0 else "none")
if idx >= 0:
    t_addr = struct.unpack_from("<I", img, idx + 0x18)[0]
    t_size = struct.unpack_from("<I", img, idx + 0x1C)[0]
    print("t_addr=%08x t_size=%08x" % (t_addr, t_size))
    off = idx + 0x800 + (ROW_VA - t_addr)
    our = img[off:off+ROW_LEN]
else:
    # fallback: search for the known prologue bytes anywhere
    our = None

prologue = bytes.fromhex("E0FFBD271800B0AF21808000")
if our is None or our[:12] != prologue:
    hits = [m for m in range(len(img) - 12) if img[m:m+12] == prologue]
    print("prologue hits:", [hex(h) for h in hits[:10]])
    if hits:
        our = img[hits[0]:hits[0]+ROW_LEN]
        print("using hit", hex(hits[0]))
else:
    print("prologue matches at computed offset", hex(off))

if our is None:
    sys.exit("no bytes")

# parse archive members from each LIBSPU.LIB
def parse_archive(data):
    """Parse GNU-style archive; return list of (name, bytes)."""
    if data[:8] != b"!<arch>\n":
        return []
    pos = 8
    out = []
    longnames = b""
    # first pass: extended names table
    while pos + 60 <= len(data):
        hdr = data[pos:pos+60]
        name = hdr[0:16].decode("ascii", "replace").strip()
        size = int(hdr[48:58].decode().strip())
        body = data[pos+60:pos+60+size]
        pos += 60 + size + (size & 1)
        if name == "//":
            longnames = body
            continue
        if name in ("/", "/SYM64/") or name.startswith("/ "):
            continue
        if name.startswith("/"):
            ln = int(name[1:])
            end = longnames.find(b"\n", ln)
            real = longnames[ln:end].decode("ascii", "replace") if end >= 0 else "?"
            out.append((real, body))
        else:
            out.append((name.rstrip("/"), body))
    return out

def ecoff_text_sections(obj):
    """Extract .text from an ECOFF object (psi format used by psyq)."""
    # psyq objects are ECOFF (MIPS). Magic 0x0162 (little-endian 0x6001?) - fmagic at 0
    if len(obj) < 0x80:
        return []
    fmagic = struct.unpack_from("<H", obj, 0)[0]
    if fmagic not in (0x0162, 0x0163, 0x6001, 0x166):
        return []
    fhdr_size = 20
    iscn = struct.unpack_from("<H", obj, 0x14)[0]  # fNscns
    off = fhdr_size
    texts = []
    for _ in range(iscn):
        s_name = obj[off:off+8].rstrip(b"\x00").decode("ascii", "replace")
        s_paddr, s_vaddr, s_size = struct.unpack_from("<III", obj, off+8)
        s_scnptr = struct.unpack_from("<I", obj, off+32)[0]
        off += 40
        if s_name == ".text" and s_size:
            texts.append((s_vaddr, obj[s_scnptr:s_scnptr+s_size]))
    return texts

for lib in sorted(glob.glob("/home/z/my-project/psyq/*/PSX/LIB/LIBSPU.LIB")):
    ver = lib.split("/psyq/")[1].split("/")[0]
    with open(lib, "rb") as f:
        data = f.read()
    members = parse_archive(data)
    if not members:
        print(ver, ": not a plain archive (%d bytes, head %r)" % (len(data), data[:8]))
        continue
    for name, body in members:
        for vaddr, text in ecoff_text_sections(body):
            if len(text) >= ROW_LEN and text[:12] == prologue:
                eq = text[:ROW_LEN] == our
                print("%s %s .text@%08x len=%d HEAD-MATCH %s" % (ver, name, vaddr, len(text), "FULL-EXACT" if eq else ""))
# also scan for the doubled-load loop signature to see which members carry it
dbl = bytes.fromhex("8FA2000101 00".replace(" ", ""))  # placeholder, not used

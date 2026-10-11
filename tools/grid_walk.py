#!/usr/bin/env python3
"""grid_walk.py - exe-wide walk of the 0x930 block grid (text transport layer).

The mainmenu text segment is organized in 0x930-byte blocks:
    [0x18 descriptor][0x800 plaintext code][0x118 encrypted payload]
repeating per block, descriptors at IDENTICAL vrams on the JP and EU discs
but with a per-disc index base (JP runs 2 lower than EU) and a per-disc
flag byte (0x17 vs 0x19). Discovered during the data_8002B7F4 / CB50 carves
(recon scripts/jp_cb50_recon*.py; commits 8159794, 1fd69db, 8974d3a, 13a0fcd).

Descriptor signature (6 little-endian words):
    FFFFFF00 FFFFFFFF 00FFFFFF <idx:flags> 00080000 00080000
with idx = word3 >> 16, flags = (word3 >> 8) & 0xFF.

This tool walks every retail baseline (proven against config/sha1 first,
like exe_map.py), finds every descriptor, and measures each block:
  - payload: 0x118 bytes before the descriptor, Shannon entropy (encrypted
    at rest measures ~7.2-7.9 bits/byte; plaintext code ~4-5)
  - code half: 0x800 bytes after the descriptor, per-word MIPS decode ratio
  - twin check: word diffs against the region counterpart (jp<->eu) across
    the code half - relocation-twin code shows scattered diffs, independent
    encrypted payloads differ wholesale
  - zone cross-reference against config/splat.<target>.yaml subsegs:
    which parts are already carved asm, still data, or C

Emits docs/GRID.md (regenerated wholesale - measurement over transcription).

Usage: python3 tools/grid_walk.py [TARGET ...]   (default: every target)
"""

import hashlib
import math
import re
import struct
import sys
from pathlib import Path

from capstone import CS_ARCH_MIPS, CS_MODE_MIPS32, Cs

REPO = Path(__file__).resolve().parent.parent
BASELINES = REPO / "baselines"
SHA1_DIR = REPO / "config" / "sha1"
CONFIG = REPO / "config"
OUT = REPO / "docs" / "GRID.md"

HEADER_SIZE = 0x800
DESC_WORDS = (0xFFFFFF00, 0xFFFFFFFF, 0x00FFFFFF)
TAIL_WORDS = (0x00080000, 0x00080000)
PAYLOAD_LEN = 0x118
DESC_LEN = 0x18
CODE_LEN = 0x800
STRIDE = 0x930

TWIN = {
    "slps_00270": "sces_00269",
    "sces_00269": "slps_00270",
    "mainmenu_jp": "mainmenu_eu",
    "mainmenu_eu": "mainmenu_jp",
    "g3_jp": "g3_eu",
    "g3_eu": "g3_jp",
    "g3org_jp": "g3org_eu",
    "g3org_eu": "g3org_jp",
}

SUBSEG_RE = re.compile(r"^\s*-\s*\[(0x[0-9A-Fa-f]+),\s*(asm|data|c|rodata),\s*([A-Za-z_0-9.]+)\]")


def sha1_of(path):
    return hashlib.sha1(path.read_bytes()).hexdigest()


def load_target(name):
    """Return (payload_bytes, t_addr, rom_base, subsegs) or (None, ...) reasons."""
    bl = BASELINES / f"{name}.bin"
    sha_file = SHA1_DIR / f"{name}.sha1"
    if not bl.exists():
        return None
    data = bl.read_bytes()
    want = None
    if sha_file.exists():
        for line in sha_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                want = line.split()[0]
                break
    got = hashlib.sha1(data).hexdigest()
    if want and want != got:
        raise SystemExit(f"{name}: baseline SHA-1 {got} != oracle {want} - refusing")
    # PS-X EXE header: t_addr at 0x18, t_size at 0x1C
    t_addr, t_size = struct.unpack_from("<II", data, 0x18)
    payload = data[HEADER_SIZE : HEADER_SIZE + t_size]
    subsegs = parse_yaml(name)
    return payload, t_addr, HEADER_SIZE, subsegs


def parse_yaml(name):
    """[(start_vram, end_vram, type, name)] - sizes derived from next start."""
    path = CONFIG / f"splat.{name}.yaml"
    if not path.exists():
        return []
    entries = []
    for line in path.read_text().splitlines():
        m = SUBSEG_RE.match(line)
        if m:
            off = int(m.group(1), 16)
            entries.append([off, m.group(2), m.group(3)])
    # vram per entry: t_addr + (rom_offset - 0x800). We add rom base later.
    return entries  # [rom_off, type, name]


def subseg_map(entries, t_addr, payload_len):
    """Resolve to [(start_vram, end_vram, type, name)] using contiguity."""
    out = []
    n = len(entries)
    for i, (off, typ, nm) in enumerate(entries):
        end = entries[i + 1][0] if i + 1 < n else 0x800 + payload_len
        start_vram = t_addr + (off - 0x800)
        end_vram = t_addr + (end - 0x800)
        out.append((start_vram, end_vram, typ, nm))
    return out


def classify_vram(vmap, v):
    for s, e, typ, nm in vmap:
        if s <= v < e:
            return f"{typ}:{nm}"
    return "?"


def entropy(b):
    if not b:
        return 0.0
    counts = [0] * 256
    for x in b:
        counts[x] += 1
    n = len(b)
    return -sum((c / n) * math.log2(c / n) for c in counts if c)


def decode_ratio(md, code, vram):
    ok = 0
    total = len(code) // 4
    for i in range(total):
        w = code[i * 4 : i * 4 + 4]
        if next(iter(md.disasm(w, vram + i * 4)), None) is not None:
            ok += 1
    return ok / total if total else 0.0


def find_descriptors(payload, t_addr):
    hits = []
    for off in range(0, len(payload) - 0x18, 4):
        w = struct.unpack_from("<6I", payload, off)
        if w[0] == DESC_WORDS[0] and w[1] == DESC_WORDS[1] and w[2] == DESC_WORDS[2]:
            if w[4] == TAIL_WORDS[0] and w[5] == TAIL_WORDS[1]:
                vram = t_addr + off
                idx = w[3] >> 16
                flags = (w[3] >> 8) & 0xFF
                # sector header bytes (LE): [min][sec][frame][mode], all BCD
                msf = (w[3] & 0xFF, (w[3] >> 8) & 0xFF, (w[3] >> 16) & 0xFF,
                       (w[3] >> 24) & 0xFF)
                hits.append((vram, idx, flags, msf))
    return hits


def main(argv):
    names = argv[1:] or sorted(p.stem for p in SHA1_DIR.glob("*.sha1"))
    data = {}
    for name in names:
        loaded = load_target(name)
        if loaded is None:
            print(f"[grid] {name}: baseline missing - skipped", file=sys.stderr)
            continue
        data[name] = loaded

    md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32)
    md.skipdata = False

    rows_by_target = {}
    for name, (payload, t_addr, rom_base, entries) in data.items():
        payload_len = len(payload)
        vmap = subseg_map(entries, t_addr, payload_len)
        descs = find_descriptors(payload, t_addr)
        rows = []
        for vram, idx, flags, msf in descs:
            p_lo = vram - PAYLOAD_LEN
            c_lo = vram + DESC_LEN
            p_bytes = b""
            c_bytes = b""
            if p_lo >= t_addr:
                p_bytes = payload[p_lo - t_addr : p_lo - t_addr + PAYLOAD_LEN]
            if c_lo + CODE_LEN <= t_addr + payload_len:
                c_bytes = payload[c_lo - t_addr : c_lo - t_addr + CODE_LEN]
            p_ent = entropy(p_bytes) if p_bytes else float("nan")
            c_ratio = decode_ratio(md, c_bytes, c_lo) if c_bytes else float("nan")
            # twin diff over the code half
            tdiff = None
            twin_name = TWIN.get(name)
            if twin_name in data and c_bytes:
                tp, tt, _, _ = data[twin_name]
                lo = c_lo - tt
                if lo >= 0 and lo + CODE_LEN <= len(tp):
                    twin_words = struct.unpack_from(f"<{CODE_LEN//4}I", tp, lo)
                    own_words = struct.unpack_from(f"<{CODE_LEN//4}I", c_bytes, 0)
                    tdiff = sum(1 for a, b in zip(own_words, twin_words) if a != b)
            zone = "/".join(
                classify_vram(vmap, v)
                for v in (p_lo, vram, c_lo, c_lo + CODE_LEN - 4)
                if p_lo >= t_addr
            )
            rows.append((vram, idx, flags, msf, p_ent, c_ratio, tdiff, zone))
        rows_by_target[name] = rows

    # emit docs/GRID.md
    lines = []
    A = lines.append
    A("# GRID: the 0x930 text-segment block grid = raw CD-ROM sectors")
    A("")
    A("Measured by `tools/grid_walk.py` (regenerated wholesale - measurement")
    A("over transcription). Baselines proven against `config/sha1/` before")
    A("measuring. Discovery and evidence: the data_8002B7F4 / data_8002CB50")
    A("carves (commits 8159794, 1fd69db, 8974d3a, 13a0fcd); sector identity")
    A("proven 2026-10-12 (scripts/idx_gap_sample.py, sector_edc_proof.py).")
    A("")
    A("## The blocks are raw Mode 2 sectors, not a game structure")
    A("")
    A("0x930 = 2352 = raw CD-ROM sector size. Each block is one raw sector")
    A("of the disc track, captured by the baseline extraction:")
    A("")
    A("    [0x18 sector header][0x800 user data][0x118 EDC+ECC region]")
    A("")
    A("The 0x18 'descriptor' is the sector header: sync `00 FF*10 00` (12)")
    A("+ BCD MSF address (min, sec, frame) + mode 0x02 (4) + subheader")
    A("`00 00 08 00` x2 (8, data sector). Header bytes advance +1 sector")
    A("per block in pure BCD. The former 'index gaps' are BCD carries")
    A("(09+1=10, 19+1=20, ...); the former '6-index gaps' are nothing more")
    A("- binary digits A..F never occur in BCD. An exe-wide scan found 0")
    A("descriptor-like records beyond the standard signature, so no")
    A("variant descriptors exist. The 'module groups' are BCD seconds:")
    A("each exe spans a contiguous MSF run (boots sec 0x02-0x03, g3org")
    A("0x06-0x09, mainmenu_jp 0x17-0x21, mainmenu_eu 0x19-0x23, g3_jp")
    A("0x28-0x31, g3_eu 0x31-0x34, g3org_eu 0x09-0x12); full sectors per")
    A("second = 75 (frame 0x00..0x74). The JP/EU 'index offset at the same")
    A("vram' (mainmenu -2, g3org -11, g3 +58) is the two discs' LBA")
    A("placement difference for the same file. File layout of every")
    A("baseline: [PS-X header 0x800 = sector 0 user data][sector 0's own")
    A("0x118 tail][raw sectors 1..N including all overhead].")
    A("")
    A("Consequences: (1) the 0x118 'encrypted payloads' are sector overhead")
    A("bytes - their high entropy is expected, they have no game meaning,")
    A("no runtime decryption exists, and they stay data forever; (2) the")
    A("only game data per sector is the 0x800 user-data window; (3) stub")
    A("rows 'j INTO payload 1' point at overlay bytes that live in a")
    A("DIFFERENT file's sectors on disc - the j targets are real code,")
    A("just not user data of THIS capture; (4) the stored 0x118 bytes do")
    A("NOT match the standard EDC (poly 0x80018001) over any standard")
    A("range - open question (Sony mastering scramble or variant); the")
    A("sector-header evidence above is independent of that.")
    A("")
    A("Reading the columns: payload entropy measures the overhead bytes")
    A("(~7.2-7.9 bits/byte is normal for parity/EDC regions). Code-half")
    A("decode 1.00 means the whole half decodes as MIPS. CAUTION on twin")
    A("diffs: they compare the user data at the SAME vram in the region")
    A("twin - where the two discs place functions at shifted vrams")
    A("(per-region deltas +0xB0/+0x60/+0x5c/0 measured on mainmenu), the")
    A("diff counts placement shift, not content difference; only near-0")
    A("counts indicate same-vram twins. ~500/512 means the halves do not")
    A("correspond at all. The sector grid is not a code template: real")
    A("linked code crosses sector boundaries freely (e.g. mainmenu")
    A("func_8002DE00 after block 5), so per-block splits must be")
    A("measured; the header positions are ground truth only for the")
    A("overhead boundaries.")
    A("")
    for name in names:
        if name not in rows_by_target:
            continue
        rows = rows_by_target[name]
        A(f"## {name}")
        A("")
        if not rows:
            A("No descriptor hits - the grid layer is not present in this image.")
            A("")
            continue
        A(f"{len(rows)} sector headers found. Columns: BCD MSF address, payload")
        A("entropy (bits/B), code-half decode ratio, word diffs vs the region")
        A("twin across the user-data half, and the yaml zones the four probe")
        A("points fall in (overhead start / header / data start / data end).")
        A("")
        A("| sector vram | MSF (mm:ss:ff) | payload H | code decode | twin diffs | zones |")
        A("| --- | --- | --- | --- | --- | --- |")
        for vram, idx, flags, msf, p_ent, c_ratio, tdiff, zone in rows:
            pe = f"{p_ent:.2f}" if p_ent == p_ent else "n/a"
            cr = f"{c_ratio:.2f}" if c_ratio == c_ratio else "n/a"
            td = str(tdiff) if tdiff is not None else "n/a"
            A(f"| {vram:08X} | {msf[0]:02x}:{msf[1]:02x}:{msf[2]:02x} | {pe} | {cr} | {td} | {zone} |")
        A("")
    OUT.write_text("\n".join(lines) + "\n")
    print(f"[grid] wrote {OUT}")
    for name, rows in rows_by_target.items():
        print(f"[grid] {name}: {len(rows)} descriptors")


if __name__ == "__main__":
    main(sys.argv)

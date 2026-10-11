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
                hits.append((vram, idx, flags))
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
        for vram, idx, flags in descs:
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
            rows.append((vram, idx, flags, p_ent, c_ratio, tdiff, zone))
        rows_by_target[name] = rows

    # emit docs/GRID.md
    lines = []
    A = lines.append
    A("# GRID: the 0x930 text-segment block grid")
    A("")
    A("Measured by `tools/grid_walk.py` (regenerated wholesale - measurement")
    A("over transcription). Baselines proven against `config/sha1/` before")
    A("measuring. Discovery and evidence: the data_8002B7F4 / data_8002CB50")
    A("carves (commits 8159794, 1fd69db, 8974d3a, 13a0fcd).")
    A("")
    A("The text segment is organized in 0x930-byte blocks:")
    A("")
    A("    [0x18 descriptor][0x800 plaintext code][0x118 encrypted payload]")
    A("")
    A("Descriptor signature (6 words): `FFFFFF00 FFFFFFFF 00FFFFFF")
    A("<idx:flags> 00080000 00080000`. The index increments by 1 per block")
    A("(with occasional gaps - e.g. a 6-index gap a few blocks into every")
    A("exe), and the FIRST descriptor of every image starts at a different")
    A("global base, so the index is a pipeline-wide counter, not per-exe:")
    A("first idx per target: slps_00270/sces_00269 549 (flags 0x02),")
    A("mainmenu_jp 562 (0x17), mainmenu_eu 564 (0x19), g3_jp 592 (0x28),")
    A("g3_eu 534 (0x31), g3org_jp 518 (0x06), g3org_eu 529 (0x09) - the")
    A("flag byte is per-target. Within an exe pair the JP/EU index offset")
    A("at the same vram is constant per exe (mainmenu -2, g3org -11, g3")
    A("+58), and descriptor vrams are identical across each JP/EU pair.")
    A("")
    A("Reading the columns: payloads are encrypted at rest (~7.2-7.9")
    A("bits/byte; some are executed only after runtime decryption - stub")
    A("rows j INTO payload 1 with real store delay slots - so at-rest low")
    A("decode there is expected and those bytes stay data until the")
    A("decryption site is understood). Code-half decode 1.00 means the")
    A("whole half decodes as MIPS. CAUTION on twin diffs: they compare the")
    A("code half at the SAME vram in the region twin - where the two")
    A("discs place functions at shifted vrams (per-region deltas +0xB0/")
    A("+0x60/+0x5c/0 measured on mainmenu), the diff counts placement")
    A("shift, not content difference; only near-0 counts indicate")
    A("same-vram twins. ~500/512 means the halves do not correspond at")
    A("all (different placement or content). The grid is a transport/")
    A("descriptor layer, not a uniform code template: per-block splits")
    A("must be measured, descriptor positions are ground truth (some")
    A("blocks' code halves are truncated by real linked code, e.g.")
    A("mainmenu func_8002DE00 after block 5).")
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
        A(f"{len(rows)} descriptors found. Columns: payload entropy (bits/B),")
        A("code-half decode ratio, word diffs vs the region twin across the")
        A("code half, and the yaml zones the four probe points fall in")
        A("(payload start / descriptor / code start / code end).")
        A("")
        A("| descriptor vram | idx | flags | payload H | code decode | twin diffs | zones |")
        A("| --- | --- | --- | --- | --- | --- | --- |")
        for vram, idx, flags, p_ent, c_ratio, tdiff, zone in rows:
            pe = f"{p_ent:.2f}" if p_ent == p_ent else "n/a"
            cr = f"{c_ratio:.2f}" if c_ratio == c_ratio else "n/a"
            td = str(tdiff) if tdiff is not None else "n/a"
            A(f"| {vram:08X} | {idx} | {flags:#04x} | {pe} | {cr} | {td} | {zone} |")
        A("")
    OUT.write_text("\n".join(lines) + "\n")
    print(f"[grid] wrote {OUT}")
    for name, rows in rows_by_target.items():
        print(f"[grid] {name}: {len(rows)} descriptors")


if __name__ == "__main__":
    main(sys.argv)

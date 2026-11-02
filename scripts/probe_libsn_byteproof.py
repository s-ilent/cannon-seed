#!/usr/bin/env python3
"""probe_libsn_byteproof.py - the per-function byte-proof road into LIBSN.

The 0859 window proved the ambiguous multiaddr census class (incl. the
156 LIBGCC2 rows) is archive-layout projections and said "only
per-function byte-proof reaches them".  With the z=0x36 path-record law
fixed, first_code_chunk() now opens the GNU members; this probe extracts
each LIBSN module's first 02-chunk (code) and searches all eight
witnessed baselines for verbatim byte placements - the direct answer to
"does the game link LIBSN.LIB's members as-is", independent of any
census row or sig-db hit.

Output: per module - chunk size, publics, per-target verbatim hit
addresses; then the cross-check against the census's 156
__builtin_vec_delete rows.
"""
import re
import struct
import sys
from collections import defaultdict

sys.path.insert(0, "/home/z/my-project/cannon-seed/tools")
import omf_pubsyms as op  # noqa: E402

REPO = "/home/z/my-project/cannon-seed"
LIB = "/home/z/psyq/3.3/PSX/LIB/LIBSN.LIB"
TARGETS = ["g3_eu", "g3_jp", "g3org_eu", "g3org_jp",
           "mainmenu_eu", "mainmenu_jp", "sces_00269", "slps_00270"]
ROW = re.compile(
    r"^//\s+(0x[0-9a-fA-F]+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*(adoptable)?")


def census_rows():
    rows = []
    for ln in open(REPO + "/config/sdk_members.txt", errors="replace"):
        m = ROW.match(ln)
        if m and m.group(2) == "LIBSN":
            rows.append((int(m.group(1), 16), m.group(3), m.group(5)))
    return rows


def first_chunk_bytes(d, mod):
    blob, pe, np_ = op.first_code_chunk(d, mod)
    if blob is None:
        return None, None, np_
    size = struct.unpack_from("<H", d, pe + 1)[0]
    return blob, d[blob:blob + size], np_


def find_all(hay, needle):
    out = []
    i = hay.find(needle)
    while i != -1:
        out.append(i)
        i = hay.find(needle, i + 1)
    return out


def all_chunk_candidates(d, mod, min_sz=0x20):
    """Grammar-free fallback: every [02][u16 size][payload] record in the
    module zone with a plausible size and a non-zero payload.  Used only
    for modules whose first_code_chunk() discovery fails (empty stubs,
    zero-leading chunks, kernel members)."""
    end = mod.offset + mod.size
    out = []
    o = mod.offset + 20
    while o + 3 <= end:
        if d[o] == 0x02:
            sz = struct.unpack_from("<H", d, o + 1)[0]
            if min_sz <= sz <= 0x2000 and o + 3 + sz <= end:
                payload = d[o + 3:o + 3 + sz]
                if any(payload):
                    out.append((o - mod.offset, payload))
                    o += 3 + sz
                    continue
        o += 1
    return out


def main():
    lib = op.PsyqLib(LIB)
    d = lib.data
    images = {}
    for t in TARGETS:
        with open(f"{REPO}/baselines/{t}.bin", "rb") as f:
            images[t] = f.read()

    # the game addresses live at file+0x800 in the PSX-EXE images
    # (0x800-n prefixed); report raw file hits translated to runtime addrs
    print(f"LIBSN.LIB modules: {len(lib.modules)}")
    hits_by_mod = {}
    nochunk = []
    for m in lib.modules:
        blob, chunk, np_ = first_chunk_bytes(d, m)
        if chunk is None or len(chunk) < 16:
            # fallback: grammar-free 02-record candidates in the whole zone
            cands = all_chunk_candidates(d, m)
            if not cands:
                nochunk.append((m.name, "empty/stub"))
                continue
            per = {}
            used = None
            for off, payload in cands:
                for t in TARGETS:
                    hits = find_all(images[t], payload)
                    if hits:
                        per.setdefault(t, []).extend(
                            (off, h) for h in hits)
                        used = (off, len(payload))
            if per:
                hits_by_mod[m.name] = (used[1], m.publics, per)
                det = "; ".join(
                    f"{t} x{len(hs)} @ "
                    + ",".join(f"0x{h + 0x800:08X}(+0x{o:x})"
                               for o, h in hs[:4])
                    for t, hs in sorted(per.items()))
                print(f"  {m.name:<10} CAND=0x{used[1]:03x}(+0x{used[0]:x}) "
                      f"publics={m.publics} -> {det}")
            else:
                nochunk.append((m.name,
                                f"{len(cands)} cand, no placement"))
            continue
        per = {}
        for t in TARGETS:
            hits = find_all(images[t], chunk)
            if hits:
                per[t] = hits
        hits_by_mod[m.name] = (len(chunk), m.publics, per)
        if per:
            det = "; ".join(
                f"{t} x{len(hs)} @ " + ",".join(f"0x{h + 0x800:08X}" for h in hs[:4])
                for t, hs in sorted(per.items()))
            print(f"  {m.name:<10} chunk=0x{len(chunk):03x} paths={np_} "
                  f"publics={m.publics} -> {det}")
        else:
            print(f"  {m.name:<10} chunk=0x{len(chunk):03x} paths={np_} "
                  f"publics={m.publics} -> no verbatim placement")
    print(f"\nmodules without a usable first chunk: {nochunk}")

    # cross-check: census __builtin_vec_delete rows vs _OP_VDEL's placement
    rows = census_rows()
    vdel = [a for a, mem, sn in rows if sn == "__builtin_vec_delete"]
    print(f"\ncensus LIBSN rows: {len(rows)} "
          f"(members: {sorted({mem for _a, mem, _s in rows})})")
    print(f"__builtin_vec_delete rows: {len(vdel)} "
          f"span 0x{max(vdel) - min(vdel):x}" if vdel else "none")
    if "_OP_VDEL" in hits_by_mod:
        sz, pubs, per = hits_by_mod["_OP_VDEL"]
        print(f"_OP_VDEL chunk=0x{sz:x} publics={pubs}")
        for t, hs in sorted(per.items()):
            addrs = [h + 0x800 for h in hs]
            match = [a for a in addrs if a in set(vdel)]
            near = [a for a in addrs
                    if any(abs(a - v) <= 8 for v in vdel)]
            print(f"  {t}: placements {[f'0x{a:08X}' for a in addrs]} "
                  f"census-hit={[f'0x{a:08X}' for a in match]} "
                  f"census-near={[f'0x{a:08X}' for a in near]}")


if __name__ == "__main__":
    main()

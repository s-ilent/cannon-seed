#!/usr/bin/env python3
"""Curation-pass family survey over the committed SDK member census.

Decomposes every census row into the curation classes the regen trio
leaves behind, groups the unadopted evidence into families, and ranks
the families by the hand-evidence hooks the 0852 discipline wants:

  - cross-target spread (the same member at the same relative story
    in several targets),
  - sig-db corroboration on the row,
  - an sdk_anchors row at the same address (independent evidence),
  - claimant shape (real-copy class vs stub-class).

Repo-external sieve: prints a report, writes nothing.

BANKED RESULTS (2026-11-02, cron-20261102-0859 window): the ~2160
adoptable-but-unadopted marks decompose as 1854 amb-no-agree (1828
multiaddr + 26 stubclash) + 113 addr-curated + 151 name-dup + 10
lane-held.  The two biggest multiaddr families are PROJECTION-DRIFTED
(see scripts/sdk_family_drift_check.py): LIBSND VMANAGER (135 rows,
def-row spread 0x6194 over 4 targets) and LIBCD SYS (161 rows, sig-db
agree x161, spread 0x9b4 x12 IDENTICAL on all 8 targets).  Their census
addresses are archive-layout projections onto game-compiled copies and
must not be adopted wholesale; only per-function byte-proof (the
1136/1406 discipline) reaches that class.
"""

import re
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path("/home/z/my-project/cannon-seed")
REPORT = REPO / "config" / "sdk_members.txt"
CURATED = REPO / "config" / "symbols.curated.txt"
ANCHORS = REPO / "config" / "sdk_anchors.txt"

ROW = re.compile(
    r"^//\s+(0x[0-9a-fA-F]+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*(adoptable)?"
    r"\s*(?:\(sig-db\s+(\w+)\))?")
TGT = re.compile(r"^// target:\s*(\S+)")
ASSIGN = re.compile(r"^([A-Za-z_]\w*) = (0x[0-9a-fA-F]+);")


def load_census():
    targets = defaultdict(list)  # t -> [(addr, lib, member, mark, sname, adopt, sig)]
    cur = None
    for ln in REPORT.read_text(errors="replace").splitlines():
        m = TGT.match(ln)
        if m:
            cur = m.group(1)
            continue
        m = ROW.match(ln)
        if m and cur:
            a, lib, member, mark, sname, adopt, sig = m.groups()
            targets[cur].append((int(a, 16), lib, member, mark, sname,
                                 bool(adopt), sig or ""))
    return targets


def agree_map(rows):
    """addr -> sorted libs: ambiguous addresses where 2+ DISTINCT members
    all define the same symbol (same rule as tools/sdk_curated.py)."""
    amb = defaultdict(list)
    for addr, lib, member, mark, sname, adopt, sig in rows:
        if mark == "ambiguous":
            amb[addr].append((lib, member, sname))
    agrees = {}
    for addr, claims in amb.items():
        members = {(lib, member) for lib, member, _ in claims}
        snames = {s for _l, _m, s in claims}
        if len(members) > 1 and len(snames) == 1:
            agrees[addr] = sorted({lib for lib, _m, _ in claims})
    return agrees


def load_adopted():
    """t -> (addr_set, name_set) from every assignment line in the
    curated file (hand head + generated block alike)."""
    addr_set = defaultdict(set)
    name_set = defaultdict(set)
    cur = None
    for ln in CURATED.read_text(errors="replace").splitlines():
        m = TGT.match(ln)
        if m:
            cur = m.group(1)
            continue
        m = ASSIGN.match(ln)
        if m and cur:
            name_set[cur].add(m.group(1))
            addr_set[cur].add(int(m.group(2), 16))
    return addr_set, name_set


def load_anchors():
    """set of (t, addr) with an anchor row + its class."""
    out = set()
    cur = None
    for ln in ANCHORS.read_text(errors="replace").splitlines():
        m = TGT.match(ln)
        if m:
            cur = m.group(1)
            continue
        m = re.match(r"^//\s+(0x[0-9a-fA-F]+)\s+(\S+)", ln)
        if m and cur:
            out.add((cur, int(m.group(1), 16)))
    return out


def main():
    targets = load_census()
    addr_cur, name_cur = load_adopted()
    anchors = load_anchors()

    cls = defaultdict(int)
    fam_multiaddr = defaultdict(list)   # (lib, member) -> [(t, addr, mark, sig)]
    fam_stubclash = defaultdict(list)   # addr-shape stub families
    amb_solo = defaultdict(list)        # ambiguous adoptable, single claimant

    for t, rows in sorted(targets.items()):
        ag = agree_map(rows)
        a_cur = addr_cur.get(t, set())
        n_cur = name_cur.get(t, set())
        # member -> addresses claimed in this target (for multi-addr shape)
        per_member = defaultdict(list)
        for addr, lib, member, mark, sname, adopt, sig in rows:
            # LIBGTE's member column renders "?" (no OMF module names in the
            # archive symbol tables the census shows) - the real family key
            # there is the symbol name itself.
            key = sname if member == "?" else member
            per_member[(lib, key)].append((addr, mark, sname, adopt, sig))
        multi_addr = {k for k, v in per_member.items() if len(v) > 1}

        for addr, lib, member, mark, sname, adopt, sig in rows:
            adopted_here = addr in a_cur
            if adopted_here:
                cls[(t, "adopted-at-addr")] += 1
                continue
            if sname in n_cur:
                cls[(t, "name-curated-elsewhere")] += 1
                continue
            if not adopt:
                cls[(t, "non-adoptable")] += 1
                if mark == "ambiguous":
                    cls[(t, "non-adoptable-ambiguous")] += 1
                continue
            # adoptable, not adopted, name not curated elsewhere
            if mark in ("anchored", "unique") or (mark == "ambiguous" and addr in ag):
                cls[(t, "ADOPTABLE-UNADOPTED-anchored/unique/agree")] += 1
                continue
            # adoptable ambiguous without agree
            cls[(t, "amb-no-agree")] += 1
            # claimant shape at this address
            claimants = [(l, m, s) for (l, m), lst in per_member.items()
                         for (a2, mk, s, ad, sg) in lst if a2 == addr]
            fkey = sname if member == "?" else member
            if (lib, fkey) in multi_addr:
                fam_multiaddr[(lib, fkey)].append((t, addr, mark, sig))
                cls[(t, "amb-no-agree-shape-multiaddr")] += 1
            elif len({(l, m) for l, m, _ in claimants}) > 1:
                fam_stubclash[(lib, fkey)].append((t, addr, mark, sig))
                cls[(t, "amb-no-agree-shape-stubclash")] += 1
            else:
                amb_solo[(lib, fkey)].append((t, addr, mark, sig))
                cls[(t, "amb-no-agree-shape-solo")] += 1

    print("== per-target class totals ==")
    ts = sorted({t for t, _ in cls})
    keys = sorted({k for _t, k in cls})
    hdr = f"{'class':<42}" + "".join(f"{t[:9]:>10}" for t in ts) + f"{'TOTAL':>9}"
    print(hdr)
    for k in keys:
        vals = [cls.get((t, k), 0) for t in ts]
        print(f"{k:<42}" + "".join(f"{v:>10}" for v in vals) + f"{sum(vals):>9}")

    def fam_report(title, fam, limit=25):
        print(f"\n== {title} (top {limit} by placements) ==")
        rows = sorted(fam.items(), key=lambda kv: -len(kv[1]))
        for (lib, member), lst in rows[:limit]:
            tgts = sorted({t for t, _a, _m, _s in lst})
            anch = sum(1 for t, a, _m, _s in lst if (t, a) in anchors)
            sigs = defaultdict(int)
            for _t, _a, _m, s in lst:
                sigs[s or "-"] += 1
            sigtxt = " ".join(f"{k}:{v}" for k, v in sorted(sigs.items()))
            print(f"  {lib:<8} {member:<24} n={len(lst):<3} tgts={len(tgts):<2} "
                  f"anchor-hits={anch:<3} sig[{sigtxt}]")
            for t, a, m, s in sorted(lst)[:4]:
                print(f"      {t:<12} 0x{a:08X} {m:<10} {s or '-'}")

    fam_report("SHAPE multi-addr: one member claims several addresses "
               "(real-copy class)", fam_multiaddr)
    fam_report("SHAPE stubclash: several members claim one address, "
               "different names", fam_stubclash)
    fam_report("SHAPE solo: ambiguous adoptable with a single claimant",
               amb_solo)


if __name__ == "__main__":
    sys.exit(main())

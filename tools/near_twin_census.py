#!/usr/bin/env python3
"""near_twin_census.py - global near-twin wave census across all 8 targets.

Re-bank in-repo (the cron-20261020-1639 repo-external scratch was eaten by
the twentieth rollback; tools/lm_probe_diff.py set the precedent for the
re-bank). Finds the GsGetTimInfo / GsClearOt decode class directly:

1. Per target: every non-matched, non-veneer, non-fragment STT_FUNC row
   with baseline bytes available (pair_report helpers).
2. BYTE-IDENTICAL groups: rows keyed by (size, sha1(bytes)) whose members
   span >= 2 targets. One C source lands every row of such a wave; the
   shared-alias mechanism (config/symbols.<t>.txt curations) carries the
   per-target symbol names.
3. NEAR groups: same-name, same-size rows across targets whose bytes agree
   on >= 95% of words (the GsGetTimInfo 56/57 shape: only relocation-
   carrying slots differ). Differing word indices are printed so the
   relocation-slot reading can be eyeballed.

Usage: python3 tools/near_twin_census.py [min_members]
Output is ranked: byte-identical waves first (by member count, then size),
near groups after. Everything printed is a DECODE CANDIDATE, not a
landing - judge_unit.py + make verify remain the oracles.
Gated (cron-20261022-0928): a target enters the pool only through
pair_report.input_gates (witnessed baseline + build ELF consistent with
the committed yaml); every requested target refused = exit 2.
"""
import hashlib
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pair_report as pr  # noqa: E402

TARGETS = [
    "slps_00270", "sces_00269",
    "mainmenu_jp", "mainmenu_eu",
    "g3_jp", "g3_eu",
    "g3org_jp", "g3org_eu",
]


def collect(targets=None):
    rows = []
    for t in (targets or TARGETS):
        funcs = pr.elf_funcs(os.path.join(pr.REPO, f"build/{t}.elf"))
        for name, (va, size) in sorted(funcs.items()):
            if pr.is_matched(t, name, va):
                continue
            if pr.fn_class(t, va, size, name) in ("veneer", "fragment"):
                continue
            b = pr.baseline_bytes(t, va, size)
            if b is None:
                continue
            rows.append((t, name, va, size, b))
    return rows


def word_diffs(a, b):
    assert len(a) == len(b)
    return [i for i in range(0, len(a), 4)
            if a[i:i + 4] != b[i:i + 4]]


def is_standalone(b):
    """True when the body is a complete function: own prologue
    (addiu sp,sp,-N paired with sw ra,N(sp) in the first two words,
    either order) and its own jr ra inside the extent. Members WITHOUT
    this shape are parent-frame-bound interior blocks - the 0x28 wave's
    lw v1,0x14(sp) counters read the ENCLOSING row's stack slots and can
    only land with their parent (cron-202610290640 finding: all 392
    byte-identical waves' members are parent-bound; the carvable
    interior class is the quartet's prologue+epilogue shape)."""
    if len(b) < 8:
        return False
    w0, w1 = struct.unpack("<II", b[:8])
    addiu_sp = (w0 >> 16) == 0x27BD
    sw_ra = (w0 >> 16) == 0xAFBF
    addiu_sp2 = (w1 >> 16) == 0x27BD
    sw_ra2 = (w1 >> 16) == 0xAFBF
    if not ((addiu_sp and sw_ra2) or (sw_ra and addiu_sp2)):
        return False
    n4 = len(b) // 4
    words = struct.unpack(f"<{n4}I", b[:n4 * 4])
    return 0x03E00008 in words


def member_class(target, va, size, b):
    """'own-row' = the VA starts a committed yaml row of the same extent
    (one-flip landing, the x7 e3dc shape); 'standalone' = complete
    function inside a bigger walk row (the quartet two-cut shape);
    'parent' = parent-frame-bound interior block, NOT carvable alone."""
    for lo, hi, _label, _kind in pr.fam_rows(target):
        if lo == va and hi - lo == size:
            return "own-row"
    return "standalone" if is_standalone(b) else "parent"


def main():
    min_members = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    allowed, refused = [], []
    for t in TARGETS:
        ok, problems = pr.input_gates(t)
        if ok:
            allowed.append(t)
        else:
            refused.append(t)
            print(f"{t}: REFUSED - {'; '.join(problems)}")
    if refused and not allowed:
        print("\nall targets REFUSED - no census. Run the disc-return "
              "sequence first (witness 8/8 STRICT).", file=sys.stderr)
        return 2
    rows = collect(allowed)
    print(f"pool: {len(rows)} unmatched non-veneer non-fragment rows "
          f"across {len(allowed)} witnessed targets")

    # ---- byte-identical groups ----
    exact = {}
    for t, name, va, size, b in rows:
        exact.setdefault((size, hashlib.sha1(b).hexdigest()), []) \
             .append((t, name, va))
    waves = [g for g in exact.values() if len(g) >= min_members
             and len({x[0] for x in g}) >= 2]
    sizes = {(t, name, va): size for t, name, va, size, _ in rows}
    waves.sort(key=lambda g: (-len(g), -sizes[g[0]]))
    print(f"\n== BYTE-IDENTICAL waves (>= {min_members} members, "
          f">= 2 targets): {len(waves)} ==")
    tally = {"own-row": 0, "standalone": 0, "parent": 0}
    best = {}
    bytes_of = {}
    for g in waves:
        cls = [member_class(t, va, sizes[(t, name, va)],
                            next(r[4] for r in rows
                                 if r[0] == t and r[1] == name
                                 and r[2] == va))
               for t, name, va in g]
        cnt = {k: cls.count(k) for k in tally}
        for k, v in cnt.items():
            tally[k] += v
        key = ("own-row" if cnt["own-row"] else
               "standalone" if cnt["standalone"] else "parent")
        best[key] = best.get(key, 0) + 1
        bytes_of[key] = bytes_of.get(key, 0) + len(g) * sizes[g[0]]
        members = " ".join(f"{t}:{name}@{va:08X}" for t, name, va in g)
        tag = (f"own-row={cnt['own-row']}"
               f" standalone={cnt['standalone']}"
               f" parent={cnt['parent']}")
        print(f"  x{len(g)} size=0x{sizes[g[0]]:X} [{tag}]  {members}")
    print(f"\n== carvable tally: "
          f"waves by best class {best}; "
          f"members own-row={tally['own-row']} "
          f"standalone={tally['standalone']} "
          f"parent-bound={tally['parent']} "
          f"(bytes {bytes_of.get('own-row', 0)}/"
          f"{bytes_of.get('standalone', 0)}/"
          f"{bytes_of.get('parent', 0)}) ==")

    # ---- near groups (same name+size across targets, >=95% words) ----
    byname = {}
    for t, name, va, size, b in rows:
        byname.setdefault((name, size), []).append((t, va, b))
    near = []
    for (name, size), mems in byname.items():
        if len(mems) < min_members:
            continue
        if len({m[0] for m in mems}) < 2:
            continue
        base_t, base_va, base_b = mems[0]
        worst = 0
        worst_idx = []
        for t, va, b in mems[1:]:
            idx = word_diffs(base_b, b)
            nw = len(base_b) // 4
            if nw and len(idx) / nw > worst:
                worst = len(idx) / nw
                worst_idx = idx
        if worst <= 0.05:
            near.append((worst, name, size, mems, worst_idx))
    print(f"\n== NEAR groups (same name+size, <= 5% words differ): "
          f"{len(near)} ==")
    for worst, name, size, mems, idx in sorted(near):
        members = " ".join(f"{t}@{va:08X}" for t, va, _ in mems)
        slots = ",".join(f"0x{i:X}" for i in idx[:12])
        print(f"  {name} size=0x{size:X} maxdiff={worst:.3f} "
              f"[{members}] diffwords=[{slots}]")


if __name__ == "__main__":
    sys.exit(main())

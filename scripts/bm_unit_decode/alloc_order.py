#!/usr/bin/env python3
"""alloc_order.py - mechanize the allocation-ORDER input of global-alloc.

The 1735 window mechanized find_reg's two-pass semantics (pass 0 reuses
already-allocated regs first) and concluded the str->a1 hoist, the -1-in-s2
and the s3 cache are global-alloc CASCADE outcomes: the input is the pseudo
set + allocation ORDER distilled from the byte-exact middle.  This tool
closes the input side: the order itself.

Sources (gcc 2.6.3, read from the local vanilla tree):
  * toplev.c pass order: flow_analysis (life_analysis + dump_flow_info)
    -> combine -> sched -> regclass + local_alloc -> global_alloc.
    NOTHING runs between local_alloc's dump and global_alloc, so the
    .lreg dump's dump_flow_info section ("Register N used X times across
    Y insns") holds the EXACT reg_n_refs / reg_live_length values that
    global-alloc's allocno_compare consumes.
  * global.c allocno_compare: pri = trunc((double)(floor_log2(n_refs) *
    n_refs) / live_length * 10000 * size); sort DESCENDING by pri, ties
    by ascending allocno (allocno index = ascending head-pseudo order).
  * global.c 383-423: pseudo -> allocno iff n_refs != 0, not already
    local-alloc-assigned, live_length != -1; merges (reg_may_share) sum
    n_refs, take max live_length; size = PSEUDO_REGNO_SIZE (SImode = 1).
  * global.c dump_conflicts prints ";; N regs to allocate:" listing
    allocno_reg[allocno_order[i]] IN ALLOCATION ORDER - the dump states
    the order the allocator will attempt.
  * global.c find_reg: pass 0 candidates = regs_used_so_far (local-alloc
    regs + every earlier GLOBAL allocation - find_reg:1179 adds each
    allocated reg) minus conflicts minus someone-prefers; scan ascending.
    Pass 1 drops the reuse-only restriction; then copy-pref / pref
    overrides (dump prints hard_reg_preferences only).

Usage: python3 scripts/bm_unit_decode/alloc_order.py <variant.c> [cc1-extra]
"""
import math
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLROOT = os.environ.get("TOOLROOT", "/home/z/my-project/tools-local/mipsel-root")
FIRST_PSEUDO_DEFAULT = 67  # vanilla config/mips/mips.h FIRST_PSEUDO_REGISTER
# o32 GR allocation window: FIXED = 0(zero),1(at),26,27(k),28(gp),29(sp);
# CALL_USED = 2..15,24,25,31 (v0/v1/a0-a3/t0-t9/t8-t9/ra); call-saved = 16..23,30.
GR_SCAN = [r for r in range(2, 32) if r not in (26, 27, 28, 29)]
FIXED = {0, 1, 26, 27, 28, 29}
CALL_USED = set(range(2, 16)) | {24, 25, 31}


def compile_variant(cand, extra):
    base = os.path.splitext(os.path.basename(cand))[0]
    stem = os.path.join(REPO, "build/judge", "ord_" + base)
    os.makedirs(os.path.join(REPO, "build/judge"), exist_ok=True)
    env = dict(os.environ, CC1FLAGS_EXTRA=extra + " -da",
               LD_LIBRARY_PATH=f"{TOOLROOT}/usr/lib/x86_64-linux-gnu")
    r = subprocess.run([os.path.join(REPO, "tools/cc.sh"), "-o", stem + ".o", cand],
                       cwd=REPO, capture_output=True, text=True, env=env)
    if r.returncode:
        print(f"COMPILE-FAIL:\n{r.stderr[-800:]}")
        sys.exit(1)
    return stem + ".i"


def parse_lreg_flowinfo(path):
    """'Register N used X times across Y insns' -> {N: (X, Y)} (post-local-alloc)."""
    refs, ll, calls = {}, {}, {}
    text = open(path, errors="replace").read()
    for m in re.finditer(r"^Register (\d+) used (\d+) times across (-?\d+) insns([^\n]*)",
                         text, re.M):
        refs[int(m.group(1))] = int(m.group(2))
        ll[int(m.group(1))] = int(m.group(3))
        c = re.search(r"crosses (\d+) call", m.group(4))
        calls[int(m.group(1))] = int(c.group(1)) if c else 0
    return refs, ll, calls


def parse_greg(path):
    """Order line, per-allocno hard conflicts/prefs, dispositions, used regs."""
    text = open(path, errors="replace").read()
    order, sizes, merges = [], {}, {}
    m = re.search(r"^;; (\d+) regs to allocate:(.*)$", text, re.M)
    if not m:
        print("GREG-PARSE-FAIL: no 'regs to allocate' line")
        sys.exit(1)
    toks = m.group(2).split()
    i = 0
    while i < len(toks):
        t = re.match(r"^(\d+)((?:\+\d+)*)$", toks[i])
        if not t:
            print(f"GREG-PARSE-FAIL: bad token {toks[i]!r}")
            sys.exit(1)
        head = int(t.group(1))
        order.append(head)
        ml = [int(x) for x in re.findall(r"\+(\d+)", t.group(2))]
        if ml:
            merges[head] = ml
        if i + 1 < len(toks) and re.match(r"^\((\d+)\)$", toks[i + 1]):
            sizes[head] = int(toks[i + 1][1:-1])
            i += 1
        i += 1
    n_alloc = int(m.group(1))
    if n_alloc != len(order):
        print(f"GREG-PARSE-FAIL: header says {n_alloc}, parsed {len(order)}")
        sys.exit(1)

    conflicts, prefs = {}, {}
    for mm in re.finditer(r"^;; (\d+) (conflicts|preferences):(.*)$", text, re.M):
        nums = [int(x) for x in mm.group(3).split()]
        (conflicts if mm.group(2) == "conflicts" else prefs)[int(mm.group(1))] = nums

    disp = {}
    m = re.search(r";; Register dispositions:\n(.*?)\n\n", text, re.S)
    if m:
        for d in re.finditer(r"(\d+) in (\d+)", m.group(1)):
            disp[int(d.group(1))] = int(d.group(2))

    used = []
    m = re.search(r";; Hard regs used:(.*)$", text, re.M)
    if m:
        used = [int(x) for x in m.group(1).split()]
    return order, sizes, merges, conflicts, prefs, disp, used


def floor_log2(n):
    return n.bit_length() - 1


def allocno_pri(n_refs, ll, size):
    """global.c allocno_compare, exact C semantics (double, trunc on assign)."""
    ll_eff = -1 if ll == 0 else ll  # global.c 541: LL 0 -> -1 before sorting
    return math.trunc((float(floor_log2(n_refs) * n_refs) / ll_eff) * 10000 * size)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    cand = os.path.abspath(sys.argv[1])
    extra = sys.argv[2] if len(sys.argv) > 2 else ""
    prefix = compile_variant(cand, extra)

    refs, ll, calls = parse_lreg_flowinfo(prefix + ".lreg")
    order, sizes, merges, conflicts, prefs, disp, used = parse_greg(prefix + ".greg")

    fp = FIRST_PSEUDO_DEFAULT
    bad = [p for p in order if p < fp]
    if bad:
        fp = min(bad)
        print(f"NOTE: pseudo below {FIRST_PSEUDO_DEFAULT} seen -> FIRST_PSEUDO={fp}")
    # conflicts/prefs lines legitimately mix pseudo (>= fp) and hard (< fp)
    # numbers; only the used/disposition TARGET sides must be purely hard.
    hard_bad = sorted({n for n in used if n >= fp}
                      | {r for r in disp.values() if r >= fp})
    if hard_bad:
        print(f"WARN: numbers >= {fp} on HARD-reg-only sides: {hard_bad}")

    # allocno groups in head order (= allocno index order)
    heads = sorted(order)
    groups = {}
    for h in heads:
        groups[h] = [h] + merges.get(h, [])

    missing = [p for h in heads for p in groups[h] if p not in refs]
    if missing:
        print(f"WARN: members without .lreg flow-info line (refs=0?): {missing}")

    pri = {}
    for h in heads:
        g = groups[h]
        n = sum(refs.get(p, 0) for p in g)
        length = max((ll.get(p, 0) for p in g), default=0)
        pri[h] = allocno_pri(n, length, sizes.get(h, 1))

    predicted = sorted(heads, key=lambda h: (-pri[h], h))
    match = predicted == order
    pos = {h: i + 1 for i, h in enumerate(order)}

    print(f"== {os.path.basename(cand)} [{extra or 'default flags'}]")
    print(f"allocnos={len(order)}  order-match: "
          f"{'EXACT (keys mechanized)' if match else 'MISMATCH - investigate'}")

    # cascade-critical pseudos (from the banked 1620/1735 records)
    CRIT = {p: label for p, label in ((73, "str (move-chain pseudo)"),
                                      (155, "const -1 (REG_EQUIV)"))
            if p in pos}

    hdr = "turn pseudo(+merge)       pri  refs   LL  sz  reg  note"
    print(hdr)
    for i, h in enumerate(order):
        g = groups[h]
        reg = disp.get(h, "-")
        note = ""
        for p in g:
            if p in CRIT:
                note = CRIT[p]
        if merges.get(h):
            note = (note + " " if note else "") + f"merged {merges[h]}"
        print(f"{i + 1:4d} {h:6d}{'+' + ','.join(map(str, merges[h])) if merges.get(h) else '':>14}"
              f" {pri[h]:7d} {sum(refs.get(p, 0) for p in g):5d}"
              f" {max((ll.get(p, 0) for p in groups[h]), default=0):5d}"
              f" {sizes.get(h, 1):3d}  {reg:>3}  {note}")

    # pass-0 reuse-pool trace at the cascade-critical turns
    local_regs = {p: r for p, r in disp.items() if p not in pos and r >= 0}
    pool0 = sorted({r for r in local_regs.values() if r < fp})
    print(f"\nlocal-alloc-assigned pseudos: {len(local_regs)}; "
          f"entry reuse pool = {pool0}")

    # full two-pass find_reg replay.  someone-prefers (prune_preferences) is
    # rebuilt from the PRINTED (already-pruned) preferences of conflicting
    # lower-priority allocnos - a conservative subset: the dump never carries
    # copy-prefs, so an allocno whose displacement came only through a
    # copy-pref may still miss.  caller-saves and the local-alloc kick-out
    # stay unmodeled (neither fires in this unit).
    heads_pos = {h: i for i, h in enumerate(order)}
    full_prefs = {h: sorted(n for n in prefs.get(h, []) if n < fp) for h in order}
    someone = {}
    for h in reversed(order):  # prune_preferences: lowest priority first
        acc = set()
        for j, prefs_j in full_prefs.items():
            if (heads_pos[j] > heads_pos[h]
                    and (CONFLICT := (j in conflicts.get(h, [])
                                      or h in conflicts.get(j, [])))):
                acc |= set(prefs_j)
                if sizes.get(j, 1) <= sizes.get(h, 1):
                    acc -= set(full_prefs[h])
        someone[h] = acc

    walk = set(pool0)
    hits = misses = 0
    for i, h in enumerate(order):
        g = groups[h]
        cc = max(calls.get(p, 0) for p in g)
        used1 = set(FIXED)
        if cc:
            used1 |= CALL_USED
        used1 |= {n for n in conflicts.get(h, []) if n < fp}
        for p in conflicts.get(h, []):
            if p in pos and order.index(p) < i:  # earlier-allocated conflicting allocno
                r = disp.get(p)
                if r is not None and r >= 0:
                    used1.update(range(r, r + sizes.get(p, 1)))
        own_prefs = sorted(n for n in prefs.get(h, []) if n < fp)
        best = None
        via = None
        c0 = [r for r in GR_SCAN if r in walk and r not in used1
              and r not in someone[h]]
        if c0:
            best, via = c0[0], "pass0"
        else:
            c1 = [r for r in GR_SCAN if r not in used1]
            if c1:
                best, via = c1[0], "pass1"
        if best is not None and own_prefs and best not in own_prefs:
            # the override's `used` is the succeeded pass's set: pass-0's
            # includes the reuse-only + someone-prefers terms
            if via == "pass0":
                freep = [r for r in own_prefs if r in walk and r not in used1
                         and r not in someone[h]]
            else:
                freep = [r for r in own_prefs if r not in used1]
            if freep:
                best, via = freep[0], via + "+pref"
        crit = [p for p in g if p in CRIT]
        got = disp.get(h)
        ok = None
        if got is not None and got >= 0:
            ok = best == got
            hits, misses = hits + ok, misses + (not ok)
        show = crit or ok is False or i < 3 or i >= len(order) - 3
        if show:
            tag = " <== " + ",".join(CRIT[p] for p in crit) if crit else ""
            print(f"  turn {i + 1:2d} pseudo {h}: cc={cc} pool={len(walk)} "
                  f"predicted={best}({via}) actual={got} "
                  f"{'OK' if ok else ('MISS' if ok is False else 'n/a')}{tag}")
        if got is not None and got >= 0:
            walk.update(range(got, got + sizes.get(h, 1)))
    print(f"\nreplay: {hits}/{hits + misses} dispositions reproduced "
          f"(someone-prefers rebuilt from printed prefs only; copy-prefs are "
          f"not in the dump - the residual misses are copy-pref-driven; "
          f"caller-saves and the kick-out do not fire in this unit)")
    print("\nverdict: allocation order = deterministic function of the middle's "
          "(n_refs, live_length, size, calls_crossed) via allocno_compare" if match else
          "verdict: computed order diverges - aggregation rule needs work")
    return 0 if match else 1


if __name__ == "__main__":
    sys.exit(main())

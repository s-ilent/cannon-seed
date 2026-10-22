#!/usr/bin/env python3
"""pair_report.py - region-pair function similarity report (coddog-compare2
replacement; coddog-cli is not installed in this sandbox rebuild).

Reads each target's build ELF symtab (plain struct parse, ELF32 LE), pairs
functions by NAME across the two regions, compares their baseline bytes
(baseline .bin offset = VA - 0x80020000 + 0x800, length = st_size), and
buckets by byte-equality ratio exactly like the banked coddog table
(100.00 / 95-99.99 / 80-94.99 / <80).

Flags: M = matched (the unit renders as C in THAT target: a build/src
section covers its VA in the target's generated linker script - see
c_sections; src/<name>.c existence alone is NOT target-scoped, src/ is
shared across all eight exes), U = unmatched (asm .s only).
Also emits, per pair, the contiguous runs ("clusters") of exact (100.00%)
UNMATCHED pairs ordered by density - the matching lane's pick list.

INPUT GATES (cron-20261022-0928): every consumer of baselines/ or build/
runs input_gates() first and refuses unwitnessed inputs -
* baseline_witness: sha1(baselines/<t>.bin) must equal the committed
  config/sha1/<t>.sha1 hash (judge_unit's gate, verify.sh's gate 2). The
  woven-set sandbox (witness 0/8 since the 40th rollback) slices garbage
  into every byte comparison - a different hash is a different build.
* stale_symbols: build/<t>.elf is ephemeral (a rollback restores it from
  a stale snapshot); any yaml c-row label the ELF links OUTSIDE its own
  row span proves the ELF predates the committed yaml (the 0658 audit's
  57 stale-ELF-VA relocations) and every VA it yields is poison.

Usage: pair_report.py [--clusters N] [pair ...]
Default pairs: the four same-program region pairs.
Exit: 0 report produced; 2 every requested pair refused (gates).

PICK DELTA (cron-20261022-1158): the density print carries a one-line
instrument delta per pair - matched_delta_line, the 0658 audit's
classes (span-coverage gains, cross-exe artifact dissolves) recomputed
against the retired pre-0658 test, so a re-derived pick list's drift
from the banked lists is attributable at a glance instead of looking
like matching progress or a regression.
"""
import hashlib
import os
import re
import struct
import sys

REPO = os.environ.get("CANNON_SEED_REPO") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
BASE_VA = 0x80020000
HDR = 0x800

PAIRS = [
    ("slps_00270", "sces_00269"),
    ("mainmenu_jp", "mainmenu_eu"),
    ("g3_jp", "g3_eu"),
    ("g3org_jp", "g3org_eu"),
]


def elf_funcs(path):
    """{name: (va, size)} for STT_FUNC global+local symbols with size>0."""
    d = open(path, "rb").read()
    assert d[:4] == b"\x7fELF", path
    _, ei_class, ei_data = d[4], d[5], d[6]
    assert ei_class == 1 and ei_data == 1, "want ELF32 LE"
    (e_type, e_machine, e_version, e_entry, e_phoff, e_shoff, e_flags,
     e_ehsize, e_phentsize, e_phnum, e_shentsize, e_shnum, e_shstrndx) = \
        struct.unpack_from("<HHIIIIIHHHHHH", d, 16)
    secs = []
    for i in range(e_shnum):
        (sh_name, sh_type, sh_flags, sh_addr, sh_offset, sh_size,
         sh_link, sh_info, sh_addralign, sh_entsize) = \
            struct.unpack_from("<IIIIIIIIII", d, e_shoff + i * e_shentsize)
        secs.append((sh_type, sh_offset, sh_size, sh_link, sh_entsize))
    # find .symtab and its linked .strtab
    out = {}
    for sh_type, sh_off, sh_size, sh_link, sh_entsize in secs:
        if sh_type != 2:  # SHT_SYMTAB
            continue
        str_off, str_size = secs[sh_link][1], secs[sh_link][2]
        strtab = d[str_off:str_off + str_size]
        for o in range(sh_off, sh_off + sh_size, 16):
            st_name, st_value, st_size, st_info, st_other, st_shndx = \
                struct.unpack_from("<IIIBBH", d, o)
            if st_size == 0:
                continue
            typ = st_info & 0xF
            if typ != 2:  # STT_FUNC
                continue
            end = strtab.index(b"\0", st_name)
            name = strtab[st_name:end].decode()
            out[name] = (st_value, st_size)
        break
    return out


def baseline_bytes(target, va, size):
    off = va - BASE_VA + HDR
    d = open(os.path.join(REPO, f"baselines/{target}.bin"), "rb").read()
    if off < 0 or off + size > len(d):
        return None
    return d[off:off + size]


def baseline_witness(target):
    """(ok, why) - is baselines/<t>.bin the committed oracle?

    Mirrors tools/judge_unit.py's baseline_gate (verify.sh's gate 2): the
    sha1sum-format file's first non-comment line's first field, lowercased,
    against sha1 of the local baseline. Post-flip (de0b0d68) the committed
    values are the TRUE baselines' hashes; the all-woven set a rollback
    restores (witness 0/8, re-confirmed every disc-blocked window since)
    slices garbage into every byte comparison. A different hash is a
    different build - never compare against it, never edit the sha1 file
    to pass. The true baselines return with the discs.
    """
    path = os.path.join(REPO, f"baselines/{target}.bin")
    if not os.path.exists(path):
        return False, "baselines/%s.bin missing" % target
    sha_file = os.path.join(REPO, f"config/sha1/{target}.sha1")
    expected = None
    with open(sha_file) as f:
        for ln in f:
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                expected = ln.split()[0].lower()
                break
    if expected is None:
        return False, "config/sha1/%s.sha1 has no hash field" % target
    with open(path, "rb") as f:
        actual = hashlib.sha1(f.read()).hexdigest()
    if expected != actual:
        return False, (
            "baselines/%s.bin sha1 %s != committed oracle %s "
            "(the woven-set class; witness 0/8)" % (target, actual[:12],
                                                    expected[:12]))
    return True, ""


_C_ROWS = {}


def c_rows(target):
    """(va_lo, va_hi, label) of the target's yaml c rows - the matched map.

    Structured parse mirroring tools/build.sh's c_list generation and
    tools/gen_ld.py's addressing exactly: yaml.safe_load over the code
    segments only, every 3+-element subsegment row of type `c`, VA =
    segment vram + (rom - 0x800). A row's span runs to the next
    subsegment row in payload order, so a merged parent covers the
    member functions split out of it (the ApplyMatrixSV data-row-host
    pattern) and `<base>.pN` piece rows cover their windows.

    The yaml (commit-tracked, oracle-gated by the next verify) is the
    right source - NOT build/<t>.gen.ld or .c_entries: those are
    ephemeral build-dir artifacts a sandbox rollback restores from a
    stale snapshot (the 40th rollback's build tree still lives in the
    woven era, thirty landings behind the committed yaml), and NOT a
    bare src/<name>.c existence test: src/ is shared across all eight
    exes, so a name can belong to another executable's build entirely
    (src/func_80037CAC.c is mainmenu_eu's; g3_eu's yaml covers
    0x80037CAC with an asm rowdef - the cron-20261022-0313b artifact).
    """
    if target in _C_ROWS:
        return _C_ROWS[target]
    import yaml
    rows = []
    with open(os.path.join(REPO, f"config/splat.{target}.yaml")) as f:
        cfg = yaml.safe_load(f)
    for si, seg in enumerate(cfg["segments"]):
        if not (isinstance(seg, dict) and seg.get("type") == "code"):
            continue
        base = seg.get("vram", BASE_VA)
        subs = [e for e in seg.get("subsegments", []) if isinstance(e, list)]
        # the segment's rom end bounds its last row's span (the next
        # segment's start; +0x40000 when the code segment is the last)
        seg_end = None
        for nxt_seg in cfg["segments"][si + 1:]:
            if isinstance(nxt_seg, dict) and nxt_seg.get("start") is not None:
                seg_end = nxt_seg["start"]
                break
        for i, e in enumerate(subs):
            if len(e) < 3 or e[1] != "c":
                continue
            lo = base + (e[0] - HDR)
            if i + 1 < len(subs):
                hi = base + (subs[i + 1][0] - HDR)
            elif seg_end is not None:
                hi = base + (seg_end - HDR)
            else:                       # last row of the last segment
                hi = lo + 0x40000
            rows.append((lo, hi, e[2]))
    _C_ROWS[target] = rows
    return rows


def is_matched(target, name, va=None):
    """Target-scoped matched test: the unit renders as C in THIS target.

    A c row of the target's own yaml covers the unit's VA (or, for
    name-only calls, a c row carries the unit's label). See c_rows for
    why the yaml decides and the file-existence test does not.
    """
    rows = c_rows(target)
    if va is not None:
        return any(lo <= va < hi for lo, hi, _ in rows)
    return any(lbl == name for _, _, lbl in rows)


def sym_funcs(target):
    """[(name, va)] for the target's curated function symbols.

    The shared symbol universe every report iterates (moved here from
    inventory_report so the delta helpers below run on the SAME
    universe the pick lists derive from). Config only - no ELF, no
    baseline - so it is legal on an unwitnessed tree.
    """
    out = []
    path = os.path.join(REPO, f"config/symbols.{target}.txt")
    for line in open(path):
        m = re.match(r"(\w+) = 0x([0-9A-Fa-f]+); // type:func", line)
        if m:
            out.append((m.group(1), int(m.group(2), 16)))
    return out


def stale_symbols(target, funcs=None):
    """[(label, va, spans)] - c-row labels the build ELF links outside
    their own yaml row span: the stale-build signature.

    build/<t>.elf is an ephemeral artifact a sandbox rollback restores
    from an old snapshot; the committed yaml is oracle-gated by the next
    verify. A c-row label linked at a VA no row of the committed yaml
    covers proves the ELF was laid out from a DIFFERENT (older) yaml -
    the cron-20261022-0658 audit's 57 True->False stale-ELF-VA
    relocations (GsSetLightMode linked at g3org_jp's woven 0x80063FD4
    while the committed true row sits at 0x8005B284; the check returns
    exactly those 57 on the 40th-rollback tree). Every elf_funcs VA is
    then poison for any VA-derived tool output. Labels absent from the
    ELF, asm/rowdef names, and multi-span labels hit in at least one
    span are all consistent - no violation.
    """
    if funcs is None:
        funcs = elf_funcs(os.path.join(REPO, f"build/{target}.elf"))
    spans = {}
    for lo, hi, lbl in c_rows(target):
        spans.setdefault(lbl, []).append((lo, hi))
    bad = []
    for lbl, (va, _size) in sorted(funcs.items()):
        sp = spans.get(lbl)
        if sp and not any(lo <= va < hi for lo, hi in sp):
            bad.append((lbl, va, sp))
    return bad


def input_gates(target, funcs=None):
    """(ok, problems) - both input gates, for every baseline/ELF consumer.

    Call BEFORE reading baselines/<t>.bin or build/<t>.elf-derived data;
    on False, print the problems and refuse (the caller decides skip vs
    exit 2). No bypass: judge_unit's oracle gate has none either.
    """
    problems = []
    ok, why = baseline_witness(target)
    if not ok:
        problems.append("witness: " + why)
    bad = stale_symbols(target, funcs)
    if bad:
        problems.append(
            "build/%s.elf stale vs committed yaml: %d c-row label(s) "
            "linked outside their own row span (first: %s at %08X)"
            % (target, len(bad), bad[0][0], bad[0][1]))
    return (not problems), problems


_RET_C_ROWS = {}


def retired_matched(target, name, va=None):
    """The RETIRED pre-0658 matched test, kept verbatim for the delta.

    This is the exact predicate the banked pick lists were generated
    with (through cron-20261022-0313b; retired by the 0658 window's
    474ebd3b): src/<name>.c existence - UNSCOPED, src/ is shared across
    all eight exes - OR the VA sits exactly ON a yaml c row's low
    address (the old line-regex c_row_vas set, NOT span coverage).

    Its known gaps are the delta's two classes: a merged-parent member
    sits MID-span with no src file of its own (under-counted - the 0658
    audit's 85 False->True span-coverage gains), and a cross-exe name
    collision has a src file while the target's yaml covers the VA with
    asm (over-counted - the audit's 15 True->False artifact fixes).
    Uses its own cache; never touches _C_ROWS (the live test's map).
    """
    if os.path.exists(os.path.join(REPO, "src", f"{name}.c")):
        return True
    if va is None:
        return False
    if target not in _RET_C_ROWS:
        vas = set()
        path = os.path.join(REPO, f"config/splat.{target}.yaml")
        with open(path) as f:
            for line in f:
                m = re.search(r"\[0x([0-9A-Fa-f]+),\s*c,", line)
                if m:
                    vas.add(int(m.group(1), 16) + BASE_VA - HDR)
        _RET_C_ROWS[target] = vas
    return va in _RET_C_ROWS[target]


def matched_delta(target):
    """(gains, dissolves) - the matched-test instrument delta, per target.

    Over the target's own symbols-file universe (sym_funcs; the same
    universe the pick lists derive from):
    * gains     - matched NOW, unmatched by the retired test: the
      span-coverage gains (merged-parent members, the ApplyMatrixSV
      data-row-host pattern). They LEFT the pick lists when the
      instrument changed - not matching progress.
    * dissolves - the retired test matched them, the yaml-span test
      does not. Two flavors, both honest corrections:
      (a) cross-exe name collisions - src/<name>.c is another exe's
      unit (func_80037CAC is mainmenu_eu's; the 0313b artifact);
      (b) cross-target landings - the unit renders as C in a SIBLING
      target's wave only, this target's yaml still renders it as asm
      (g3_eu's NormalColor sits in the asm gap between RotTrans and
      NormalColor3 while src/NormalColor.c exists). Flavor (b) units
      are REAL unmatched work the old lists hid - the dissolves RE-ADD
      them to the pick lists.
    Reads yaml + src/ + the symbols file ONLY: no baseline, no build
    ELF - so unlike the gated report paths this delta is legal on an
    unwitnessed tree (inventory_report --delta runs it there, and the
    gated runs print the same numbers inline).
    """
    gains, dissolves = [], []
    for name, va in sym_funcs(target):
        new = is_matched(target, name, va)
        old = retired_matched(target, name, va)
        if new and not old:
            gains.append((name, va))
        elif old and not new:
            dissolves.append((name, va))
    return gains, dissolves


def matched_delta_line(a, b):
    """One-line delta summary for a report/pair header (the 0928 bank:
    'the pick list re-derives with the 85 span gains and the dissolves
    visible at a glance')."""
    ga, da = matched_delta(a)
    gb, db = matched_delta(b)
    return ("pick delta vs the retired test: %s +%d/-%d, %s +%d/-%d "
            "(span gains / dissolves; instrument, not progress)"
            % (a, len(ga), len(da), b, len(gb), len(db)))


_ANCHORS = None
_LIBNAMES = None


def sdk_spans(target):
    """Anchored SDK-member spans for the target, from config/sdk_anchors.txt.

    Rows are grouped under `// target: <t>` headers; a cluster function is
    library-class when its VA starts an anchor or falls inside one.
    """
    global _ANCHORS
    if _ANCHORS is None:
        _ANCHORS = {}
        cur = None
        path = os.path.join(REPO, "config/sdk_anchors.txt")
        for line in open(path):
            m = re.match(r"// target: (\S+)", line)
            if m:
                cur = _ANCHORS.setdefault(m.group(1), [])
                continue
            f = line.split()
            if cur is not None and len(f) == 6 and f[0].startswith("0x"):
                cur.append((int(f[0], 16), int(f[1], 16)))
    return sorted(_ANCHORS.get(target, []))


def sdk_names():
    """Every SDK symbol name the reports define, across all targets.

    The build ELF already carries these names; the same member recurs at
    different addresses per target (and several times per image), so the
    name is the stable library-class signal, not the span.
    """
    global _LIBNAMES
    if _LIBNAMES is None:
        _LIBNAMES = set()
        for line in open(os.path.join(REPO, "config/sdk_anchors.txt")):
            f = line.split()
            if len(f) == 6 and f[0].startswith("0x"):
                _LIBNAMES.add(f[2])
        for line in open(os.path.join(REPO, "config/sdk_members.txt")):
            f = line.split()
            if len(f) >= 7 and f[0] == "//" and f[1].startswith("0x"):
                _LIBNAMES.add(f[6])
    return _LIBNAMES


def is_veneer(target, va, size):
    """The 3-word dispatch stub: addiu t2,vec; jr t2; addiu t1,idx.

    Vectors 0xA0/0xB0/0xC0 are the libc/kernel/B-call tables. The row may
    pad one zero word past the stub (the banked pad law).
    """
    if size not in (0xC, 0x10):
        return False
    b = baseline_bytes(target, va, size)
    if b is None:
        return False
    w = struct.unpack_from("<%dI" % (size // 4), b, 0)
    return (w[0] in (0x240A00A0, 0x240A00B0, 0x240A00C0)
            and w[1] == 0x01400008
            and (w[2] & 0xFFFF0000) == 0x24090000
            and all(x == 0 for x in w[3:]))


def is_fragment(target, va, size):
    """A symbol that starts at a function tail or inside a body.

    The scan's split detection emits these where a symbol boundary landed
    inside one function; they are not matchable units of their own. A real
    function of this size always ends in jr $ra (or a tail j), so a small
    symbol with no terminator is a body slice.

    Over 0x10 the epilogue-tail signatures no longer decide; the
    out-of-symbol branch signal does (the cron-20261022-0313b class:
    func_8002E3D0, sz 0x28, first insn move s0,v0, closing bne 0x4c past
    the symbol end). A compiled function's local branches never leave its
    own bounds, so any branch targeting outside [va, va+size) marks the
    symbol as a mid-body slice of the enclosing body. bal (branch-and-
    link with rs=0) is a call, not a local branch, and does not count.
    """
    if size > 0x10:
        return _branch_out_of_symbol(target, va, size)
    b = baseline_bytes(target, va, size)
    if b is None:
        return False
    w = struct.unpack_from("<%dI" % (size // 4), b, 0)
    if (w[0] & 0xFFFF0000) == 0x8FBF0000 or w[0] == 0x03E00008:
        return True                                  # starts at the epilogue
    op, base = (w[0] >> 26) & 0x3F, (w[0] >> 21) & 0x1F
    rt = (w[0] >> 16) & 0x1F
    if op == 0x23 and base == 29 and (16 <= rt <= 23 or rt == 31):
        return True                  # restores a saved reg before any store
    return 0x03E00008 not in w                       # no return at all


def _branch_out_of_symbol(target, va, size):
    """True when any local branch inside the symbol targets outside it."""
    b = baseline_bytes(target, va, size)
    if b is None:
        return False
    n = size // 4
    w = struct.unpack_from("<%dI" % n, b, 0)
    end = va + size
    for i, x in enumerate(w):
        op = (x >> 26) & 0x3F
        rs = (x >> 21) & 0x1F
        rt = (x >> 16) & 0x1F
        if op in (0x04, 0x05, 0x06, 0x07):           # beq/bne/blez/bgtz
            pass
        elif op == 0x01 and rt in (0x00, 0x01, 0x10, 0x11):
            if rs == 0:          # bltzal/bgezal with rs=0 is bal, a call
                continue
        else:
            continue
        off = x & 0xFFFF
        if off >= 0x8000:
            off -= 0x10000
        tgt = va + 4 * i + 4 + off * 4
        if tgt < va or tgt >= end:
            return True
    return False


def fn_class(target, va, size, name=""):
    if is_veneer(target, va, size):
        return "veneer"
    if is_fragment(target, va, size):
        return "fragment"
    if name in sdk_names():
        return "sdk"
    for ava, asz in sdk_spans(target):
        if ava <= va < ava + asz:
            return "sdk"
    return "compiler"


def sim(a, b):
    if a is None or b is None:
        return None
    if a == b:
        return 1.0
    eq = sum(1 for x, y in zip(a, b) if x == y)
    return eq / max(len(a), len(b))


def bucket(s):
    if s is None:
        return "bytefail"
    if s == 1.0:
        return "100.00"
    if s >= 0.95:
        return "95-99.99"
    if s >= 0.80:
        return "80-94.99"
    return "<80"


def main():
    want = sys.argv[1:] or None
    all_rows = {}
    refused = []
    gates = {}                     # per-target gate memo across pairs

    def gated(t):
        if t not in gates:
            gates[t] = input_gates(t)
        return gates[t]

    for a, b in PAIRS:
        label = f"{a}-{b}"
        if want and label not in want and a not in want and b not in want:
            continue
        ga_ok, ga = gated(a)
        gb_ok, gb = gated(b)
        if not (ga_ok and gb_ok):
            refused.append(label)
            print(f"== {label}: REFUSED - inputs not witnessed/consistent ==")
            for t, probs in ((a, ga), (b, gb)):
                for p in probs:
                    print(f"   {t}: {p}")
            continue
        fa = elf_funcs(os.path.join(REPO, f"build/{a}.elf"))
        fb = elf_funcs(os.path.join(REPO, f"build/{b}.elf"))
        rows = []
        for name, (va, size) in sorted(fa.items()):
            if name not in fb:
                continue
            va2, size2 = fb[name]
            sa = baseline_bytes(a, va, size)
            sb = baseline_bytes(b, va2, size2)
            s = sim(sa, sb)
            rows.append((name, va, size, va2, size2, s,
                         is_matched(a, name, va), is_matched(b, name, va2)))
        counts = {}
        ucounts = {}
        for r in rows:
            counts[bucket(r[5])] = counts.get(bucket(r[5]), 0) + 1
            if r[6] is False and r[7] is False:
                ucounts[bucket(r[5])] = ucounts.get(bucket(r[5]), 0) + 1
        print(f"\n== {label}: {len(rows)} pairs ==  "
              f"100.00%:{counts.get('100.00',0)}  95-99.99%:"
              f"{counts.get('95-99.99',0)}  80-94.99%:"
              f"{counts.get('80-94.99',0)}  <80%:{counts.get('<80',0)}"
              f"  bytefail:{counts.get('bytefail',0)}")
        print(f"   unmatched:  100.00%:{ucounts.get('100.00',0)}  "
              f"95-99.99%:{ucounts.get('95-99.99',0)}  "
              f"80-94.99%:{ucounts.get('80-94.99',0)}  "
              f"<80%:{ucounts.get('<80',0)}")
        # every unmatched pair with its ratio, for the near-twin pools
        with open(os.path.join(REPO, f"build/pairs_{a}_unmatched.txt"),
                  "w") as f:
            for r in sorted(rows, key=lambda r: -(r[5] or 0)):
                if r[6] is False and r[7] is False:
                    f.write(f"{bucket(r[5])} {r[5]:.4f} {r[0]} "
                            f"{r[1]:08X} {r[2]} {r[3]:08X} {r[4]}\n")
        all_rows[label] = rows

    # exact unmatched pairs -> contiguous clusters per JP side
    print("\n== exact (100.00%) UNMATCHED clusters, JP-side contiguous ==")
    for label, rows in all_rows.items():
        exact = sorted((r for r in rows if r[5] == 1.0
                        and r[6] is False and r[7] is False),
                       key=lambda r: r[1])
        if not exact:
            continue
        clusters = []
        cur = [exact[0]]
        for r in exact[1:]:
            if r[1] - (cur[-1][1] + cur[-1][2]) <= 0x20:
                cur.append(r)
            else:
                clusters.append(cur)
                cur = [r]
        clusters.append(cur)
        # density order: compiler-output functions first (the progress unit),
        # tactical library classes last - veneers are pinned, not matchable.
        tgt = label.split("-")[0]
        clusters = [[list(r) + [fn_class(tgt, r[1], r[2], r[0])] for r in c]
                    for c in clusters]
        clusters.sort(key=lambda c: (-sum(r[8] == "compiler" for r in c),
                                     -len(c)))
        jp = label.split("-")[0]
        nc = sum(1 for c in clusters for r in c if r[8] == "compiler")
        nlib = sum(1 for c in clusters for r in c if r[8] != "compiler")
        print(f"\n-- {label}: {len(exact)} exact unmatched, "
              f"{len(clusters)} clusters; {nc} compiler / {nlib} library "
              f"subject; density order --")
        print(f"   {matched_delta_line(jp, label.split('-')[1])}")
        shown_lib = 0
        for c in clusters:
            ncomp = sum(1 for r in c if r[8] == "compiler")
            if ncomp == 0:
                shown_lib += 1
                if shown_lib == 1:
                    print("    -- library-class clusters (tail work) --")
                print(f"   {len(c):3d} funcs  {c[0][1]:08X}.."
                      f"{c[-1][1]+c[-1][2]:08X}  [{c[0][8]}]")
                continue
            lo, hi = c[0][1], c[-1][1] + c[-1][2]
            print(f"   {len(c):3d} funcs ({ncomp} compiler)  "
                  f"{lo:08X}..{hi:08X} ({hi-lo:#x} bytes)")
            for r in c[:6]:
                print(f"        {r[0]}  {r[1]:08X} sz={r[2]:#x} [{r[8]}]")
            if len(c) > 6:
                print(f"        ... +{len(c)-6} more")
        if not shown_lib:
            pass
        # stash the pick list for the biggest target
        if want or True:
            with open(os.path.join(REPO, f"build/pairs_{jp}_exact.txt"),
                      "w") as f:
                for r in exact:
                    f.write(f"{r[0]} {r[1]:08X} {r[2]} {r[3]:08X} {r[4]}\n")
            with open(os.path.join(REPO, f"build/pairs_{jp}_density.txt"),
                      "w") as f:
                for c in clusters:
                    for r in c:
                        f.write(f"{r[8]} {r[0]} {r[1]:08X} {r[2]}\n")

    if refused and not all_rows:
        print("\nall requested pairs REFUSED - no report produced. The "
              "witness gate needs the disc-return sequence (witness 8/8 "
              "STRICT), then `make verify TARGET=<t>` per target to "
              "rebuild the stale build/ tree before this report means "
              "anything.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""pair_report.py - region-pair function similarity report (coddog-compare2
replacement; coddog-cli is not installed in this sandbox rebuild).

Reads each target's build ELF symtab (plain struct parse, ELF32 LE), pairs
functions by NAME across the two regions, compares their baseline bytes
(baseline .bin offset = VA - 0x80020000 + 0x800, length = st_size), and
buckets by byte-equality ratio exactly like the banked coddog table
(100.00 / 95-99.99 / 80-94.99 / <80).

Flags: M = matched (src/<name>.c exists, or the target's splat yaml row
at that VA is already a `c` row - curated-name C rows keep the func_
row name, so the file-existence test alone false-flags them unmatched),
U = unmatched (asm .s only).
Also emits, per pair, the contiguous runs ("clusters") of exact (100.00%)
UNMATCHED pairs ordered by density - the matching lane's pick list.

Usage: pair_report.py [--clusters N] [pair ...]
Default pairs: the four same-program region pairs.
"""
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


_C_ROWS = {}


def c_row_vas(target):
    """VAs of the target's splat yaml rows already flipped to C."""
    vas = set()
    path = os.path.join(REPO, f"config/splat.{target}.yaml")
    with open(path) as f:
        for line in f:
            m = re.search(r"\[0x([0-9A-Fa-f]+),\s*c,", line)
            if m:
                # yaml offsets are file offsets (baseline .bin offsets,
                # 0x800 header included): VA = off + 0x80020000 - 0x800
                vas.add(int(m.group(1), 16) + BASE_VA - HDR)
    return vas


def is_matched(target, name, va=None):
    if os.path.exists(os.path.join(REPO, f"src/{name}.c")):
        return True
    if va is None:
        return False
    if target not in _C_ROWS:
        _C_ROWS[target] = c_row_vas(target)
    return va in _C_ROWS[target]


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
    """
    if size > 0x10:
        return False
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
    for a, b in PAIRS:
        label = f"{a}-{b}"
        if want and label not in want and a not in want and b not in want:
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


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""split_classifier.py - classify invariant_census DATA-ROW candidates into
the split-landing classes, on the corrected label-vs-VA mapping.

The census (tools/invariant_census.py, f9b3e68e) finds landed-member copies
sitting as data rows but does not know the enclosing yaml geometry. This
tool closes that gap: for every DATA-ROW candidate it resolves the covering
yaml row of the target (by OFFSET ARITHMETIC - yaml_off = VA - 0x8001F800 -
never by label spelling, the cron-20261023-0442 lesson) and the landed
function's size from the source target's build ELF symtab, then classifies:

  WHOLE-ROW   candidate start == row start and fn size == row extent
              -> flip the whole row to c (the SsSetSerialVol mainmenu_eu
                 / GsGetTimInfo class; the old data .s retires).
  HEAD-SPLIT  candidate start == row start and fn size <  row extent
              -> c head + re-home the tail as a hand-written data row named
                 by its TRUE VA (the RotTransPers g3_jp template, ae3489da).
  SPILL       candidate start == row start and fn size >  row extent
              -> the body crosses into the following row(s); the split must
                 absorb them (list the span it would cover).
  MID-ROW     candidate start > row start -> the two-cut split pattern
              (SetColorMatrix class) with boundaries on both sides.

word-eq n/N rides in from the census line: n == N (dw=0) is the
byte-identical class the first-shot landings want; lower ratios need the
diff words explained BEFORE any landing (the 58-percent vintage lesson).

Usage: python3 tools/split_classifier.py [census.txt]
       (default build/invariant_census.txt; it is the gated artifact -
        run invariant_census.py first on a fresh oracle tree)
Output: stdout table + build/split_classifier.txt
Exit: 0 report produced; 2 no census file or no candidates.
"""
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pair_report import REPO, input_gates  # noqa: E402

BASE_VA = 0x8001F800   # yaml offset -> retail VA (pair_report convention)
HDR_NOTE = "yaml_off + 0x8001F800 = VA"

ROW_RE = re.compile(
    r"^\s*-\s*\[\s*(0x[0-9A-Fa-f]+)\s*,\s*([a-z0-9_]+)\s*,\s*([A-Za-z0-9_]+)"
    r"\s*\]\s*#\s*(0x[0-9A-Fa-f]+)")
CEN_RE = re.compile(
    r"^(DATA-ROW)\s+([0-9A-F]{8})\s+(\S+)\s+\|\s+src\s+(\S+)\s+(\S+)\s+"
    r"size\s+(0x[0-9A-Fa-f]+)\s+word-eq\s+(\d+)/(\d+)\s+votes\s+(\d+)")


def elf_syms(path):
    """{name: (va, size, type)} for STT_FUNC|STT_OBJECT symbols, size>0."""
    d = open(path, "rb").read()
    assert d[:4] == b"\x7fELF", path
    (e_type, e_machine, e_version, e_entry, e_phoff, e_shoff, e_flags,
     e_ehsize, e_phentsize, e_phnum, e_shentsize, e_shnum, e_shstrndx) = \
        struct.unpack_from("<HHIIIIIHHHHHH", d, 16)
    secs = []
    for i in range(e_shnum):
        (sh_name, sh_type, sh_flags, sh_addr, sh_offset, sh_size,
         sh_link, sh_info, sh_addralign, sh_entsize) = \
            struct.unpack_from("<IIIIIIIIII", d, e_shoff + i * e_shentsize)
        secs.append((sh_type, sh_offset, sh_size, sh_link))
    out = {}
    for sh_type, sh_off, sh_size, sh_link in secs:
        if sh_type != 2:
            continue
        str_off, str_size = secs[sh_link][1], secs[sh_link][2]
        strtab = d[str_off:str_off + str_size]
        for o in range(sh_off, sh_off + sh_size, 16):
            st_name, st_value, st_size, st_info, st_other, st_shndx = \
                struct.unpack_from("<IIIBBH", d, o)
            typ = st_info & 0xF
            if st_size == 0 or typ not in (1, 2):
                continue
            name = strtab[st_name:strtab.index(b"\0", st_name)]
            name = name.decode("utf-8", "replace")
            out[name] = (st_value, st_size, typ)
    return out


def yaml_rows(t):
    """[(start, extent, kind, label)] parsed from config/splat.<t>.yaml."""
    path = os.path.join(REPO, f"config/splat.{t}.yaml")
    rows = []
    for line in open(path, encoding="utf-8", errors="replace"):
        m = ROW_RE.match(line.strip().replace("- - ", "- "))
        if not m:
            m = ROW_RE.match(line.strip())
        if not m:
            continue
        start = int(m.group(1), 16)
        extent = int(m.group(4), 16)
        rows.append((start, extent, m.group(2), m.group(3)))
    rows.sort()
    return rows


def covering(rows, off):
    for start, extent, kind, label in rows:
        if start <= off < start + extent:
            return start, extent, kind, label
        if start > off:
            break
    return None


def main():
    cen = sys.argv[1] if len(sys.argv) > 1 else \
        os.path.join(REPO, "build/invariant_census.txt")
    if not os.path.exists(cen):
        print(f"split_classifier: no census file {cen} "
              f"(run tools/invariant_census.py first)")
        return 2
    cands = []
    for line in open(cen, encoding="utf-8", errors="replace"):
        m = CEN_RE.match(line)
        if m:
            cands.append(m.groups())
    if not cands:
        print("split_classifier: no DATA-ROW candidates in the census file")
        return 2

    yrows, fsyms, refused = {}, {}, []
    for t in sorted({c[2] for c in cands}):
        ok, problems = input_gates(t)
        if not ok:
            refused.append(f"{t}: {'; '.join(problems)}")
            continue
        yrows[t] = yaml_rows(t)
    for st in sorted({c[3] for c in cands}):
        p = os.path.join(REPO, f"build/{st}.elf")
        if os.path.exists(p):
            fsyms[st] = elf_syms(p)

    out = []
    for cls, va_s, tgt, src_t, name, size_s, eq_s, n_s, votes_s in cands:
        va = int(va_s, 16)
        fn_size = int(size_s, 16)
        eq, n = int(eq_s), int(n_s)
        votes = int(votes_s)
        if tgt not in yrows:
            continue
        yaml_off = va - BASE_VA
        cov = covering(yrows[tgt], yaml_off)
        if cov is None:
            out.append((9, "NO-ROW", tgt, va_s, src_t, name, fn_size,
                        eq, n, votes, "no covering yaml row"))
            continue
        rstart, rextent, rkind, rlabel = cov
        rel = yaml_off - rstart
        if rel != 0:
            verdict = f"MID-ROW rel +0x{rel:X} in {rlabel}({rkind} 0x{rextent:X})"
            rank = 3
        elif fn_size == rextent:
            verdict = (f"WHOLE-ROW {rlabel}({rkind} 0x{rextent:X}) "
                       f"-> flip whole row to c {name}")
            rank = 0
        elif fn_size < rextent:
            tail = rextent - fn_size
            tail_va = va + fn_size
            verdict = (f"HEAD-SPLIT {rlabel}({rkind} 0x{rextent:X}) "
                       f"-> c head 0x{fn_size:X} + tail 0x{tail:X} "
                       f"data_{tail_va:08X}")
            rank = 1
        else:
            span = fn_size - rextent
            verdict = (f"SPILL {rlabel}({rkind} 0x{rextent:X}) "
                       f"-> body overruns by 0x{span:X}; absorb next row(s)")
            rank = 2
        kind_note = "" if rkind == "data" else f" KIND={rkind}"
        dw = "dw=0" if eq == n else f"dw={n - eq}/{n}"
        out.append((rank, verdict.split()[0], tgt, va_s, src_t, name,
                    fn_size, eq, n, votes,
                    f"{verdict}{kind_note} | fn size 0x{fn_size:X} "
                    f"{dw} eq {eq}/{n} votes {votes}"))

    order = {0: "A-WHOLE-ROW", 1: "B-HEAD-SPLIT", 2: "C-SPILL",
             3: "D-MID-ROW", 9: "E-NO-ROW"}
    out.sort(key=lambda r: (r[0], -(r[7] - r[8]), r[2], r[3]))
    lines = []
    lines.append("== split classifier: census DATA-ROW candidates -> "
                 "split-landing classes ==")
    lines.append(f"mapping: {HDR_NOTE}; fn sizes from build/<src_t>.elf "
                 f"symtabs; census {os.path.basename(cen)}")
    lines.extend("gate: " + r for r in refused)
    for rank, _, tgt, va_s, src_t, name, fn_size, eq, n, votes, verdict \
            in out:
        lines.append(f"{order[rank]:<13} {va_s} {tgt:<12} | src {src_t:<12} "
                     f"{name:<22} {verdict}")
    text = "\n".join(lines) + "\n"
    sys.stdout.write(text)
    dst = os.path.join(REPO, "build/split_classifier.txt")
    with open(dst, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"... {len(out)} candidates -> {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

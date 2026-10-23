#!/usr/bin/env python3
"""invariant_census.py - the data-row copy census.

Generalizes cron-20261023-0212's x8 invariant back-edge scan (the
hand-picked 4-word pattern addiu s6,1 / slt / bnez / addiu fp,4 that
found SsSeqCalledTbyT's three DATA-row copies at g3_jp 0x8006BF8C /
g3org_eu 0x80069F98 / mainmenu_jp 0x800815A8) into a pass over EVERY
landed member body against EVERY target's full symbol map, FUNC and
OBJECT rows alike.

The class the x8 completion proved: a landed member's near-identical
copies can sit as DATA rows - the walk never carved them as code, so
neither the sibling probe (its pool needs fn_class compiler rows) nor
the pick lists can see them, and the census undercounts one layer
deeper than the name undercount.

Instrument (no hand-picked invariant):
  * every 4-word window of the landed RETAIL body (step 4 words for
    bodies >= 0x100, step 1 below) votes for a candidate start VA in
    each target: start = hitVA - window's byte offset in the body;
  * a candidate start confirmed by >= MINWIN distinct windows is a
    copy candidate; zero-word windows and windows whose first word
    occurs > MAXOCC times in the target image are skipped (nop/zero
    swamps);
  * the enclosing walk symbol decides the class:
      same-name matched row = the known copy (instrument sanity),
      STT_FUNC row          = the sibling class (name-blind here),
      STT_OBJECT row        = THE DATA-ROW COPY CLASS,
      no enclosing symbol   = uncarved gap (same class, deeper);
  * word-eq percent of the candidate extent vs the body ranks it.

Usage: python3 tools/invariant_census.py [target ...]   (default: all 8)
Output: stdout summary + build/invariant_census.txt (full row list).
Gated (cron-20261022-0928): input_gates per target; refusals printed.
Exit: 0 report produced (possibly partial); 2 every target refused.
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pair_report import (REPO, baseline_bytes, elf_funcs,  # noqa: E402
                         input_gates, is_matched)

TARGETS = ["slps_00270", "sces_00269", "mainmenu_jp", "mainmenu_eu",
           "g3_jp", "g3_eu", "g3org_jp", "g3org_eu"]
BASE_VA = 0x80020000
HDR = 0x800
MIN_BODY = 0x18       # below this a window vote is too weak to mean anything
MAXOCC = 512          # window-head word too common in the image -> skip
MINWIN_BIG = 3        # distinct windows voting, bodies >= 0x100 (step 4)
MINWIN_SMALL = 2      # bodies < 0x100 (step 1, denser windows)
MIN_EQ = 0.50         # candidate must agree on >= half its words


def better_eq(new_eq, new_n, p_eq, p_n):
    """True when the new row's word-eq fraction beats the prev row's.
    Cross-multiplied (no floats), strict: ties keep the first-seen row."""
    return new_eq * p_n > p_eq * new_n


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
        if sh_type != 2:  # SHT_SYMTAB
            continue
        str_off, str_size = secs[sh_link][1], secs[sh_link][2]
        strtab = d[str_off:str_off + str_size]
        for o in range(sh_off, sh_off + sh_size, 16):
            st_name, st_value, st_size, st_info, st_other, st_shndx = \
                struct.unpack_from("<IIIBBH", d, o)
            typ = st_info & 0xF
            if st_size == 0 or typ not in (1, 2):  # OBJECT | FUNC
                continue
            end = strtab.index(b"\0", st_name)
            name = strtab[st_name:end].decode()
            out[name] = (st_value, st_size, typ)
        break
    return out


class TargetImage:
    """Retail bytes + word index for one target's baseline exe image."""

    def __init__(self, target):
        self.target = target
        self.buf = open(os.path.join(REPO, f"baselines/{target}.bin"),
                        "rb").read()
        n = (len(self.buf) - HDR) // 4
        self.words = struct.unpack_from("<%dI" % n, self.buf, HDR)
        self.occ = {}
        for w in self.words:
            self.occ[w] = self.occ.get(w, 0) + 1
        self._pos = {}

    def positions(self, w):
        if w not in self._pos:
            if self.occ.get(w, 0) > MAXOCC:
                self._pos[w] = ()
            else:
                wl = self.words
                self._pos[w] = tuple(i for i, x in enumerate(wl) if x == w)
        return self._pos[w]

    def find_window(self, quad):
        """[(word_index)] where the 4-word quad matches consecutively."""
        wl = self.words
        n = len(wl)
        out = []
        for i in self.positions(quad[0]):
            if (i + 3 < n and wl[i + 1] == quad[1]
                    and wl[i + 2] == quad[2] and wl[i + 3] == quad[3]):
                out.append(i)
        return out

    def bytes_at(self, start, size):
        off = start - BASE_VA + HDR
        if off < HDR or off + size > len(self.buf):
            return None
        return self.buf[off:off + size]


def word_eq(img, start, body):
    """(#equal words, #compared) of body vs the image at start."""
    b = img.bytes_at(start, len(body))
    if b is None:
        return 0, max(1, len(body) // 4)
    n = len(body) // 4
    x = struct.unpack("<%dI" % n, body)
    y = struct.unpack_from("<%dI" % n, b)
    return sum(1 for a, c in zip(x, y) if a == c), n


class SymMap:
    """Sorted enclosing-symbol map for one target's walk rows."""

    def __init__(self, syms):
        self.rows = sorted(((va, va + size, name, typ)
                            for name, (va, size, typ) in syms.items()))

    def enclosing(self, va):
        for lo, hi, name, typ in self.rows:
            if lo <= va < hi:
                return name, typ
            if lo > va:
                break
        return None, None


def scan_member(src_t, name, va, size, body, imgs, symmaps):
    """[(tgt, start, class, enclosing_name, eq, n, nvotes)] for one body."""
    nw = size // 4
    step = 4 if size >= 0x100 else 1
    minwin = MINWIN_BIG if size >= 0x100 else MINWIN_SMALL
    found = {}
    for tgt, img in imgs.items():
        votes = {}
        for woff in range(0, nw - 3, step):
            quad = struct.unpack_from("<4I", body, woff * 4)
            if 0 in quad:
                continue
            for h in img.find_window(quad):
                s = BASE_VA + h * 4 - woff * 4
                votes.setdefault(s, set()).add(woff)
        for s, wset in votes.items():
            if len(wset) < minwin:
                continue
            encl, typ = symmaps[tgt].enclosing(s)
            if encl == name and is_matched(tgt, name, s):
                cls = "known"
            elif typ == 2:
                cls = "sibling-asm" if encl == name else "func-row"
            elif typ == 1:
                cls = "DATA-ROW"
            else:
                cls = "uncarved"
            eq, n = word_eq(img, s, body)
            if cls != "known" and eq < n * MIN_EQ:
                continue
            key = (tgt, s)
            prev = found.get(key)
            if prev is None or better_eq(eq, n, prev[4], prev[5]):
                found[key] = (tgt, s, cls, encl or "-", eq, n, len(wset))
    return list(found.values())


def dedupe_best(rows):
    """One row per (tgt, start) key: keep the best-eq row.
    row = (src_t, name, size, tgt, start, cls, encl, eq, n, votes)"""
    best = {}
    for r in rows:
        key = (r[3], r[4])
        prev = best.get(key)
        if prev is None or better_eq(r[7], r[8], prev[7], prev[8]):
            best[key] = r
    return list(best.values())


def main():
    want = sys.argv[1:] or TARGETS
    imgs, symmaps, funcs, refused = {}, {}, {}, []
    for t in want:
        ok, problems = input_gates(t)
        if not ok:
            refused.append(t)
            print(f"{t}: REFUSED - {'; '.join(problems)}")
            continue
        imgs[t] = TargetImage(t)
        syms = elf_syms(os.path.join(REPO, f"build/{t}.elf"))
        symmaps[t] = SymMap(syms)
        funcs[t] = elf_funcs(os.path.join(REPO, f"build/{t}.elf"))
    if not imgs:
        print("invariant_census: every requested target refused")
        return 2

    rows = []
    sanity = 0
    for src_t in imgs:
        for name, (va, size) in sorted(funcs[src_t].items()):
            if size < MIN_BODY or not is_matched(src_t, name, va):
                continue
            body = baseline_bytes(src_t, va, size)
            if body is None:
                continue
            for hit in scan_member(src_t, name, va, size, body, imgs,
                                   symmaps):
                if hit[2] == "known":
                    sanity += 1
                    continue
                rows.append((src_t, name, size) + hit)

    # dedupe (tgt, start) surfacing under several members: keep best eq
    rows = sorted(dedupe_best(rows),
                  key=lambda r: (r[5] != "DATA-ROW", r[5] != "uncarved",
                                 -r[7] / max(1, r[8]), r[3], r[4]))

    order = {"DATA-ROW": 0, "uncarved": 1, "func-row": 2, "sibling-asm": 3}
    counts = {}
    for r in rows:
        counts[r[5]] = counts.get(r[5], 0) + 1

    lines = []
    lines.append("== invariant census: landed bodies vs all %d targets' "
                 "FUNC+OBJECT maps ==" % len(imgs))
    lines.append("known-copy sanity hits (instrument self-check): %d"
                 % sanity)
    lines.append("candidates: %s" % ", ".join(
        "%s %d" % (k, counts[k]) for k in sorted(counts, key=lambda
                                                 k: order.get(k, 9))))
    lines.append("")
    for r in rows:
        lines.append(
            "%-12s %08X %-12s | src %-12s %-22s size 0x%-5X "
            "word-eq %3d/%-3d votes %d"
            % (r[5], r[4], r[3], r[0], r[1], r[2], r[7], r[8], r[9]))
    out_path = os.path.join(REPO, "build/invariant_census.txt")
    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines[:24]))
    if len(lines) > 24:
        print("... %d more rows -> %s" % (len(lines) - 24, out_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())

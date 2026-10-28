#!/usr/bin/env python3
"""gmd_launch_audit.py - complete the GsMapModelingData multi-target launch map
offline (matching lane; oracle-independent).

Banked context (Log cron-20261028-0118 NEXT): the g3org_jp leader gmd_v14.c is
BYTE-EXACT offline; the return-window landing is the one-line yaml flip on
g3org_jp plus "the 4-row flip (g3_jp/g3org_eu byte-identical twins +
mainmenu_jp/mainmenu_eu - re-check the mainmenu two against the standalone-row
finding before flipping)".  This tool closes the remaining map questions
WITHOUT the oracle:

  1. which targets carry the 0x78 body as a committed nonmatching listing
     (spimdisasm names it GsMapModelingData out of the symbol map);
  2. are the six listings WORD-IDENTICAL to the g3org_jp reference (the
     encoding column of the committed .s - relative branch offsets make
     identical layouts produce identical words, so a word match is a
     byte match);
  3. per target, the exact yaml row (offset/type/name), whether it is
     STANDALONE (the one-line-flip class) or inside a giant row (surgery
     class), the row extent, and the true VA under the corrected law
     VA = yaml_off + 0x8001F800 (Log cron-20261027-2248);
  4. do the boots (slps_00270, sces_00269) carry an UNNAMED copy anywhere in
     their committed asm (fingerprint scan over every listing's word column).

Usage: python3 scripts/bm_unit_decode/gmd_launch_audit.py
Exit 0 always (audit tool); findings print as the banked table.
"""
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REF_S = "asm/g3org_jp/nonmatchings/func_80053528.s"
TARGETS = ["slps_00270", "sces_00269", "mainmenu_jp", "mainmenu_eu",
           "g3_jp", "g3_eu", "g3org_jp", "g3org_eu"]
GAMED_MODULES = ["mainmenu_jp", "mainmenu_eu", "g3_jp", "g3_eu",
                 "g3org_jp", "g3org_eu"]
VA_BASE = 0x8001F800  # corrected law: true VA = yaml_off + 0x8001F800

# every /* OFF VA WORD */ comment's third field
_WORD = re.compile(r"/\*\s+[0-9A-Fa-f]+\s+[0-9A-Fa-f]+\s+([0-9A-Fa-f]{8})\s*\*/")


def words_of(path):
    out = []
    with open(path, "r", errors="replace") as fh:
        for line in fh:
            m = _WORD.search(line)
            if m:
                out.append(m.group(1).upper())
    return out


def ref_words():
    return words_of(os.path.join(REPO, REF_S))


def find_named_copies():
    """Listing files whose spimdisasm header names GsMapModelingData."""
    hits = []
    for t in TARGETS:
        d = os.path.join(REPO, "asm", t)
        for root, _dirs, files in os.walk(d):
            for fn in files:
                if not fn.endswith(".s"):
                    continue
                p = os.path.join(root, fn)
                try:
                    with open(p, "r", errors="replace") as fh:
                        txt = fh.read()
                except OSError:
                    continue
                if re.search(r"nonmatching\s+GsMapModelingData,\s*0x78", txt):
                    hits.append((t, os.path.relpath(p, REPO)))
    return hits


def yaml_row_for(target, asm_rel):
    """The config/splat.<t>.yaml row that names this listing's basename."""
    base = os.path.basename(asm_rel)[:-2]  # strip .s
    yml = os.path.join(REPO, "config", "splat.%s.yaml" % target)
    with open(yml, "r", errors="replace") as fh:
        for ln, line in enumerate(fh, 1):
            if re.search(r",\s*%s\s*\]" % re.escape(base), line):
                st = line.strip()
                return ln, st
    return None, None


def parse_row(line):
    """[off, type, name] + extent comment -> (off, type, name, extent)."""
    m = re.search(r"\[\s*(0x[0-9A-Fa-f]+)\s*,\s*(\w+)\s*,\s*([^\]]+)\]\s*(.*)$",
                  line.strip())
    if not m:
        return None
    ext = re.search(r"#\s*(0x[0-9A-Fa-f]+)", m.group(4))
    return (int(m.group(1), 16), m.group(2), m.group(3).strip(),
            int(ext.group(1), 16) if ext else None)


def main():
    ref = ref_words()
    print("reference: %s  (%d words / 0x%x bytes)" % (REF_S, len(ref),
                                                      len(ref) * 4))
    named = find_named_copies()
    print("\n== named 0x78 listings (spimdisasm symbol-map names) ==")
    for t, p in sorted(named):
        w = words_of(os.path.join(REPO, p))
        diff = sum(1 for a, b in zip(w, ref) if a != b) if len(w) == len(ref) else -1
        ln, row = yaml_row_for(t, p)
        if row:
            off, typ, name, ext = parse_row(row)
            va = off + VA_BASE
            shape = "STANDALONE" if ext == 0x78 else "NON-0x78(ext=%s)" % (
                hex(ext) if ext else "?")
            print("%-12s %s  words=%d worddiff_vs_ref=%d" % (t, p, len(w), diff))
            print("             yaml L%s: %s" % (ln, row))
            print("             off=%s type=%s name=%s ext=%s VA=%08X  %s" % (
                hex(off), typ, name, hex(ext) if ext else "?", va, shape))
        else:
            print("%-12s %s  words=%d worddiff_vs_ref=%d  YAML ROW NOT FOUND"
                  % (t, p, len(w), diff))

    # boots fingerprint scan: every listing's word column, sliding 30-window
    fp = ref[:6] + ref[-4:]  # head+tail fingerprint
    print("\n== boots fingerprint scan (any 30-word window equal to ref) ==")
    any_hit = False
    for t in ["slps_00270", "sces_00269"]:
        d = os.path.join(REPO, "asm", t)
        for root, _dirs, files in os.walk(d):
            for fn in sorted(files):
                if not fn.endswith(".s"):
                    continue
                p = os.path.join(root, fn)
                w = words_of(p)
                for i in range(0, max(0, len(w) - len(ref) + 1)):
                    if w[i:i + len(ref)] == ref:
                        print("%s: EXACT COPY at %s window %d" % (t, p, i))
                        any_hit = True
                        break
                # looser: head+tail fingerprint only
                if not any(w[i:i + len(ref)] == ref
                           for i in range(0, max(0, len(w) - len(ref) + 1))):
                    joined = ",".join(w)
                    if ",".join(fp) in joined:
                        print("%s: PARTIAL (head/tail fp) at %s" % (t, p))
                        any_hit = True
        if not any_hit:
            print("%s: no copy found in committed asm" % t)


if __name__ == "__main__":
    sys.exit(main())

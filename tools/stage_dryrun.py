#!/usr/bin/env python3
"""stage_dryrun.py - offline validator for staged data-row split recipes.

The staged-landing workflow banks first-shot recipes (docs/TASKS.md) while
the oracle is down; the landing itself waits for a witnessed oracle window.
The recipe line anchors drift when upstream moves the tree, and the dry-run
script that validated them originally lived in the (wiped) agent workspace.
This tool rebuilds that validation IN-REPO so any window can re-prove a
staged recipe against the current tree in seconds, offline.

What it checks per recipe (pure text - reads no baseline, no build tree):
  * the source .data.s exists with the spimdisasm header shape;
  * every word line obeys the yaml-offset law (VA = file_off + 0x8001F800,
    word == byte-swapped encoding column) - corruption catches here;
  * each planned piece (c row / gap row / tail row) covers exactly its
    extent, is word-contiguous, starts/ends at the claimed yaml offsets,
    and the pieces tile the covering row with no gap or overlap;
  * the boundary words (last head word, first/last c words, first tail
    word) carry the recipe's expected encodings - the landed-class
    signatures (e.g. GsInitCoord2param's 0x34021000..0xAC800018 schedule);
  * the simulated head extract balances dlabel/enddlabel (appending the
    walk enddlabel where the recipe says so) and the simulated tail
    extract contains no c/gap words and no orphan enddlabel;
  * the yaml covering row exists with the claimed extent comment and the
    insert arithmetic closes (piece extents sum to the row extent);
  * the walk labels' spellings agree with their content VAs (the name-VA
    law for func_ labels) and the c member sits at the staged block-rel;
  * the reference inventory still holds: each externally-referenced label
    has its recipe-stated number of textual references outside the source
    file (jal sites / rowdef mentions), and for a retiring block the jal
    sites to rename are all present at the staged count.

Usage: python3 tools/stage_dryrun.py [recipe ...]   (default: all)
Output: per-check [ok]/[FAIL] lines + final verdict per recipe.
Exit: 0 all recipes pass; 1 any failure; 2 unknown recipe name.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASE_VA = 0x8001F800   # yaml offset -> retail VA (the pair_report law)

WORD_RE = re.compile(
    r"^\s*/\*\s*([0-9A-Fa-f]+)\s+([0-9A-Fa-f]{8})\s+([0-9A-Fa-f]{8})\s*\*/"
    r"\s*\.word\s+0x([0-9A-Fa-f]{8})\s*$")
LABEL_RE = re.compile(r"^(dlabel|enddlabel|nonmatching|glabel)\s+(\S+)\s*$")
YAML_ROW_RE = re.compile(
    r"^\s*-\s*\[\s*(0x[0-9A-Fa-f]+)\s*,\s*([a-z0-9_]+)\s*,\s*([A-Za-z0-9_.]+)"
    r"\s*\]\s*#\s*(0x[0-9A-Fa-f]+)")

# ---------------------------------------------------------------------------
# Recipes. Line anchors are 1-based and were pinned at HEAD 6f7ae8d4; every
# check re-derives the geometry independently so a drifted anchor surfaces
# as a concrete failure instead of a silent wrong cut.
# Piece dict: kind (head/c/gap/tail), label (yaml row name), yaml, extent,
# first/last = source line span of the piece's WORD lines (head spans the
# whole file prefix), tail_ranges = the sed ranges that build the tail row.
# ---------------------------------------------------------------------------

RECIPES = {
    # The table carries STAGED (not-yet-executed) recipes only; executed
    # entries retire in the window that lands them (the default suite must
    # stay green - a permanently-red validator is useless). Retired on
    # execution: gsinit-g3org_jp / gsinit-mainmenu_jp / readsz4-mainmenu_jp
    # (landed GREEN first shot, 1b127649 + d366138c), normcolor3-g3_jp /
    # normdpq3-g3_jp (c259ba64), rotpers4-g3org_eu (5c8b9fd7),
    # rotnclipdpq3-g3org_jp (the first c_retire landing: the c head
    # swallowed func_800587F0 + func_80058858's first 24 words, tail
    # data_800588B8 re-homed verbatim past the skipped orphan enddlabel),
    # rotnclip4-g3org_jp (the first ABSORB landing: the 0xB0 body
    # flush-covered five woven rows summing exactly to it - the C-SPILL
    # class proven), rotnclipcol3-mainmenu_jp (the second ABSORB landing:
    # the 0xD0 row span - fn 0xc8 + 8 ld-zero-fill pad bytes, the pad
    # law inside the validator - flush-covered three woven rows),
    # rotpers3-mainmenu_eu (the third ABSORB landing: the first .rowdef
    # absorption - the dotted-label regex widening, the rowdef's live
    # glabel retires with zero consumers, the woven plain name's jal
    # collision survivor untouched), colordpq-mainmenu_eu (the fourth:
    # the C-SPILL wave drains 4/4).
    # The head-split class fields walk_label=None / orphan_line=None
    # remain legal (no walk block; the whole source file retires; woven
    # row names LIE - the label-vs-VA law).
    #
    # The ABSORB class ("class": "absorb") is the C-SPILL recipe: the
    # matched C body is LONGER than its covering woven row, so the c row
    # replaces a contiguous RUN of yaml rows whose extents sum exactly to
    # the body. No cutting, no re-homing - the whole absorbed span retires
    # (the census proves the bytes dw=0 eq N/N against the landed source;
    # the build + verify arbitrate the landing itself). Checks re-derive
    # the yaml geometry: per-row type/extent/abutment, tiling sum, flush
    # end at the next row, the c name not yet landed, and the per-label
    # reference inventory (absorbed labels must have no LIVE consumers -
    # self-refs inside a retiree's own nonmatchings file are pinned, any
    # external consumer changes the count and fails).
    # NOTE the pad law: the census's fn size (0xc8 here) can be SMALLER
    # than the landed row extent (0xd0, the source twin's span) - the
    # trailing pad words are ld zero fill, the c_extent field tracks the
    # ROW span (absorbed sum), the build + verify arbitrate the fill.
    # Retired on execution: lenparam-g3_eu / lenparam-g3org_eu /
    # lenparam-mainmenu_eu (landed GREEN first shot x3 - the
    # source-mapping answer's first wave; see git history for the
    # recipe bodies, pinned at HEAD 5e6709a7).
    #
    # The len_param x3 wave (docs/TASKS.md, cron-20261023-1517 next-window
    # (a), unblocked by the SOURCE-MAPPING ANSWER of cron-20261024-0503:
    # build.sh compiles src/<row>.c only for targets whose yaml lists the
    # row, and none of g3_eu/g3org_eu/mainmenu_eu carries a len_param
    # definer (the MATRIX3 units func_80036DCC/func_8005436C/func_8006EA84
    # compile only in slps_00270/g3org_jp/mainmenu_jp) - a new
    # src/len_param.c collides with nothing. memclr stays PARKED: every
    # target already carries exactly one memclr definer row (the LIBETC
    # intr.c curated unit), so a new src/memclr.c would be a second
    # definition per target - a lane decision, not a recipe. The cut is
    # c-at-row-end single-cut (head 0x580 + c 0x1C, no tail) inside
    # scan-era true-position files, so the walk label is the file's own
    # dlabel (name-VA true) and the c row takes the last 7 words
    # (0x18800004..0x00000000, the blez-guarded bit-length leaf). refs=6
    # = the three slps-space MATRIX3 definer files' two textual mentions
    # each; zero in the target subtrees. Line anchors pinned at HEAD
    # 5e6709a7.
}


def parse_source(path: Path):
    """Return (lines, words, labels). words = (lineno, file_off, va, word)."""
    lines = path.read_text().splitlines()
    words, labels = [], []
    for i, text in enumerate(lines, start=1):
        m = WORD_RE.match(text)
        if m:
            off = int(m.group(1), 16)
            va = int(m.group(2), 16)
            enc = bytes.fromhex(m.group(3))
            word = int(m.group(4), 16)
            words.append((i, off, va, enc, word))
            continue
        m = LABEL_RE.match(text)
        if m:
            labels.append((i, m.group(1), m.group(2)))
    return lines, words, labels


def byteswap(word: int) -> bytes:
    return word.to_bytes(4, "big")[::-1]


class Checker:
    def __init__(self, name: str):
        self.name = name
        self.fails = 0

    def check(self, label: str, ok: bool, detail: str = "") -> bool:
        if ok:
            print(f"  [ok]   {label}")
        else:
            self.fails += 1
            print(f"  [FAIL] {label}{': ' + detail if detail else ''}")
        return ok


def words_in_range(words, first, last):
    return [w for w in words if first <= w[0] <= last]


def run_recipe(name: str, r: dict) -> int:
    print(f"recipe {name} (target {r['target']})")
    ck = Checker(name)
    src = REPO / r["src"]

    # 1. source present
    if not ck.check("src-exists", src.is_file(), str(r["src"])):
        return 1
    lines, words, labels = parse_source(src)

    # 2. header shape
    ok = (len(lines) >= 7
          and lines[0].startswith('.include "macro.inc"')
          and lines[2].startswith(".section .data")
          and "Generated by spimdisasm" in lines[4]
          and lines[6].startswith("nonmatching"))
    ck.check("header-shape", ok)

    # 3. parse coverage: the file must be fully understood
    n_word_lines = sum(1 for t in lines if t.strip().startswith("/* ") and ".word" in t)
    ck.check("parse-coverage", len(words) == n_word_lines and len(words) > 0,
             f"{len(words)}/{n_word_lines} word lines parsed")

    # 4. VA + encoding law on every word line
    bad = [w for w in words
           if w[2] != w[1] + BASE_VA or bytes.fromhex(w[3].hex()) != byteswap(w[4])]
    ck.check("va-law", not bad,
             f"{len(bad)} offending lines" if bad else
             f"{len(words)} words, VA = file_off + 0x{BASE_VA:X} holds")

    by_line = {w[0]: w for w in words}

    # 5/6. per-piece geometry: word count, contiguity, yaml anchors
    for p in r["pieces"]:
        if p["kind"] == "tail":
            span_words = []
            for a, b in p["tail_ranges"]:
                span_words += words_in_range(words, a, b if b else len(lines))
        else:
            span_words = words_in_range(words, p["first"], p["last"])
        want = p["extent"] // 4
        ck.check(f"piece {p['label']} word-count",
                 len(span_words) == want,
                 f"{len(span_words)} != {want}")
        offs = [w[1] for w in span_words]
        contiguous = all(offs[i + 1] - offs[i] == 4 for i in range(len(offs) - 1))
        ck.check(f"piece {p['label']} contiguity", contiguous)
        if offs:
            ck.check(f"piece {p['label']} start-offset",
                     offs[0] == p["yaml"], f"0x{offs[0]:X} != 0x{p['yaml']:X}")
            ck.check(f"piece {p['label']} end-offset",
                     offs[-1] == p["yaml"] + p["extent"] - 4,
                     f"0x{offs[-1]:X} != 0x{p['yaml'] + p['extent'] - 4:X}")
        if p["kind"] in ("c", "gap"):
            labels_inside = [l for l in labels if p["first"] <= l[0] <= p["last"]]
            retire = r.get("c_retire") if p["kind"] == "c" else None
            if retire:
                # The c head swallows complete spimdisasm blocks whose
                # dlabel/enddlabel pairs CROSS the word span (the dlabel of
                # the first block opens before the span's first word, the
                # last block's enddlabel closes after its last word). The
                # whole source file retires, so the labels are fictional -
                # but the recipe must attest exactly which names the c row
                # consumes: names_inside == c_retire, and every retiree is
                # a proper single dlabel/enddlabel pair in the full file.
                names_inside = sorted({l[2] for l in labels_inside})
                expected = sorted(retire)
                ck.check(f"piece {p['label']} retire-labels",
                         names_inside == expected,
                         f"{names_inside} != {expected}")
                for nm in expected:
                    d_all = [l for l in labels
                             if l[1] == "dlabel" and l[2] == nm]
                    e_all = [l for l in labels
                             if l[1] == "enddlabel" and l[2] == nm]
                    ck.check(f"piece {p['label']} retire {nm} file-pair",
                             len(d_all) == 1 and len(e_all) == 1,
                             f"{len(d_all)} dlabel / {len(e_all)} enddlabel")
            else:
                ck.check(f"piece {p['label']} label-free", not labels_inside,
                         str(labels_inside[:3]))

    # 7. tiling: head + pieces == row, pieces abut
    total = r["head_extent"] + sum(p["extent"] for p in r["pieces"])
    ck.check("tiling-sum", total == r["row_extent"],
             f"0x{total:X} != 0x{r['row_extent']:X}")
    edge = r["row_yaml"] + r["head_extent"]
    for p in r["pieces"]:
        ck.check(f"tiling-abut {p['label']}", p["yaml"] == edge,
                 f"0x{p['yaml']:X} != 0x{edge:X}")
        edge += p["extent"]
    ck.check("tiling-row-end", edge == r["row_yaml"] + r["row_extent"],
             f"0x{edge:X} != 0x{r['row_yaml'] + r['row_extent']:X}")

    # 8. boundary words
    for lineno, want in sorted(r["boundary"].items()):
        w = by_line.get(lineno)
        ck.check(f"boundary line {lineno}",
                 w is not None and w[4] == want,
                 "" if w is None else f"0x{w[4]:08X} != 0x{want:08X}")

    # 9. simulated head extract
    head_words = words_in_range(words, 1, r["head_last"])
    ck.check("head word-count", len(head_words) == r["head_extent"] // 4,
             f"{len(head_words)} != {r['head_extent'] // 4}")
    head_labels = [l for l in labels if l[0] <= r["head_last"]]
    d = sum(1 for l in head_labels if l[1] == "dlabel")
    e = sum(1 for l in head_labels if l[1] == "enddlabel")
    if r["append_enddlabel"]:
        e += 1  # the recipe appends the walk enddlabel at head end
        ck.check("head walk-dlabel-open",
                 any(l[1] == "dlabel" and l[2] == r["walk_label"]
                     for l in head_labels) and e == d)
    else:
        ck.check("head labels-balanced-in-place", d == e, f"{d} dlabel / {e} enddlabel")

    # 10. simulated tail extract
    tail_specs = [p for p in r["pieces"] if p["kind"] == "tail"]
    for p in tail_specs:
        span_words = []
        for a, b in p["tail_ranges"]:
            span_words += words_in_range(words, a, b if b else len(lines))
        ck.check(f"tail {p['label']} word-count",
                 len(span_words) == p["extent"] // 4,
                 f"{len(span_words)} != {p['extent'] // 4}")
        c_gaps = {q["yaml"] + k for q in r["pieces"]
                  if q["kind"] in ("c", "gap")
                  for k in range(0, q["extent"], 4)}
        leaked = [w for w in span_words if w[1] in c_gaps]
        ck.check(f"tail {p['label']} no-c/gap-leak", not leaked,
                 f"{len(leaked)} leaked words" if leaked else "")
        tail_labels = [l for l in labels if any(a <= l[0] and (b is None or l[0] <= b)
                                                for a, b in p["tail_ranges"])]
        d = sum(1 for l in tail_labels if l[1] == "dlabel")
        e = sum(1 for l in tail_labels if l[1] == "enddlabel")
        ck.check(f"tail {p['label']} labels-balanced", d == e,
                 f"{d} dlabel / {e} enddlabel")

    # 11. orphan enddlabel (skipped when the whole file retires:
    # head-split class, orphan_line=None)
    if r.get("orphan_line") is not None:
        orphan = lines[r["orphan_line"] - 1].strip() if r["orphan_line"] <= len(lines) else ""
        ck.check("orphan-line", orphan == r["orphan_text"],
                 f"{orphan!r} != {r['orphan_text']!r}")

    # 12. yaml covering row + next-row extent proof
    ytext = (REPO / r["yaml"]).read_text().splitlines()
    row_re = None
    next_row = None
    for t in ytext:
        m = YAML_ROW_RE.match(t)
        if not m:
            continue
        off = int(m.group(1), 16)
        if row_re is not None and next_row is None:
            next_row = off, m.group(2), m.group(3)
        if (off == r["row_yaml"] and m.group(3) == r["row_label"]):
            row_re = m
    ck.check("yaml-row-present", row_re is not None)
    if row_re is not None:
        ck.check("yaml-row-extent",
                 int(row_re.group(4), 16) == r["row_extent"],
                 f"0x{int(row_re.group(4), 16):X} != 0x{r['row_extent']:X}")
    if next_row:
        ck.check("yaml-next-row-abuts",
                 next_row[0] == r["row_yaml"] + r["row_extent"],
                 f"next row 0x{next_row[0]:X} != 0x{r['row_yaml'] + r['row_extent']:X}")

    # 13. yaml insert arithmetic + landed-name collision
    for p in r["pieces"]:
        line = f"- [0x{p['yaml']:X}, {p['kind']}, {p['label']}]   # 0x{p['extent']:x}"
        if p["kind"] == "c":
            dup = [t for t in ytext
                   if YAML_ROW_RE.match(t) and YAML_ROW_RE.match(t).group(3) == p["label"]]
            ck.check(f"yaml-insert {p['label']} not-yet-landed", not dup,
                     dup[0].strip() if dup else "")
        else:
            ck.check(f"yaml-insert {p['label']} shape-ok",
                     line.endswith(f"# 0x{p['extent']:x}"))

    # 14. name-VA law on walk + tail dlabels; walk member sits at walk_rel
    # (both skipped when walk_label=None: the head-split class has no walk
    # block, and the woven row names LIE by design - label-vs-VA law)
    def label_first_word(label):
        for i, l in enumerate(labels):
            if l[1] == "dlabel" and l[2] == label:
                nxt = [w for w in words if w[0] > l[0]]
                return nxt[0] if nxt else None
        return None

    walk = r.get("walk_label")
    for lbl in ([walk] if walk else []) + [p.get("keep") for p in r["pieces"] if p.get("keep")]:
        w = label_first_word(lbl)
        if not ck.check(f"name-VA {lbl}", w is not None):
            continue
        name_va = int(lbl.split("_")[1], 16)
        ck.check(f"name-VA {lbl} agrees", w[2] == name_va,
                 f"content VA 0x{w[2]:X} != name 0x{name_va:X}")
    if walk:
        walk_first = label_first_word(walk)
        member_yaml = r["pieces"][0]["yaml"]
        ck.check("walk-member-rel",
                 walk_first is not None
                 and member_yaml == walk_first[1] + r["walk_rel"],
                 f"0x{member_yaml:X} != walk+0x{r['walk_rel']:X}")

    # 15. reference inventory outside the source file.
    # Scoped to the recipe's target subtree: label names collide across
    # targets (each target has its own 0x800xxxxx namespace), so a global
    # count reads other targets' same-named labels.
    for lbl, expect in sorted(r["refs"].items()):
        pat = re.compile(r"\b" + re.escape(lbl) + r"\b")
        count = 0
        files = set()
        bases = [REPO / "asm" / r["target"], REPO / "src", REPO / "include"]
        for base in bases:
            for p in base.rglob("*") if base.is_dir() else []:
                if not p.is_file() or p == src:
                    continue
                try:
                    text = p.read_text(errors="replace")
                except OSError:
                    continue
                hits = pat.findall(text)
                if hits:
                    count += len(hits)
                    files.add(str(p.relative_to(REPO)))
        ck.check(f"refs {lbl} == {expect}", count == expect,
                 f"{count} refs in {sorted(files)[:3]}")

    # 16. rename inventory (retiring block; same per-target scoping)
    for retiree, new_name in r.get("rename", {}).items():
        jal_re = re.compile(r"jal\s+" + re.escape(retiree) + r"\b")
        sites = []
        for p in (REPO / "asm" / r["target"]).rglob("*.s"):
            if p == src:
                continue
            for i, t in enumerate(p.read_text(errors="replace").splitlines(), 1):
                if jal_re.search(t):
                    sites.append((str(p.relative_to(REPO)), i))
        ck.check(f"rename {retiree} jal-sites == {len(r['refs']) and r['refs'][retiree]}",
                 len(sites) == r["refs"][retiree],
                 f"{len(sites)} sites")
        ck.check(f"rename target {new_name} not-yet-used-here",
                 not [t for t in ytext
                      if re.search(r"\b" + re.escape(new_name) + r"\b", t)
                      and "c," in t])

    verdict = "ALL CHECKS PASS" if ck.fails == 0 else f"{ck.fails} FAILURE(S)"
    print(f"== {name}: {verdict} ==")
    return 0 if ck.fails == 0 else 1


def run_absorb_recipe(name: str, r: dict) -> int:
    """The C-SPILL absorb-next-row class: a matched C row replaces a
    contiguous run of yaml rows whose extents sum exactly to the body.
    No cutting, no re-homing - the whole absorbed span retires (the census
    proves the bytes dw=0 eq N/N against the landed source; build + verify
    arbitrate the landing). Every check re-derives the geometry from the
    yaml itself so a drifted anchor surfaces as a concrete failure."""
    print(f"recipe {name} (target {r['target']}) [absorb class]")
    ck = Checker(name)
    src = REPO / r["src"]

    # 1. source present
    if not ck.check("src-exists", src.is_file(), str(r["src"])):
        return 1

    # 2. parse the yaml once, index rows by offset (file order = offset order)
    ytext = (REPO / r["yaml"]).read_text().splitlines()
    rows = {}
    order = []
    for t in ytext:
        m = YAML_ROW_RE.match(t)
        if m:
            off = int(m.group(1), 16)
            rows[off] = (m.group(2), m.group(3), int(m.group(4), 16))
            order.append(off)
    by_label = {rows[off][1]: off for off in order}

    # 3. each absorbed row: present, right type, right extent, abutting
    edge = None
    for lbl, typ, ext in r["absorb"]:
        off = by_label.get(lbl)
        if not ck.check(f"absorb {lbl} present", off is not None):
            continue
        ck.check(f"absorb {lbl} type", rows[off][0] == typ,
                 f"{rows[off][0]} != {typ}")
        ck.check(f"absorb {lbl} extent", rows[off][2] == ext,
                 f"0x{rows[off][2]:X} != 0x{ext:X}")
        if edge is not None:
            ck.check(f"absorb {lbl} abuts", off == edge,
                     f"0x{off:X} != 0x{edge:X}")
        edge = off + rows[off][2]
    if edge is None:
        print(f"== {name}: 1 FAILURE(S) ==")
        return 1

    # 4. tiling: first absorbed offset == c yaml, extent sum == c extent
    start = edge - sum(ext for _, _, ext in r["absorb"])
    ck.check("c-start", start == r["c_yaml"],
             f"0x{start:X} != 0x{r['c_yaml']:X}")
    total = sum(ext for _, _, ext in r["absorb"])
    ck.check("tiling-sum", total == r["c_extent"],
             f"0x{total:X} != 0x{r['c_extent']:X}")

    # 5. flush end: the next yaml row abuts the absorbed run's end
    nxt = [off for off in order if off >= edge]
    ck.check("next-row-abuts", bool(nxt) and nxt[0] == edge,
             "no next row" if not nxt else f"0x{nxt[0]:X} != 0x{edge:X}")

    # 6. c name not yet landed in this yaml
    dup = [t for t in ytext
           if YAML_ROW_RE.match(t) and YAML_ROW_RE.match(t).group(3) == r["c_name"]]
    ck.check("c not-yet-landed", not dup, dup[0].strip() if dup else "")

    # 7. reference inventory across the target subtree + src/include
    # (same scoping law as the head-split class: labels collide across
    # targets, so the count is per-target; absorbed labels must have no
    # LIVE consumers - the pinned counts cover each retiree's own
    # nonmatchings self-refs, any external consumer changes the count)
    for lbl, expect in sorted(r["refs"].items()):
        pat = re.compile(r"\b" + re.escape(lbl) + r"\b")
        count = 0
        files = set()
        bases = [REPO / "asm" / r["target"], REPO / "src", REPO / "include"]
        for base in bases:
            for p in base.rglob("*") if base.is_dir() else []:
                if not p.is_file():
                    continue
                try:
                    text = p.read_text(errors="replace")
                except OSError:
                    continue
                hits = pat.findall(text)
                if hits:
                    count += len(hits)
                    files.add(str(p.relative_to(REPO)))
        ck.check(f"refs {lbl} == {expect}", count == expect,
                 f"{count} refs in {sorted(files)[:3]}")

    verdict = "ALL CHECKS PASS" if ck.fails == 0 else f"{ck.fails} FAILURE(S)"
    print(f"== {name}: {verdict} ==")
    return 0 if ck.fails == 0 else 1


def main() -> int:
    names = sys.argv[1:] or list(RECIPES)
    unknown = [n for n in names if n not in RECIPES]
    if unknown:
        print(f"unknown recipe(s): {', '.join(unknown)}", file=sys.stderr)
        print(f"known: {', '.join(RECIPES)}", file=sys.stderr)
        return 2
    rc = 0
    for n in names:
        r = RECIPES[n]
        rc |= (run_absorb_recipe if r.get("class") == "absorb"
               else run_recipe)(n, r)
    return rc


if __name__ == "__main__":
    sys.exit(main())

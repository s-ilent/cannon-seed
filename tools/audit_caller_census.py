#!/usr/bin/env python3
"""audit_caller_census.py — the total static-reference census for a set of
code addresses in one carved module (read-only, exit 0).

Born from the R1 pass-18 correction (docs/research/
G3_MUSIC_LANE_CALLERS_20261125.md): pass 17's "empty caller census" was an
artifact of two grep gaps. This tool closes both, mechanically:

  1. INTRA-ROW REFERENCES COUNT. Splat rows are carve units, not functions;
     a chunk-to-chunk call inside one row file is a real reference. Only the
     glabel/nonmatching/endlabel declaration lines are definitions; every
     other occurrence of a target's name (jal/j, %hi/%lo, .word labels,
     comments) is reported.
  2. UN-SPLIT FUNCTIONS LIVE IN DATA ROWS. Every `.word 0x...` value in
     every row is also decoded as a MIPS op: op 2/3 = j/jal, so a data row's
     call map is visible. Raw pointer words, encoded j/jal words, raw
     lui/addiu-ori hi/lo materializations and adjacent .half pointer pairs
     are swept as well.

The sweep is TOTAL for a module whose yaml tiles its whole image (the
g3_jp/g3_eu/... configs do): every carved byte is inside some row and every
row file is scanned.

Usage:
  python3 tools/audit_caller_census.py                    # the music-lane set, g3_jp
  python3 tools/audit_caller_census.py --module g3_eu
  python3 tools/audit_caller_census.py --add myName=0x80012345

Exit 0 always (census discipline, like tools/audit_c_names.py).
"""
import argparse, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The R1 pass-18 music-lane caller set (g3_jp true-space VAs).
DEFAULT_TARGETS = {
    "func_800270E8": 0x800270E8,  # tick 2
    "func_800276B8": 0x800276B8,  # tick 1
    "func_80026B64": 0x80026B64,  # the initializer (scene-reset tail)
    "func_800299D8": 0x800299D8,  # the playlist scheduler (unreferenced)
    "func_8002FF48": 0x8002FF48,  # music tick driver 1
    "func_8002FFB8": 0x8002FFB8,  # music tick driver 2 (unreferenced)
    "func_8002FC68": 0x8002FC68,  # the frame function (main's callee)
    "func_8002343C": 0x8002343C,  # the tick-consumer orchestrator
    "func_800236F8": 0x800236F8,  # the tick-2 consumer function
    "func_80026718": 0x80026718,  # the tick-1 consumer (stride-12 records)
    "func_80026A80": 0x80026A80,  # the scene reset head
    "func_80042C6C": 0x80042C6C,  # the dispatcher body (main's callee)
    "func_80022FE4": 0x80022FE4,  # the scene update head
}

LABEL_RE = re.compile(r"glabel\s+(\S+)")
WORD_RE = re.compile(r"\.word\s+([^#\n]+)")
HALF_RE = re.compile(r"\.half\s+(-?0x[0-9A-Fa-f]+)")
LUI_RE = re.compile(r"lui\s+\$\w+,\s*(0x[0-9A-Fa-f]+|%hi\([^)]*\))")
IMM_RE = re.compile(r"(addiu|ori|li)\s+\$\w+,\s*(\$[a-z0-9]+,\s*)?(-?0x[0-9A-Fa-f]+)")
ENCWORD_RE = re.compile(r"/\* [0-9A-Fa-f]{4,5} ([0-9A-Fa-f]{8}) [0-9A-Fa-f]{8} \*/")


def encodings(addr):
    e = {}
    e["jal"] = 0x0C000000 | ((addr >> 2) & 0x03FFFFFF)
    e["j"] = 0x08000000 | ((addr >> 2) & 0x03FFFFFF)
    e["word"] = addr
    lo_u = addr & 0xFFFF
    hi = (addr >> 16) & 0xFFFF
    if lo_u & 0x8000:
        hi = (hi + 1) & 0xFFFF
    e["hi"] = hi
    e["lo_u"] = lo_u
    return e


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--module", default="g3_jp")
    ap.add_argument("--add", action="append", default=[],
                    help="extra target NAME=0xADDRESS")
    args = ap.parse_args()

    targets = dict(DEFAULT_TARGETS)
    for spec in args.add:
        name, _, val = spec.partition("=")
        targets[name.strip()] = int(val, 16)

    module = os.path.join(ROOT, "asm", args.module)
    if not os.path.isdir(module):
        print("audit_caller_census: no module dir %s" % module)
        return 0

    ENC = {n: encodings(a) for n, a in targets.items()}
    files = []
    for dp, _, fns in os.walk(module):
        for fn in fns:
            if fn.endswith(".s"):
                files.append(os.path.join(dp, fn))
    files.sort()

    sym_hits, raw_hits = [], []
    prev_half = {}
    for fp in files:
        rel = os.path.relpath(fp, ROOT)
        with open(fp, "r", errors="replace") as fh:
            lines = fh.readlines()
        for lineno, raw in enumerate(lines, 1):
            text = raw.rstrip("\n")
            for name in targets:
                if re.search(r"\b" + name + r"\b", text) and \
                   not re.match(r"\s*(glabel|endlabel|nonmatching)\s+" + name + r"\b", text):
                    sym_hits.append((name, rel, lineno, text.strip()))
            m = LUI_RE.search(text)
            if m and not m.group(1).startswith("%"):
                v = int(m.group(1), 16)
                for name, e in ENC.items():
                    if v == e["hi"]:
                        raw_hits.append(("lui-raw", name, rel, lineno, text.strip()))
            m = IMM_RE.search(text)
            if m:
                v = int(m.group(3), 16) & 0xFFFF
                for name, e in ENC.items():
                    if v == e["lo_u"]:
                        raw_hits.append(("lo-raw", name, rel, lineno, text.strip()))
            m = WORD_RE.search(text)
            if m:
                for tok in m.group(1).replace(",", " ").split():
                    if re.fullmatch(r"0x[0-9A-Fa-f]+", tok):
                        v = int(tok, 16)
                        for name, e in ENC.items():
                            if v == e["word"]:
                                raw_hits.append(("word-ptr", name, rel, lineno, text.strip()))
                            if v in (e["jal"], e["j"]):
                                raw_hits.append(("word-enc", name, rel, lineno, text.strip()))
            m = ENCWORD_RE.search(text)
            if m:
                v = int(m.group(1), 16)
                for name, e in ENC.items():
                    if v in (e["jal"], e["j"]):
                        raw_hits.append(("code-enc", name, rel, lineno, text.strip()))
            m = HALF_RE.search(text)
            if m:
                v = int(m.group(1), 16) & 0xFFFF
                if rel in prev_half:
                    pv = prev_half[rel]
                    for name, a in targets.items():
                        if pv == ((a >> 16) & 0xFFFF) and v == (a & 0xFFFF):
                            raw_hits.append(("half-pair", name, rel, lineno, text.strip()))
                prev_half[rel] = v

    print("=== audit_caller_census (read-only) ===")
    print("module: %s, files: %d, targets: %d" % (args.module, len(files), len(targets)))
    interesting = [h for h in raw_hits if h[0] not in ("lo-raw", "lui-raw")]
    by_name = {}
    for h in sym_hits:
        by_name.setdefault(h[0], []).append(h)
    for name in sorted(targets):
        refs = by_name.get(name, [])
        print("\n[%s @0x%08X] %d non-definition symrefs" % (name, targets[name], len(refs)))
        for h in refs[:40]:
            print("  %s:%d %s" % (h[1], h[2], h[3][:100]))
    print("\n-- pointer/encoded-word hits (word-ptr/word-enc/code-enc/half-pair) --")
    for h in interesting:
        print("  [%s/%s] %s:%d %s" % (h[0], h[1], h[2], h[3], h[4][:100]))
    if not interesting:
        print("  (none)")
    print("\n(lo-raw/lui-raw immediate noise: %d lines, suppressed)" %
          (len(raw_hits) - len(interesting)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

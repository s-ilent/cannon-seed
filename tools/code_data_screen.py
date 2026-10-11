#!/usr/bin/env python3
"""code_data_screen.py - flag code subsegments whose bytes look like data.

Read-only. Scores every `asm`/`c` subsegment in a target's splat layout by
cheap, decisive byte evidence so a mislabeled carve - a string pool or a
pointer table typed `asm` - stands out from real MIPS-I code:

  ASCII  longest printable-byte run >= 8, and >= 40% of the range text
  ZEROS  longest 0x00 run >= 12, and >= 40% of the range zero
  PTR    words in the payload's own vram window (self-referential data)
  OPS    plausible-MIPS1 fraction over non-zero words; real code is high
  END    final word is jr $ra / branch / break; real code terminates so

Any ASCII, ZEROS or PTR signal flags DATA outright, as does OPS <= 0.34
over >= 3 non-zero words (high-entropy blobs decode as nothing); weaker
evidence is SUSPECT; otherwise CODE. END only moves the score.

Ground truth: slps_00270's `asm` range at vram 0x80021800 holds the string
"CD_cachefile"; this tool flags it (str12).

Usage: python3 tools/code_data_screen.py [TARGET] [--json]
       python3 tools/code_data_screen.py --all
"""
import re
import struct
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASE = 0x80020000
HDR = 0x800
TARGETS = ("slps_00270", "sces_00269", "mainmenu_jp", "mainmenu_eu",
           "g3_jp", "g3_eu", "g3org_jp", "g3org_eu")

# MIPS-I primary opcodes GCC 2.6.3 emits; gaps are unassigned on MIPS-I.
VALID_OPS = frozenset(
    list(range(0x00, 0x14)) +      # SPECIAL..COP3
    list(range(0x20, 0x27)) +      # lb..lwr
    list(range(0x28, 0x2C)) +      # sb..sw
    list(range(0x30, 0x34)) +      # lwc0..lwc3
    list(range(0x38, 0x3C)))       # swc0..swc3
VALID_FUNCT = frozenset(
    list(range(0x00, 0x0E)) + [0x0F] + list(range(0x10, 0x14)) +
    [0x18, 0x19, 0x1A, 0x1B] + list(range(0x20, 0x28)) + [0x2A, 0x2B])
REGIMM_RT = frozenset([0x00, 0x01, 0x02, 0x03, 0x10, 0x11, 0x12, 0x13])
BRANCH_OPS = frozenset([0x01, 0x04, 0x05, 0x06, 0x07])
CODE_END = frozenset(["jr_ra", "teardown", "jr_r", "j/jal_end", "branch_end",
                      "break"])


def plausible(w):
    """True if the word decodes as a plausible MIPS-I instruction. Zero is
    excluded (nop is real code, but runs of it are the data signal)."""
    if w == 0:
        return False
    op = w >> 26
    if op == 0x00:
        return (w & 0x3F) in VALID_FUNCT
    if op == 0x01:
        return ((w >> 16) & 31) in REGIMM_RT
    return op in VALID_OPS


def ascii_run(data):
    """Longest run of printable bytes, counting 0x09/0x0a/0x0d as text so a
    string's newline does not split the run."""
    best = cur = 0
    for b in data:
        if 0x20 <= b <= 0x7E or b in (0x09, 0x0A, 0x0D):
            cur += 1
            if cur > best:
                best = cur
        else:
            cur = 0
    return best


def zero_run(data):
    best = cur = 0
    for b in data:
        if b == 0:
            cur += 1
            if cur > best:
                best = cur
        else:
            cur = 0
    return best


def end_shape(words):
    if not words:
        return "empty"
    last = words[-1]
    if last == 0x03E00008:
        return "jr_ra"
    op = last >> 26
    if op == 0x00 and (last & 0x3F) == 0x0D:
        return "break"
    if op in BRANCH_OPS:
        return "branch_end"
    if op in (0x02, 0x03):
        return "j/jal_end"
    if op == 0x00 and (last & 0x3F) == 0x08:
        return "jr_r"
    return "data_stop"


def screen(payload, off, size):
    """Score one subsegment. `off` is a payload offset (file offset - 0x800)."""
    data = payload[off:off + size]
    n = size // 4
    words = list(struct.unpack("<%dI" % n, data[:n * 4])) if n else []
    vb = BASE + off

    nzw = [w for w in words if w]
    opfrac = (sum(1 for w in nzw if plausible(w)) / len(nzw)) if nzw else 0.0
    ptrs = sum(1 for w in words if BASE <= w < BASE + len(payload))
    ptr_frac = ptrs / n if n else 0.0
    text_words = sum(1 for i in range(n)
                     if all(0x20 <= b <= 0x7E for b in data[i * 4:i * 4 + 4]))
    text_frac = text_words / n if n else 0.0
    zrun = zero_run(data)
    zero_frac = data.count(0) / len(data) if data else 0.0
    arun = ascii_run(data)
    end = end_shape(words)

    ev = []
    pts = 0
    decisive = False
    if arun >= 8 and text_frac >= 0.4:
        decisive = True
        pts += 50
        ev.append("str%d(%.0f%%)" % (arun, text_frac * 100))
    elif arun >= 16:
        decisive = True
        pts += 40
        ev.append("str%d" % arun)
    if zrun >= 12 and zero_frac >= 0.4:
        decisive = True
        pts += 40
        ev.append("zero%d(%.0f%%)" % (zrun, zero_frac * 100))
    elif zrun >= 24:
        decisive = True
        pts += 30
        ev.append("zero%d" % zrun)
    if ptrs >= 2 and ptr_frac >= 0.12:
        decisive = True
        pts += 50
        ev.append("ptr%d(%.0f%%)" % (ptrs, ptr_frac * 100))
    elif ptrs >= 1 and ptr_frac >= 0.25:
        pts += 20
        ev.append("ptr%d" % ptrs)
    if len(nzw) >= 3 and opfrac <= 0.34:
        decisive = True
        pts += 45
        ev.append("ops%.2f(%dw)" % (opfrac, len(nzw)))
    elif nzw and opfrac < 0.5:
        pts += 25
        ev.append("ops%.2f" % opfrac)
    elif nzw and opfrac < 0.75:
        pts += 10
        ev.append("ops%.2f" % opfrac)
    if end in CODE_END and words and plausible(words[-1]):
        pts -= 20
    else:
        ev.append("end=%s" % end)
    verdict = "DATA" if decisive else ("SUSPECT" if pts >= 25 else "CODE")
    return dict(s=vb, e=vb + size, size=size, words=n, verdict=verdict,
                score=max(0, min(100, pts)), ev=ev, end=end,
                opfrac=opfrac, ptrs=ptrs, arun=arun, zrun=zrun)


def load(target):
    blob = (REPO / "baselines" / ("%s.bin" % target)).read_bytes()
    payload = blob[HDR:]
    subs = []
    for ln in (REPO / "config" / ("splat.%s.yaml" % target)).read_text().splitlines():
        m = re.match(r"\s*-\s*\[(0x[0-9A-Fa-f]+),\s*(asm|c|data),\s*(\w+)\]"
                     r"\s*#\s*(0x[0-9A-Fa-f]+)", ln)
        if m:
            subs.append((int(m.group(1), 16) - HDR, m.group(2), m.group(3),
                         int(m.group(4), 16)))
    return payload, subs


def run(target):
    payload, subs = load(target)
    rows = []
    ncode = 0
    for off, typ, name, size in subs:
        if typ not in ("asm", "c"):
            continue
        ncode += 1
        r = screen(payload, off, size)
        r["name"] = name
        r["typ"] = typ
        rows.append(r)
    return ncode, rows


def main(argv):
    as_json = "--json" in argv
    all_t = "--all" in argv
    args = [a for a in argv[1:] if not a.startswith("--")]
    targets = list(TARGETS) if all_t else [args[0] if args else "slps_00270"]

    out = {}
    for t in targets:
        ncode, rows = run(t)
        flagged = [r for r in rows if r["verdict"] == "DATA"]
        suspect = [r for r in rows if r["verdict"] == "SUSPECT"]
        flagged.sort(key=lambda r: (-r["score"], -r["size"]))
        out[t] = dict(code=ncode, flagged=flagged, suspect=len(suspect))
        if as_json:
            continue
        print("== %s: %d asm/c subsegs, %d DATA, %d SUSPECT =="
              % (t, ncode, len(flagged), len(suspect)))
        for r in flagged:
            print("  DATA %#x-%#x %5dB score=%3d  %s"
                  % (r["s"], r["e"], r["size"], r["score"], " ".join(r["ev"])))
        if not flagged:
            print("  clean: no subsegment carries a data signal")
    if as_json:
        import json

        def ser(r):
            return dict(s=r["s"], e=r["e"], size=r["size"], typ=r["typ"],
                        name=r["name"], verdict=r["verdict"], score=r["score"],
                        end=r["end"], opfrac=round(r["opfrac"], 3),
                        ptrs=r["ptrs"], ascii_run=r["arun"],
                        zero_run=r["zrun"], ev=r["ev"])

        print(json.dumps({t: dict(code=v["code"],
                                  data=[ser(r) for r in v["flagged"]],
                                  suspect=v["suspect"])
                          for t, v in out.items()}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

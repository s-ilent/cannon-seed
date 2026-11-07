#!/usr/bin/env python3
"""Per-row decode census of mainmenu_jp's data rows (offline judge-prep).

The cron-202611072216 window proved mainmenu_jp's deep region holds REAL
psyq library code typed as `data` by the walk (the Witness-A carve-skew
mechanism caught outside mainmenu_eu): data_8006C4D4 decodes as the
LIBGPU prim-function region (GetTPage's body), data_8005E898 holds the
seven callback members (InterruptCallback / VSyncCallback dispatchers),
data_8006EAA0 SquareRoot0/SquareRoot12, data_8006F0F0 RotMatrixX/Y/Z_C,
data_8006FD54 IsIdMatrix, data_8005DB1C MulRotMatrix/MulRotMatrix0,
data_8005E1B8 ReadColorMatrix/ReadLightMatrix/ReadRotMatrix.  The
coordination-gated decision (framed oracle vs de-framed payload +
re-framing build) wants a per-row evidence table BEFORE any carve work.

This script produces that table.  It is READ-ONLY judge-prep: no yaml,
no listings, no carve changes.  For EVERY `data` row in the mainmenu_jp
yaml (deep region flagged, game region as the presumed-data control) it
reports:

  - word metrics decoded from the hardened baseline bytes with capstone
    (MIPS32 little-endian, the decode_84924_row.py convention): jal/j/jr
    $ra/branches (with backward count), sp-frame prologues (addiu
    $sp,$sp,-N), ra frame stores (sw $ra,N($sp)), GTE (COP2) and COP1
    words, pointer-shaped words (0x8xxxxxxx), zero words, odd words;
  - the census members (config/sdk_members.txt) whose linear VA lands
    inside the row, with the census's own reviewed markers per member
    line - "(sig-db agree)" (the tools/sdk_members.py cross_check verdict
    for the member's OBJ placement) and "adoptable"
  - a CODE-LIKE / MIXED / DATA-LIKE verdict from documented thresholds,
    calibrated on the 2216 window's proven-code rows (they MUST come out
    code-like).  The game region is NOT used as a presumed-data control:
    the first run already showed it holds coherent instruction streams
    too (eyeball-confirmed jal/delay call sequences at 0x80027800 and
    0x80031000) - that is a FINDING the report states, not noise.

Deep-region boundary: file off >= 0x3E31C (data_8005DB1C, the first of
the 2216-named library rows); rows below are the game region where the
walk's typing is believed sound.  Lane-owned surfaces (the setIntr/
startIntr/trapIntr trio, the GsTMDdiv/Fast family) are FLAGGED, never
counted as adoption candidates.

Run: /home/z/my-project/.venv/bin/python scripts/deep_region_decode_census.py
"""
import collections
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from tools.sdk_members import yaml_anchors  # noqa: E402

sys.path.insert(0, str(REPO / "scripts"))
from check_b_class_filter import LINEAR_BASE  # noqa: E402

from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN

TARGET = "mainmenu_jp"
DEEP_OFF = 0x3E31C          # data_8005DB1C - first 2216-named library row
CENSUS = REPO / "config" / "sdk_members.txt"
TARGET_HDR = re.compile(r"^// target: (\S+)")
MEMBER = re.compile(r"^//   0x([0-9a-f]{8}) +(\S+) +(\S+) +(\S+) +(\S+)")

# Calibration anchors: rows the 2216 window PROVED hold library code
# (decoded from the hardened baseline + census-unique).  Their verdicts
# gate the metric: any config where these read DATA-LIKE is wrong.
ANCHORS = {
    0x3E31C: "MulRotMatrix / MulRotMatrix0 (2216 decode)",
    0x3E9B8: "ReadColorMatrix / ReadLightMatrix / ReadRotMatrix (2216)",
    0x3F098: "seven callback members incl. InterruptCallback / VSyncCallback (2216)",
    0x42EE4: "LIBGPU prim-function region, GetTPage body (2216)",
    0x44FF0: "SquareRoot0 / SquareRoot12 (2216)",
    0x45510: "RotMatrixX / RotMatrixY / RotMatrixZ_C (2216)",
    0x46000: "IsIdMatrix (2216)",
}
# Owner-gated member names: shown but never counted as candidates
# (SsSetTableSize = psylib lane; SsSetTickMode + the SsInit/SsInitHot
# apply ride the func_8006AF70 row landing - Silent's call, per the
# cron-20261101-0507 decision brief).
GATED_RE = re.compile(r"^(SsSetTableSize|SsSetTickMode|SsInit|SsInitHot)$")

# Phantom-macro names (2216 residue class 1): LIBGTE/LIBGPU macros have
# no linked bodies - their census addresses are archive-walk placements,
# NOT body evidence.  Rows holding them stay listed (the bytes still
# decode code-like) but the annotation blocks over-reading the names.
PHANTOM_RE = re.compile(
    r"^(SetIR0|SetIR123|SetRGBfifo|SetSXSYfifo|SetData32|SetMAC123"
    r"|SetRii|SetDQA|SetDQB|SetGeomScreen|ReadRGBfifo|ReadSXSYfifo"
    r"|ReadGeomScreen|AddPrims?|SetPoly|SetSprt|SetTile)")

# Lane-owned member names: flagged, excluded from adoption candidates.
LANE_RE = re.compile(r"^(setIntr|startIntr|trapIntr|GsTMDdiv|GsTMDfast)")
LANE_ROWS = {0x3F5A0: "data_80068340 holds setIntr 0x8005EF88 (intr lane)"}

# Verdict thresholds (calibrated; see the report's calibration section).
CODE_MIN_SIG = 2          # signature words needed at all
CODE_SIG_DENSITY = 0.004  # signature words per byte
CODE_PTR_MAX = 0.30       # pointer-shaped word fraction ceiling
DATA_MAX_SIG = 1          # more than this many signature words = not data


def load_census(target):
    """{file_off: [(va, names, adoptable, sigdb)]} for one target.

    The census lines carry the reviewed evidence markers themselves
    ("(sig-db agree)" = the tools/sdk_members.py cross_check verdict for
    the member's OBJ placement; "adoptable" = the adoption flag), so the
    census reads them back verbatim instead of re-deriving them here.
    The census line address is the FUNCTION address (the OBJ label); the
    sig marker is the OBJ placement's, anchored at the member's start -
    for a label at OBJ offset 0 (GetTPage at the PRIM row start) the two
    coincide, and the report prints the marker as recorded.
    """
    out = {}
    cur = None
    for line in CENSUS.read_text().splitlines():
        m = TARGET_HDR.match(line)
        if m:
            cur = m.group(1)
            continue
        if cur != target:
            continue
        m = MEMBER.match(line)
        if not m:
            continue
        va = int(m.group(1), 16)
        name = m.group(5)
        rest = line[m.end():]
        adopt = "adoptable" in rest
        sigdb = "sig-db agree" in rest
        out.setdefault(va - LINEAR_BASE, []).append((va, name, adopt, sigdb))
    return out


def load_rows():
    rows = sorted(yaml_anchors(TARGET, with_kind=True), key=lambda r: r[0])
    out = []
    for i, (off, kind, name, nv) in enumerate(rows):
        if kind != "data":
            continue
        # extent runs to the next subsegment OF ANY KIND - the yaml is a
        # scatter list and code rows interleave; taking the next data row
        # would swallow whole asm/c rows into the decode span (the first
        # run's game-region "all code" artifact - fixed here)
        nxt = rows[i + 1][0] if i + 1 < len(rows) else None
        ext = (nxt - off) if nxt is not None else None
        drift = (nv - (off + LINEAR_BASE)) if nv is not None else None
        out.append({"off": off, "ext": ext, "name": name, "nv": nv,
                    "drift": drift})
    return out


def row_metrics(md, buf):
    """Decode 4-byte words; return the metric dict."""
    m = collections.Counter()
    nwords = len(buf) // 4
    printable = sum(1 for b in buf if 0x20 <= b <= 0x7E)
    m["printx"] = round(100 * printable / max(1, len(buf)))
    for i in range(nwords):
        w = int.from_bytes(buf[i * 4:i * 4 + 4], "little")
        va = i * 4
        if w == 0:
            m["zero"] += 1
            continue
        if (w >> 24) == 0x80:
            m["ptr"] += 1
        insn = next(md.disasm(buf[i * 4:i * 4 + 4], va), None)
        if insn is None:
            m["bad"] += 1
            continue
        mn = insn.mnemonic
        ops = insn.op_str
        if mn == "jal":
            m["jal"] += 1
        elif mn == "j":
            m["j"] += 1  # weak: ASCII text words decode j-shaped
        elif mn == "jr" and ops.endswith("$ra"):
            m["jrra"] += 1
        elif mn == "jalr":
            m["jalr"] += 1
        elif mn in ("bgezal", "bltzal"):
            m["bal"] += 1
        elif mn[0] == "b" and mn not in ("break",):
            # conditional branch; backward = loop-shaped
            mm = re.search(r"0x([0-9a-f]+)$", ops)
            if mm and int(mm.group(1), 16) < va:
                m["brtbw"] += 1
            else:
                m["brtfw"] += 1
        elif mn == "addiu" and ops.startswith("$sp, $sp, -"):
            m["prologue"] += 1
        elif mn == "sw" and ", $ra(" in ops.replace(" ", ""):
            base = ops.split("(")[0].rsplit(",", 1)[-1].strip()
            if base == "$sp":
                m["rastore"] += 1
        elif (w >> 26) == 0x12:
            m["gte"] += 1
        elif (w >> 26) == 0x11:
            m["cop1"] += 1
        else:
            m["plain"] += 1
    m["words"] = nwords
    return m


def sig_words(m):
    return (m["jal"] + m["jrra"] + m["jalr"] + m["bal"] + m["prologue"]
            + m["rastore"] + m["brtbw"])


def verdict(m, ext):
    """CODE-LIKE / MIXED / DATA-LIKE from documented thresholds.

    Text guard first: rows of mostly-printable bytes are string tables -
    their words decode j/jal/branch-shaped in bulk (b3>>2 lands in the
    8..31 opcode range), which the first run read as code.  jal alone is
    the strong shape (op 3 = 0x0C prefix, a text word needs a digit at
    byte 3); j is worthless as evidence.
    """
    if m["printx"] >= 60:
        return "DATA-LIKE"
    sig = sig_words(m)
    ptrf = m["ptr"] / max(1, m["words"])
    if sig >= max(CODE_MIN_SIG, CODE_SIG_DENSITY * ext) and ptrf < CODE_PTR_MAX:
        return "CODE-LIKE"
    if sig <= DATA_MAX_SIG:
        return "DATA-LIKE"
    return "MIXED"


def main():
    md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 | CS_MODE_LITTLE_ENDIAN)
    payload = (REPO / "baselines" / f"{TARGET}.bin").read_bytes()
    import hashlib
    sha = hashlib.sha1(payload).hexdigest()[:8]
    rows = load_rows()
    census = load_census(TARGET)
    by_off = census
    nmem = sum(len(v) for v in census.values())
    ninside = 0
    row_members = {}
    for r in rows:
        lo = r["off"]
        hi = lo + (r["ext"] if r["ext"] is not None else 0)
        mems = []
        for fo, hits in sorted(by_off.items()):
            if lo <= fo < hi:
                for va, nm, adopt, sigdb in hits:
                    mems.append((va, nm, adopt, sigdb))
        row_members[r["off"]] = mems
        ninside += len(mems)

    print(f"deep-region decode census - {TARGET}")
    print(f"baseline sha1 {sha}; {len(rows)} data rows; "
          f"{ninside} census member lines land inside data rows "
          f"(target total {nmem}); "
          f"deep boundary off 0x{DEEP_OFF:X}")
    print("verdict thresholds: CODE-LIKE sig>={} and sig/ext>={:.4f} and "
          "ptr-frac<{:.2f}; DATA-LIKE sig<={}; else MIXED".format(
              CODE_MIN_SIG, CODE_SIG_DENSITY, CODE_PTR_MAX, DATA_MAX_SIG))

    # calibration section first: the 2216-proven rows MUST read code-like
    print("\n== calibration anchors (2216 window's proven-code rows) ==")
    cache = {}
    for r in rows:
        if r["ext"] is None or r["ext"] < 0x10:
            continue
        buf = payload[r["off"]:r["off"] + r["ext"]]
        m = row_metrics(md, buf)
        cache[r["off"]] = (m, verdict(m, r["ext"]))
    ok = True
    for off, why in sorted(ANCHORS.items()):
        if off not in cache:
            print(f"  off 0x{off:X}: NOT A DATA ROW ANYMORE (moved?) - {why}")
            ok = False
            continue
        m, v = cache[off]
        flag = "OK" if v == "CODE-LIKE" else "MISSED"
        if v != "CODE-LIKE":
            ok = False
        print(f"  {flag} off 0x{off:05X} {v:9s} sig={sig_words(m):3d} "
              f"jal={m['jal']} jrra={m['jrra']} brtbw={m['brtbw']} "
              f"pro={m['prologue']} txt={m['printx']}% - {why}")
    print(f"  calibration: {'PASS' if ok else 'FAIL - thresholds need work'}")

    lane_rows = []
    print("\n== per-row table (all data rows; D=deep, G=game) ==")
    print(f"{'span':4s} {'off':>7s} {'ext':>6s} {'drift':>7s} {'verdict':9s} "
          f"{'sig':>4s} {'jal':>4s} {'j':>4s} {'jrra':>4s} {'brt':>4s} "
          f"{'pro':>4s} {'ptr%':>5s} {'zero%':>5s} {'txt%':>5s} {'mem':>4s} "
          f"{'sgdb':>4s} {'adop':>4s} name")
    total = {"CODE-LIKE": 0, "MIXED": 0, "DATA-LIKE": 0}
    deep_bytes = collections.Counter()
    candidates = []
    for r in rows:
        off, ext = r["off"], r["ext"]
        if ext is None or ext < 0x10:
            continue
        m, v = cache[off]
        span = "D" if off >= DEEP_OFF else "G"
        total[v] += 1
        if span == "D":
            deep_bytes[v] += ext
        mems = row_members.get(off, [])
        memn = len(mems)
        sigok = sum(1 for _va, _nm, _ad, sd in mems if sd)
        adoptn = sum(1 for _va, _nm, ad, _sd in mems if ad)
        lanelist = sorted({nm for _va, nm, _ad, _sd in mems
                           if LANE_RE.match(nm)})
        gatedlist = sorted({nm for _va, nm, _ad, _sd in mems
                            if GATED_RE.match(nm)})
        phantomlist = sorted({nm for _va, nm, _ad, _sd in mems
                              if PHANTOM_RE.match(nm)})
        if off in LANE_ROWS or lanelist:
            lane_rows.append((off, r["name"], sorted(lanelist)))
        dtxt = "lin" if r["drift"] == 0 else (
            "?" if r["drift"] is None else f"+{r['drift']:X}")
        print(f"{span:4s} 0x{off:05X} 0x{ext:05X} {dtxt:>7s} {v:9s} "
              f"{sig_words(m):4d} {m['jal']:4d} {m['j']:4d} {m['jrra']:4d} "
              f"{m['brtbw'] + m['brtfw']:4d} {m['prologue']:4d} "
              f"{100 * m['ptr'] / m['words']:5.1f} "
              f"{100 * m['zero'] / m['words']:5.1f} {m['printx']:5d} "
              f"{memn:4d} {sigok:4d} {adoptn:4d} {r['name']}")
        if (span == "D" and v in ("CODE-LIKE", "MIXED")
                and off not in ANCHORS and off not in LANE_ROWS
                and not lanelist):
            candidates.append((off, r["name"], v, mems, m, gatedlist,
                               phantomlist))

    print("\n== summary ==")
    print(f"  verdict counts (rows with ext>=0x10): {dict(total)}")
    print(f"  deep-region bytes by verdict: "
          f"{ {k: f'0x{v:X}' for k, v in deep_bytes.items()} }")
    gbytes = collections.Counter()
    for r in rows:
        if r["ext"] is None or r["ext"] < 0x10:
            continue
        if r["off"] < DEEP_OFF:
            gbytes[cache[r["off"]][1]] += r["ext"]
    print(f"  game-region bytes by verdict: "
          f"{ {k: f'0x{v:X}' for k, v in gbytes.items()} }")
    print("  game-region note: the typing is NOT uniformly sound there - "
          "the census's biggest code signals include game-region rows "
          "(data_8003386C sig=389, data_80038C2C sig=65, data_80040BD0 "
          "sig=125, all eyeball-confirmed coherent call/loop streams), "
          "and data_80020000's tail holds a function that jal's the "
          "VSyncCallback region then restores a full ra/fp/s7-s0 frame "
          "at VA ~0x80024000; the head of that same row is the payload's "
          "ASCII text.  Island-shaped, like mainmenu_eu's twin islands.")
    print(f"  lane-owned rows flagged: {len(lane_rows)}")
    for off, name, names in sorted(lane_rows):
        print(f"    off 0x{off:05X} {name}: {names}")
    print(f"\n== adoption-candidate rows (deep, code-like/mixed, "
          f"unclaimed by lanes, not 2216 anchors): {len(candidates)} ==")
    for off, name, v, mems, m, gated, phantom in candidates:
        nmlist = sorted({nm for _va, nm, _ad, _sd in mems})
        gtxt = f"  OWNER-GATED inside: {gated}" if gated else ""
        ptxt = (f"  PHANTOM-MACRO names inside (archive-walk placements, "
                f"not body evidence): {phantom}") if phantom else ""
        print(f"  off 0x{off:05X} {name} [{v}] sig={sig_words(m)} "
              f"members={len(mems)}: {nmlist[:12]}"
              + (" ..." if len(nmlist) > 12 else "") + gtxt + ptxt)
    print("\n(judge-prep only: NO carve changes; lane-owned rows stay "
          "untouched; the framed-vs-de-framed call is coordination-gated)")





if __name__ == "__main__":
    main()

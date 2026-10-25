#!/usr/bin/env python3
"""probe_graveyard_walk.py - bank the walk of mainmenu_jp's two re-homed
graveyard data rows (window cron-202610251551, offline).

data_80066CF4 (yaml 0x3E1B4 # 0x6e0) and data_8005E1B8 (yaml 0x3E9B8 # 0x43c)
hold the walk's function boundaries as `nonmatching`/`dlabel` markers and the
instruction stream as data words (the walk claimed the region as data; the
census's six dw=2 SetRotMatrix inline-exposure interiors live inside). This
probe decodes the word stream (MIPS I + COP2/GTE transfers + LWC2/SWC2) and
banks per function:

  - extent (VA..VA, size), word-class histogram
  - jal targets (callee VAs) and jr/jalr structure
  - GTE transfer inventory (mtc2/ctc2/mfc2/cfc2 rt -> reg, lwc2/swc2)
  - the ten-word SetRotMatrix head signature (lw $8..$12 0..16($4) +
    five mtc2 into data regs 0..4) and its rel offset, the banked
    inline-exposure law
  - the $5-continuation loads right after a matched head (lhu/lw shapes)

plus a cross-reference pass: every jal in mainmenu_jp's committed .s tree
whose target lands inside a walked function, and every data reference
(lui/ori pairs aside, direct absolute words) - the callers are the carve
plan's anchors.

Output: the walk table to stdout; nothing in-repo changes.
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ASM = REPO / "asm" / "mainmenu_jp"

ROW1 = ASM / "nonmatchings" / "data" / "data_80066CF4.data.s"  # 0x6e0
ROW2 = ASM / "nonmatchings" / "data" / "data_8005E1B8.data.s"  # 0x43c

# the six parked dw=2 sites (census DATA-ROW, banked inline-exposure class)
SITES = [0x8005D9BC, 0x8005DB1C, 0x8005DDF4, 0x8005DF04, 0x8005E3DC, 0x8005E4E8]

LINE = re.compile(r"/\* ([0-9A-F]{5}) ([0-9A-F]{8}) ([0-9A-F]{8}) \*/")
BNDRY = re.compile(r"nonmatching (\S+)")
DLABEL = re.compile(r"dlabel (\S+)")


def parse(path):
    """-> list of functions: (name, va, [(va, word), ...])"""
    funcs, cur = [], None
    for raw in path.read_text().splitlines():
        m = BNDRY.search(raw)
        if m:
            cur = {"name": m.group(1), "va": None, "words": []}
            funcs.append(cur)
            continue
        m = DLABEL.search(raw)
        if m and cur is not None:
            cur["va"] = int(m.group(1).replace("func_", ""), 16)
            continue
        m = LINE.search(raw)
        if m and cur is not None:
            word = int.from_bytes(bytes.fromhex(m.group(3)), "little")
            cur["words"].append((int(m.group(2), 16), word))
    return funcs


def dec(w):
    """decode one word -> (cls, detail)"""
    op = w >> 26
    if op == 0:
        f = w & 0x3F
        if f == 0:
            sa = (w >> 6) & 0x1F
            return ("sll" if (w >> 21) & 0x1F == 0 else "sllv", f"sa={sa}")
        if f in (2, 3):
            return ("srl/sra", "")
        if f in (8, 9):
            return ("jr/jalr", "")
        if f == 0x18:
            return ("mult", "")
        if f == 0x19:
            return ("multu", "")
        if f in (0x1A, 0x1B):
            return ("div/divu", "")
        if f in (0x10, 0x11, 0x12, 0x13):
            return ("mfhi/mflo", "")
        if f in (0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27):
            return ("addu/add/subu/and/or/xor/nor/slt", "")
        return (f"special f=0x{f:02x}", "")
    if op == 1:
        return ("regimm bltz/bgez", "")
    if op in (2, 3):
        tgt = (w & 0x3FFFFFF) << 2
        return ("j/jal", f"op{'jal' if op == 3 else 'j'}")
    if op == 4:
        return ("beq", "")
    if op == 5:
        return ("bne", "")
    if op == 6:
        return ("blez", "")
    if op == 7:
        return ("bgtz", "")
    if op in (8, 9):
        imm = w & 0xFFFF
        return ("addi/addiu", f"imm={imm:#06x}")
    if op == 0xA or op == 0xB:
        return ("slti/sltiu", "")
    if op == 0xC:
        return ("andi", f"imm={w & 0xFFFF:#06x}")
    if op == 0xD:
        return ("ori", f"imm={w & 0xFFFF:#06x}")
    if op == 0xE:
        return ("xori", "")
    if op == 0xF:
        return ("lui", f"imm={w & 0xFFFF:#06x}")
    if op in (0x20, 0x21, 0x23, 0x24, 0x25):
        rt = (w >> 16) & 0x1F
        imm = w & 0xFFFF
        base = (w >> 21) & 0x1F
        m = {0x20: "lb", 0x21: "lh", 0x23: "lw", 0x24: "lbu", 0x25: "lhu"}[op]
        return ("load", f"{m} ${rt}, {imm & 0xFFFF:#06x}(${base})")
    if op in (0x28, 0x29, 0x2B):
        rt = (w >> 16) & 0x1F
        imm = w & 0xFFFF
        base = (w >> 21) & 0x1F
        m = {0x28: "sb", 0x29: "sh", 0x2B: "sw"}[op]
        return ("store", f"{m} ${rt}, {imm & 0xFFFF:#06x}(${base})")
    if op == 0x12:  # COP2
        rs = (w >> 21) & 0x1F
        rt = (w >> 16) & 0x1F
        rd = (w >> 11) & 0x1F
        if rs == 0:
            return ("mfc2", f"${rt} <- r{rd}")
        if rs == 2:
            return ("cfc2", f"${rt} <- c{rd}")
        if rs == 4:
            return ("mtc2", f"${rt} -> r{rd}")
        if rs == 6:
            return ("ctc2", f"${rt} -> c{rd}")
        f = w & 0x3F
        names = {0x01: "RTPS", 0x06: "NCLIP", 0x12: "MVMVA", 0x2D: "RTPT",
                 0x30: "NCDS", 0x38: "NCDT"}
        return ("gte-cmd", names.get(f, f"funct=0x{f:02x}"))
    if op == 0x32:
        rt = (w >> 16) & 0x1F
        imm = w & 0xFFFF
        return ("lwc2", f"${rt} <- {imm & 0xFFFF:#06x}({(w >> 21) & 0x1F})")
    if op == 0x3A:
        rt = (w >> 16) & 0x1F
        imm = w & 0xFFFF
        return ("swc2", f"${rt} -> {imm & 0xFFFF:#06x}({(w >> 21) & 0x1F})")
    return (f"op=0x{op:02x}", "")


ROT_HEAD = [
    (0x23, 8, 0), (0x23, 9, 4), (0x23, 10, 8), (0x23, 11, 12), (0x23, 12, 16),
    (0x12, 6, 8, 0), (0x12, 6, 9, 1), (0x12, 6, 10, 2),
    (0x12, 6, 11, 3), (0x12, 6, 12, 4),
]


def rot_head_at(words, i):
    """the ten-word SetRotMatrix head (lw $8..$12 0..16($4) + mtc2 r0..r4)"""
    if i + 10 > len(words):
        return False
    for k, want in enumerate(ROT_HEAD):
        w = words[i + k][1]
        op = w >> 26
        if want[0] == 0x23:
            if op != 0x23 or (w >> 16) & 0x1F != want[1]:
                return False
            if (w >> 21) & 0x1F != 4 or (w & 0xFFFF) != want[2]:
                return False
        else:
            if w >> 26 != 0x12 or (w >> 21) & 0x1F != 6:
                return False
            if (w >> 16) & 0x1F != want[2] or (w >> 11) & 0x1F != want[3]:
                return False
    return True


def profile(fn, row_lo, row_hi, row_name):
    words = fn["words"]
    va0 = fn["va"]
    size = len(words) * 4
    hist = {}
    jals, gte, stores5 = [], [], []
    heads, conts = [], []
    for i, (va, w) in enumerate(words):
        cls, det = dec(w)
        hist[cls] = hist.get(cls, 0) + 1
        if cls == "j/jal" and w >> 26 == 3:
            tgt = ((w & 0x3FFFFFF) << 2) | ((va + 4) & 0xF0000000)
            jals.append((va, f"-> 0x{tgt:08x}"))
        if cls.startswith(("mtc2", "ctc2", "mfc2", "cfc2", "lwc2", "swc2")):
            gte.append((va, cls, det))
        if rot_head_at(words, i):
            heads.append(va)
            # continuation loads through $5 within the next 4 words
            for j in range(i + 10, min(i + 14, len(words))):
                w2 = words[j][1]
                if w2 >> 26 in (0x21, 0x23, 0x25) and (w2 >> 21) & 0x1F == 5:
                    conts.append((words[j][0], dec(w2)[0], dec(w2)[1]))
                else:
                    break
        if cls == "store" and det == "" :
            pass
    sites = [s for s in SITES if va0 <= s < va0 + size]
    print(f"\n== {fn['name']}  0x{va0:08x}..0x{va0 + size:08x}  size 0x{size:x} ({len(words)} words)")
    if sites:
        print(f"   parked dw=2 sites: " + ", ".join(f"0x{s:08x} (rel +0x{s - va0:x})" for s in sites))
    if heads:
        for h in heads:
            print(f"   SetRotMatrix ten-word head at rel +0x{h - va0:x}")
        for c in conts:
            print(f"   $5-continuation after head: 0x{c[0]:08x} {c[1]} {c[2]}")
    if jals:
        print("   jals: " + "; ".join(f"0x{v:08x} {d}" for v, d in jals))
    gte_sum = ", ".join(sorted({f"{c} {d}" for _, c, d in gte}))
    print(f"   GTE xfers ({len(gte)}): {gte_sum[:200]}")
    top = sorted(hist.items(), key=lambda kv: -kv[1])
    print("   classes: " + " ".join(f"{k}:{v}" for k, v in top))


def callers():
    """jal cross-reference over the whole mainmenu_jp asm tree"""
    los = []
    for path in (ROW1, ROW2):
        for raw in path.read_text().splitlines():
            m = DLABEL.search(raw)
            if m:
                los.append(int(m.group(1).replace("func_", ""), 16))
    lo, hi = min(los), 0x8005E5F4
    pat = re.compile(r"jal\s+0x([0-9A-Fa-f]{8})|jal\s+func_([0-9A-Fa-f]{8})")
    hits = []
    for path in sorted(ASM.rglob("*.s")):
        if path in (ROW1, ROW2) or "rowdef" in path.name:
            continue
        text = path.read_text(errors="replace")
        for m in pat.finditer(text):
            tgt = int(m.group(1) or m.group(2), 16)
            if lo <= tgt < hi:
                line = text[: m.start()].count("\n") + 1
                hits.append((path.relative_to(REPO), line, tgt))
    return hits


def main():
    funcs1 = parse(ROW1)
    funcs2 = parse(ROW2)
    print("== graveyard head row data_80066CF4 (yaml 0x3E1B4 # 0x6e0, 0x8005D9B4..0x8005E094)")
    for fn in funcs1:
        profile(fn, 0x8005D9B4, 0x8005E094, "head")
    print("\n== graveyard tail row data_8005E1B8 (yaml 0x3E9B8 # 0x43c, 0x8005E1B8..0x8005E5F4)")
    for fn in funcs2:
        profile(fn, 0x8005E1B8, 0x8005E5F4, "tail")
    print("\n== callers (jal targets inside the graveyard, over mainmenu_jp's committed .s tree)")
    hits = callers()
    if not hits:
        print("   (none - the graveyard functions are unreferenced by any committed jal)")
    for rel, line, tgt in hits:
        print(f"   {rel}:{line} jal -> 0x{tgt:08x}")




# ---------- sibling pass: byte-identical copies of every host across targets ----------
TARGETS = ["slps_00270", "sces_00269", "mainmenu_jp", "mainmenu_eu",
           "g3_jp", "g3_eu", "g3org_jp", "g3org_eu"]
DELTA = 0x8001F800  # VA = raw_off + DELTA (banked classifier law)


def yaml_rows(target):
    """-> sorted [(off, type, name, size)] from the target's splat yaml"""
    rows = []
    y = REPO / "config" / f"splat.{target}.yaml"
    for m in re.finditer(r"- \[0x([0-9A-Fa-f]+), (\w+), (\S+)\]\s*(?:#\s*(?:0x)?([0-9a-fA-F]+))?", y.read_text()):
        off = int(m.group(1), 16)
        size = int(m.group(4), 16) if m.group(4) else 0
        rows.append((off, m.group(2), m.group(3), size))
    rows.sort()
    return rows


def covering(rows, off):
    import bisect
    i = bisect.bisect_right([r[0] for r in rows], off + 1) - 1
    if i < 0:
        return None
    r = rows[i]
    if r[3] and off >= r[0] + r[3]:
        return None
    return r


def siblings():
    funcs = parse(ROW1) + parse(ROW2)
    bins = {t: (REPO / "baselines" / f"{t}.bin").read_bytes() for t in TARGETS}
    ytabs = {t: yaml_rows(t) for t in TARGETS}
    print("\n== sibling pass: byte-identical host copies across the eight fresh baselines")
    for fn in funcs:
        words = fn["words"]
        body = b"".join(w.to_bytes(4, "little") for _, w in words)
        if len(body) < 8:
            continue
        hits = []
        for t, data in bins.items():
            start = 0
            while True:
                i = data.find(body, start)
                if i < 0:
                    break
                va = i + DELTA
                cov = covering(ytabs[t], i)
                cd = f"{cov[1]} {cov[2]} #0x{cov[3]:x}" if cov else "UNCOVERED"
                hits.append(f"{t} 0x{va:08x} [{cd}]")
                start = i + 1
        sites = [s for s in SITES if fn["va"] <= s < fn["va"] + len(words) * 4]
        tag = " SITE" if sites else ""
        print(f"\n{fn['name']} 0x{fn['va']:08x} 0x{len(body):x}{tag}: {len(hits)} hit(s)")
        for h in hits:
            print(f"   {h}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--siblings":
        siblings()
    else:
        main()

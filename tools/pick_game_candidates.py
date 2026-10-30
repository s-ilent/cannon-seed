#!/usr/bin/env python3
"""pick_game_candidates.py - rank untagged (game-code) asm rows by real-C landing promise.

The window-29 real-C pivot's workhorse. Re-derived after sandbox rollback #4
ate the scripts/ copy - banked IN-REPO this time so rollbacks cannot eat it.

A candidate row:
  - is an `asm` yaml row with NO `sdk` tag in its size comment,
  - whose name is not in config/symbols.curated.txt under this target,
  - whose VA (0x80000000 | yaml address) sits OUTSIDE every
    config/sdk_windows.txt span for the target,
  - whose .s body is self-contained (split continuation rows - body that
    reads t0-t3 without ever writing one and stores no ra - are skipped),
  - is not a BIOS-thunk (`li tX,0xA0/0xB0/0xC0; jr tX` = libc jumps).

Score = extent + 8*branches + 16*jals. Caller evidence (who jal's the
candidate, and whether the caller is a game row or an sdk row) decides game
vs SDK in the end; the score only orders the reading list.

Usage: python3 tools/pick_game_candidates.py [target] [--top N]
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ROW_RE = re.compile(
    r"^\s*-\s*\[0x([0-9a-fA-F]+),\s*(asm|c)\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\]\s*#\s*(.*)$"
)
SPAN_RE = re.compile(r"^0x([0-9a-fA-F]+)\s+0x([0-9a-fA-F]+)\s+(verbatim|fixed)\b")
TARGET_RE = re.compile(r"^//\s*target:\s*(\S+)")
CURATED_NAME_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=")

BRANCH_MN = ("beq", "bne", "blez", "bgtz", "bltz", "bgez", "bltzal", "bgezal")
WRITER_MN = ("li", "la", "lw", "lbu", "lhu", "move", "addiu", "addi", "addu",
             "ori", "lui", "sll", "srl", "sra", "andi", "sltiu", "slti", "lhu")


def parse_yaml_rows(target):
    rows = []
    text = (ROOT / "config" / f"splat.{target}.yaml").read_text()
    for line in text.splitlines():
        m = ROW_RE.match(line)
        if not m:
            continue
        addr_s, kind, name, comment = m.groups()
        toks = comment.split()
        size = 0
        sdk_tag = False
        for t in toks:
            if t.startswith("0x") or t.startswith("0X"):
                try:
                    size = int(t, 16)
                except ValueError:
                    pass
            elif t == "sdk":
                sdk_tag = True
        rows.append({"va": 0x80000000 | int(addr_s, 16), "kind": kind,
                     "name": name, "size": size, "sdk": sdk_tag})
    return rows


def parse_windows(target):
    spans = []
    cur = None
    for line in (ROOT / "config" / "sdk_windows.txt").read_text().splitlines():
        m = TARGET_RE.match(line)
        if m:
            cur = m.group(1)
            continue
        if cur != target:
            continue
        m = SPAN_RE.match(line)
        if m:
            start = int(m.group(1), 16)
            spans.append((start, start + int(m.group(2), 16)))
    return spans


def parse_curated(target):
    names = set()
    cur = None
    for line in (ROOT / "config" / "symbols.curated.txt").read_text().splitlines():
        m = TARGET_RE.match(line)
        if m:
            cur = m.group(1)
            continue
        if cur != target:
            continue
        m = CURATED_NAME_RE.match(line)
        if m:
            names.add(m.group(1))
    return names


def row_kind_map(target, rows):
    """name -> ('asm-sdk' | 'asm-game' | 'c', ...) for caller classification."""
    out = {}
    for r in rows:
        if r["kind"] == "c":
            out[r["name"]] = "c"
        elif r["sdk"]:
            out[r["name"]] = "asm-sdk"
        else:
            out.setdefault(r["name"], "asm-game")
    return out


def read_s(target, name):
    p = ROOT / "asm" / target / "nonmatchings" / f"{name}.s"
    if not p.is_file():
        return None
    return p.read_text().splitlines()


def ins_lines(lines):
    """code lines: not labels, not directives, not comments."""
    out = []
    for ln in lines:
        s = ln.strip()
        if not s or s.startswith(("#", "//", ".")) or s.endswith(":"):
            continue
        out.append(s)
    return out


def mnem(s):
    return s.split()[0].split("\t")[0].lower()


def ops(s):
    s = s.split(None, 1)
    return s[1].replace("$", "").split(",") if len(s) > 1 else []


def shape(target, name):
    lines = read_s(target, name)
    if lines is None:
        return None
    code = ins_lines(lines)
    n_br = sum(1 for c in code if mnem(c) in BRANCH_MN or mnem(c) == "b")
    n_jal = sum(1 for c in code if mnem(c) == "jal")
    n_jalr = sum(1 for c in code if mnem(c) == "jalr")
    has_sw_ra = any(mnem(c) == "sw" and ops(c) and ops(c)[0].replace("$", "") == "ra"
                    for c in code)
    has_gte = any(m in ("cop2", "lwc2", "swc2", "mfc2", "mtc2", "ctc2", "cfc2") for m in map(mnem, code))
    has_float = any(".s" in m or ".w" in m or m in ("lwc1", "swc1", "mtc1", "mfc1", "ctc1", "cfc1")
                    for m in map(mnem, code))
    # BIOS thunk: li tX, 0xA0/0xB0/0xC0 ... jr tX
    thunk = False
    for i, c in enumerate(code):
        m = mnem(c)
        if m == "li":
            o = ops(c)
            if len(o) == 2 and o[1].lower().lstrip("0x") in ("a0", "b0", "c0") and o[1].lower() in ("0xa0", "0xb0", "0xc0", "a0", "b0", "c0"):
                if any(mnem(x) == "jr" and ops(x) and ops(x)[0].replace("$", "") == o[0].replace("$", "")
                       for x in code[i + 1:i + 4]):
                    thunk = True
                    break
    # split continuation: reads t0-t3 but never writes one, and stores no ra
    t_regs = ("t0", "t1", "t2", "t3")
    uses_t = any(any(o.strip().replace("$", "") in t_regs for o in ops(c)) for c in code)
    init_t = any(mnem(c) in WRITER_MN and ops(c) and ops(c)[0].strip().replace("$", "") in t_regs
                 for c in code)
    split = uses_t and not init_t and not has_sw_ra
    return {"n_br": n_br, "n_jal": n_jal, "n_jalr": n_jalr, "sw_ra": has_sw_ra,
            "gte": has_gte, "float": has_float, "thunk": thunk, "split": split,
            "n_ins": len(code)}


def callers_of(target, name, kind_map):
    """who jal's this name (asm bodies) or calls it (src C). game vs sdk evidence."""
    game, sdk = [], []
    pat_asm = re.compile(r"\bjal\s+%s\b" % re.escape(name))
    for s in (ROOT / "asm" / target / "nonmatchings").glob("*.s"):
        txt = s.read_text()
        if pat_asm.search(txt):
            tag = kind_map.get(s.stem, "?")
            (game if tag in ("asm-game", "c") else sdk).append(s.stem)
    for s in (ROOT / "src").glob("*.c"):
        txt = s.read_text()
        if re.search(r"\b%s\s*\(" % re.escape(name), txt):
            game.append(s.stem)
    return game, sdk


def main():
    args = sys.argv[1:]
    target = "g3_eu"
    top = 25
    if args and not args[0].startswith("-"):
        target = args.pop(0)
    if "--top" in args:
        top = int(args[args.index("--top") + 1])

    rows = parse_yaml_rows(target)
    spans = parse_windows(target)
    curated = parse_curated(target)
    kind_map = row_kind_map(target, rows)

    cands = []
    for r in rows:
        if r["kind"] != "asm" or r["sdk"] or not r["size"]:
            continue
        if r["name"] in curated:
            continue
        va, end = r["va"], r["va"] + r["size"]
        if any(s <= va < e or (va < s < end) for s, e in spans):
            continue
        sh = shape(target, r["name"])
        if sh is None or sh["thunk"] or sh["split"]:
            continue
        game, sdk = callers_of(target, r["name"], kind_map)
        score = r["size"] + 8 * sh["n_br"] + 16 * sh["n_jal"]
        cands.append({"name": r["name"], "va": r["va"], "size": r["size"],
                      "score": score, "game_callers": game, "sdk_callers": sdk, **sh})

    cands.sort(key=lambda c: -c["score"])
    print(f"target {target}: {len(rows)} rows, {len(cands)} candidates after filters\n")
    hdr = f"{'name':<18}{'va':>10}{'sz':>6}{'score':>7}{'br':>4}{'jal':>4} {'gte':<4}{'flt':<4}{'ra':<3} callers(game) / (sdk)"
    print(hdr)
    print("-" * len(hdr))
    for c in cands[:top]:
        gc = ",".join(c["game_callers"][:4]) or "-"
        sc = ",".join(c["sdk_callers"][:3]) or "-"
        print(f"{c['name']:<18}0x{c['va']:08x}{c['size']:>6}{c['score']:>7}"
              f"{c['n_br']:>4}{c['n_jal']:>4} {'Y' if c['gte'] else '-':<4}"
              f"{'Y' if c['float'] else '-':<4}{'Y' if c['sw_ra'] else '-':<3} {gc} / {sc}")


if __name__ == "__main__":
    main()

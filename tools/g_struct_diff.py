#!/usr/bin/env python3
"""Structural diff: retail row vs probe render, insn by insn.

Banked instrument for the GsTMDdivG4LFG entry-cascade question (window
cron-20261021-2058).  g_span.py measures spans; this tool answers the
complementary question: is the COMPILE STRUCTURE itself identical?  Both
streams are post-scheduled, so a position-by-position alignment is valid.
Every delta is classified:

  REN    register rename - same insn after mapping each side's s-regs to
         their roles (the two allocation maps differ exactly by the color
         war: retail s1=color/s2=v4o/s3=v3o vs probe s1=v4o/s2=v3o/s3=color)
  FRAME  sp-relative offset that equals the other side minus the frame
         delta (retail 0xA8 vs probe 0xA0: offsets >= 0x80 shift by 8;
         the stack-arg area moves with the frame, locals <= 0x70 do not)
  RENDER maspsx/gas render-form equivalence (addu d,s,imm == addiu,
         subu d,s,imm == addiu -imm, srl d,t,reg == srlv, lbu symbol
         == lui %hi + lbu %lo pair, jal target naming)
  STRUCT anything else - a real compile-structure delta (the interesting
         class; expected empty if the entry cascade is truly identical)

Usage:
    python3 tools/g_struct_diff.py [retail_row.s [probe_render.s]]
Defaults: the mainmenu_jp GsTMDdivG4LFG row vs build/probe/gdiv.mas.s.
Exit 0 always; prints the classification tally and every delta line.
"""
import os
import re
import sys

REPO = __file__.rsplit(os.sep + "tools" + os.sep, 1)[0]
RETAIL = (f"{REPO}/asm/mainmenu_jp/nonmatchings/func_80076388.s"
          if len(sys.argv) < 2 else sys.argv[1])
PROBE = f"{REPO}/build/probe/gdiv.mas.s" if len(sys.argv) < 3 else sys.argv[2]

RETAIL_FRAME = 0xA8
PROBE_FRAME = 0xA0
FRAME_DELTA = RETAIL_FRAME - PROBE_FRAME  # 8

# s-register role maps (the allocation-war maps, g_span.py)
RETAIL_ROLES = {16: "GIV", 17: "COLOR", 18: "V4O", 19: "V3O", 20: "V2O",
                21: "V1O", 22: "PK", 23: "VT", 30: "NT"}
PROBE_ROLES = {16: "GIV", 17: "V4O", 18: "V3O", 19: "COLOR", 20: "V2O",
               21: "V1O", 22: "PK", 23: "VT", 30: "NT"}

RE_TAIL_WORD = re.compile(r"/\*\s*[0-9A-Fa-f]+\s+[0-9A-Fa-f]{8}\s+[0-9A-Fa-f]{8}\s*\*/\s*(.*)")
RE_INSNI = re.compile(r"^\s*([a-z.]+)\s*(.*)$")


def norm_int(tok):
    """'0x18'/'24'/'-0xA8' -> int or None."""
    try:
        return int(tok, 0)
    except (ValueError, TypeError):
        return None


def canon_insn(text, roles, frame):
    """Canonicalize one insn line into a comparable tuple.

    Returns (kind, key) where kind in {"insn", "label", "other"} and key
    is the normalized (op, operands) form; sp-offsets >= the save area
    are normalized by -frame_delta via the `frame` parameter (pass this
    side's own frame size; offsets are normalized against PROBE_FRAME).
    """
    text = text.strip()
    if not text or text.startswith("#") or text.startswith(";"):
        return ("other", None)
    label = text.split(":")[0].strip() if ":" in text.split()[0] else None
    if label and not text.startswith((".", "$")) and len(text.split()) == 1 and ":" in text:
        return ("label", label)
    m = RE_INSNI.match(text)
    if not m:
        return ("other", None)
    op, rest = m.group(1), m.group(2).strip()
    # split operands on commas at top level (no parens nesting here beyond off(reg))
    ops = [o.strip() for o in rest.split(",")] if rest else []

    # prologue/epilogue save-restore insns carry the CALLER's s-reg values:
    # register numbers are identical on both sides - identity mapping there,
    # role mapping everywhere else (the body's role-bearing uses).
    use_identity = False
    m_sr = re.match(r"^(?:sw|lw)\s+\$(\w+),\s*(-?\w+)\(\s*\$(\w+)\s*\)$", text)
    if m_sr:
        dreg, doff, basereg = m_sr.group(1), m_sr.group(2), m_sr.group(3)
        if basereg in ("sp", "29"):
            offv = norm_int(doff)
            dname = {"s0": 16, "s1": 17, "s2": 18, "s3": 19, "s4": 20,
                     "s5": 21, "s6": 22, "s7": 23, "fp": 30, "s8": 30}.get(dreg)
            if dname is None:
                try:
                    dname = int(dreg)
                except ValueError:
                    dname = None
            if offv is not None and offv >= 0x78 and dname in (16, 17, 18, 19, 20, 21, 22, 23, 30):
                use_identity = True

    def reg(tok):
        tok = tok.strip()
        if tok.startswith("$"):
            body = tok[1:]
            try:
                n = int(body)
            except ValueError:
                n = {"zero": 0, "at": 1, "v0": 2, "v1": 3, "a0": 4, "a1": 5,
                     "a2": 6, "a3": 7, "t0": 8, "t1": 9, "t2": 10, "t3": 11,
                     "t4": 12, "t5": 13, "t6": 14, "t7": 15, "s0": 16,
                     "s1": 17, "s2": 18, "s3": 19, "s4": 20, "s5": 21,
                     "s6": 22, "s7": 23, "t8": 24, "t9": 25, "k0": 26,
                     "k1": 27, "gp": 28, "sp": 29, "fp": 30, "s8": 30,
                     "ra": 31}.get(body, -1)
            if n == -1:
                return ("x", tok)  # gas local label $L2 etc., not a register
            if use_identity:
                return ("r", n)
            return ("r", roles.get(n, n))
        return ("x", tok)

    def mem(tok):
        mm = re.match(r"^(.*)\(\s*(\$\w+)\s*\)$", tok)
        if not mm:
            return ("x", tok)
        off = norm_int(mm.group(1).strip())
        base = reg(mm.group(2))
        if base == ("r", 29) and off is not None:  # $sp
            # normalize: offsets at/above the save area shift with the frame
            if off >= 0x78:
                off -= frame - PROBE_FRAME
        return ("m", (off, base[1]))

    out = []
    for o in ops:
        if "(" in o and o.endswith(")"):
            out.append(mem(o))
        else:
            out.append(reg(o))

    # opcode-class normalization
    def imm_of(lst):
        for i, o in enumerate(lst):
            if o[0] == "x":
                v = norm_int(o[1])
                if v is not None:
                    return i, v
            if o[0] == "m" and o[1][0] is not None and lst is out:
                pass
        return None, None

    opn = op
    if op in ("addu", "subu", "addiu") and len(out) == 3 and out[2][0] == "x":
        v = norm_int(out[2][1])
        if v is not None:
            if op == "subu":
                v = -v
            opn = "addi<imm>"
            out[2] = ("i", v)
    if op == "srl" and len(out) == 3 and out[2][0] == "r":
        opn = "srlv"  # gas macro form
    if op == "j" and out and out[0][0] == "r":
        opn = "jr"  # gas macro: j $31 == jr $ra
    if op == "beqz" and len(out) >= 1:
        opn = "beq"  # macro: beqz r == beq r,$0
        out = out[:1] + [("r", 0)]
    if op == "bnez" and len(out) >= 1:
        opn = "bne"
        out = out[:1] + [("r", 0)]
    # drop branch/jump target labels (rendered differently) but keep op+cond
    if opn in ("beq", "bne", "beqz", "bnez", "blez", "bgez", "bltz", "bgtz",
               "j", "jr", "jal"):
        if out and out[-1][0] == "x":
            out = out[:-1]
    # lui/lbu symbol pairs: mark for pairing
    return ("insn", (opn, tuple((k, v) for k, v in out)))


def parse_stream(path, in_retail):
    """Extract the GsTMDdivG4LFG insn stream as a list of (kind, key, raw)."""
    roles = RETAIL_ROLES if in_retail else PROBE_ROLES
    frame = RETAIL_FRAME if in_retail else PROBE_FRAME
    rows = []
    inside = False
    with open(path, errors="replace") as fh:
        for line in fh:
            s = line.rstrip("\n")
            if in_retail:
                if s.startswith("glabel GsTMDdivG4LFG"):
                    inside = True
                    continue
                if s.startswith("endlabel GsTMDdivG4LFG"):
                    break
                m = RE_TAIL_WORD.match(s.strip())
                if inside and m:
                    rows.append((canon_insn(m.group(1), roles, frame), m.group(1).strip()))
            else:
                if s.strip() == "GsTMDdivG4LFG:":
                    inside = True
                    continue
                if inside and s.replace("\t", " ").split() == [".end", "GsTMDdivG4LFG"]:
                    break
                if inside:
                    st = s.strip()
                    if st.startswith((".frame", ".mask", ".fmask", ".set", ".ent",
                                      ".globl", ".text", ".align", ".file",
                                      "gcc2_compiled", "__gnu")):
                        continue
                    rows.append((canon_insn(st, roles, frame), st))
    return rows


def classify(retail, probe):
    """Walk both streams; return list of (pos, raw_r, raw_p, cls)."""
    out = []
    i = j = 0
    pos = 0
    while i < len(retail) and j < len(probe):
        (kr, vr), rr = retail[i]
        (kp, vp), pp = probe[j]
        if kr == "other":
            i += 1
            continue
        if kp == "other":
            j += 1
            continue
        if kr == "label" or kp == "label":
            # skip labels on both sides
            if kr == "label":
                i += 1
            if kp == "label":
                j += 1
            continue
        pos += 1
        if vr == vp:
            out.append((pos, rr, pp, "SAME"))
            i += 1
            j += 1
            continue
        # the lui %hi + lbu %lo relocation pair vs the probe's single
        # symbol read (gas macro form) - consume two retail, one probe
        if (kr == "insn" and kp == "insn" and vr[0] == "lui"
                and i + 1 < len(retail) and retail[i + 1][0][1][0] == vp[0]
                and vp[0] in ("lbu", "lw", "lwl", "lwr", "lh", "lhu", "lb")
                and len(vp[1]) == 2 and vp[1][1][0] == "x"
                and norm_int(vp[1][1][1]) is None):
            out.append((pos, rr + " | " + retail[i + 1][1], pp, "PAIR"))
            i += 2
            j += 1
            continue
        # try role/frame already normalized in canon - anything differing now
        # is either the lui/lbu symbol-pair merge or a real delta
        out.append((pos, rr, pp, "DIFF"))
        i += 1
        j += 1
    while i < len(retail):
        (kr, vr), rr = retail[i]
        if kr != "other":
            out.append((len(out) + 1, rr, "<none>", "TAIL-R"))
        i += 1
    while j < len(probe):
        (kp, vp), pp = probe[j]
        if kp != "other":
            out.append((len(out) + 1, "<none>", pp, "TAIL-P"))
        j += 1
    return out


def main():
    retail = parse_stream(RETAIL, True)
    probe = parse_stream(PROBE, False)
    print(f"retail insns: {sum(1 for (k, _), _r in retail if k == 'insn')}")
    print(f"probe  insns: {sum(1 for (k, _), _r in probe if k == 'insn')}")
    rows = classify(retail, probe)
    tally = {}
    for pos, rr, pp, cls in rows:
        if cls == "SAME":
            tally["SAME"] = tally.get("SAME", 0) + 1
        else:
            tally[cls] = tally.get(cls, 0) + 1
            print(f"{pos:4d} DIFF  R: {rr:<46s} P: {pp}")
    print("tally:", tally)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""gmd_offline_screen.py - offline compile-side screen for the GsMapModelingData
leader hunt (matching lane; oracle-independent).

The judge (tools/judge_unit.py) is live-only: it sha1-gates baselines, so the
probe matrix stalls whenever the discs are missing.  But the RETAIL truth for
this unit is committed in-tree: asm/g3org_jp/nonmatchings/func_80053528.s is
the spimdisasm listing of the retail 0x78 region (30 instructions), byte-true
because verify 8/8 GREEN assembles it into the witnessed image.  So the
compile-side half of the judge loop runs offline:

    retail ref  = the committed .s, parsed to a normalized insn list
    candidate   = tools/cc.sh -o /tmp/x.o VARIANT.c  (cc1+maspsx, no build ctx)
    verdict     = normalized mnemonic/operand diff + insn count vs 30

Normalization makes the two syntaxes comparable: o32 reg names -> numbers,
hex immediates -> decimal, subu/addiu canonicalized, spimdisasm address
comments stripped, LABELS REWRITTEN TO DEFINITION ORDINALS (branch targets
compare structurally, not by name).

Trust model (banked): the compile side reproduces offline; the live judge
still owns acceptance on return.

Usage: python3 scripts/bm_unit_decode/gmd_offline_screen.py [VARIANT.c ...]
       no args = screen every scripts/bm_unit_decode/gmd_v*.c
"""
import re
import subprocess
import sys
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RETAIL_S = os.path.join(REPO, "asm/g3org_jp/nonmatchings/func_80053528.s")
CC = os.path.join(REPO, "tools/cc.sh")

_REGNAMES = {
    "$zero": "$0", "$at": "$1", "$v0": "$2", "$v1": "$3",
    "$a0": "$4", "$a1": "$5", "$a2": "$6", "$a3": "$7",
    "$t0": "$8", "$t1": "$9", "$t2": "$10", "$t3": "$11",
    "$t4": "$12", "$t5": "$13", "$t6": "$14", "$t7": "$15",
    "$s0": "$16", "$s1": "$17", "$s2": "$18", "$s3": "$19",
    "$s4": "$20", "$s5": "$21", "$s6": "$22", "$s7": "$23",
    "$t8": "$24", "$t9": "$25", "$k0": "$26", "$k1": "$27",
    "$gp": "$28", "$sp": "$29", "$fp": "$30", "$s8": "$30", "$ra": "$31",
}

_LABELDEF = re.compile(r"^(\.L[0-9a-fA-F]+|\$L\d+)\s*:\s*$")
_LABELREF = re.compile(r"(?<![0-9a-zA-Z_])(\.L\S+|\$L\d+)\b")


def _base_norm(s):
    s = re.sub(r"-?0x[0-9a-fA-F]+", lambda m: str(int(m.group(0), 16)), s)
    for name, num in _REGNAMES.items():
        s = re.sub(re.escape(name) + r"\b", num, s)
    s = re.sub(r"\s+", "", s)
    s = s.lower()
    # macro spellings -> canonical single insns (identical encodings)
    s = re.sub(r"^bne(\$\d+),\$0,", r"bnez\1,", s)
    s = re.sub(r"^beq(\$\d+),\$0,", r"beqz\1,", s)
    s = re.sub(r"^move(\$\d+),(\$\d+)$", r"addu\1,\2,$0", s)
    # addu/subu rd,rs,imm assemble as addiu rd,rs,±imm (no imm form of addu)
    s = re.sub(r"^addu([^,]*,[^,]*),(-?\d+)$", r"addiu\1,\2", s)
    # j $reg assembles as jr $reg (gas macro; byte-proven: both -> 0x03e00008
    # for $31, tools-local binutils, banked cron-20261028-0118)
    s = re.sub(r"^j(\$\d+)$", r"jr\1", s)
    return s


def norm_insns(text):
    """-> [(kind, ...)] where kind 'l' = label def (ordinal), 'i' = insn str."""
    lines = []
    for raw in text.splitlines():
        if "/*" in raw and "*/" in raw:
            raw = raw.split("*/", 1)[1]  # spimdisasm: insn after the addr comment
        line = raw.split("#")[0].strip()
        if not line:
            continue
        if line.startswith(".") and not _LABELDEF.match(line):
            continue
        lines.append(line)
    # collect label definitions in order
    order = {}
    for line in lines:
        m = _LABELDEF.match(line)
        if m and m.group(1) not in order and not m.group(1).lower().startswith("gsmap"):
            order[m.group(1)] = len(order)
    out = []
    for line in lines:
        m = _LABELDEF.match(line)
        if m:
            out.append(("l", order[m.group(1)]))
            continue
        line = _LABELREF.sub(lambda m: "@%d@" % order.get(m.group(1), -1), line)
        line = line.rstrip(";").strip()
        if not line:
            continue
        s = _base_norm(line)
        # canonicalize subu/addiu with constant imm (s has no spaces now)
        m2 = re.match(r"(subu|addiu)([^,]*,[^,]*),(-?\d+)$", s)
        if m2:
            mn, ops, imm = m2.group(1), m2.group(2), int(m2.group(3))
            if mn == "subu" and imm > 0:
                s = "addiu%s,%d" % (ops, -imm)  # canonical: addiu + signed imm
        out.append(("i", s))
    return out


def parse_retail():
    with open(RETAIL_S) as f:
        text = f.read()
    body = text.split("glabel GsMapModelingData", 1)[1].split("endlabel", 1)[0]
    return norm_insns(body)


def compile_candidate(cfile, workdir="/tmp/gmd_screen"):
    os.makedirs(workdir, exist_ok=True)
    out_o = os.path.join(workdir, os.path.basename(cfile)[:-2] + ".o")
    env = dict(os.environ)
    env["LD_LIBRARY_PATH"] = ("/home/z/my-project/tools-local/mipsel-root"
                              "/usr/lib/x86_64-linux-gnu")
    r = subprocess.run(["sh", CC, "-o", out_o, cfile], cwd=REPO,
                       capture_output=True, text=True, env=env, timeout=120)
    base = out_o[:-2]
    for suf in (".r.s", ".mas.s", ".s"):
        p = base + suf
        if os.path.exists(p):
            return p, r
    return None, r


def parse_candidate(path):
    with open(path) as f:
        text = f.read()
    m = re.search(r"^GsMapModelingData:\s*$", text, re.M)
    if not m:
        return None
    body = text[m.end():]
    stop = re.search(r"^\.(end|size)\b", body, re.M)
    if stop:
        body = body[:stop.start()]
    return norm_insns(body)


def screen(cfile):
    ref = parse_retail()
    path, r = compile_candidate(cfile)
    if path is None:
        print("%s: COMPILE-FAIL\n%s" % (os.path.basename(cfile), r.stderr[-400:]))
        return
    got = parse_candidate(path)
    if got is None:
        print("%s: NO-LABEL in %s" % (os.path.basename(cfile), path))
        return
    n_ref = len([t for t in ref if t[0] == "i"])
    n_got = len([t for t in got if t[0] == "i"])
    if got == ref:
        print("%s: SHAPE-EXACT (%d insns; offline; live judge pending)"
              % (os.path.basename(cfile), n_got))
        return
    verdict = ["SIZE %d vs %d (%+d)" % (n_got, n_ref, n_got - n_ref)]
    first = None
    for i, (a, b) in enumerate(zip(got, ref)):
        if a != b:
            first = (i, a, b)
            break
    if first:
        i, a, b = first
        verdict.append("first diff @%d: got %r want %r" % (i, a, b))
    else:
        verdict.append("prefix equal, length differs")
    print("%s: %s" % (os.path.basename(cfile), "; ".join(verdict)))


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        import glob
        args = sorted(glob.glob(os.path.join(REPO, "scripts/bm_unit_decode/gmd_v*.c")))
    for c in args:
        screen(c)

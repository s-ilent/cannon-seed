#!/usr/bin/env python3
"""waveC8_screen.py - offline compile-side screen for the select_max_param
x8 wave (matching lane; oracle-independent).

waveE8E4_screen.py pattern, wave-adapted: the retail truth is the committed
listings' hex comment columns (byte-true because verify 8/8 GREEN assembles
them into the witnessed image), so BOTH halves of the proof run offline:
  shape   = normalized insn-text diff (debug aid)
  bytes   = the compiled .o's .text section vs the retail bytes (THE VERDICT)

    python3 scripts/waveC8_screen.py               # screen the template
    python3 scripts/waveC8_screen.py path/to/X.c   # screen a specific file

Exit 0 = all screened candidates BYTE-EXACT.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CC = REPO / "tools" / "cc.sh"
OBJCOPY = Path("/home/z/my-project/tools-local/mipsel-root/usr/bin/mipsel-linux-gnu-objcopy")
HEXCOL = re.compile(r"/\*\s*[0-9A-Fa-f]+\s+[0-9A-Fa-f]+\s+([0-9A-Fa-f]{8})\s*\*/")

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

# template stem -> (target, walk-name listing file); the glabel inside the
# listing is parsed dynamically (pinned-name listings carry the psyq name)
RETAIL = {
    "select_max_param": ("slps_00270", "func_80036D04"),
}


def listing_path(target, fn):
    if target == "slps_00270":
        return REPO / "asm" / "nonmatchings" / f"{fn}.s"
    return REPO / "asm" / target / "nonmatchings" / f"{fn}.s"


def parse_retail(fn):
    """-> (insn_texts, retail_bytes) between glabel/endlabel (glabel found
    dynamically - pinned listings carry select_max_param, walk-named ones
    carry the walk name)."""
    text = listing_path("slps_00270", fn).read_text()
    m = re.search(r"^glabel (\S+)", text, re.M)
    if not m:
        raise SystemExit(f"{fn}: no glabel in listing")
    label = m.group(1)
    body = text.split(f"glabel {label}", 1)[1].split("endlabel", 1)[0]
    insns, raw = [], []
    for ln in body.splitlines():
        hm = HEXCOL.search(ln)
        if not hm:
            continue
        raw.append(bytes.fromhex(hm.group(1)))
        t = ln.split("*/", 1)[1] if "*/" in ln else ln
        t = t.split("/*")[0].strip()
        insns.append(t)
    return label, insns, b"".join(raw)


def norm(t):
    s = t.split("#")[0].strip().lower()
    s = re.sub(r"-?0x[0-9a-fA-F]+", lambda m: str(int(m.group(0), 16)), s)
    for name, num in _REGNAMES.items():
        s = re.sub(re.escape(name) + r"\b", num, s)
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"^j(\$\d+)$", r"jr\1", s)
    if s.startswith("mvmva") or s.startswith(".word"):
        return ".word"
    return s


def compile_candidate(cfile, workdir="/tmp/waveC8"):
    os.makedirs(workdir, exist_ok=True)
    out_o = os.path.join(workdir, Path(cfile).stem + ".o")
    env = dict(os.environ)
    env["LD_LIBRARY_PATH"] = "/home/z/my-project/tools-local/mipsel-root/usr/lib/x86_64-linux-gnu"
    r = subprocess.run(["sh", str(CC), "-o", out_o, str(cfile)], cwd=str(REPO),
                       capture_output=True, text=True, env=env, timeout=180)
    return out_o, r


def parse_candidate_asm(out_o):
    base = out_o[:-2]
    for suf in (".r.s", ".mas.s", ".s"):
        p = base + suf
        if os.path.exists(p):
            return Path(p).read_text(), p
    return None, None


def candidate_insns(text, label):
    m = re.search(rf"^{label}:\s*$", text, re.M)
    if not m:
        return None
    body = text[m.end():]
    stop = re.search(r"^\.(end|size|section|ent|end)\b|^[A-Za-z_][A-Za-z0-9_]*:", body, re.M)
    if stop:
        body = body[: stop.start()]
    out = []
    for ln in body.splitlines():
        t = ln.split("#")[0].strip()
        if not t:
            continue
        if t.startswith(".") and not t.startswith(".word"):
            continue
        out.append(t)
    return out


def screen(cfile):
    name = Path(cfile).stem
    if name not in RETAIL:
        print(f"{name}: not a known template (want select_max_param)")
        return False
    target, fn = RETAIL[name]
    label, ref_insns, ref_bytes = parse_retail(fn)
    out_o, r = compile_candidate(cfile)
    if r.returncode != 0:
        print(f"{name}: COMPILE-FAIL\n{r.stderr[-600:]}")
        return False
    text, s_path = parse_candidate_asm(out_o)
    got = candidate_insns(text, name) if text else None
    if got is None:
        print(f"{name}: NO-LABEL ({s_path})")
        return False
    n_ref, n_got = len(ref_insns), len(got)
    shape_ok = [norm(x) for x in got] == [norm(x) for x in ref_insns]
    # byte verdict
    dump = out_o[:-2] + ".text"
    env2 = dict(os.environ)
    env2["LD_LIBRARY_PATH"] = "/home/z/my-project/tools-local/mipsel-root/usr/lib/x86_64-linux-gnu"
    subprocess.run([str(OBJCOPY), "--dump-section", f".text={dump}", out_o],
                   check=True, capture_output=True, env=env2)
    got_bytes = Path(dump).read_bytes()
    # the .o .text is 16-byte section-aligned (gas artifact): the FUNCTION
    # bytes are the ref-length prefix; a zero tail beyond that is padding and
    # never links (ld follows the splat script's per-row addresses - the
    # wave104 0x104 rows landed through the same alignment)
    tail = got_bytes[len(ref_bytes):]
    byte_ok = got_bytes[: len(ref_bytes)] == ref_bytes and (
        len(tail) == 0 or set(tail) <= {0}
    )
    first = None
    if not byte_ok:
        for i in range(min(len(got_bytes), len(ref_bytes))):
            if got_bytes[i] != ref_bytes[i]:
                first = (i // 4, got_bytes[i : i + 4].hex(), ref_bytes[i : i + 4].hex())
                break
    print(f"{name}: ref={n_ref} insns got={n_got} | shape={'OK' if shape_ok else 'DIFF'} "
          f"bytes={'EXACT' if byte_ok else 'DIFF'}")
    if first:
        print(f"  first byte diff: word {first[0]} got {first[1]} want {first[2]}")
    if not shape_ok:
        for i, (g, rf) in enumerate(zip(got, ref_insns)):
            if norm(g) != norm(rf):
                print(f"  insn {i}: got '{g}' want '{rf}'")
    return byte_ok


def main() -> int:
    argv = sys.argv[1:]
    if argv:
        files = argv
    else:
        files = [str(REPO / "scripts" / "waveC8" / "select_max_param.c")]
    ok = all(screen(f) for f in files)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""judge_unit.py - fast per-unit candidate screen for C matches.

  python3 tools/judge_unit.py TARGET [NAME ...]     # default: every c row

NAME is a splat-yaml `c` subsegment with src/<NAME>.c (multi-piece
`<base>.pN` units are rejected for now). Compiles the one unit through the
full build's own pipeline - cc.sh -S, tools/stage_c.py, mipsel-as with the
build's ASFLAGS - then mini-links it ALONE at its retail VA with the build's
two-pass undefined-symbol resolution (tools/undef_syms.py) and compares the
resulting section bytes against the retail baseline slice.

This is a CANDIDATE SCREEN for the match-edit loop (~2 s/unit vs a ~53 s
full build), not an oracle. It cannot see the rest of the image: a unit
that judges EXACT here can still fail `make verify` if another unit, an asm
row, or the link layout disagrees. Acceptance is always a whole-image
`make verify`; nothing here feeds ratchets or progress.

Exit codes: 0 = every judged unit EXACT, 1 = at least one unit not EXACT,
2 = usage/environment error.
Per-unit verdicts: EXACT / DIFF <n>/<total> words / SIZE <built> vs <row> /
NO-SOURCE / COMPILE-FAIL / STAGE-FAIL / AS-FAIL / LINK-FAIL / UNRESOLVED.
"""
import hashlib
import os
import re
import subprocess
import sys
import time

import yaml

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLROOT = os.environ.get("TOOLROOT", "/home/z/my-project/tools-local/mipsel-root")
PY = os.environ.get("PY", "python3")
AS = os.path.join(TOOLROOT, "usr/bin/mipsel-linux-gnu-as")
OBJCOPY = os.path.join(TOOLROOT, "usr/bin/mipsel-linux-gnu-objcopy")
LD = os.path.join(TOOLROOT, "usr/bin/mipsel-linux-gnu-ld")
BASE_VA = 0x80020000
HDR = 0x800
ASFLAGS_BASE = ["-march=mips64", "-mabi=32", "-EL", "-G0",
                "-I", "include", "-I", "asm/nonmatchings"]

try:
    import capstone
except ImportError:
    capstone = None


def run(cmd, **kw):
    # build.sh exports the binutils' private libdir for every child; as
    # links against a private libopcodes there.
    env = dict(os.environ, LD_LIBRARY_PATH=
               f"{TOOLROOT}/usr/lib/x86_64-linux-gnu")
    kw.setdefault("env", env)
    return subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, **kw)


def c_rows(target):
    """[(name, offset, extent)] for every c subsegment, in yaml order.

    Offsets are splat yaml file offsets (the 0x800 PS-X EXE header
    INCLUDED - build.sh's .r_<offset> convention). Extent runs to the next
    subsegment of ANY type, not the next c row.
    """
    cfg = yaml.safe_load(open(f"config/splat.{target}.yaml"))
    allsubs, cs = [], []
    for seg in cfg["segments"]:
        if isinstance(seg, dict) and seg.get("type") == "code":
            for e in seg.get("subsegments", []):
                if isinstance(e, list) and len(e) >= 2:
                    allsubs.append(e)
                    if len(e) >= 3 and e[1] == "c":
                        cs.append(e)
    out = []
    for e in cs:
        i = allsubs.index(e)
        end = allsubs[i + 1][0] if i + 1 < len(allsubs) else e[0] + 0x10
        out.append((e[2], e[0], end - e[0]))
    return out


def disasm(words, va):
    if capstone is None:
        return None
    md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32 |
                     capstone.CS_MODE_LITTLE_ENDIAN)
    line = next(md.disasm(words, va), None)
    return f"{line.mnemonic} {line.op_str}" if line else ""


def judge(target, name, rom, extent, gp_flags, asflags):
    """-> (verdict, detail_lines)"""
    work = f"build/judge/{name}"
    os.makedirs(os.path.join(REPO, "build/judge"), exist_ok=True)
    for stale in (f"{work}.o", f"{work}.mas.s", f"{work}.r.s", f"{work}.elf",
                  f"{work}.bin", f"{work}.ld", f"{work}.undef.ld", f"{work}.ld.err"):
        if os.path.exists(os.path.join(REPO, stale)):
            os.unlink(os.path.join(REPO, stale))
    if not os.path.exists(os.path.join(REPO, f"src/{name}.c")):
        return "NO-SOURCE", []
    t0 = time.time()
    r = run([f"{REPO}/tools/cc.sh", "-S", "-o", f"{work}.o", f"src/{name}.c"])
    if r.returncode:
        return "COMPILE-FAIL", ["  " + ln for ln in r.stderr.strip().splitlines()[-5:]]
    gp_rewrite, gp_info = gp_flags
    r = run([PY, "tools/stage_c.py", f"{work}.mas.s", f"{work}.r.s",
             f"{rom:X}", gp_rewrite, gp_info])
    if r.returncode:
        return "STAGE-FAIL", ["  " + ln for ln in r.stderr.strip().splitlines()[-5:]]
    r = run([AS] + asflags + ["-o", f"{work}.o", f"{work}.r.s"])
    if r.returncode:
        return "AS-FAIL", ["  " + ln for ln in r.stderr.strip().splitlines()[-5:]]

    va = BASE_VA + rom - HDR
    sec = f"r_{rom:X}"
    with open(os.path.join(REPO, f"{work}.ld"), "w") as f:
        f.write("SECTIONS {\n")
        if gp_rewrite == "1":
            f.write(f"  _gp = 0x{int(gp_info.split()[0], 16):X};\n")
        f.write(f"  . = 0x{va:X};\n  .{sec} : {{ *(.{sec}) }}\n}}\n")
    # Real placements for every known symbol, as a prelude to BOTH link
    # passes. Judged alone, the unit lacks the objects that define its
    # neighbours in the full build (witnessed: func_8002C478's extern
    # state_block_N jump-target data, defined by a data row's labels in the
    # full link); left undefined, the two-pass fallback would resolve the
    # suffix-shaped ones at their suffix (state_block_0 -> 0x0) instead of
    # the retail placement. Script assignments cannot override object
    # definitions, so this only fills genuinely external references.
    with open(os.path.join(REPO, f"{work}.pre.ld"), "w") as f:
        for ln in open(os.path.join(REPO, f"config/symbols.{target}.txt")):
            m = re.match(r"^(\w+) = 0x([0-9A-Fa-f]+);", ln)
            if m:
                f.write(f"{m.group(1)} = 0x{m.group(2)};\n")
    r = run([LD, "-N", "-T", f"{work}.ld", "-T", f"{work}.pre.ld",
             "--no-check-sections", "-o", f"{work}.elf", f"{work}.o"])
    err = r.stderr
    if "undefined reference" in err:
        with open(os.path.join(REPO, f"{work}.ld.err"), "w") as f:
            f.write(err)
        r2 = run([PY, "tools/undef_syms.py", target, f"{work}.ld.err"])
        if r2.returncode:
            return "UNRESOLVED", ["  " + ln for ln in r2.stderr.strip().splitlines()]
        with open(os.path.join(REPO, f"{work}.undef.ld"), "w") as f:
            f.write(r2.stdout)
        r = run([LD, "-N", "-T", f"{work}.ld", "-T", f"{work}.pre.ld",
                 "-T", f"{work}.undef.ld", "--no-check-sections",
                 "-o", f"{work}.elf", f"{work}.o"])
        err = r.stderr
    if r.returncode or "undefined reference" in err:
        return "LINK-FAIL", ["  " + ln for ln in err.strip().splitlines()[-5:]]
    r = run([OBJCOPY, "-O", "binary", "--only-section", f".{sec}",
             f"{work}.elf", f"{work}.bin"])
    built = open(os.path.join(REPO, f"{work}.bin"), "rb").read()
    base = open(os.path.join(REPO, f"baselines/{target}.bin"), "rb")
    base.seek(rom)
    retail = base.read(extent)
    size_note = None
    if len(built) != extent:
        size_note = f"SIZE built {len(built)} vs row {extent}"
    n = min(len(built), len(retail))
    bad = [(i, built[i:i + 4], retail[i:i + 4])
           for i in range(0, n, 4) if built[i:i + 4] != retail[i:i + 4]]
    if not bad and size_note is None:
        return f"EXACT ({extent} bytes, {time.time() - t0:.1f}s)", []
    verdict = size_note or "DIFF"
    if bad:
        verdict = (f"{verdict}; " if size_note else "") + \
            f"DIFF {len(bad)}/{n // 4} words"
    detail = ["  first diffs (built vs retail):"]
    for i, bw, rw in bad[:8]:
        va_i = va + i
        txt = disasm(bw, va_i)
        suffix = f"  {txt}" if txt else ""
        detail.append(f"  0x{va_i:08X}  {bw.hex().upper()}  {rw.hex().upper()}{suffix}")
    if len(bad) > 8:
        detail.append(f"  ... {len(bad) - 8} more")
    return verdict, detail


def baseline_gate(target):
    """Refuse to judge unless the local baseline IS the committed oracle.

    The judge's expected bytes are a slice of baselines/<target>.bin at the
    row's yaml offset. Post-flip (de0b0d68) the committed config/sha1/<t>.sha1
    values are the TRUE baselines' hashes, while a sandbox holding the
    all-woven set (or any other re-extraction) slices garbage here: witnessed
    2026-10-19 as judge 0/33 EXACT on sces_00269, a target whose whole image
    had verified EXACT. A different hash is a different build - never compare
    against it. Mirrors verify.sh's gate 2.
    """
    path = os.path.join(REPO, f"baselines/{target}.bin")
    if not os.path.exists(path):
        print(f"judge: no baseline at baselines/{target}.bin", file=sys.stderr)
        return False
    sha_file = os.path.join(REPO, f"config/sha1/{target}.sha1")
    expected = None
    for ln in open(sha_file):
        ln = ln.strip()
        if ln and not ln.startswith("#"):
            expected = ln.split()[0].lower()
            break
    actual = hashlib.sha1(open(path, "rb").read()).hexdigest()
    if expected != actual:
        print(f"judge: baselines/{target}.bin does not match the committed "
              f"oracle config/sha1/{target}.sha1", file=sys.stderr)
        print(f"  expected sha1: {expected}", file=sys.stderr)
        print(f"  actual   sha1: {actual}", file=sys.stderr)
        print("A different hash is a different build - the retail slice this "
              "judge compares against is not in the building (woven set in "
              "the disc-blocked sandbox; the true baselines return with the "
              "discs). Never edit the sha1 file to pass.", file=sys.stderr)
        return False
    return True


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    target = argv[1]
    if not baseline_gate(target):
        return 2
    rows = c_rows(target)
    names = argv[2:]
    if names:
        known = {n: (n, r, x) for n, r, x in rows}
        want = []
        for n in names:
            m = re.match(r"^([A-Za-z_]\w*)\.p\d+$", n)
            if m or any(row[0].startswith(n + ".p") for row in rows):
                print(f"{n}: multi-piece unit not supported yet", file=sys.stderr)
                return 2
            if n not in known:
                print(f"{n}: no c row in config/splat.{target}.yaml", file=sys.stderr)
                return 2
            want.append(known[n])
    else:
        want = rows
    r = run([PY, "tools/gp_flags.py", "rewrite", target])
    gp_rewrite = r.stdout.strip()
    r = run([PY, "tools/gp_flags.py", "info", target])
    gp_info = r.stdout.strip()
    cfg = yaml.safe_load(open(f"config/splat.{target}.yaml"))
    asm_path = cfg["options"]["asm_path"].rstrip("/")
    asflags = ASFLAGS_BASE + ["-I", asm_path]

    ok = 0
    for name, rom, extent in want:
        verdict, detail = judge(target, name, rom, extent, (gp_rewrite, gp_info),
                                asflags)
        print(f"{name}: {verdict}")
        for ln in detail:
            print(ln)
        if verdict.startswith("EXACT"):
            ok += 1
    print(f"judge: {ok}/{len(want)} EXACT ({target})")
    return 0 if ok == len(want) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))

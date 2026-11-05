#!/usr/bin/env python3
"""minilink.py - the offline SIZE half of judge_unit.py (no oracle needed).

  python3 tools/minilink.py TARGET NAME [SRCPATH] [ROM_HEX]

Compiles one unit through the full build's own pipeline (cc.sh -S with the
unit's maspsx_flags.txt flags, stage_c.py, mipsel-as with the build's
ASFLAGS), then mini-links it ALONE at its retail VA with the build's
two-pass undefined-symbol resolution (tools/undef_syms.py) and prints the
linked .r_<rom> section size. This is the judge's SIZE law reproduced
without baselines/gate: THE TRUE LIVE-SIZE LAW (runbook H.1, banked
cron-202611050728, validated draft1 904 = judged 904; draft20 knob-alive
1096 = judged 1096 = THE ROW; re-validated cron-202611051228 first-pass:
draft46 1104 / draft47 1140).

ROM_HEX: probe drafts park the row as asm until the landing (H.2 step 2
flips it); pass the row's yaml offset in hex to judge those pre-landing.

Written cron-202611051228, lost to the fifteenth rollback uncommitted,
re-written verbatim cron-202611051343 and COMMITTED so it survives. The
reconstruction notes it banks:
  - build/judge/ must exist before cc.sh runs (the cpp step needs it);
  - the binutils root feeds as/ld/objcopy LD_LIBRARY_PATH but is NOT
    exported to cc.sh;
  - the symbols prelude regex strips the `// type:func` tails exactly as
    judge_unit.py's regex does;
  - the ASFLAGS carry the yaml's asm_path as a fourth -I;
  - objcopy --only-section needs the DOT-PREFIXED section name (.r_48864) -
    a bare name exits 0 with an EMPTY binary (hit live cron-202611051228).

Exit codes: 0 = linked (size printed), 1 = link failure, 2 = usage/env.
"""
import os
import re
import subprocess
import sys

import yaml

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLROOT = os.environ.get("TOOLROOT", "/home/z/my-project/tools-local/mipsel-root")
AS = os.path.join(TOOLROOT, "usr/bin/mipsel-linux-gnu-as")
OBJCOPY = os.path.join(TOOLROOT, "usr/bin/mipsel-linux-gnu-objcopy")
LD = os.path.join(TOOLROOT, "usr/bin/mipsel-linux-gnu-ld")
BASE_VA = 0x80020000
HDR = 0x800
ASFLAGS_BASE = ["-march=mips64", "-mabi=32", "-EL", "-G0",
                "-I", "include", "-I", "asm/nonmatchings"]


def run(cmd, **kw):
    env = dict(os.environ, LD_LIBRARY_PATH=
               f"{TOOLROOT}/usr/lib/x86_64-linux-gnu")
    kw.setdefault("env", env)
    return subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, **kw)


def maspsx_unit_flags(target, name):
    path = os.path.join(REPO, "tools", "maspsx_flags.txt")
    if not os.path.exists(path):
        return ""
    tgt_flags = unit_flags = ""
    for ln in open(path):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        fields = ln.split(None, 1)
        head = fields[0]
        rest = fields[1] if len(fields) > 1 else ""
        if head == f"target:{target}":
            tgt_flags = rest
        elif head == f"unit:{name}":
            unit_flags = rest
    return unit_flags or tgt_flags


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    target, name = argv[1], argv[2]
    csrc = argv[3] if len(argv) > 3 else f"src/{name}.c"
    if not os.path.exists(os.path.join(REPO, csrc)):
        print(f"minilink: no source at {csrc}", file=sys.stderr)
        return 2
    rom_override = int(argv[4], 16) if len(argv) > 4 else None

    rom = None
    asm_path = "asm"
    for seg in yaml.safe_load(open(f"config/splat.{target}.yaml"))["segments"]:
        if isinstance(seg, dict) and seg.get("type") == "code":
            asm_path = seg.get("asm_path", asm_path).rstrip("/")
            for e in seg.get("subsegments", []):
                if isinstance(e, list) and len(e) >= 3 and e[1] == "c" \
                        and e[2] == name:
                    rom = e[0]
    if rom is None:
        rom = rom_override
    if rom is None:
        print(f"minilink: no c row for {name} in config/splat.{target}.yaml",
              file=sys.stderr)
        return 2
    va = BASE_VA + rom - HDR
    sec = f"r_{rom:X}"
    work = f"build/judge/{name}"
    os.makedirs(os.path.join(REPO, "build/judge"), exist_ok=True)

    env = dict(os.environ)
    flags = maspsx_unit_flags(target, name)
    if flags:
        env["MASPSX_UNIT_FLAGS"] = flags
    r = run([f"{REPO}/tools/cc.sh", "-S", "-o", f"{work}.o", csrc], env=env)
    if r.returncode:
        print("COMPILE-FAIL:\n" + "\n".join(r.stderr.splitlines()[-5:]),
              file=sys.stderr)
        return 1
    r = run(["python3", "tools/stage_c.py", f"{work}.mas.s", f"{work}.r.s",
             f"{rom:X}", "0", ""])
    if r.returncode:
        print("STAGE-FAIL:\n" + "\n".join(r.stderr.splitlines()[-5:]),
              file=sys.stderr)
        return 1
    asflags = ASFLAGS_BASE + ["-I", asm_path]
    r = run([AS] + asflags + ["-o", f"{work}.o", f"{work}.r.s"])
    if r.returncode:
        print("AS-FAIL:\n" + "\n".join(r.stderr.splitlines()[-5:]),
              file=sys.stderr)
        return 1

    with open(os.path.join(REPO, f"{work}.ld"), "w") as f:
        f.write("SECTIONS {\n")
        f.write(f"  . = 0x{va:X};\n  .{sec} : {{ *(.{sec}) }}\n}}\n")
    with open(os.path.join(REPO, f"{work}.pre.ld"), "w") as f:
        for ln in open(os.path.join(REPO, f"config/symbols.{target}.txt")):
            m = re.match(r"^(\w+) = 0x([0-9A-Fa-f]+);", ln)
            if m:
                f.write(f"{m.group(1)} = 0x{m.group(2)};\n")
        cur_target = None
        for ln in open(os.path.join(REPO, "config/symbols.curated.txt")):
            h = re.match(r"^// target: (\S+)", ln)
            if h:
                cur_target = h.group(1)
                continue
            if cur_target != target:
                continue
            m = re.match(r"^(\w+) = 0x([0-9A-Fa-f]+);", ln)
            if m:
                f.write(f"{m.group(1)} = 0x{m.group(2)};\n")

    ld_cmd = [LD, "-N", "-T", f"{work}.ld", "-T", f"{work}.pre.ld",
              "--no-check-sections", "-o", f"{work}.elf", f"{work}.o"]
    r = run(ld_cmd)
    if "undefined reference" in r.stderr:
        with open(os.path.join(REPO, f"{work}.ld.err"), "w") as f:
            f.write(r.stderr)
        r2 = run(["python3", "tools/undef_syms.py", target, f"{work}.ld.err"])
        if r2.returncode:
            print("UNRESOLVED:\n" +
                  "\n".join(r2.stderr.splitlines()[-5:]), file=sys.stderr)
            return 1
        with open(os.path.join(REPO, f"{work}.undef.ld"), "w") as f:
            f.write(r2.stdout)
        r = run(ld_cmd + ["-T", f"{work}.undef.ld"])
    if r.returncode or "undefined reference" in r.stderr:
        print("LINK-FAIL:\n" + "\n".join(r.stderr.splitlines()[-5:]),
              file=sys.stderr)
        return 1
    r = run([OBJCOPY, "-O", "binary", "--only-section", f".{sec}",
             f"{work}.elf", f"{work}.bin"])
    if r.returncode:
        print("OBJCOPY-FAIL:\n" + "\n".join(r.stderr.splitlines()[-5:]),
              file=sys.stderr)
        return 1
    size = os.path.getsize(os.path.join(REPO, f"{work}.bin"))
    print(f"{name}: linked {size} bytes (VA 0x{va:X}, section .{sec})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

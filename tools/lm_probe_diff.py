#!/usr/bin/env python3
"""GsSetLightMode offline probe diff (tools/lm_probe_diff.py).

Compiles a probe .c through the pinned toolchain (tools/cc.sh: cc1
2.6.3 under qemu -> maspsx -> cc_post -> mipsel as), disassembles the
relocatable object, and compares its instruction words slot-by-slot
against the retail words of one reference target's stale nonmatching
.s. Relocation-carrying fields are masked (j/jal 26-bit targets, %hi/
%lo 16-bit immediates) so the comparison checks SHAPE, not addresses;
every non-relocated field (register assignments, branch displacements,
immediate constants) must match exactly.

Window cron-20261020-0957 ran this comparison from repo-external
scratch (scripts/lm_probe_diff.py, eaten by the fifteenth rollback);
this is the in-repo re-bank. The 34/35 result and the one open item
(retail's entry addu $a1,$a0,$zero) are recorded in the probe draft's
prose.

Usage:
    python3 tools/lm_probe_diff.py probes/gcc263/GsSetLightMode.c \
        [asm/g3org_jp/nonmatchings/func_80063FD4.s] [funcname]

Exit 0 = all slots match, 1 = mismatches, 2 = tool failure.
"""
import os
import re
import subprocess
import sys

REPO = __file__.rsplit("/tools/", 1)[0]
LINE = re.compile(r"/\*\s*[0-9A-Fa-f]+\s+[0-9A-Fa-f]{8}\s+([0-9A-Fa-f]{8})\s*\*/")
TOOLROOT = os.environ.get("TOOLROOT", "/home/z/my-project/tools-local")
OBJDUMP = f"{TOOLROOT}/mipsel-root/usr/bin/mipsel-linux-gnu-objdump"
# the mipsel binutils ship private libopcodes/libbfd copies (same env as
# tools/cc.sh sets for `as`)
os.environ["LD_LIBRARY_PATH"] = (
    f"{TOOLROOT}/mipsel-root/usr/lib/x86_64-linux-gnu"
    + (":" + os.environ["LD_LIBRARY_PATH"] if os.environ.get("LD_LIBRARY_PATH") else "")
)


def ref_words(path):
    out = []
    for ln in open(f"{REPO}/{path}"):
        m = LINE.search(ln)
        if m:
            out.append(int.from_bytes(bytes.fromhex(m.group(1)), "little"))
    return out


def obj_words(obj, funcname):
    """(words, masks) from objdump -d; masks from objdump -r relocations."""
    d = subprocess.run([OBJDUMP, "-d", obj], capture_output=True, text=True, check=True).stdout
    words = []
    in_func = False
    for ln in d.splitlines():
        m = re.match(r"^[0-9a-f]+ <(.+)>:$", ln)
        if m:
            in_func = m.group(1) == funcname
            continue
        if not in_func:
            continue
        m = re.match(r"^\s*[0-9a-f]+:\s+([0-9a-f]{8})\s", ln)
        if m:
            words.append(int(m.group(1), 16))
    if not words:
        print(f"FATAL: no words for <{funcname}> in {obj}")
        sys.exit(2)

    # gas pads the default .text section to a 16-byte boundary with zero
    # words (see tools/cc.sh header - build.sh works around it with a
    # fresh section name). Trim the padding: keep everything up to the
    # last non-zero word plus exactly one word (the jr's delay-slot nop).
    last = max(i for i, w in enumerate(words) if w != 0)
    while len(words) > last + 2 and words[-1] == 0:
        words.pop()

    masks = [0xFFFFFFFF] * len(words)
    r = subprocess.run([OBJDUMP, "-r", obj], capture_output=True, text=True, check=True).stdout
    cur_off = None
    for ln in r.splitlines():
        m = re.match(r"^([0-9a-f]+)\s+(\S+)\s+(\S+)", ln.strip() and ln or "")
        # objdump -r lines: "OFFSET  TYPE  SYMBOL" under section headers
        m = re.match(r"^([0-9a-f]{8})\s+([A-Z0-9_]+)\s+", ln)
        if not m:
            continue
        off = int(m.group(1), 16) // 4
        typ = m.group(2)
        if off >= len(masks):
            continue
        if typ in ("R_MIPS_26", "R_MIPS_JALR"):
            masks[off] &= 0xFC000000
        elif typ.startswith("R_MIPS_16") or typ in ("R_MIPS_HI16", "R_MIPS_LO16",
                                                     "R_MIPS_GPREL16", "R_MIPS_GOT16",
                                                     "R_MIPS_CALL16", "R_MIPS_GPREL32"):
            masks[off] &= 0xFFFF0000
    return words, masks


def main():
    probe = sys.argv[1]
    ref = sys.argv[2] if len(sys.argv) > 2 else "asm/g3org_jp/nonmatchings/func_80063FD4.s"
    func = sys.argv[3] if len(sys.argv) > 3 else "GsSetLightMode"

    obj = f"{REPO}/build/probe/lm_probe.o"
    subprocess.run(["sh", f"{REPO}/tools/cc.sh", "-o", obj, probe],
                   cwd=REPO, check=True)

    rw = ref_words(ref)
    cw, masks = obj_words(obj, func)
    if len(cw) != len(rw):
        print(f"WORD COUNT differs: retail {len(rw)}, probe {len(cw)}")
        for i in range(max(len(rw), len(cw))):
            r = f"{rw[i]:08x}" if i < len(rw) else "--------"
            c = f"{cw[i]:08x}" if i < len(cw) else "--------"
            mk = f"{masks[i]:08x}" if i < len(masks) else "--------"
            mark = "" if (i < len(rw) and i < len(cw) and (cw[i] & masks[i]) == (rw[i] & masks[i])) else "  <<"
            print(f"  slot {i:2d} retail {r} probe {c} mask {mk}{mark}")
        return 1

    bad = 0
    for i, (rv, cv, mk) in enumerate(zip(rw, cw, masks)):
        if (cv & mk) != (rv & mk):
            bad += 1
            print(f"  slot {i:2d} MISMATCH retail {rv:08x} probe {cv:08x} mask {mk:08x}")
        else:
            print(f"  slot {i:2d} ok       retail {rv:08x} probe {cv:08x} mask {mk:08x}")
    n = len(rw)
    print(f"{n - bad}/{n} slots match ({func} vs {ref})")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

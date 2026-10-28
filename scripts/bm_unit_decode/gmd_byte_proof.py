#!/usr/bin/env python3
"""gmd_byte_proof.py - the banked BYTE-exact proof for the GsMapModelingData
leader (matching lane; oracle-independent).

The offline screen (gmd_offline_screen.py) certifies SHAPE (normalized
mnemonics/operands/label ordinals).  This tool upgrades the proof to BYTES,
reproducing the cron-20261028-0118 finding as a one-command artifact:

    candidate .c --cc.sh--> .o --objcopy--> .text bytes
    reference               = the committed listing's word column
                              (asm/g3org_jp/nonmatchings/func_80053528.s,
                               30 words, byte-true because verify 8/8 GREEN
                               assembled it into the witnessed image)

The listing's word column is the big-endian image of the instruction word;
the repo's mipsel as -EL emits the little-endian image of the same encoding,
so both sides compare as u32 values after LE-unpacking (bytes.fromhex(col)
then struct '<I').

The assembler pads the default .text section to 16 bytes on MIPS, so the
candidate words are read from the section START and only the first 0x78
bytes (30 words) are compared; a trailing-pad mismatch is not a diff.

Usage:  python3 scripts/bm_unit_decode/gmd_byte_proof.py [VARIANT.c ...]
        no args = prove gmd_v14.c and gmd_v15.c (the banked leaders)

Exit 0 = all variants byte-exact; 1 = any diff; 2 = setup error.
"""
import os
import re
import struct
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REF_S = os.path.join(REPO, "asm/g3org_jp/nonmatchings/func_80053528.s")
CC = os.path.join(REPO, "tools/cc.sh")
OBJCOPY = ("/home/z/my-project/tools-local/mipsel-root/usr/bin/"
           "mipsel-linux-gnu-objcopy")
WORKDIR = "/tmp/gmd_byte_proof"
N_BYTES = 0x78
DEFAULT_VARIANTS = ["scripts/bm_unit_decode/gmd_v14.c",
                    "scripts/bm_unit_decode/gmd_v15.c"]

_WORD = re.compile(r"/\*\s+[0-9A-Fa-f]+\s+[0-9A-Fa-f]+\s+([0-9A-Fa-f]{8})\s*\*/")


def tool_env():
    env = dict(os.environ)
    env["LD_LIBRARY_PATH"] = ("/home/z/my-project/tools-local/mipsel-root"
                              "/usr/lib/x86_64-linux-gnu")
    return env


def ref_words():
    out = []
    with open(REF_S) as fh:
        for line in fh:
            m = _WORD.search(line)
            if m:
                out.append(struct.unpack("<I", bytes.fromhex(m.group(1)))[0])
    return out


def compile_obj(cfile):
    os.makedirs(WORKDIR, exist_ok=True)
    base = os.path.basename(cfile)[:-2]
    out_o = os.path.join(WORKDIR, base + ".o")
    env = tool_env()
    r = subprocess.run(["sh", CC, "-o", out_o, cfile], cwd=REPO,
                       capture_output=True, text=True, env=env, timeout=180)
    if r.returncode != 0 or not os.path.exists(out_o):
        print("COMPILE FAIL %s\n%s%s" % (cfile, r.stdout, r.stderr))
        return None
    return out_o


def text_words(out_o):
    binp = out_o[:-2] + ".text.bin"
    subprocess.run([OBJCOPY, "-O", "binary", "--only-section=.text",
                    out_o, binp], check=True, env=tool_env(),
                   capture_output=True, text=True)
    with open(binp, "rb") as fh:
        data = fh.read()
    os.unlink(binp)
    n = N_BYTES // 4
    if len(data) < N_BYTES:
        return None
    return list(struct.unpack("<%dI" % n, data[:N_BYTES]))


def main(argv):
    variants = argv[1:] or DEFAULT_VARIANTS
    ref = ref_words()
    print("reference: %s (%d words)" % (os.path.relpath(REF_S, REPO), len(ref)))
    rc = 0
    for v in variants:
        cfile = v if os.path.isabs(v) else os.path.join(REPO, v)
        out_o = compile_obj(cfile)
        if out_o is None:
            rc = 2
            continue
        w = text_words(out_o)
        if w is None:
            print("%s: .text too small (<0x%x bytes)" % (v, N_BYTES))
            rc = 1
            continue
        diffs = [(i, a, b) for i, (a, b) in enumerate(zip(w, ref)) if a != b]
        if not diffs:
            print("%s: BYTE-EXACT (first 0x78 bytes = retail words 30/30)"
                  % v)
        else:
            print("%s: %d/%d WORD DIFFS" % (v, len(diffs), len(ref)))
            for i, a, b in diffs[:10]:
                print("   insn %2d: got %08x want %08x" % (i, a, b))
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))

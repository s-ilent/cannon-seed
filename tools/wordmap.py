#!/usr/bin/env python3
"""wordmap.py - the in-repo judge-slice word map.

Window cron-202611062231 derived the func_8007736C 122-word class map with
a scripts-repo-external tool that died with the sandbox rollbacks; the
cc_post rule-class survey (docs/CC_POST_RULE_CLASSES.md, section 6) pins
the method in-repo instead. After a `tools/judge_unit.py <target> <name>`
run has produced build/judge/<name>.bin (the unit's built bytes), this
tool maps EVERY differing word against the baselines/<target>.bin slice at
the row's yaml extent, tags each diff with a coarse field class, and
prints the index/VA/hex/disasm table that the rule implementations derive
their site lists from.

The tags (per differing word, both words decoded little-endian):
  same-op-imm    opcode (+funct) equal, register fields equal, the
                 immediate/displacement/branch-offset field differs
                 (the class-A displacement cascade lives here)
  same-op-reg    opcode (+funct) equal, register fields differ
                 (the [61]-[62] compare retarget, the walk i-home
                 reg-field sites, the class-D list)
  same-op-mixed  opcode (+funct) equal, both register and immediate
                 fields differ
  same-op-target j/jal with only the target field differing
  funct          opcode 0 with a different funct field
  opcode         different major opcode (a shape change)

Read-only: never builds, never stages, never writes unless --out is given.
The baseline gate mirrors the judge's (baseline_gate): a woven or
otherwise non-oracle baseline is refused - a different hash is a different
build, never compare against it.

Usage:
  python3 tools/wordmap.py <target> <name> [--limit N] [--out FILE]

Exit codes: 0 = mapped (or identical), 1 = differences found (the map is
the product, the exit mirrors judge_unit's convention), 2 = usage or
environment error (missing judge artifacts, refused baseline, no such row).
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import judge_unit  # noqa: E402  (REPO, BASE_VA, HDR, c_rows, disasm, baseline_gate)


def classify(b: bytes, r: bytes) -> str:
    """Coarse field class for one differing word pair."""
    w1 = int.from_bytes(b, "little")
    w2 = int.from_bytes(r, "little")
    o1, o2 = w1 >> 26, w2 >> 26
    if o1 != o2:
        return "opcode"
    if o1 in (2, 3):  # j / jal
        return ("same-op-target"
                if (w1 & 0x3FFFFFF) != (w2 & 0x3FFFFFF) else "same-op")
    if o1 == 0:  # SPECIAL: funct + rd/rt/rs/shamt
        if (w1 & 0x3F) != (w2 & 0x3F):
            return "funct"
        return "same-op-reg" if (w1 >> 6) != (w2 >> 6) else "same-op"
    # I-type: register fields are bits 25..16, the imm/disp/offset is 15..0
    regs1, regs2 = (w1 >> 16) & 0xFFFF, (w2 >> 16) & 0xFFFF
    imm1, imm2 = w1 & 0xFFFF, w2 & 0xFFFF
    if regs1 == regs2:
        return "same-op-imm" if imm1 != imm2 else "same-op"
    return "same-op-reg" if imm1 == imm2 else "same-op-mixed"


def word_pairs(built: bytes, retail: bytes):
    """[(index, built_word, retail_word)] - the judge's own diff loop,
    untruncated (judge_unit prints only the first 8)."""
    n = min(len(built), len(retail))
    return [(i, built[i:i + 4], retail[i:i + 4])
            for i in range(0, n, 4) if built[i:i + 4] != retail[i:i + 4]]


def va_of(rom: int, index: int) -> int:
    return judge_unit.BASE_VA + rom - judge_unit.HDR + index


def main(argv) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("target")
    ap.add_argument("name")
    ap.add_argument("--limit", type=int, default=None,
                    help="print only the first N diff lines")
    ap.add_argument("--out", default=None,
                    help="also write the full map to this file")
    args = ap.parse_args(argv)

    rows = {n: (n, rom, ext) for n, rom, ext in judge_unit.c_rows(args.target)}
    if args.name not in rows:
        print(f"wordmap: no c row {args.name} in config/splat.{args.target}.yaml - "
              f"the row is asm at rest; stage the judge pipeline first "
              f"(yaml row asm->c + the probe copy), then judge_unit, then this tool",
              file=sys.stderr)
        return 2
    _, rom, extent = rows[args.name]

    if not judge_unit.baseline_gate(args.target):
        return 2
    binpath = os.path.join(judge_unit.REPO, f"build/judge/{args.name}.bin")
    if not os.path.exists(binpath):
        print(f"wordmap: no judge artifact at build/judge/{args.name}.bin - "
              f"run tools/judge_unit.py {args.target} {args.name} first "
              f"(verdicts live-only)", file=sys.stderr)
        return 2
    built = open(binpath, "rb").read()
    with open(os.path.join(judge_unit.REPO,
                           f"baselines/{args.target}.bin"), "rb") as base:
        base.seek(rom)
        retail = base.read(extent)

    lines = []
    if len(built) != extent:
        lines.append(f"SIZE built {len(built)} vs row {extent}")
    pairs = word_pairs(built, retail)
    lines.append(f"wordmap {args.target} {args.name}: "
                 f"{len(pairs)}/{min(len(built), len(retail)) // 4} words differ")
    tags: dict[str, list[int]] = {}
    for i, bw, rw in pairs:
        tag = classify(bw, rw)
        tags.setdefault(tag, []).append(i)
        va = va_of(rom, i)
        txt_b = judge_unit.disasm(bw, va)
        txt_r = judge_unit.disasm(rw, va)
        lines.append(f"idx={i} 0x{va:08X} built={bw.hex().upper()} "
                     f"retail={rw.hex().upper()} {tag}")
        if txt_b or txt_r:
            lines.append(f"          built: {txt_b or '-'}")
            lines.append(f"          retail: {txt_r or '-'}")
    lines.append("class summary: " + ", ".join(
        f"{t}={len(v)}" for t, v in sorted(tags.items())) or "none")
    for t, v in sorted(tags.items()):
        lines.append(f"  {t}: {' '.join(str(i) for i in v)}")

    text = "\n".join(lines) + "\n"
    if args.out:
        with open(args.out, "w") as f:
            f.write(text)
    shown = text.splitlines(keepends=True)
    if args.limit is not None:
        head = [ln for ln in shown[:2]]
        body = [ln for ln in shown[2:] if not ln.startswith("  ")]
        tail = [ln for ln in shown[2:] if ln.startswith("  ")]
        shown = head + body[:args.limit] + ["...\n"] + tail
    sys.stdout.write("".join(shown))
    return 1 if pairs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

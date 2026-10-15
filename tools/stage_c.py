#!/usr/bin/env python3
"""stage_c.py - stage one cc.sh -S product for assembling into the image.

  python3 tools/stage_c.py <in.mas.s> <out.s> <SEC-HEX> <gp_rewrite 0|1> "<gp_info>"

Extracted verbatim from tools/build.sh's PYSEC heredoc so the unit judge
(tools/judge_unit.py) stages exactly what the full build stages.

Renames `.text` to `.r_<SEC>` (gas pads the default .text to 16 bytes on
MIPS; custom sections are immune, and gen_ld.py links one .r_<rom> per
subsegment). With gp_rewrite=1 (boot targets), rewrites cc1's bare-symbol
load/store operands to the explicit %gp_rel form when the symbol is known
and within +/-0x7FFF of the gp base; `!`-suffixed names in <gp_info> are
curated gp:absolute evidence and keep the absolute form. Targets without a
gp base keep the bare form, which -G0 as expands to the absolute lui/$at
pair their retail shows.
"""
import re
import sys


def main(argv):
    src, dst, sec, gp_rewrite, gp_info = argv[1], argv[2], argv[3], argv[4], argv[5]
    text = open(src).read()
    text = re.sub(r"^\s*\.text\s*$",
                  f'.section .r_{sec}, "awx", @progbits', text, flags=re.M)
    # Small-data rewrite, gp targets only (GP_REWRITE=1: yaml options.gp_value
    # exists, _gp is in the linker script): cc1 -G8 emits bare-symbol memory
    # operands for gp-relative globals (aspsx would relax them via .extern
    # size + -G). maspsx only registers .comm/.sdata symbols, so
    # extern-referenced globals pass through bare - GNU as would emit
    # HI16/LO16 (absolute), which does NOT round-trip when retail used
    # gp-relative form. Convert to the explicit form; the linker resolves
    # GPREL16 against _gp. Targets WITHOUT a gp base (GP_REWRITE=0) keep the
    # bare form; with -G0 gas expands it to the absolute lui/$at pair that
    # those targets' retail shows.
    if gp_rewrite == "1":
        gp_base_str, _, tbl = gp_info.partition(" ")
        gp_base = int(gp_base_str, 16)
        symaddr = {}
        gp_abs = set()
        for tok in tbl.split():
            n, _, a = tok.rpartition(":")
            if not n:
                continue
            if n.endswith("!"):
                # curated gp:absolute marker (splat absolute:true): retail
                # provably loads this datum absolutely; never rewrite it.
                gp_abs.add(n[:-1])
                n = n[:-1]
            symaddr[n] = int(a, 16)

        def gp_rewrite_one(m):
            name = m.group(2)
            base_name = name.split("+", 1)[0]
            if base_name in gp_abs:
                return m.group(0)
            a = symaddr.get(base_name)
            if a is None or abs(a - gp_base) <= 0x7FFF:
                return f"{m.group(1)}%gp_rel({name})($gp)"
            return m.group(0)

        text = re.sub(
            r"(?m)^(\s*(?:lb|lbu|lh|lhu|lw|lwl|lwr|sb|sh|sw|swl|swr)\s+\$[a-z0-9]+,)"
            r"([A-Za-z_][A-Za-z0-9_]*(?:\+[0-9]+)?)\s*$",
            gp_rewrite_one,
            text,
        )
    open(dst, "w").write(text)


if __name__ == "__main__":
    main(sys.argv)

#!/usr/bin/env python3
"""gp_flags.py - gp rewrite inputs for the C staging path, one query at a time.

  python3 tools/gp_flags.py rewrite <TARGET>   -> "0" or "1"
  python3 tools/gp_flags.py info    <TARGET>   -> "<gp_base> <name:addr> ..."

Extracted verbatim from tools/build.sh's heredocs so the unit judge
(tools/judge_unit.py) computes exactly what the full build computes.

`rewrite` is 1 only when the target's yaml carries options.gp_value: cc1 -G8
emits bare-symbol memory operands for gp-relative globals and the staging
step rewrites the in-range ones to %gp_rel. `info` is the range table for
that rewrite: the gp base plus name:address pairs from the committed
symbols file, `!`-suffixed when a curated gp:absolute marker proves retail
loads the symbol absolutely (per-symbol evidence the range test cannot see).
"""
import re
import sys

import yaml


def main(argv):
    what, target = argv[1], argv[2]
    cfg = yaml.safe_load(open(f"config/splat.{target}.yaml"))
    if what == "rewrite":
        print("1" if cfg["options"].get("gp_value") is not None else "0")
        return
    if what == "info":
        gp = cfg["options"].get("gp_value") or 0
        addr = {}
        # A curated entry may carry a 'gp:absolute' marker when retail provably
        # loads that symbol with an absolute lui+lo pair even though it sits
        # inside +/-32 KB of the gp base (first case: LIBSPU's _spu_inTransfer,
        # an 8-byte S_INI flag that S_ITC loads absolutely in slps_00270, while
        # same-range 4-byte flags like boot_flag_0 are gp-relative there). The
        # range test alone cannot know this - it is per-symbol retail evidence -
        # so the marker flags the name (a '!' suffix in the staging table) and
        # the rewrite skips it, keeping the absolute form the non-gp targets
        # prove.
        for ln in open(f"config/symbols.{target}.txt"):
            m = re.match(r"^(\w+) = 0x([0-9A-Fa-f]+);", ln)
            if m:
                # splat's native absolute:true boolean (curated gp:absolute)
                # marks per-symbol retail evidence: load it absolutely even in
                # range. The '!' suffix tells the stager to skip the rewrite
                # for this name (exclusion alone would fall into the
                # unknown-name rewrite path).
                marked = "absolute:true" in ln
                addr[m.group(1) + ("!" if marked else "")] = int(m.group(2), 16)
        print(f"{gp:#x} " + " ".join(f"{n}:{a:#x}" for n, a in sorted(addr.items())))
        return
    raise SystemExit(f"unknown query: {what}")


if __name__ == "__main__":
    main(sys.argv)

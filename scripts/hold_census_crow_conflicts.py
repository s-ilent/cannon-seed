#!/usr/bin/env python3
"""Hold the census curated entries that collide with landed C-row names.

The cron-202611062346 scan application is the first build-test of the
c32d807d census block, and it surfaced the class: a census placement
(sdk_members.py module_base + member .text offset) can land on an address
whose NAME is already a landed C row's name at a different address in the
same target. Applying the name at the census address re-labels every
retail jal that targets the census address, the assembler resolves the
label to the strong C definition elsewhere, and the image diverges from
retail (witnessed live: slps ApplyMatrixLV, five INTR-cluster jal words;
then the seven slps LIBSND members).

Both facts are real - the census address is where the archive member's
signature sits, the C row is where the landed unit defines the symbol -
but one name can label one address. This is a decode/ownership question
(the sdk-curation lane's), not a scan one: the scan holds the census
entry the same way c32d807d held SsSetTableSize (commented out, evidence
inline, the skip is loud in the commit message).
"""
import re
import sys

PATH = "config/symbols.curated.txt"
ROW = re.compile(r"\s*- \[(0x[0-9A-Fa-f]+),\s*(\w+),\s*([\w.]+)\]\s*#\s*(0x[0-9A-Fa-f]+)")

HOLD_NOTE = (" [HELD cron-202611062346: collides with the landed C row of the "
             "same name at a different address - the census name cannot label "
             "two addresses; the sdk-curation lane owns the reconciliation]")


def main():
    lines = open(PATH).read().splitlines(keepends=True)
    # pass 1: per-target c-row name -> vrams (from the fresh yamls)
    crows = {}
    targets = ["slps_00270", "sces_00269", "g3_jp", "g3_eu",
               "g3org_jp", "g3org_eu", "mainmenu_eu"]
    for t in targets:
        d = {}
        for ln in open(f"config/splat.{t}.yaml"):
            m = ROW.match(ln)
            if m and m.group(2) == "c":
                d.setdefault(m.group(3), []).append(
                    0x80020000 + int(m.group(1), 16) - 0x800)
        crows[t] = d
    # pass 2: comment out conflicting live entries
    out = []
    scope = None
    held = 0
    for ln in lines:
        mt = re.match(r"\s*//\s*target:\s*(\w+)", ln)
        if mt:
            scope = mt.group(1)
        m = re.match(r"([A-Za-z_][\w.]*)\s*=\s*(0x[0-9A-Fa-f]+)", ln)
        if (m and scope in crows and not ln.lstrip().startswith("//")):
            n, a = m.group(1), int(m.group(2), 16)
            if n in crows[scope] and all(o != a for o in crows[scope][n]):
                out.append("// " + ln.rstrip("\n") + HOLD_NOTE + "\n")
                held += 1
                continue
        out.append(ln)
    open(PATH, "w").write("".join(out))
    print(f"held {held} census entries")


if __name__ == "__main__":
    main()

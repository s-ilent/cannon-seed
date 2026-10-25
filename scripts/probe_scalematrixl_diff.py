#!/usr/bin/env python3
"""probe_scalematrixl_diff.py - stage-A probe for the staged ScaleMatrixL
x8 landing (window cron-202610251321).

Compiles the landed src/ScaleMatrix.c template, then word-diffs its 73
.text words against the oracle at every ScaleMatrixL site. The census
scored the family uniform eq 65/73 dw=8/73 - this probe pins WHICH words
differ so the variant body can be derived, then prove_scalematrixl.py
re-checks with the real src/ScaleMatrixL.c.

Whole-row sites (yaml/baseline file offsets straight off the splat rows):

  slps_00270   0x14EB0   sces_00269   0x14978  (census-blind, anchor-banked)
  g3_jp        0x2A380   g3_eu        0x29D98
  g3org_jp     0x2781C   g3org_eu     0x271EC
  mainmenu_eu  0x3E274   mainmenu_jp  <data-row block, VA 0x8005E094>

mainmenu_jp's copy is the D-MID-ROW block inside the data_80066CF4
graveyard row; its file offset is resolved by grepping the target's asm
tree for the block VA (spimdisasm stamps "fileoff VA" on every line).
"""
import struct
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from prove_scalematrix import o_text_words, CC, N  # noqa: E402

SITES = [
    ("slps_00270", 0x14EB0),
    ("sces_00269", 0x14978),
    ("g3_jp", 0x2A380),
    ("g3_eu", 0x29D98),
    ("g3org_jp", 0x2781C),
    ("g3org_eu", 0x271EC),
    ("mainmenu_eu", 0x3E274),
]


def resolve_mainmenu_jp_offset():
    """The data-row block's file offset, from the asm tree's VA stamps."""
    hits = []
    for asm in (REPO / "asm" / "mainmenu_jp").rglob("*.s"):
        text = asm.read_text(errors="replace")
        for line in text.splitlines():
            if "8005E094" in line:
                hits.append((asm.name, line.strip()))
    return hits


src = REPO / "src" / "ScaleMatrix.c"
out = Path("/home/z/my-project/build/probe_sml/ScaleMatrix.o")
out.parent.mkdir(parents=True, exist_ok=True)
subprocess.run(["sh", str(CC), "-o", str(out), str(src)],
               check=True, capture_output=True, text=True)
tmpl = o_text_words(out)
print(f"template .text: {len(tmpl)} words (need {N})")

hits = resolve_mainmenu_jp_offset()
print(f"mainmenu_jp VA 0x8005E094 asm hits: {len(hits)}")
for name, line in hits[:4]:
    print(f"   {name}: {line[:110]}")

failures = 0
for target, off in SITES:
    data = open(REPO / "baselines" / f"{target}.bin", "rb").read()
    expected = list(struct.unpack_from(f"<{N}I", data, off))
    diffs = [(i, expected[i], tmpl[i]) for i in range(min(len(tmpl), N))
             if expected[i] != tmpl[i]]
    print(f"\n{target:12} @{off:06x}: {len(diffs)} diff word(s)")
    for i, e, g in diffs:
        print(f"   [{i:2d}] oracle {e:08x} vs ScaleMatrix {g:08x}")
    if len(diffs) != 8:
        failures += 1

sys.exit(1 if failures else 0)

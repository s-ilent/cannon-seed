#!/usr/bin/env python3
"""audit_mainmenu_jp_regen.py - byte-payload audit for mainmenu_jp's
extract regeneration (ScaleMatrixL landing, window cron-202610251321).

The extract re-emitted 36 unrelated files in the current toolchain's
label presentation. Before letting them ride in the landing commit,
prove they are LABEL-LEVEL ONLY: for every modified file, the sequence
of embedded byte payloads (the third field of every `/* off VA bytes *`
comment line, which carries the actual bytes) must be IDENTICAL between
HEAD and the worktree. data_80066CF4.data.s is excluded (its payload
shrank by the cut by construction; the tail file carries the removed
bytes - separately checked here against the baseline slice).
"""
import subprocess
import sys
from pathlib import Path

REPO = Path("/home/z/my-project/cannon-seed")

modified = subprocess.run(
    ["git", "diff", "--name-only", "HEAD", "--", "asm/mainmenu_jp/"],
    capture_output=True, text=True, check=True).stdout.split()

CUT = "asm/mainmenu_jp/nonmatchings/data/data_80066CF4.data.s"
TAIL = "asm/mainmenu_jp/nonmatchings/data/data_8005E1B8.data.s"


def payloads(text):
    out = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("/*") and "*/" in s:
            fields = s[2:s.index("*/")].split()
            if len(fields) >= 3:
                out.append(fields[2])
    return out


failures = []
regen = []
for path in modified:
    if path == CUT:
        continue
    head = subprocess.run(["git", "show", f"HEAD:{path}"],
                          capture_output=True, text=True, check=True).stdout
    work = (REPO / path).read_text()
    if payloads(head) == payloads(work):
        regen.append(path)
    else:
        failures.append(path)

print(f"checked {len(modified) - 1} regenerated files (excl. cut row)")
print(f"label-level only: {len(regen)}")
for p in failures:
    print(f"PAYLOAD CHANGED: {p}")

# The tail file's payload must equal the removed slice of the cut row.
head_cut = subprocess.run(["git", "show", f"HEAD:{CUT}"],
                          capture_output=True, text=True, check=True).stdout
work_cut = (REPO / CUT).read_text()
removed = payloads(head_cut)[len(payloads(work_cut)):]
tail_pay = payloads((REPO / TAIL).read_text())
if removed == tail_pay:
    print(f"tail file payload == removed slice ({len(tail_pay)} words) OK")
else:
    print(f"TAIL MISMATCH: removed {len(removed)} words vs tail {len(tail_pay)} words")
    failures.append(TAIL)

sys.exit(1 if failures else 0)

#!/usr/bin/env python3
"""scan_functions.py - bootstrap the code/data map of a PS-X EXE payload.

Deterministic MIPS-I linear-sweep scanner. It does not replace the
compiler-idiom or matching work; it produces the first-pass subsegment
list so splat can split per-function and progress/ratchets have something
honest to count.

Method (v2, documented and re-runnable):

1. Anchors: the proven entry point (pc0) plus every `jal` target found in
   the payload. `jal` encodes an absolute image address, so its target is
   a function start unless the word is data that happens to decode as jal
   (filtered later by the plausibility walk).
2. Linear walk from every uncovered anchor: consume instructions while
   they are plausible MIPS-I; stop after a `jr`/`j` plus its delay slot
   (function return or tail jump), after a run of >= 3 zero words
   (padding), or after 4 consecutive implausible words (embedded data).
3. v2 flow-through: a `jr`+delay does NOT end the walk when (a) the
   boundary address is not a jal target and (b) plausible code follows.
   GCC 2.6.3 places mid-function epilogues (early `return`s) whose
   fall-through continues the same function; v1 stopped there and
   manufactured prologue-less fragments (104 of 253 subsegments on
   slps_00270, see tools/prologue_hunt.py).
4. v2 branch-target rescue: branch/jump targets that land in remaining
   data gaps seed additional walks. A rescued run is kept only when it
   connects to (reaches or overlaps) an existing or other rescued range —
   orphaned walks would create NEW mid-function fragments, the very
   disease being fixed.
5. v3 jr/prologue boundary: a jr flow-through does NOT continue when the
   following words form a fresh function prologue (addiu $sp,$sp,-N plus
   a `sw $ra,(N-4|N-8)($sp)` within two instructions). GCC sets the
   frame once per function, so such a boundary is the START of the next
   function, not this function's continuation — stopping there keeps
   pointer-called function chains (see 6) as separate subsegments.
6. v3 prologue rescue: functions called through pointers (task/init
   tables, pc0 callbacks) are never jal targets, so nothing anchors them
   and whole prologue'd functions hide in data gaps (176 candidates /
   several KB found on slps_00270, e.g. the chain at 0x80021DCC).
   Walks are seeded at every `addiu $sp,$sp,-N` + `sw $ra` candidate
   inside remaining gaps; a rescued run is kept when it terminates in a
   matching epilogue teardown (`jr $ra` + `addiu $sp,$sp,+N`) or
   connects to an existing range. Everything else stays data.
7. Ranges are merged; every uncovered aligned gap is data.
8. Type preservation: subsegments the tree already carries as `c`
   (C-matched functions) keep their type across re-scans.
9. v3c continuation merge: a prologue-less range whose PREDECESSOR
   branches into it (start or interior, never jal) and which no OTHER
   range references is the continuation of that predecessor - one
   function split by an embedded literal pool / barrier stop. It is
   merged back; the pool bytes ride inside the merged range (spimdisasm
   emits the same bytes however it decodes them; verify is the gate).
   Guarded: never merges a range other code enters (shared tail), never
   across a preserved c-function, never one starting a fresh prologue.
   (applies to rule 11's rescues too: a strong rescue is merged into a
   branching predecessor only when the guards hold)
10. v3d image-integrity rejection: real code never jal/j's outside the
   executable's own image (or the BIOS call regions A0/B0/C0); packed
   and encrypted data blobs that walk as plausible code do it constantly
   (witnessed: g3_eu 0x8004035C, a 0x46C compressed blob whose words
   decode through sdc1/jal-to-0x802F8978/bgezall $ra/cache until GAS
   hard-fails on the bgezall). Such ranges are rejected wholesale and
   their bytes return to the data side, where they belong.
11. v4 strong anchors: a bare `j` (op 2) inside a covered code range is
   a tail call/dispatch, and a tail call only ever targets code. Its
   target is a function entry that has NO frame (leaf, so v3's prologue
   rescue never fires) and NO jal pointing at it (so v1 never anchors
   it) - without this rule such functions hide in data gaps forever
   (witnessed: g3_eu data_8004712C swallowed three of them; the j from
   func_8004D744 enters at 0x80047924, two more at 0x8004899C/0x80048A44).
   A j-seeded walk is accepted when it ends at a jr boundary (the shape
   of a function end), is at least 0x14 B, and is an ISLAND - it never
   overlaps or touches covered code. The island rule matters: a rescue
   glued to a covered range joins it in the final merge, and one bad
   jump inside the rescue then makes v3d reject the glued whole,
   taking verified code down with it (witnessed on slps_00270:
   0x8003F9EC..0x800402B8 swallowed 0x818 B of verified code; on
   g3_eu the rescues even reached the matched C functions). The seed
   set is recomputed and the strong rescue iterated, so dispatch chains
   resolve. Branch targets keep the strict v2 connection rule with the
   original single-pass semantics (they are intra-function flow or
   pool words - far weaker evidence). v3d still vetts integrity
   downstream; blobs that walk far die on it.
12. v5 short-head reclaim: a gap that STARTS with a real prologue pair
   is a function head even when the rescue walk is shorter than the
   generic 0x14 minimum, provided the walk ends on a barrier (covered
   code) or a clean epilogue teardown. The disease: noise words that
   decode as jal create phantom v1 anchors whose walks claim the BODY
   of a real function (anchored walks are unconditionally accepted),
   the prologue rescue's walk from the true prologue is then
   barrier-stopped after a few words and died on the 0x14 minimum,
   and the prologue pair stayed data forever (witnessed: mainmenu_eu
   data_80037B6C / data_80037B98, each a 0x8-0xC B prologue head of a
   function whose body sat in the next subseg starting mid-instruction).
   The short head is merged with the sliced body by the normal merge
   pass; v3d still vets the joined range.

Outputs (regenerated wholesale):
  - config/splat.slps_00270.yaml  subsegments section (between markers)
  - config/symbols.slps_00270.txt function symbols (between markers)
  - stdout summary

Usage: python3 tools/scan_functions.py [TARGET]     (default slps_00270)
"""

import re
import struct
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASELINES = REPO / "baselines"
SHA1_DIR = REPO / "config" / "sha1"

BASE = 0x80020000
HDR = 0x800

SPECIAL_FUNCTS = {0x00, 0x02, 0x03, 0x04, 0x06, 0x07, 0x08, 0x09, 0x0C,
                  0x0D, 0x10, 0x11, 0x12, 0x13, 0x18, 0x19, 0x1A, 0x1B,
                  0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x2A, 0x2B}
REGIMM_RT = {0x00, 0x01, 0x10, 0x11, 0x12, 0x13}
VALID_OPS = ({0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09,
              0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x10, 0x11, 0x12, 0x13}
             | set(range(32, 39))          # lb..lwr
             | {40, 41, 42, 43, 46}        # sb..swr
             | {49, 53, 57, 61})           # lwc1, ldc1, swc1, sdc1

JR = (0 << 26) | 0x08          # opcode 0, funct 8 (any register)
J = 2 << 26
JAL = 3 << 26


def prologue_frame(words, i, n):
    """Frame size if words[i..] starts a GCC function prologue, else None.

    Pattern: `addiu $sp,$sp,-N` (8 <= N <= 0x7F00) followed within two
    instructions by `sw $ra,(N-4)($sp)` or `sw $ra,(N-8)($sp)`. GCC 2.6.3
    always saves $ra when a function makes calls, at frame-4 or frame-8
    (the largest first-word slot). Data that happens to decode as addiu
    is rejected by the required sw within the two-instruction window.
    """
    if i >= n:
        return None
    w = words[i]
    if (w & 0xFFFF0000) != 0x27BD0000:
        return None
    imm = w & 0xFFFF
    if imm >= 0x8000:
        imm -= 0x10000
    if not (-0x7F00 <= imm <= -8):
        return None
    frame = -imm
    for j in (1, 2):
        if i + j >= n:
            break
        w2 = words[i + j]
        if (w2 & 0xFFFF0000) == 0xAFBF0000:
            k = w2 & 0xFFFF
            if k >= 0x8000:
                k -= 0x10000
            if k in (frame - 4, frame - 8):
                return frame
    return None


def plausible(w: int) -> bool:
    if w == 0:
        return True
    op = w >> 26
    if op not in VALID_OPS:
        return False
    if op == 0x00 and (w & 0x3F) not in SPECIAL_FUNCTS:
        return False
    if op == 0x01 and (w & 0x1F) not in REGIMM_RT:
        return False
    return True


def scan(payload: bytes, entry_off: int, hard_stops=frozenset(), barrier=None):
    n = len(payload) // 4
    words = struct.unpack(f"<{n}I", payload[: n * 4])

    def v2o(v):  # vram -> offset (or None)
        return v - BASE if 0 <= v - BASE < len(payload) else None

    anchors = set()
    if 0 <= entry_off < len(payload):
        anchors.add(entry_off & ~3)
    for i, w in enumerate(words):
        if (w >> 26) == 3:  # jal
            tgt = ((w & 0x3FFFFFF) << 2) | (BASE & 0xF0000000)
            o = v2o(tgt)
            if o is not None:
                anchors.add(o & ~3)
    # jal targets inside data produce garbage anchors; the walk from an
    # implausible anchor dies immediately, so no special filtering needed.

    def branch_target(i, w):
        """vram address a branch/jump at word i targets, or None."""
        op = w >> 26
        pc = BASE + i * 4
        if op in (0x04, 0x05, 0x06, 0x07) or op == 0x01:
            simm = w & 0xFFFF
            if simm >= 0x8000:
                simm -= 0x10000
            return pc + 4 + (simm << 2)
        if op == 0x02:  # j (not jal — jal targets are anchors already)
            return ((w & 0x3FFFFFF) << 2) | (BASE & 0xF0000000)
        return None

    def walk(start_off, barrier=None):
        """Forward walk with v1 stop rules + v2 jr flow-through + v3
        prologue boundary. Returns (start, end) with end exclusive, or
        None."""
        a = start_off
        end = a
        bad = 0
        zeros = 0
        i = a // 4
        while i < n:
            # v3 barrier (rescue walks): never consume words that belong to
            # an already-covered range — the walk ends at its boundary so
            # rescued runs cannot swallow covered functions.
            if barrier is not None and i != a // 4 and barrier[i]:
                return (a, i * 4) if i * 4 > a else None
            w = words[i]
            if w == 0:
                zeros += 1
                if zeros >= 3:
                    return (a, end)
            else:
                zeros = 0
            if not plausible(w):
                bad += 1
                if bad >= 4:
                    return (a, end)
            else:
                bad = 0
                if (w >> 26) == 0 and (w & 0x3F) == 0x08:  # jr (any reg)
                    nxt = words[i + 1] if i + 1 < n else 0
                    stop = ((i + 2) if (nxt == 0 or plausible(nxt)) else (i + 1)) * 4
                    end = stop
                    # v2: flow through the jr when the boundary is not a
                    # jal target (nor a preserved C-matched function entry)
                    # and real code follows — this is a mid-function
                    # epilogue, not a function end.
                    # v3: do NOT flow through when the following words are
                    # a fresh prologue: GCC sets the frame once per
                    # function, so that boundary is the next function's
                    # start (pointer-called chains sit back to back).
                    if (stop not in anchors
                            and stop not in hard_stops
                            and stop // 4 < n
                            and words[stop // 4] != 0
                            and plausible(words[stop // 4])
                            and prologue_frame(words, stop // 4, n) is None):
                        i = stop // 4
                        zeros = 0
                        bad = 0
                        continue
                    return (a, end)
            i += 1
            end = i * 4
        if end > len(payload):
            end = len(payload)
        return (a, end) if end > a else None

    covered = {}  # start_off -> end_off (function ranges)
    for a in sorted(anchors):
        if any(s <= a < e for s, e in covered.items()):
            continue
        r = walk(a)
        if r and r[1] > r[0]:
            covered[r[0]] = r[1]

    # v2 branch-target rescue for the remaining gaps
    def in_covered(o):
        return any(s <= o < e for s, e in covered.items())

    def jr_end(e):
        """True if a walk ending at e terminated on a jr(+delay) boundary
        (shape A: jr at e-8 with its delay slot consumed; shape B: jr at
        e-4, delay slot implausible and unconsumed). The end shape of a
        real function return or tail jump."""
        if e < 8:
            return False
        return ((words[(e // 4) - 2] & 0xFC00003F) == JR
                or (words[(e // 4) - 1] & 0xFC00003F) == JR)

    def bad_jump_target(s, e):
        """v3d image-integrity (docstring 10): the first j/jal target in
        [s, e) outside the image and the BIOS call regions, else None."""
        for j in range(s // 4, e // 4):
            op = words[j] >> 26
            if op == 2 or op == 3:  # j / jal
                tgt = ((words[j] & 0x3FFFFFF) << 2) | (BASE & 0xF0000000)
                if not (BASE <= tgt < BASE + len(payload)) and not (
                        0xA0000000 <= tgt < 0xC0003000):
                    return tgt
        return None

    # v2 branch-target rescue for the remaining gaps - ORIGINAL single-pass
    # semantics, unchanged: seeds from the initial covered set only,
    # barrier-less walks, connection-only acceptance.
    seeds = set()
    for s, e in list(covered.items()):
        for i in range(s // 4, e // 4):
            t = branch_target(i, words[i])
            if t is None:
                continue
            o = v2o(t)
            if o is not None and not in_covered(o & ~3) and (o & ~3) not in hard_stops:
                seeds.add(o & ~3)
    for a in sorted(seeds):
        if in_covered(a):
            continue
        r = walk(a)
        if not r:
            continue
        s, e = r
        # keep the rescued run only when it CONNECTS to an existing range:
        # its end reaches/overlaps one, or another seed's walk does.
        if any(s < e2 and e > s2 for s2, e2 in covered.items()):
            covered[s] = max(e, covered.get(s, 0))
        elif any(e2 == s for s2, e2 in covered.items()) or any(
            s2 == e for s2, e2 in covered.items()
        ):
            covered[s] = e

    # v4 strong-anchor rescue (docstring 11): iterated `j`-target islands.
    def build_mask():
        m = bytearray(n)
        for s2, e2 in covered.items():
            for o in range(s2 // 4, min(e2 // 4, n)):
                m[o] = 1
        return m

    def island(s, e):
        """True if [s, e) neither overlaps nor touches covered code."""
        if any(s < e2 and e > s2 for s2, e2 in covered.items()):
            return False
        return not any(e2 == s or s2 == e for s2, e2 in covered.items())

    rescued_strong = 0
    while True:
        strong = set()
        for s, e in list(covered.items()):
            for i in range(s // 4, e // 4):
                if (words[i] >> 26) != 0x02:
                    continue
                o = v2o(((words[i] & 0x3FFFFFF) << 2) | (BASE & 0xF0000000))
                if o is not None and not in_covered(o & ~3) and (o & ~3) not in hard_stops:
                    strong.add(o & ~3)
        mask = build_mask()
        grew = False
        for a in sorted(strong):
            if in_covered(a):
                continue
            r = walk(a, barrier=mask)
            if not r:
                continue
            s, e = r
            # image-integrity at acceptance time: a rescue carrying an
            # out-of-image jump must never become code at all. Letting it
            # through glues it to whatever v3/merge put next to it and the
            # v3d wholesale kill then takes the NEIGHBOR down too
            # (witnessed on sces_00269: [0xD40C,0xD4E8) doomed the verified
            # 0x7D4 B at 0xD4E8 in the merged range).
            if e - s >= 0x14 and jr_end(e) and island(s, e) \
                    and bad_jump_target(s, e) is None:
                covered[s] = e
                rescued_strong += 1
                grew = True
        if not grew:
            break
    if rescued_strong:
        print(f"scan: v4 strong-anchor rescue recovered "
              f"{rescued_strong} j-target range(s) from data gaps")

    # v3 prologue rescue: pointer-called functions are never jal targets,
    # so their prologues hide in data gaps. Seed a walk at every prologue
    # candidate inside a gap; keep the run when it ends in a matching
    # epilogue teardown (jr $ra + addiu $sp,$sp,+frame within the last two
    # words) or connects to an existing range. Rescuing a function can
    # expose the next one in the chain (the walk now stops at prologues,
    # see walk()), so iterate until nothing new is accepted.
    rescued_bytes = 0
    short_heads = {}  # v5: s -> (e, frame), deferred to post-v3d
    mask = bytearray(n)  # 1 = word belongs to a covered/rescued range
    for s, e in covered.items():
        for o in range(s // 4, e // 4):
            mask[o] = 1
    while True:
        accepted = False
        for i in range(n):
            off = i * 4
            if mask[i]:
                continue
            frame = prologue_frame(words, i, n)
            if frame is None:
                continue
            r = walk(off, barrier=mask)
            if not r:
                continue
            s, e = r
            ends_clean = (
                e >= 8
                and words[(e // 4) - 2] == 0x03E00008  # jr $ra
                and (words[(e // 4) - 1] & 0xFFFF0000) == 0x27BD0000
                and (words[(e // 4) - 1] & 0xFFFF) == frame
            )
            connects = any(s < e2 and e > s2 for s2, e2 in covered.items()) or any(
                e2 == s or s2 == e for s2, e2 in covered.items()
            )
            if e - s < 0x14:
                # v5 short-head reclaim (docstring 12): a gap that STARTS
                # with a real prologue is a function head even when the
                # walk is shorter than the generic 0x14 minimum. Phantom
                # anchors (noise words decoding as jal) slice real
                # functions mid-body: the anchor walk claims the body, and
                # this rescue's walk from the true prologue gets
                # barrier-stopped after a few words and dies on the
                # minimum, leaving the prologue as data (witnessed:
                # mainmenu_eu data_80037B6C / data_80037B98, prologue
                # pairs carved off while walks from noise-jal anchors
                # carried the bodies at 0x80037B7C / 0x80037BA4).
                # NOT accepted here: `covered` is pre-merge, pre-v3d
                # state, and gluing the head forward can bridge a verified
                # range into a junk-bound fragment that v3d then kills
                # wholesale, taking the predecessor down with it
                # (witnessed: mainmenu_eu 0x800264EC, an 8-save prologue
                # sliced at its 4th save; 0x800268C4 / 0x800355A4 heads
                # bridging into out-of-image-jump fragments). Cheap
                # filters now - full prologue pair, the slice falls AFTER
                # the save sequence (the neighbor must not open with
                # another sp-relative save below the ra slot), and the
                # walk ends on a barrier or a clean epilogue - and the
                # real acceptance is DEFERRED until after v3d pass 1,
                # when every doomed fragment is already back on the data
                # side and the head can only rejoin a surviving body.
                barrier_stop = e < len(payload) and mask[e // 4]
                save_cont = False
                if e < len(payload):
                    nxt = words[e // 4]
                    if (nxt >> 26) == 0x2B and ((nxt >> 21) & 0x1F) == 29:
                        imm = nxt & 0xFFFF
                        if imm >= 0x8000:
                            imm -= 0x10000
                        save_cont = 0 <= imm < frame
                if e - s >= 8 and not save_cont \
                        and (ends_clean or barrier_stop):
                    if s not in short_heads or short_heads[s][0] < e:
                        short_heads[s] = (e, frame)
                continue
            elif not (ends_clean or connects):
                continue
            covered[s] = e
            rescued_bytes += e - s
            for o in range(s // 4, min(e // 4, n)):
                mask[o] = 1
            accepted = True
        if not accepted:
            break
    if rescued_bytes:
        print(f"scan: v3 prologue rescue recovered {rescued_bytes:,} B "
              f"of pointer-called code from data gaps")

    # merge overlapping ranges, then trim trailing all-zero runs (>= 2
    # words) out of code ranges into the data side so spimdisasm never gets
    # the chance to classify real file bytes as NOBITS .bss (the retail
    # payload carries those zeros as actual bytes).
    merged = []
    for s in sorted(covered):
        if merged and s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], covered[s])
        else:
            merged.append([s, covered[s]])
    trimmed = []
    for s, e in merged:
        z = e
        while z - 8 >= s and words[(z // 4) - 1] == 0 and words[(z // 4) - 2] == 0:
            z -= 4
        trimmed.append([s, z])

    # v3d: image-integrity rejection (see docstring item 10). Runs BEFORE
    # the v3c merge so a doomed range can never serve as a merge
    # predecessor, and AGAIN after it (a merge can reassemble pieces into
    # a range containing a bad word none of the v3d-pass-1 parts tripped
    # on). Rejected bytes fall back to the data side.
    def v3d_reject(rts):
        rejected = 0
        rejected_bytes = 0
        keep = []
        for s, e in rts:
            if s in hard_stops:
                keep.append([s, e])
                continue
            bad_tgt = bad_jump_target(s, e)
            if bad_tgt is None:
                keep.append([s, e])
                continue
            print(f"scan: v3d REJECT {BASE + s:08X}..{BASE + e:08X} "
                  f"({e - s:#x} B): jump to {bad_tgt:08X} outside image")
            rejected += 1
            rejected_bytes += e - s
        if rejected:
            print(f"scan: v3d rejected {rejected} ranges "
                  f"({rejected_bytes:,} B) back to data")
            return keep
        return rts

    trimmed = v3d_reject(trimmed)

    # v5 deferred short-head reclaim (docstring 12): the prologue heads
    # collected during the v3 rescue are accepted HERE, against the
    # post-v3d layout, so a head can only ever rejoin a body that
    # survived image-integrity vetting - it can no longer bridge verified
    # code into a doomed fragment. The head extends the surviving range
    # that starts exactly at the head's walk end (its sliced body); a
    # head whose body died with v3d stays data, honestly.
    if short_heads:
        reclaimed = 0
        reclaimed_bytes = 0
        changed = True
        while changed:
            changed = False
            for s in sorted(short_heads):
                e, frame = short_heads[s]
                if any(s2 <= s < e2 for s2, e2 in trimmed):
                    continue  # covered by some range already
                if prologue_frame(words, s // 4, n) is None:
                    continue
                body_idx = next((k for k, (s2, _) in enumerate(trimmed)
                                 if s2 == e), None)
                ends_clean = (
                    e >= 8
                    and words[(e // 4) - 2] == 0x03E00008
                    and (words[(e // 4) - 1] & 0xFFFF0000) == 0x27BD0000
                    and (words[(e // 4) - 1] & 0xFFFF) == frame
                )
                if body_idx is not None:
                    trimmed[body_idx][0] = s  # extend the body leftward
                elif ends_clean and s not in hard_stops:
                    trimmed.append([s, e])
                    trimmed.sort(key=lambda r: r[0])
                else:
                    continue  # the sliced body did not survive v3d
                reclaimed += 1
                reclaimed_bytes += e - s
                changed = True
                break  # trimmed shifted; rescan from the smallest head
        if reclaimed:
            print(f"scan: v5 reclaimed {reclaimed} short prologue head(s) "
                  f"({reclaimed_bytes:,} B) into their sliced bodies")
            # re-merge (the head may now touch its predecessor) + re-trim
            m2 = []
            for s, e in trimmed:
                if m2 and s <= m2[-1][1]:
                    m2[-1][1] = max(m2[-1][1], e)
                else:
                    m2.append([s, e])
            trimmed = []
            for s, e in m2:
                z = e
                while (z - 8 >= s and words[(z // 4) - 1] == 0
                       and words[(z // 4) - 2] == 0):
                    z -= 4
                trimmed.append([s, z])

    # v3c: merge prologue-less continuations back into their predecessor.
    # GCC 2.6.3 embeds literal pools / jump tables INSIDE functions; the
    # walk stops at the implausible words and the code after the pool
    # becomes a prologue-less fragment. When the predecessor branches into
    # the fragment (start or interior - branches are intra-function by
    # construction) and nothing else references it, the fragment rejoins
    # the predecessor and the pool rides inside the merged range.
    # Guards: the fragment must not start a fresh prologue (that is the
    # NEXT function, see 5), must have no referrer other than the
    # predecessor (a jal/branch from elsewhere = shared block or a real
    # pointer-called function), and no preserved c-function may sit in
    # the swallowed gap (matched C files own their exact bytes).
    merged_fragments = 0
    merged_bytes = 0
    while True:
        # referrers: range index -> set of OTHER range indices whose code
        # branches/jumps/jals to this range's exact start
        idx_of = {s: i for i, (s, _) in enumerate(trimmed)}
        referrers = {i: set() for i in range(len(trimmed))}
        for i, (s, e) in enumerate(trimmed):
            for j in range(s // 4, e // 4):
                t = branch_target(j, words[j])
                if t is None:
                    continue
                ri = idx_of.get(t - BASE)
                if ri is not None and ri != i:
                    referrers[ri].add(i)
        done = True
        for i, (s, e) in enumerate(trimmed):
            if i == 0 or s in hard_stops:
                continue
            if prologue_frame(words, s // 4, n) is not None:
                continue
            if referrers[i] - {i - 1}:
                continue  # entered from elsewhere: shared block, keep
            ps, pe = trimmed[i - 1]
            if ps in hard_stops:
                continue  # predecessor is a matched C function: fixed size
            if any(ps <= k < s for k in hard_stops):
                continue  # a c-function sits in the gap
            hit = False
            for j in range(ps // 4, pe // 4):
                op = words[j] >> 26
                if op == 3 or op not in (1, 2, 4, 5, 6, 7):
                    continue  # jal = a call: that is a function, not flow
                t = branch_target(j, words[j])
                if t is not None and s <= t - BASE < e:
                    hit = True
                    break
            if not hit:
                continue
            trimmed[i - 1][1] = e
            del trimmed[i]
            merged_fragments += 1
            merged_bytes += e - s
            done = False
            break  # indices shifted; recompute referrers
        if done:
            break
    if merged_fragments:
        print(f"scan: v3c merged {merged_fragments} continuation fragments "
              f"({merged_bytes:,} B) back into their predecessors")
        # re-merge (the join may now touch the next range) and re-trim
        m2 = []
        for s, e in trimmed:
            if m2 and s <= m2[-1][1]:
                m2[-1][1] = max(m2[-1][1], e)
            else:
                m2.append([s, e])
        trimmed = []
        for s, e in m2:
            z = e
            while (z - 8 >= s and words[(z // 4) - 1] == 0
                   and words[(z // 4) - 2] == 0):
                z -= 4
            trimmed.append([s, z])
        # v3d pass 2: a merged range can contain a bad word none of its
        # parts tripped on alone — never let one through.
        trimmed = v3d_reject(trimmed)

    # v3b: cross-range branch targets need NAMES, not boundaries. Each
    # subsegment is one spimdisasm file that defines only its start glabel;
    # a j/branch landing inside a DIFFERENT subsegment would emit a
    # file-local `.L` reference the linker cannot resolve (witnessed:
    # func_8002C2F4 -> 0x8002ACF4 after v3 merged the shared-tail block
    # away). Splitting ranges at such targets explodes (every split
    # creates new cross-range references), so instead they are returned
    # to main() and written as `func_<addr>` symbols: spimdisasm then
    # references them by name and tools/build.sh's second link pass
    # auto-defines the address-encoded names.
    starts = {s for s, _ in trimmed}
    cross = set()
    for s, e in trimmed:
        for j in range(s // 4, e // 4):
            t = branch_target(j, words[j])
            if t is None:
                continue
            o = v2o(t)
            if o is None or o in starts:
                continue
            if any(s2 <= o < e2 for s2, e2 in trimmed):
                cross.add(o)
    return trimmed, cross


def data_gaps(code_ranges, payload_len):
    gaps = []
    cur = 0
    for s, e in code_ranges:
        if s > cur:
            gaps.append((cur, s))
        cur = max(cur, e)
    if cur < payload_len:
        gaps.append((cur, payload_len))
    return gaps


def preserved_types(yaml_path: Path):
    """Offsets the tree carries with a HAND-set type: `c` for C-matched
    functions. Returns {offset: (type, name, size)} and the set of offsets
    as hard walk-stop boundaries.

    v3 note: only `c` entries are preserved. `data` subsegments are the
    scanner's own auto-named output and get regenerated wholesale — and
    since v3 rescues real code out of data gaps, treating old data starts
    as immutable types would re-type rescued functions back to data.
    The recorded SIZE matters as much as the type: the C file was matched
    against a subsegment of exactly that size, so the defensive split in
    main() must carve the c-range out at that size, not to the end of the
    merged range (the range may contain v3-rescued code the C file must
    not swallow — witnessed with the 0x10-byte func_80025AE0 stub).
    """
    kept = {}
    if not yaml_path.exists():
        return kept
    in_block = False
    for ln in yaml_path.read_text().splitlines():
        if "# BEGIN GENERATED SUBSEGMENTS" in ln:
            in_block = True
            continue
        if "# END GENERATED SUBSEGMENTS" in ln:
            break
        if not in_block:
            continue
        m = re.match(r"\s*- \[(0x[0-9A-Fa-f]+),\s*(\w+),\s*(\w+)\]\s*#\s*(0x[0-9A-Fa-f]+)", ln)
        if m and m.group(2) == "c":
            kept[int(m.group(1), 16) - HDR] = (
                m.group(2), m.group(3), int(m.group(4), 16))
    return kept


def main(argv):
    target = argv[1] if len(argv) > 1 else "slps_00270"
    binpath = BASELINES / f"{target}.bin"
    if not binpath.exists():
        raise SystemExit(f"missing baseline {binpath}")
    blob = binpath.read_bytes()
    payload = blob[HDR:]
    header_words = struct.unpack_from("<I", blob, 0x10)
    pc0 = header_words[0]
    entry_off = pc0 - BASE

    kept = preserved_types(yaml_path := REPO / "config" / f"splat.{target}.yaml")
    hard_stops = frozenset(kept)

    ranges, cross_targets = scan(payload, entry_off, hard_stops)
    gaps = data_gaps(ranges, len(payload))

    # Defensive: a preserved c-function must START its own subsegment at
    # its ORIGINAL size. If a v3 merged/rescued range swallowed it, carve
    # [off, off+size) out (the C file was matched against exactly those
    # bytes); leftover range parts stay code. Logs loudly.
    for off in sorted(kept):
        typ, name, csize = kept[off]
        for i, (s, e) in enumerate(ranges):
            if s < off < e:
                ce = min(off + csize, e)
                print(f"scan: WARNING: carving c-function {name} "
                      f"[{off:#x}+{ce - off:#x}] out of range {s:#x}..{e:#x}")
                parts = [[s, off], [off, ce]]
                if ce < e:
                    parts.append([ce, e])
                ranges[i:i + 1] = parts
                break
            if s == off and e - s != csize and e - s > csize:
                print(f"scan: WARNING: trimming c-function {name} to its "
                      f"matched size {csize:#x} (range was {e - s:#x})")
                ranges[i:i + 1] = [[s, s + csize], [s + csize, e]]
                break

    subsegs = []
    for s, e in ranges:
        typ, name = "asm", f"func_{BASE + s:08X}"
        if s in kept:
            typ, name = kept[s][0], kept[s][1]
        subsegs.append((s, typ, name, e - s))
    for s, e in gaps:
        subsegs.append((s, "data", f"data_{BASE + s:08X}", e - s))
    subsegs.sort()

    code_bytes = sum(e - s for s, e in ranges)
    data_bytes = sum(e - s for s, e in gaps)
    print(f"scan {target}: {len(ranges)} code ranges "
          f"({code_bytes:,} B, {100.0 * code_bytes / len(payload):.1f}%), "
          f"{len(gaps)} data gaps ({data_bytes:,} B)")

    # --- rewrite the splat yaml subsegments (regenerate wholesale) --------
    # One code segment covering the payload, subsegments in payload order.
    # splat 0.50 refuses top-level asm segments (needs a code parent), so
    # the interleaved layout is restored at LINK time instead:
    # tools/gen_ld.py gives every subsegment its own output section at its
    # explicit vram/rom address, in order.
    # The PS-X EXE header is NOT a segment: tools/mkpsxexe.py regenerates it
    # from committed config, so the linked image is the payload only.
    # NOTE on the rewrite regex: the group pattern requires `]` directly
    # after the hex digits, so it only matches a bare `- [0xNNN]` segment
    # reference line AFTER the generated block — the generated entries
    # themselves (`- [0xNNN, type, name]`) can never match, which is what
    # makes the wholesale replace + idempotent re-runs work.
    ytext = yaml_path.read_text()
    gen = ["    # BEGIN GENERATED SUBSEGMENTS (tools/scan_functions.py - make scan)"]
    for off, typ, name, size in subsegs:
        gen.append(f"      - [0x{HDR + off:X}, {typ}, {name}]   # {size:#x}")
    gen.append("    # END GENERATED SUBSEGMENTS")
    block = "\n".join(gen)
    new_ytext, count = re.subn(
        r"segments:\n.*?\n(\s*- \[0x[0-9A-Fa-f]+\])",
        "segments:\n"
        "  - name: payload\n"
        "    type: code\n"
        "    start: 0x800\n"
        "    vram: 0x80020000\n"
        "    subsegments:\n"
        + block + "\n\\1",
        ytext, flags=re.S)
    if count != 1:
        raise SystemExit(f"could not locate segments/end-marker in {yaml_path}")
    yaml_path.write_text(new_ytext)

    # --- rewrite function symbols between markers -------------------------
    sym_path = REPO / "config" / f"symbols.{target}.txt"
    stext = sym_path.read_text() if sym_path.exists() else ""
    head = stext.split("// BEGIN GENERATED FUNCTION SYMBOLS")[0]
    head = head.split("# BEGIN GENERATED FUNCTION SYMBOLS")[0].rstrip("\n")
    gen_syms = ["// BEGIN GENERATED FUNCTION SYMBOLS (tools/scan_functions.py)"]
    for s, e in ranges:
        gen_syms.append(f"func_{BASE + s:08X} = 0x{BASE + s:08X}; // type:func")
    # v3b: cross-range branch targets (see scan()). Naming them lets
    # spimdisasm emit `j func_XXXXXXXX` instead of an unresolvable
    # file-local `.L`; the second link pass defines address-encoded names.
    for o in sorted(cross_targets):
        gen_syms.append(f"func_{BASE + o:08X} = 0x{BASE + o:08X}; // type:func (branch target)")
    gen_syms.append("// END GENERATED FUNCTION SYMBOLS")
    sym_path.write_text(head + "\n" + "\n".join(gen_syms) + "\n")

    print(f"wrote subsegments into {yaml_path.relative_to(REPO)} "
          f"and symbols into {sym_path.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

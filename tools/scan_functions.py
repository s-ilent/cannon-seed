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
13. v6 SDK anchors (--sdk-anchors, config/sdk_anchors.txt GENERATED by
   tools/sdk_anchors.py from the member report + the Psy-Q archives): one
   row per byte-verified library function the report places in the
   image - verdict `anchored` or `unique`, never `ambiguous` - with the
   function's extent from its member's own .text symbol table. Each
   anchor span becomes a pinned-class asm row at its exact address: it
   joins the no-walk pin set BEFORE the scan (walks stop at its start,
   seeds inside are refused - the same mechanism as hand-carved rows),
   and after the scan the gap-carve pass lifts it out of the data side.
   The extent is what makes the carve END where the member ends; the
   tree's own kept rows win over the file (same offset, different size =
   the hand-verified state stands and the anchor is skipped with a
   warning). Names stay evidence, not configuration: adoption goes
   through config/symbols.curated.txt.

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


def load_curated(target):
    """offset -> name, from config/symbols.curated.txt for this target.

    Curated names are facts established outside the scan (identified SDK
    library members, recovered subsystem names). Every name sits under a
    `// target: <name>` header: the same VRAM address holds different code
    in different builds, so a name applies to exactly one target.
    """
    cpath = REPO / "config" / "symbols.curated.txt"
    out = {}
    if not cpath.is_file():
        return out
    scope = None
    for line in cpath.read_text(errors="replace").splitlines():
        mt = re.match(r"\s*//\s*target:\s*(\w+)", line)
        if mt:
            scope = mt.group(1)
            continue
        m = re.match(r"\s*([A-Za-z_]\w*)\s*=\s*(0x[0-9A-Fa-f]+)", line)
        if m and scope == target:
            out[int(m.group(2), 16) - BASE] = m.group(1)
    return out


def load_curated_gp_markers(target):
    """offset -> True for curated entries carrying a 'gp:absolute' marker.

    The marker records per-symbol retail evidence that the object loads
    that datum with an absolute lui+lo pair even inside the gp range
    (first case: LIBSPU's _spu_inTransfer, an 8-byte S_INI flag that
    S_ITC loads absolutely in slps_00270 while same-range 4-byte flags
    are gp-relative there). scan carries it into the generated symbols
    file so tools/build.sh's gp_rel rewrite can honour it.
    """
    cpath = REPO / "config" / "symbols.curated.txt"
    out = set()
    if not cpath.is_file():
        return out
    scope = None
    for line in cpath.read_text(errors="replace").splitlines():
        mt = re.match(r"\s*//\s*target:\s*(\w+)", line)
        if mt:
            scope = mt.group(1)
            continue
        m = re.match(r"\s*([A-Za-z_]\w*)\s*=\s*(0x[0-9A-Fa-f]+)", line)
        if m and scope == target and "gp:absolute" in line:
            out.add(int(m.group(2), 16) - BASE)
    if not out:
        return out
    # The marker exists for build.sh's gp_rel rewrite, which only fires on
    # a target that actually has a gp base. Emitting splat's native
    # absolute:true attribute on non-gp targets is inert for the build but
    # changes splat's symbol handling (references to the symbol render as
    # bare D_ labels in neighbour .s files), so gate the whole marker set
    # on the yaml carrying a nonzero gp_value.
    has_gp = False
    ypath = REPO / "config" / f"splat.{target}.yaml"
    if ypath.is_file():
        for line in ypath.read_text(errors="replace").splitlines():
            mg = re.match(r"\s*gp_value:\s*(0x[0-9A-Fa-f]+|\d+)\s*$", line)
            if mg:
                has_gp = int(mg.group(1), 0) != 0
                break
    return out if has_gp else set()


def load_sdk_anchors(target):
    """offset -> (size, name, member, lib, verdict) from
    config/sdk_anchors.txt (GENERATED by tools/sdk_anchors.py; see
    docstring item 13). Same per-target scoping as the curated names:
    the same VRAM address holds different code in different builds."""
    apath = REPO / "config" / "sdk_anchors.txt"
    out = {}
    if not apath.is_file():
        return out
    scope = None
    for line in apath.read_text(errors="replace").splitlines():
        mt = re.match(r"\s*//\s*target:\s*(\w+)", line)
        if mt:
            scope = mt.group(1)
            continue
        if scope != target or line.lstrip().startswith("//"):
            continue
        m = re.match(r"(0x[0-9A-Fa-f]+)\s+(0x[0-9A-Fa-f]+)\s+(\S+)\s+(\S+)"
                     r"\s+(\S+)\s+(\S+)", line)
        if m:
            out[int(m.group(1), 16) - BASE] = (
                int(m.group(2), 16), m.group(3), m.group(4), m.group(5),
                m.group(6))
    return out


def scan(payload: bytes, entry_off: int, hard_stops=frozenset(), barrier=None,
         pin_spans=(), c_spans=()):
    n = len(payload) // 4
    words = struct.unpack(f"<{n}I", payload[: n * 4])

    # Pinned spans (hand-verified rows: audited data AND hand-carved code
    # islands) are no-walk zones: no walk may start inside one or consume a
    # word of one. hard_stops alone only blocks seeds AT the pinned START
    # offset - a j-target landing a few words into the span still seeded a
    # walk that swallowed the rest of the pin (witnessed: g3_eu
    # func_80022A1C carved out of the pinned data_80022A18's first four
    # bytes onward).
    pin_mask = bytearray(n)
    for ps, pe in pin_spans:
        for w in range(ps // 4, min((pe + 3) // 4, n)):
            pin_mask[w] = 1

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
        if pin_mask[a // 4]:
            return None  # pinned data: never start a walk inside a pin
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
            # pinned data: stop BEFORE consuming the first pin word
            if i != a // 4 and pin_mask[i]:
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
    # `noseed` rows (cron-20261012-1141): pre-seed them into covered so
    # every seed filter (in_covered, the rescue's mask scan) refuses to
    # START a walk inside one - a prologue pair at the function's second
    # instruction or a mid-function .L trampoline target must not anchor
    # a walk that re-decomposes the oracle-verified zone (witnessed:
    # mainmenu_jp func_8002C478). Scoped per row: unmarked rows behave
    # exactly as before. The v2/v3b seed passes below also skip these
    # ranges - the matched code's own branch targets must not seed walks
    # into the (screened) zones around it.
    c_starts = {ps for ps, _pe in c_spans}
    for ps, pe in c_spans:
        covered[ps] = pe
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
        if s in c_starts:
            continue
        for i in range(s // 4, e // 4):
            t = branch_target(i, words[i])
            if t is None:
                continue
            o = v2o(t)
            if o is not None and not in_covered(o & ~3) \
                    and (o & ~3) not in hard_stops \
                    and not pin_mask[(o & ~3) // 4]:
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
            if s in c_starts:
                continue
            for i in range(s // 4, e // 4):
                if (words[i] >> 26) != 0x02:
                    continue
                o = v2o(((words[i] & 0x3FFFFFF) << 2) | (BASE & 0xF0000000))
                if o is not None and not in_covered(o & ~3) \
                        and (o & ~3) not in hard_stops \
                        and not pin_mask[(o & ~3) // 4]:
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
            if mask[i] or pin_mask[i]:
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
                if body_idx is not None and trimmed[body_idx][0] in hard_stops:
                    continue  # never extend a kept row (matched C / pins)
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
    functions. Returns {offset: (type, name, size)}, the set of `pinned`
    offsets, and the set of `sdk` offsets (byte-verified SDK member rows
    carved by the v6 rule) - the latter two are pinned-class: hard
    no-walk spans whose marker must be re-emitted into the generated
    block. A `c` row carrying an `sdk` marker keeps the ANNOTATION only
    (`sdk_c`): the row is already preserved by type, and a matched C
    function must never join the no-walk pin set - but the marker is
    evidence and must survive the re-scan (it was being dropped, the
    d683dc9 marker-loss class for the sdk annotation).

    v3 note: `c` entries are always preserved, and a `data` entry carrying a
    `pinned` marker is preserved too (a range verified by hand to be data).
    Unmarked `data` subsegments are the scanner's own auto-named output and
    get regenerated wholesale — since v3 rescues real code out of data gaps,
    treating old data starts as immutable types would re-type rescued
    functions back to data.
    The recorded SIZE matters as much as the type: the C file was matched
    against a subsegment of exactly that size, so the defensive split in
    main() must carve the c-range out at that size, not to the end of the
    merged range (the range may contain v3-rescued code the C file must
    not swallow — witnessed with the 0x10-byte func_80025AE0 stub).
    """
    kept = {}
    pinned = set()
    sdk = set()
    sdk_c = set()
    noseed = set()
    if not yaml_path.exists():
        return kept, pinned, sdk, sdk_c, noseed
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
        if not m:
            continue
        # `c` is hand-set and always preserved. A row carrying a `pinned`
        # marker is a hand-verified row of the type written on the line:
        # `data` pins are hand-audited data (code_data_screen DATA verdicts),
        # `asm` pins are hand-carved code islands (FABRIC honesty carves).
        # A row carrying an end-of-line `sdk` marker is a byte-verified SDK
        # member row carved by the v6 rule out of config/sdk_anchors.txt -
        # preserved the same way, so the tree keeps its carve even if the
        # anchors file is absent. All become exact-size hard rows below.
        # Blanket-preserving unmarked rows stays wrong (v3 rescues real code
        # from data gaps); only the explicit marker counts. A `c` row never
        # joins the no-walk pin set (walks may flow into a matched C
        # function and the defensive split in main() owns its exact-size
        # carve-out) - but a c row CAN carry a `noseed` marker: its zone
        # then refuses every walk SEED (v1 anchors, the v3 rescue's
        # prologue scan, v2/v3b branch-target seeds) while walks from
        # outside still flow through. Use it when the function's head is
        # not a prologue pair (a gp load or hand-asm opener defeats the
        # walk's anchor alignment) or mid-function .L trampoline targets
        # would anchor a walk that re-decomposes the oracle-verified zone
        # (witnessed: mainmenu_jp func_8002C478, whose prologue pair sits
        # one word past its head). Scoped per row on purpose: unmarked rows
        # behave exactly as before, so existing targets keep byte-identical
        # scans.
        is_sdk = re.search(r"#\s*0x[0-9A-Fa-f]+\s+sdk\s*$", ln) is not None
        is_noseed = re.search(r"#\s*0x[0-9A-Fa-f]+\s+noseed\s*$", ln) is not None
        if m.group(2) == "c" or "pinned" in ln or is_sdk:
            off = int(m.group(1), 16) - HDR
            kept[off] = (m.group(2), m.group(3), int(m.group(4), 16))
            if m.group(2) != "c":
                if is_sdk:
                    sdk.add(off)
                else:
                    pinned.add(off)
            elif is_sdk:
                sdk_c.add(off)
            elif is_noseed:
                noseed.add(off)
    return kept, pinned, sdk, sdk_c, noseed


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

    kept, pinned, sdk, sdk_c, noseed = preserved_types(
        yaml_path := REPO / "config" / f"splat.{target}.yaml")

    # v6 SDK anchors (docstring 13): byte-verified member spans become
    # pinned-class asm rows. The tree's kept rows win: an anchor at an
    # already-kept offset (a hand pin, a c function, or a previously carved
    # sdk row) is redundant at best and contradicted at worst - a size
    # mismatch means the archive extent disagrees with the hand-verified
    # state, and the tree is the thing that passes verify. Anchors
    # overlapping a DIFFERENT kept row are skipped loudly for the same
    # reason. Everything else becomes a kept row now, so the pin set below
    # covers it BEFORE the scan and the gap-carve pass lifts it out of the
    # data side afterwards.
    if "--no-sdk-anchors" not in argv[2:]:
        anchors = load_sdk_anchors(target)
    else:
        anchors = {}
    n_sdk_new = 0
    n_sdk_redundant = 0
    n_sdk_clash = 0
    for off, (size, name, member, lib, verdict) in sorted(anchors.items()):
        end = off + size
        if off in kept:
            kt, kn, ks = kept[off]
            if ks != size:
                print(f"scan: sdk anchor {name} ({member}/{lib}) at "
                      f"{BASE + off:08X}: archive extent {size:#x} != kept "
                      f"row size {ks:#x} - the tree wins")
                n_sdk_clash += 1
            else:
                n_sdk_redundant += 1
            continue
        clash = next(((k, ks) for k, (_kt, _kn, ks) in kept.items()
                      if k < end and off < k + ks), None)
        if clash:
            print(f"scan: sdk anchor {name} ({member}/{lib}) at "
                  f"{BASE + off:08X}: spans kept row at "
                  f"{BASE + clash[0]:08X} ({clash[1]:#x}) - skipped")
            n_sdk_clash += 1
            continue
        if end > len(payload):
            print(f"scan: sdk anchor {name} ({member}/{lib}) at "
                  f"{BASE + off:08X}: extent runs past the payload - skipped")
            n_sdk_clash += 1
            continue
        kept[off] = ("asm", f"func_{BASE + off:08X}", size)
        sdk.add(off)
        n_sdk_new += 1
    if anchors:
        print(f"scan: v6 sdk anchors: {n_sdk_new} carved, "
              f"{n_sdk_redundant} already carried by the tree, "
              f"{n_sdk_clash} skipped (tree wins)")

    hard_stops = frozenset(kept)
    # pinned rows (hand) and sdk rows (byte-verified members) are hard
    # no-walk spans, not just stop offsets. Rows carrying `noseed` (matched
    # c functions whose head the walk cannot align with) pre-seed `covered`
    # inside scan() instead: no walk may START inside one, while walks
    # from outside still flow through and the defensive split below owns
    # the exact-size carve.
    pin_spans = [(off, off + kept[off][2]) for off in pinned | sdk]
    noseed_spans = [(off, off + kept[off][2]) for off in noseed]

    ranges, cross_targets = scan(payload, entry_off, hard_stops,
                                 pin_spans=pin_spans, c_spans=noseed_spans)
    # Pin-span hygiene (cron-20261012-1026): the passes inside scan() (the
    # v3c merge, the v5 body-extension and its adjacency re-merge) can
    # bridge a range ACROSS a no-walk span - witnessed: slps_00270
    # func_80025AE0's 4-byte head extended leftward over its own pin and
    # merged with the predecessor, swallowing the matched C row. No range
    # may contain a byte-verified row's bytes: subtract every pin span
    # from every range here, before the defensive split and the gap
    # accounting see them.
    if pin_spans:
        clean = []
        for s, e in ranges:
            pieces = [[s, e]]
            for ps, pe in pin_spans:
                nxt = []
                for a, b in pieces:
                    if ps <= a and b <= pe:
                        continue  # fully inside the pin
                    if b <= ps or a >= pe:
                        nxt.append([a, b])
                        continue
                    if a < ps:
                        nxt.append([a, ps])
                    if pe < b:
                        nxt.append([pe, b])
                pieces = nxt
            clean.extend(pieces)
        ranges = clean
    # Same hygiene for kept c rows (cron-20261013-0741): a range may START
    # inside a matched C function - witnessed: sces_00269 jal's directly to
    # SsSetStereo+0x4 (a shared tail whose caller pre-loads $at), so the
    # walk covered the tail and left the function's head in a gap too small
    # to hold the row; the gap-carve then skipped it (off + size > gap end)
    # and the head was re-typed data, splitting the matched function.
    # Subtract every c span from every range here: the bytes become a hole
    # the gap-carve emits with the row's own type, and any walk range that
    # merely extended past the row is truncated at its end exactly as the
    # defensive split below would have done.
    c_spans = [(off, off + kept[off][2]) for off in kept if kept[off][0] == "c"]
    if c_spans:
        clean = []
        for s, e in ranges:
            pieces = [[s, e]]
            for ps, pe in c_spans:
                nxt = []
                for a, b in pieces:
                    if ps <= a and b <= pe:
                        continue  # fully inside the C row
                    if b <= ps or a >= pe:
                        nxt.append([a, b])
                        continue
                    if a < ps:
                        nxt.append([a, ps])
                    if pe < b:
                        nxt.append([pe, b])
                pieces = nxt
            clean.extend(pieces)
        ranges = clean
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

    # Kept rows inside a GAP: pin enforcement keeps code ranges from
    # covering a pinned span, so the surrounding gap would swallow it
    # (witnessed: mainmenu_jp data_800253C4 and the g3 pins absorbed into
    # the leading data row when no walk started at the pin). Carve every
    # kept row that sits fully inside a gap out as its own subsegment
    # piece; the leftovers stay data gaps. This is also the path every
    # hand-carved asm pin takes: its span is a no-walk zone, so the walk
    # never rediscovers it and the carve's own bytes are authoritative.
    kept_gap_rows = []
    carved_gaps = []
    for gs, ge in gaps:
        cur = gs
        for off in sorted(kept):
            typ, name, ksize = kept[off]
            if off < cur or off + ksize > ge:
                continue
            if cur < off:
                carved_gaps.append((cur, off))
            kept_gap_rows.append((off, typ, name, ksize))
            cur = off + ksize
        if cur < ge:
            carved_gaps.append((cur, ge))
    gaps = carved_gaps

    curated = load_curated(target)
    subsegs = []
    for s, e in ranges:
        typ, name = "asm", f"func_{BASE + s:08X}"
        if s in kept:
            typ, name = kept[s][0], kept[s][1]
        # NOTE: curated names are deliberately NOT applied to subsegment
        # names. splat derives each output file's name from them, and
        # tools/build.sh reads each section's address out of that file
        # name (`func_XXXXXXXX`). Curated names go into the symbols file
        # only, where the linker resolves them by address.
        subsegs.append((s, typ, name, e - s))
    for off, typ, name, ksize in kept_gap_rows:
        subsegs.append((off, typ, name, ksize))
    for s, e in gaps:
        subsegs.append((s, "data", f"data_{BASE + s:08X}", e - s))
    subsegs.sort()

    code_bytes = sum(e - s for s, e in ranges)
    data_bytes = sum(e - s for s, e in gaps)
    for _, typ, _, k in kept_gap_rows:
        if typ == "data":
            data_bytes += k
        else:
            code_bytes += k
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
        # Re-emit the `pinned`/`sdk`/`noseed` marker or the NEXT scan reads
        # an unmarked row, drops it from kept, and re-types the range.
        if off in pinned:
            mark = " pinned"
        elif off in sdk:
            mark = " sdk"
        elif off in sdk_c:
            mark = " sdk"
        elif off in noseed:
            mark = " noseed"
        else:
            mark = ""
        gen.append(f"      - [0x{HDR + off:X}, {typ}, {name}]   # {size:#x}{mark}")
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
    # Curated names win (loaded above, same mapping used for the yaml).
    sym_path = REPO / "config" / f"symbols.{target}.txt"
    stext = sym_path.read_text() if sym_path.exists() else ""
    head = stext.split("// BEGIN GENERATED FUNCTION SYMBOLS")[0]
    head = head.split("# BEGIN GENERATED FUNCTION SYMBOLS")[0].rstrip("\n")
    gen_syms = ["// BEGIN GENERATED FUNCTION SYMBOLS (tools/scan_functions.py)"]
    n_curated = 0
    for s, e in ranges:
        if s in curated:
            gen_syms.append(f"{curated[s]} = 0x{BASE + s:08X}; // type:func")
            n_curated += 1
        else:
            gen_syms.append(f"func_{BASE + s:08X} = 0x{BASE + s:08X}; // type:func")
    # Pinned hand-carved rows (e.g. SDK member entries re-typed out of data
    # gaps) can carry curated names too: the row start IS the member's
    # byte-verified entry address even though the walk never produced a
    # code range there. Symbols-file-only, like every curated name.
    for off, typ, _name, _k in kept_gap_rows:
        if typ == "asm" and off in curated:
            gen_syms.append(
                f"{curated[off]} = 0x{BASE + off:08X}; "
                f"// type:func (pinned member row)")
            n_curated += 1
    # v3b: cross-range branch targets (see scan()). Naming them lets
    # spimdisasm emit `j func_XXXXXXXX` instead of an unresolvable
    # file-local `.L`; the second link pass defines address-encoded names.
    # A cross target the target's curated scope already names (e.g. a
    # curated jal callee inside a still-data row) must NOT get an
    # address-encoded label too - splat rejects duplicate vram symbols
    # and the curated name wins (same rule as the pinned rows above).
    for o in sorted(cross_targets):
        if o in curated:
            continue
        gen_syms.append(f"func_{BASE + o:08X} = 0x{BASE + o:08X}; // type:func (branch target)")
    gen_syms.append("// END GENERATED FUNCTION SYMBOLS")
    # Curated data symbols: any curated offset that is not a function
    # entry names a data location (state-map words, record tables). Emit
    # them as `// type:s32` (the curated data contract: all current
    # curated data are `extern int`) so splat applies them to the
    # dlabels - the generated asm then defines the names and C externs
    # resolve against them. Mid-row splits follow automatically
    # (referenced-symbol splitting, same mechanism that splits dlabels
    # at code operands). splat's symbol parser has no bare `data` type;
    # a future non-int curated datum needs its own type plumbed through.
    consumed = set()
    for s, _e in ranges:
        if s in curated:
            consumed.add(s)
    for off, typ, _name, _k in kept_gap_rows:
        if typ == "asm" and off in curated:
            consumed.add(off)
    data_syms = []
    gp_abs = load_curated_gp_markers(target)
    for off in sorted(curated):
        if off in consumed:
            continue
        marker = " absolute:true" if off in gp_abs else ""
        data_syms.append(f"{curated[off]} = 0x{BASE + off:08X}; // type:s32{marker}")
        n_curated += 1
    out = head + "\n" + "\n".join(gen_syms) + "\n"
    if data_syms:
        out += "// BEGIN GENERATED DATA SYMBOLS (tools/scan_functions.py)\n"
        out += "\n".join(data_syms) + "\n"
        out += "// END GENERATED DATA SYMBOLS\n"
    sym_path.write_text(out)
    if n_curated:
        print(f"scan: kept {n_curated} curated symbol name(s)")

    print(f"wrote subsegments into {yaml_path.relative_to(REPO)} "
          f"and symbols into {sym_path.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

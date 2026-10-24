#!/usr/bin/env python3
"""sdk_members.py - locate Psy-Q library members in a retail binary.

This is the *linking* integration of the Psy-Q SDK, the counterpart to
tools/sdk_symbols.py's naming integration.

sdk_symbols.py answers "which SDK function does this three-instruction
veneer dispatch to?" by pattern-scanning the archives for stubs. That
only ever names pure veneers: a framed library function (LIBC's
`malloc` body, LIBSND's player routines) is invisible to it.

This tool answers the larger question - "which parts of this binary are
SDK library code at all?" - by re-doing what the original linker did:

  1. Parse the .LIB archives properly (Sony LNK object records: section
     directory, section data, relocations, symbol table).
  2. For every member, slide its .text over the retail payload and
     require every non-relocated byte to match. Relocated fields are
     zero in the unlinked object, so they are wildcards.
  3. RECONSTRUCT THE LINK for each candidate placement: resolve the
     member's own relocations against the image and require them to
     come out right --
       * a reference to a symbol defined in the same member must land
         exactly on that symbol's offset within the member;
       * a reference to another SDK member must land on the address
         where THAT member was located (global link-map consistency);
       * a reference to the member's own .data/.rdata must land in the
         small, plausible range that section occupies.
     A placement that satisfies 2 and 3 is not a coincidence: it is the
     address the original link put the member at.

Usage:
    python3 tools/sdk_members.py --libs ~/psyq/4.0/PSX/LIB
    python3 tools/sdk_members.py --libs <dir> --check
    python3 tools/sdk_members.py --libs <dir> --target slps_00270 --json
    python3 tools/sdk_members.py --windows \
        --libs ~/psyq/3.3/PSX/LIB --libs ~/psyq/3.5/PSX/LIB \
        --libs ~/psyq/3.6/PSX/LIB --libs ~/psyq/4.0/PSX/LIB

`--libs` may be repeated to index several Psy-Q versions; members whose
bytes are identical across versions collapse to one entry. `--windows`
switches to the symbol-window census: instead of requiring a whole member
to sit contiguously in the image (which presumes the game's SDK grouped
functions into members like the local drop), every function-symbol window
of every member is slid over the payload and exact byte spans are kept.
That mode writes config/sdk_windows.txt and never edits the whole-member
report.

The archives are the ones tools/sdk_symbols.py already reads (see
docs/MATCHING.md section 3b for how to get them); this script exits 0
and writes nothing if the directory is missing, so bare checkouts keep
working.
"""
import argparse
import json
import struct
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "config" / "sdk_members.txt"
OUT_WINDOWS = REPO / "config" / "sdk_windows.txt"

SEC_TEXT = 2          # section id of .text in every Psy-Q object seen
SEC_NAMES = {1: ".rdata", 2: ".text", 3: ".data", 4: ".sdata", 5: ".sbss",
             6: ".bss", 7: ".ctors", 8: ".dtors"}
_SEC_CANON = {v: k for k, v in SEC_NAMES.items()}

# Relocation field kinds, inferred from the instruction the linker patched.
# The object's stream gives a type byte; the encoding is checked against the
# image word anyway, so a wrong guess degrades to "unverified", never to a
# false claim.
R26 = "26"
RHI = "hi16"
RLO = "lo16"


# --------------------------------------------------------------------------
# archive parsing
# --------------------------------------------------------------------------
class Member:
    __slots__ = ("lib", "srcfile", "sections", "sec_ids", "relocs", "syms",
                 "xrefs", "xbss", "locals", "cur", "secmap")

    def __init__(self, lib):
        self.lib = lib
        self.srcfile = "?"
        self.sections = {}       # section id -> bytearray
        self.sec_ids = {}        # section id -> name
        self.secmap = {}         # raw record-stream id -> canonical SEC_NAMES id
                                 # (the 0xF000-section vintage: LIBAPI/LIBC/
                                 # LIBCARD/LIBCOMB/LIBSN number .text 0xF000,
                                 # .data 0xF001, ... instead of 2/3/...)
        self.relocs = []         # (section, offset, type, expr)
        self.syms = {}           # symbol number -> (section, offset, name)
        self.xrefs = {}          # symbol number -> external name
        self.xbss = {}           # symbol number -> external name
        self.locals = []         # (section, offset, name)
        self.cur = 0             # current section in the record stream

    @property
    def name(self):
        """Member name: the source file stem, e.g. `S_M_INIT` for S_M_INIT.C.

        The SDK records DOS paths ("C:\\PSX\\SRC\\..."), which os.path does
        not split on a POSIX host, so both separators are handled here.
        """
        leaf = self.srcfile.replace("\\", "/").rsplit("/", 1)[-1]
        return leaf.rsplit(".", 1)[0].upper()

    def text(self):
        return bytes(self.sections.get(SEC_TEXT, b""))

    def text_syms(self):
        """[(offset, name)] for symbols defined in .text, by offset.

        Exported (xdef) and local symbols both land in .text; an offset of 0
        is the start of the first function in the object.
        """
        out = [(o, n) for (s, o, n) in self.syms.values() if s == SEC_TEXT]
        out += [(o, n) for (s, o, n) in self.locals if s == SEC_TEXT]
        return sorted(set(out))


def _expr(data, i, member):
    """((kind, payload), next_i) for one relocation expression.

    0x00 constant, 0x02 address of symbol, 0x04 section base, 0x2c add,
    0x2e sub. Operands of add/sub are themselves expressions.
    """
    op = data[i]
    i += 1
    if op == 0x00:                                  # constant
        return ("const", struct.unpack_from("<I", data, i)[0]), i + 4
    if op == 0x02:                                  # address of symbol
        return ("sym", struct.unpack_from("<H", data, i)[0]), i + 2
    if op == 0x04:                                  # section base
        raw = struct.unpack_from("<H", data, i)[0]
        return ("sec", member.secmap.get(raw, raw)), i + 2
    if op in (0x2C, 0x2E):                          # add / sub
        left, i = _expr(data, i, member)
        right, i = _expr(data, i, member)
        return (("add" if op == 0x2C else "sub"), (left, right)), i
    raise ValueError(f"expression op {op:#x}")


def _record_stream(data, i, member, depth=0):
    """Walk the LNK record stream from `i`. Returns the offset after the end."""
    patch_offset = 0
    while i < len(data):
        tag = data[i]
        i += 1
        if tag == 0x00:                                     # end of member
            return i
        if tag == 0x02:                                     # section bytes
            n = struct.unpack_from("<H", data, i)[0]
            i += 2
            blob = data[i:i + n]
            i += n
            sec = member.cur
            buf = member.sections.setdefault(sec, bytearray())
            buf += blob
        elif tag == 0x06:                                   # section switch
            raw = struct.unpack_from("<H", data, i)[0]
            member.cur = member.secmap.get(raw, raw)
            i += 2
            patch_offset = len(member.sections.get(member.cur, b""))
        elif tag == 0x08:                                   # uninitialised
            n = struct.unpack_from("<I", data, i)[0]
            i += 4
            member.sections.setdefault(member.cur, bytearray()).extend(b"\0" * n)
        elif tag == 0x0A:                                   # relocation
            rtype = data[i]                                 # field kind
            i += 1
            off = struct.unpack_from("<H", data, i)[0]
            i += 2
            expr, i = _expr(data, i, member)
            member.relocs.append((member.cur, off + patch_offset, rtype, expr))
        elif tag == 0x0C:                                   # xdef
            num, sec, off = struct.unpack_from("<HHI", data, i)
            i += 8
            ln = data[i]
            nm = data[i + 1:i + 1 + ln].decode("latin1")
            i += 1 + ln
            member.syms[num] = (member.secmap.get(sec, sec), off, nm)
        elif tag == 0x0E:                                   # xref
            num = struct.unpack_from("<H", data, i)[0]
            i += 2
            ln = data[i]
            nm = data[i + 1:i + 1 + ln].decode("latin1")
            i += 1 + ln
            member.xrefs[num] = nm
        elif tag == 0x10:                                   # section def
            sec, _grp = struct.unpack_from("<HB", data, i)
            i += 3
            i += 2                                          # align
            ln = data[i]
            nm = data[i + 1:i + 1 + ln].decode("latin1")
            i += 1 + ln
            canon = _SEC_CANON.get(nm, sec)
            member.secmap[sec] = canon
            member.sec_ids[canon] = nm
        elif tag == 0x12:                                   # local symbol
            sec, off = struct.unpack_from("<HI", data, i)
            i += 6
            ln = data[i]
            nm = data[i + 1:i + 1 + ln].decode("latin1")
            i += 1 + ln
            member.locals.append((member.secmap.get(sec, sec), off, nm))
        elif tag == 0x1C:                                   # source file name
            _num = struct.unpack_from("<H", data, i)[0]
            i += 2
            ln = data[i]
            member.srcfile = data[i + 1:i + 1 + ln].decode("latin1")
            i += 1 + ln
        elif tag == 0x2E:                                   # cpu
            i += 1
        elif tag == 0x30:                                   # xbss
            num, _sec, _size = struct.unpack_from("<HHI", data, i)
            i += 8
            ln = data[i]
            nm = data[i + 1:i + 1 + ln].decode("latin1")
            i += 1 + ln
            member.xbss[num] = nm
        else:
            raise ValueError(f"record tag {tag:#x} at {i - 1:#x}")
    return i


def parse_archive(path):
    """[Member] for one .LIB."""
    data = path.read_bytes()
    lib = path.stem
    out = []
    i = 0
    while True:
        j = data.find(b"LNK\x02", i)
        if j < 0:
            return out
        m = Member(lib)
        # The first record after the 4-byte header is 0x2e (cpu). Start there.
        try:
            end = _record_stream(data, j + 4, m)
        except (ValueError, struct.error, IndexError):
            i = j + 4
            continue
        if m.text():
            out.append(m)
        i = end if end > j else j + 4


# --------------------------------------------------------------------------
# placement + link reconstruction
# --------------------------------------------------------------------------
def _word_at(payload, off):
    if off < 0 or off + 4 > len(payload):
        return None
    return struct.unpack_from("<I", payload, off)[0]

def _resolve(expr, base_off, member):
    """Address a relocation expression evaluates to, or None if unknown.

    None means "into a section this tool does not reconstruct" (the member's
    own .data/.rdata/.bss): those sections sit outside the .text placement we
    are testing, so the expression cannot be checked against the image. The
    relocation is recorded but not counted either way.
    """
    kind, val = expr
    if kind == "const":
        return val
    if kind == "sec":
        return base_off if val == SEC_TEXT else None
    if kind == "sym":
        if val in member.syms:
            sec, off, _nm = member.syms[val]
            return base_off + off if sec == SEC_TEXT else None
        return None                        # external: named, resolved by link map
    if kind in ("add", "sub"):
        left = _resolve(val[0], base_off, member)
        right = _resolve(val[1], base_off, member)
        if left is None or right is None:
            return None
        return left + right if kind == "add" else left - right
    return None


def _label_of(expr, member):
    """External symbol name the expression references, else None."""
    if expr[0] == "sym":
        n = expr[1]
        if n in member.xrefs:
            return member.xrefs[n]
        if n in member.xbss:
            return member.xbss[n]
    return None


def _flatten(expr):
    """(refkind, refval, addend) for an expression with a single reference.

    value = ref + addend. refkind is "const" (no reference), "sec" or "sym".
    Returns None for anything more tangled (sym - sym, two sections, ...):
    those cannot be pinned to one address and are counted as unverifiable.
    """
    kind = expr[0]
    if kind == "const":
        return ("const", None, expr[1])
    if kind in ("sec", "sym"):
        return (kind, expr[1], 0)
    if kind in ("add", "sub"):
        left = _flatten(expr[1][0])
        right = _flatten(expr[1][1])
        if left is None or right is None:
            return None
        if right[0] == "const":                       # ref +- const
            sign = 1 if kind == "add" else -1
            return (left[0], left[1], left[2] + sign * right[2])
        if kind == "add" and left[0] == "const":       # const + ref
            return (right[0], right[1], left[2] + right[2])
        return None
    return None


def verify(payload, member, base):
    """Reconstruct the link for one candidate placement.

    Every relocation in the member's .text is decoded out of the image and
    checked against what the expression says it must be:

      * a reference to the member's own .text (a symbol in it, or the section
        base) must land exactly on the address the placement implies;
      * a reference to one of the member's other sections (.data, .rdata,
        .sdata) yields that section's address -- and all the member's
        references to it must yield the SAME address, which is how the
        layout of a member whose data sits elsewhere is recovered;
      * a reference to another member's symbol is an external: it is
        resolved from the image and cross-checked against the global link
        map once every member has been placed.

    A placement where all of these hold is the address the original link
    used, not a byte-pattern coincidence.
    """
    stats = {"internal": 0, "internal_ok": 0, "external": 0, "other": 0,
             "externals": {}, "bases": {}, "bad": [], "secref": 0}
    fields = []
    for (sec, off, _type, expr) in member.relocs:
        if sec != SEC_TEXT:
            continue
        word = _word_at(payload, base + off)
        if word is None:
            stats["other"] += 1
            continue
        op = word >> 26
        if op in (2, 3):                       # j / jal: 26-bit target
            fields.append([off, expr, ((word & 0x03FFFFFF) << 2)
                           | (base & 0xF0000000), None, None])
        elif op == 0x0F:                       # lui: high half
            fields.append([off, expr, None, word & 0xFFFF, None])
        else:                                  # low half
            fields.append([off, expr, None, None, word & 0xFFFF])
    # A lui and the instruction that consumes its register form one address;
    # the linker wrote both halves, so pair them up.
    by_off = {f[0]: f for f in fields}
    for f in fields:
        if f[2] is None and f[3] is not None:
            nxt = by_off.get(f[0] + 4)
            if nxt is not None and nxt[4] is not None:
                f[2] = ((f[3] << 16) + ((nxt[4] ^ 0x8000) - 0x8000)) & 0xFFFFFFFF
    sec_bases = {}                             # section id -> {derived address}
    for f in fields:
        off, expr, full, hi, lo = f
        flat = _flatten(expr)
        if flat is None:
            stats["other"] += 1
            continue
        rkind, rval, addend = flat
        if rkind == "sym" and rval not in member.syms:
            # Defined outside the member: named by an xref (another member's
            # symbol) or an xbss (its own uninitialised data). Resolved from
            # the image; the label is what the link map is keyed on.
            label = member.xrefs.get(rval) or member.xbss.get(rval)
            stats["external"] += 1
            if label and full is not None:
                stats["externals"][label] = full
            continue
        want = None
        target_sec = None
        if rkind == "const":
            want = addend
        elif rkind == "sec":
            target_sec = rval
            # A section-relative reference. The image's field gives the
            # address the linker handed out; the difference from what this
            # placement implies is a constant for the member (the section's
            # share of the object), so every reference into the same section
            # must yield the SAME implied base. That agreement is the check.
            if full is None:
                stats["secref"] += 1
                if hi is not None:
                    continue
                continue
            implied = full - addend
            stats.setdefault("secbase", {}).setdefault(rval, set()).add(implied)
            cnt = stats.setdefault("secrefcnt", {})
            cnt[rval] = cnt.get(rval, 0) + 1
            continue
        elif rkind == "sym":
            tsec, toff, _nm = member.syms[rval]
            target_sec = tsec
            want = base + toff + addend if tsec == SEC_TEXT else None
        if want is None:
            # A section we do not know yet: the image tells us its address.
            if full is None:
                stats["other"] += 1
                continue
            if rkind == "sec":
                derived = full - addend
            else:
                derived = full - member.syms[rval][1] - addend
            stats["bases"].setdefault(target_sec, set()).add(derived)
            continue
        stats["internal"] += 1
        hit = False
        if full is not None:
            hit = full == want
        else:
            if hi is not None:
                hit = (want >> 16) & 0xFFFF == hi or \
                      ((want + 0x8000) >> 16) & 0xFFFF == hi
            else:
                hit = (want & 0xFFFF) == lo
        if hit:
            stats["internal_ok"] += 1
        else:
            stats["bad"].append((off, hex(want),
                                 hex(full if full is not None else (hi if hi is not None else lo))))
    stats["bases"] = {k: v for k, v in stats["bases"].items() if v}
    return stats


def is_anchor(stats):
    """True when the placement reconstructs: relocations either land exactly
    on the member's own symbols, or every reference into one of its sections
    agrees on a single link base.

    The second form is what the objects use for intra-object jumps: the
    image's target is not `member + offset` (the object's section is not the
    code alone), but all of a member's references into one section do share
    one implied base, and a false placement does not reproduce that.
    """
    if stats["internal"] and stats["internal_ok"] == stats["internal"]:
        return True
    bases = stats.get("secbase") or {}
    if not bases:
        return False
    # Every reference into a section must agree on one base, and there must
    # be at least two references: one field agrees with itself by default.
    if any(len(v) != 1 for v in bases.values()):
        return False
    return sum((stats.get("secrefcnt") or {}).values()) >= 2


def locate(payload, member, min_fixed=8):
    """[(offset, stats)] candidate placements of `member` in `payload`.

    The unlinked object carries zeroes at relocated fields, so a byte that is
    zero in the object constrains nothing; every non-zero byte must match.
    """
    text = member.text()
    fixed = [i for i, b in enumerate(text) if b]
    if len(fixed) < min_fixed or not text:
        return []
    # Anchor on the first fixed byte. .text is word aligned in both the
    # object and the image, so only congruent offsets can be placements.
    k = fixed[0]
    anchor = bytes([text[k]])
    out = []
    start = 0
    while True:
        j = payload.find(anchor, start)
        if j < 0:
            return out
        start = j + 1
        s = j - k
        if s < 0 or (s & 3) or s + len(text) > len(payload):
            continue
        for i in fixed:
            if payload[s + i] != text[i]:
                break
        else:
            out.append((s, verify(payload, member, s)))


def locate_windows(payload, member, min_span=0x40, probe=0x40,
                   min_fixed=8, max_wild_run=0x10):
    """[(offset, size, [(delta, name)], mark)] member-text spans in payload.

    The whole-member slide above assumes the game's SDK grouped functions
    into archive members exactly like the local drop. When it grouped them
    differently (a member ends early, or continues with functions ours puts
    elsewhere), the whole member is not in the image and the slide sees
    nothing - even though a contiguous run of library functions is there
    byte for byte. Slide from every function symbol instead and extend to
    the first divergence.

    mark is 'verbatim' when every byte of the span equals the unlinked
    object's .text, or 'fixed' when bytes that are zero in the object
    (relocated fields at link time) were treated as wildcards and every
    other byte matched - the same standard the whole-member slide uses,
    gated on `min_fixed` non-wildcard bytes so a span cannot ride on a
    handful of coincidences. A span breaks after `max_wild_run` consecutive
    wildcard bytes, so it cannot wander through unrelated data on a chain
    of zero fields.
    """
    text = member.text()
    syms = [s for s in member.text_syms()
            if isinstance(s, tuple) and len(s) == 2]
    if len(text) < min_span or len(syms) < 2:
        return []
    out = []
    for soff, _sname in syms:
        window = text[soff:]
        if len(window) < min_span:
            break
        # needle: longest run of non-zero bytes in the probe. A masked
        # scan needs at least 4 fixed bytes or the window is degenerate
        # (the BIOS-thunk families) and stays the whole-member report's
        # business.
        head = window[:probe]
        run = 0
        best = (0, 0)          # (length, start)
        for i, b in enumerate(head + b"\x01"):
            if b:
                run += 1
                if run > best[0]:
                    best = (run, i - run + 1)
            else:
                run = 0
        nlen, noff = best
        if nlen < 4:
            continue
        needle = head[noff:noff + nlen]
        off = payload.find(needle)
        while off != -1:
            s = off - noff
            off = payload.find(needle, off + 1)
            if s < 0 or s & 3:
                continue
            # extend over whole words; a word matches when every nonzero
            # object byte in it equals the payload byte
            end = 0
            wild = 0
            for k in range(0, len(window) - 3, 4):
                if s + k + 4 > len(payload):
                    break
                w = window[k:k + 4]
                pw = payload[s + k:s + k + 4]
                if not any(w):
                    wild += 4
                    if wild > max_wild_run:
                        break
                    end = k + 4
                    continue
                if any(a and a != b for a, b in zip(w, pw)):
                    break
                wild = 0
                end = k + 4
            size = end
            if size < min_span:
                continue
            fixed = sum(1 for b in window[:size] if b)
            if fixed < min_fixed:
                continue
            names = [(s2 - soff, str(n)) for s2, n in syms
                     if soff <= s2 < soff + size and soff + size - s2 >= 8]
            if len(names) < 2 and size < 0x100:
                continue
            exact = window[:size] == payload[s:s + size]
            out.append((s, size, names, "verbatim" if exact else "fixed"))
    # nested windows of the same span collapse to the longest
    out.sort(key=lambda x: (x[0], -x[1]))
    kept = []
    for off, size, names, mark in out:
        if kept and off < kept[-1][0] + kept[-1][1]:
            continue
        kept.append((off, size, names, mark))
    return kept


def load_sigs(sigdir):
    """{MEMBER: (pattern, mask)} from psx_psyq_signatures JSON, if available.

    That database is generated independently from the same Psy-Q archives
    (lab313ru/psx_psyq_signatures, version 400 = 4.0) and marks relocated
    bytes `??`. Matching it is a second opinion on where a member sits.
    """
    out = {}
    if not sigdir.is_dir():
        return out
    for f in sorted(sigdir.glob("*.json")):
        try:
            objs = json.loads(f.read_text())
        except ValueError:
            continue
        for o in objs:
            sig = o.get("sig", "").strip()
            if not sig:
                continue
            pat = bytearray()
            msk = bytearray()
            for tok in sig.split():
                if tok == "??":
                    pat.append(0)
                    msk.append(0)
                else:
                    pat.append(int(tok, 16))
                    msk.append(1)
            out.setdefault(Path(o["name"]).stem.upper(),
                           (bytes(pat), bytes(msk)))
    return out


def cross_check(payload, member, off, sigs):
    """Where the signature DB puts this member: "agree", "elsewhere", ""."""
    ent = sigs.get(member.name)
    if ent is None:
        return ""
    pat, msk = ent
    fixed = [i for i, v in enumerate(msk) if v]
    if not fixed:
        return ""
    k = fixed[0]
    hits = []
    start = 0
    while True:
        j = payload.find(bytes([pat[k]]), start)
        if j < 0:
            break
        start = j + 1
        s = j - k
        if s < 0 or (s & 3) or s + len(pat) > len(payload):
            continue
        if all(payload[s + i] == pat[i] for i in fixed):
            hits.append(s)
    if off in hits:
        return "agree"
    return "elsewhere" if hits else "no-hit"


def _overlaps(off, member, placements):
    """True when another member claims bytes this placement covers.

    Library members come in near-identical groups (GsDrawOt / GsDrawOtIO,
    the 32-byte SYSCALL stubs). A member that is not alone in its bytes is
    not evidence on its own.
    """
    lo, hi = off, off + len(member.text())
    for o, m, _st in placements:
        if (o, id(m)) == (off, id(member)):
            continue
        if o < hi and off < o + len(m.text()):
            return True
    return False


def cfg_subsegments(target):
    """VRAM addresses that start a subsegment in the target's splat yaml."""
    import yaml
    yml = REPO / "config" / f"splat.{target}.yaml"
    if not yml.is_file():
        return []
    cfg = yaml.safe_load(yml.read_text())
    seg = cfg["segments"][0]
    lo, vram = seg["start"], seg["vram"]
    out = []
    for sub in seg["subsegments"]:
        if isinstance(sub, list) and len(sub) >= 2 and isinstance(sub[0], int) \
                and sub[1] in ("asm", "c"):
            out.append(vram + sub[0] - lo)
    return out


def subsegment_kinds(target):
    """[(vram_start, kind, name)] for every named subsegment in the yaml.

    vram_start is the address carried in the subsegment NAME - the ground
    truth the build links by - not the linear vram+off-lo map (the yaml is
    a scatter list; see yaml_anchors).
    """
    out = []
    for off, kind, name, nv in yaml_anchors(target, with_kind=True):
        if nv is not None:
            out.append((nv, kind, name))
    return out


_NAME_RE = None


def yaml_anchors(target, with_kind=False):
    """[(raw_file_off, name_vram)] anchors from the target's yaml.

    The yaml is a scatter list: build.sh places each subsegment's file
    range at the vram in its name, and vram is NOT linear in file offset -
    the images carry load-region gaps (mainmenu_eu names drift up to
    0xf5d0 past any linear map). Names are the ground truth: verify is
    green against them. Convert offsets and vram through these anchors.

    Only names carrying an _XXXXXXXX address anchor positions; with_kind
    also returns (off, kind, name, vram) for EVERY typed subsegment -
    vram None for real names (a landed `c` row like LightColor has no
    address in its name), which is how callers find landed starts.
    """
    global _NAME_RE
    import re
    import yaml
    if _NAME_RE is None:
        _NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*_([0-9A-Fa-f]{8})"
                              r"(?:\.[A-Za-z0-9_]+)?$")
    yml = REPO / "config" / f"splat.{target}.yaml"
    if not yml.is_file():
        return []
    cfg = yaml.safe_load(yml.read_text())
    out = []
    for sub in cfg["segments"][0]["subsegments"]:
        if isinstance(sub, list) and len(sub) >= 3 and isinstance(sub[0], int):
            m = _NAME_RE.match(str(sub[2]))
            if with_kind:
                out.append((sub[0], sub[1], str(sub[2]),
                            int(m.group(1), 16) if m else None))
            elif m:
                out.append((sub[0], int(m.group(1), 16)))
    out.sort(key=lambda x: x[0])
    return out


def raw_to_name(off, anchors):
    """File offset -> vram, linear within the bracketing anchor pair."""
    import bisect
    if not anchors:
        return None
    i = bisect.bisect_right([a[0] for a in anchors], off) - 1
    if i < 0:
        return None
    a0, v0 = anchors[i]
    return v0 + (off - a0)


def name_to_raw(v, anchors):
    """vram -> file offset, linear within the bracketing anchor pair."""
    import bisect
    if not anchors:
        return None
    byv = sorted((v0, a0) for a0, v0 in anchors)
    i = bisect.bisect_right([b[0] for b in byv], v) - 1
    if i < 0:
        return None
    v0, a0 = byv[i]
    return a0 + (v - v0)


def known_addresses(target):
    """RAW file offsets already reported for `target` in sdk_anchors.txt
    and sdk_members.txt, so window hits can be flagged.

    Those reports carry linear-space addresses (address - segment vram =
    payload offset; the scan's consumption contract), so each address is
    converted back to the raw offset it was found at - the space the
    window census works in.
    """
    out = set()
    yml = REPO / "config" / f"splat.{target}.yaml"
    if not yml.is_file():
        return out
    import yaml
    cfg = yaml.safe_load(yml.read_text())
    seg = cfg["segments"][0]
    lo, vram = seg["start"], seg["vram"]
    for fn in ("sdk_anchors.txt", "sdk_members.txt"):
        p = REPO / "config" / fn
        if not p.is_file():
            continue
        cur = None
        for line in p.read_text().splitlines():
            if line.startswith("// target:"):
                cur = line.split()[2]
            elif cur == target:
                body = line.lstrip("/ ").strip()
                if body.startswith("0x"):
                    out.add(int(body.split()[0], 16) - vram + lo)
    return out


def load_target(target):
    """(payload, file_offset_of_payload, vram_of_payload) from the splat yaml."""
    import yaml
    yml = REPO / "config" / f"splat.{target}.yaml"
    if not yml.is_file():
        return None
    cfg = yaml.safe_load(yml.read_text())
    seg = cfg["segments"][0]
    # base_path is relative to the yaml's own directory, the way splat reads it.
    path = (yml.parent / cfg["options"]["base_path"]
            / cfg["options"]["target_path"]).resolve()
    if not path.is_file():
        return None
    return path.read_bytes(), seg["start"], seg["vram"]


def run_windows(args, members, targets):
    """--windows mode: symbol-window census -> config/sdk_windows.txt.

    Addresses in the output are the yaml NAME space (the vram the build
    links by), converted through yaml_anchors; the star comparison works
    in raw file offsets.
    """
    report = {}
    for t in targets:
        loaded = load_target(t)
        if not loaded:
            print(f"  {t:<12} skipped (no yaml or no baseline image)")
            continue
        payload, lo, vram = loaded
        anchors = yaml_anchors(t)
        spans = []
        for m, vers in members:
            for off, size, names, mark in locate_windows(payload, m):
                spans.append((off, size, m, "+".join(sorted(vers)),
                              names, mark))
        spans.sort(key=lambda x: (x[0], -x[1]))
        kept = []
        for off, size, m, vers, names, mark in spans:
            if kept and off < kept[-1][0] + kept[-1][1]:
                continue
            kept.append((off, size, m, vers, names, mark))
        report[t] = kept
        nf = sum(len(k[4]) for k in kept)
        nv = sum(1 for k in kept if k[5] == "verbatim")
        print(f"  {t:<12} {len(kept):<4} spans ({nv} verbatim), {nf} functions")

    lines = [
        "// SDK symbol-window report - GENERATED by tools/sdk_members.py --windows.",
        "//",
        "// Regenerate:  python3 tools/sdk_members.py --windows \\",
        "//     --libs ~/psyq/3.3/PSX/LIB --libs ~/psyq/3.5/PSX/LIB \\",
        "//     --libs ~/psyq/3.6/PSX/LIB --libs ~/psyq/4.0/PSX/LIB",
        "//",
        "// The whole-member report (sdk_members.txt) assumes the game's SDK",
        "// grouped functions into archive members exactly like the local drop.",
        "// When it grouped them differently, a contiguous run of library",
        "// functions can sit in the image and the whole-member slide sees",
        "// nothing. This report slides every function-symbol window of every",
        "// member (all indexed Psy-Q versions).",
        "//",
        "// MARKS",
        "//",
        "//   verbatim  every byte of the span equals the unlinked object's",
        "//             .text: library code verbatim.",
        "//   fixed     bytes that are zero in the object (relocated fields at",
        "//             link time) were wildcards and every other byte",
        "//             matched - the whole-member slide's standard, with its",
        "//             >= 8 fixed-byte gate. A span breaks after 0x10",
        "//             consecutive wildcard bytes.",
        "//",
        "// Columns: address, size, mark, member@versions, [kind of the yaml",
        "// subsegment the span starts in], function symbols inside the span.",
        "// A trailing * on a name: no line in sdk_anchors.txt or",
        "// sdk_members.txt carries that address - i.e. new evidence.",
        "// Names are evidence, not configuration: adopted names live in",
        "// config/symbols.curated.txt - read the guard block at its top first.",
        "",
    ]
    for t in sorted(report):
        kept = report[t]
        known = known_addresses(t)
        kinds = subsegment_kinds(t)
        anchors = yaml_anchors(t)
        nf = sum(len(k[4]) for k in kept)
        nv = sum(1 for k in kept if k[5] == "verbatim")
        lines.append(f"// target: {t}  ({len(kept)} spans, {nv} verbatim, "
                     f"{nf} functions)")
        for off, size, m, vers, names, mark in kept:
            vr = raw_to_name(off, anchors)
            if vr is None:
                continue
            kind = ""
            for start, k, _n in kinds:
                if start <= vr:
                    kind = k
            marked = [n + ("*" if (off + d) not in known else "")
                      for d, n in names]
            lines.append(f"  {vr:#010x} {size:#06x} {mark:<9} {m.lib}@{vers} "
                         f"{m.name} [{kind}] " + " ".join(marked))
        lines.append("")
    OUT_WINDOWS.parent.mkdir(parents=True, exist_ok=True)
    OUT_WINDOWS.write_text("\n".join(lines))
    print(f"sdk_members: wrote {OUT_WINDOWS.relative_to(REPO)}")
    return 0


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--libs", type=Path, required=True, action="append",
                    help="directory holding the Psy-Q *.LIB archives; "
                         "repeat to index several Psy-Q versions")
    ap.add_argument("--windows", action="store_true",
                    help="scan for verbatim symbol-window spans instead of "
                         "whole members; writes config/sdk_windows.txt")
    ap.add_argument("--target", action="append", default=None)
    ap.add_argument("--check", action="store_true", help="report only")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--min-fixed", type=int, default=8,
                    help="minimum number of non-wildcard bytes in a member "
                         "(8 so the 16-byte zero-relocation BIOS thunks "
                         "census - they carry exactly 9 non-zero bytes)")
    ap.add_argument("--sigs", type=Path, default=None,
                    help="psx_psyq_signatures/<ver> dir; corroborate placements")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args(argv[1:])

    import re
    members = []          # (Member, {psy-q versions it was parsed from})
    seen = {}
    for libdir in args.libs:
        if not libdir.is_dir():
            print(f"sdk_members: {libdir} is not a directory", file=sys.stderr)
            return 0
        m = re.search(r"(\d+\.\d+)", str(libdir))
        ver = m.group(1) if m else libdir.name
        for lib in sorted(libdir.glob("LIB*.LIB")):
            for mem in parse_archive(lib):
                if not mem.text():
                    continue
                key = (mem.lib, mem.name, mem.text())
                if key in seen:
                    seen[key][1].add(ver)
                else:
                    seen[key] = (mem, {ver})
                    members.append(seen[key])
    print(f"sdk_members: {len(members)} distinct SDK members parsed from "
          f"{len(args.libs)} lib dir(s)")
    if not members:
        print(f"sdk_members: no members found under {args.libs}", file=sys.stderr)
        return 0

    sigs = load_sigs(args.sigs) if args.sigs else {}
    if args.sigs:
        print(f"sdk_members: {len(sigs)} signature patterns from {args.sigs}")
    targets = args.target or [p.name[len("splat."):-len(".yaml")]
                              for p in sorted((REPO / "config").glob("splat.*.yaml"))]

    if args.windows:
        return run_windows(args, members, targets)

    report = {}
    for t in targets:
        loaded = load_target(t)
        if not loaded:
            print(f"  {t:<12} skipped (no yaml or no baseline image)")
            continue
        payload, lo, vram = loaded
        placements = []
        for m, _vers in members:
            for off, stats in locate(payload, m, args.min_fixed):
                placements.append((off, m, stats))
        placements.sort(key=lambda x: x[0])
        # Anchors are placements whose own symbol references were restored:
        # the member's internal call graph lands where its symbol table says.
        # Their symbols define the link map -- the addresses the original
        # link gave each library symbol.
        anchors = [(o, m, st) for o, m, st in placements if is_anchor(st)]
        linkmap = {}
        for off, m, _st in anchors:
            base = vram + (off - lo)
            for soff, sname in m.text_syms():
                linkmap.setdefault(sname, set()).add(base + soff)
        # Every other placement is checked against that map: a reference to a
        # symbol the map knows must resolve to the mapped address.
        verified = []
        conflicts = []
        for off, m, st in placements:
            bad = [(n, hex(got)) for n, got in st["externals"].items()
                   if n in linkmap and len(linkmap[n]) == 1
                   and got not in linkmap[n]]
            if bad:
                conflicts.append((hex(vram + off - lo), m.name, bad[:2]))
            else:
                verified.append((off, m, st))
        for off, m, st in placements:
            st["cross"] = cross_check(payload, m, off, sigs)
        starts = set()
        for sub in cfg_subsegments(t):
            starts.add(sub)
        report[t] = (lo, vram, placements, anchors, verified, linkmap,
                     conflicts, starts)
        amb = sum(1 for off, m, _st in placements if _overlaps(off, m, placements))
        uniq = len(placements) - amb - len(anchors)
        xagree = sum(1 for _o, _m, st in placements if st.get("cross") == "agree")
        xtail = f", {xagree} signature-DB agreements" if sigs else ""
        print(f"  {t:<12} {len(placements):<4} placements -> {len(anchors)} anchored, "
              f"{uniq} unique, {amb} ambiguous{xtail}")

    if args.json:
        out = {}
        for t, r in report.items():
            placements, anchors, verified, linkmap, conflicts = r[3], r[4], r[5], r[6], r[7]
            out[t] = {
                "placements": len(placements),
                "cross_agreements": sum(1 for _o, _m, st in placements
                                        if st.get("cross") == "agree"),
                "anchored": {m.name: hex(r[1] + (o - r[0]))
                             for o, m, _s in anchors},
                "named": {n: [hex(a) for a in sorted(v)] for n, v in linkmap.items()},
                "conflicts": conflicts,
            }
        print(json.dumps(out, indent=1))
        return 0

    if args.check:
        return 0

    lines = [
        "// SDK member report - GENERATED by tools/sdk_members.py.",
        "//",
        "// Regenerate:  python3 tools/sdk_members.py --libs <psyq lib dir>",
        "//",
        "// This is the LINKING integration of the Psy-Q SDK, the counterpart to",
        "// the veneer naming in tools/sdk_symbols.py: it locates whole library",
        "// members - framed functions, not just three-instruction stubs - and",
        "// reports the names each one defines.",
        "//",
        "// MARKS",
        "//",
        "//   anchored   the member's own relocations were reconstructed: either",
        "//              a reference into its .text lands exactly on one of its",
        "//              symbols, or every reference into one of its sections",
        "//              agrees on a single link base. A wrong placement does",
        "//              not reproduce that agreement.",
        "//   unique     structural match only (the whole member .text is in the",
        "//              image, relocated fields excluded), but the member was",
        "//              found at exactly one address and no other member claims",
        "//              that address.",
        "//   ambiguous  several members claim one address, or one member claims",
        "//              several addresses. Library stubs are near-identical -",
        "//              the 32-byte SYSCALL veneers especially - so these are",
        "//              NOT evidence. tools/sdk_symbols.py resolves the veneers",
        "//              that are pure stubs by vector/index instead.",
        "//",
        "// `adoptable` marks a name whose address is also the start of an `asm`",
        "// or `c` subsegment in the target's splat yaml, i.e. a name the scanner",
        "// could apply. Names ending inside another function are evidence about",
        "// that region but cannot be applied as they stand.",
        "//",
        "// Names are evidence, not configuration: adopted names live in",
        "// config/symbols.curated.txt - read the guard block at its top first.",
        "",
    ]
    for t in sorted(report):
        (lo, vram, placements, anchors, verified, linkmap, conflicts,
         starts) = report[t]
        anchorset = {id(x) for x in anchors}
        lines.append(f"// target: {t}  ({len(placements)} placements, "
                     f"{len(anchors)} anchored, {len(linkmap)} named symbols)")
        for off, m, st in placements:
            addr = vram + (off - lo)
            if id((off, m, st)) in anchorset:
                mark = "anchored"
            elif _overlaps(off, m, placements):
                mark = "ambiguous"
            else:
                mark = "unique"
            base = vram + (off - lo)
            for soff, sname in m.text_syms():
                a = base + soff
                adopt = " adoptable" if a in starts else ""
                x = st.get("cross") or ""
                lines.append(f"//   {a:#010x} {m.lib:<9} {m.name:<14} "
                             f"{mark:<10} {sname}{adopt}"
                             f"{'  (sig-db ' + x + ')' if x else ''}")
        lines.append("")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines))
    print(f"sdk_members: wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

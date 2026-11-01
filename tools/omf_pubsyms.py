#!/usr/bin/env python3
"""omf_pubsyms - the psyq .LIB (LIB\\x01 container) symbol-table extractor.

The psyq-symbol curation pass's evidence step for the held numeric statics
(D_800AB0B0/C8/D0..F4 in src/func_800642A0.c): the archive's own symbol
tables carry (module, section-class, offset) triples that - IF the game
linked this archive - would anchor the game-side D_ slots to archive names.

CONTAINER LAYOUT (reverse-engineered 2026-10-31 off psyq 3.3 LIBSPU.LIB,
verified against 66 modules + LIBSND/LIBAPI/LIBGPU smoke runs; format is
NOT the GNU ar shape and NOT raw OMF - it is Sony's PSYLIB container):

  0x00  "LIB\\x01" magic
  0x04  lib name, 8 bytes, space padded ("SPU     ")
  0x04  module chain; each module:
          name8 (first module reuses the lib name)
          +8   "4c 1f" + u8 + "a1" + u32 0x20 + u32 size   (12-byte header;
               size = module name offset -> next module name offset)
          +20  publics: [u8 len][name] pairs, 0x00-terminated
               then "LNK" section-name table:
                 [u8 len][name][0x10][u32 index][0x08] entries; the last
                 entry is followed by 0x1c (debug source-path region;
                 multi-file modules carry REPEATED 1c-path records:
                 [0x1c][u8][0x00][u8 len][path] - VMANAGER has 17)
               then section blobs (06 xx 00 / 02 yy 00 chunk headers -
               NOT parsed by this tool; see the base-note below), then the
               symbol ROW STREAM (one continuous run to the tail):
                 [u8 len][name][kind][payload] entries, kinds
                   0x0c -> (u16 a, u16 b, u32 off)  # def (code class)
                   0x0e -> u16 index                # lib-wide ref
                   0x12 -> (u16 w, u32 v)           # second ref class
                   0x30 -> (u16 a, u16 b, u32 off)  # def (data class)
               (the walk stops at any other kind byte)
          module tail: [u8 len][name] 0x00 ending exactly at the next
          module (observed tail name = the module's last public)

GROUP MODEL (banked cron-20261101-0536, resolves the ALIAS? class): a
module's publics are the COMPILATION GROUP's exports, not per-object
defs - a public whose only row is a 0x0e/0x12 ref is defined in a
SIBLING module of the same group (VMANAGER's SpuVmKeyOff ref idx=85
defines in SEQREAD; SpuVmInit DOES def here at .text+0x314c). Def-row
offsets are base-relative; VMANAGER's base measured at file 0x10668
(23/38 def starts on addiu-sp prologues + the _svm_damper def-boundary
identity) - see the CHUNK-GRAMMAR note below for the banked laws.

CHUNK GRAMMAR (banked cron-20261101-0651, the post-LNK region between
the LNK table and the symbol row stream; probe =
scripts/probe_psylib_chunks.py, scripts/probe_psylib_bases.py):

  after the LNK table's index-less last entry, the 0x1c byte of that
  entry DOUBLES as the kind byte of the first debug-path record:
    [0x1c][u8 tag][0x00][u8 len][path]   (ascii, e.g.
     1c 40 00 1f 'E:\\PS-X~~00\\SRC\\SND\\VM\\UT_AKO.C'; VMANAGER has 18
     with DECREASING tags 0x40..0x09 - tag meaning open)
  then the chunk zone, shapes observed:
    [0x06][u8 seg][0x00]                 3-byte section marker
    [0x02][u16 size][size bytes]         data chunk (code or data)
    [0x0a][u8 t][u16 off]                4-byte record, offsets strictly
                                         increasing across the run
    [0x2c][0x00][u32 v]                  6-byte record
    [0x2c][0x04][u16 w][u32 v]           9-byte record (w/v = the 0x12
                                         payload shape: w=2 code, w=6
                                         data class)
  the 02-record's u16 size bounds its data EXACTLY (VMANAGER chunk 1:
  size 0x0ffc, data 0xf6c2..0x106be, ends jr $ra + nop, next byte is a
  0x0a record) - but the general inter-record law (what bounds a run
  of 0a/2c records, when a 02-chunk starts without an 0x06 marker) is
  NOT yet derived; the record zone between VMANAGER's two code blobs
  (0x106be..0x11820) carries no addiu-sp/sw-ra word at either 4-byte
  alignment, then code resumes mid-stream at 0x11820 WITHOUT a header.

DEF-BASE LAW (empirical, cron-20261101-0651 + 0806; the base DERIVATION
from the record structure stays open - LANE FLAG): every module's 0x0c
b=2 def offsets are FLAT ARCHIVE-FILE offsets from ONE per-module base
(VMANAGER: all 38 land on valid MIPS heads under base 0x10668 - 21
addiu-sp prologues, 3 jr-veneers, the rest lui/andi/ori/addu
first-compute heads; the offsets map THROUGH the record zone
0x106be..0x11820 as if its bytes counted in the image). The base equals
the first 02-chunk's data start for single-object modules (delta 0 on
20+ LIBSND/LIBSPU modules) and sits INSIDE the first code chunk for
multi-cluster ones (VMANAGER chunk1_data+0xfa6). TWO base solvers:
solve_def_base = prologue-vote maximization with the epilogue refusal
(0x27bd followed by jr $ra is the PREVIOUS function's frame restore,
not a head - VMANAGER ghost 0x1065c had 26 such votes vs the true 23);
solve_def_base_valid = the ALL-LANDINGS-VALID constraint (0806): every
candidate base must land EVERY def on a valid head word (head_ok),
which kills the epilogue ghost MECHANICALLY (it lands prologue-first
defs 12 bytes early, inside the previous tail's delay nop) and makes
VMANAGER's base UNIQUE (0x10668, 23/38 strict). An empty valid set is
the MULTI-CLUSTER DISCRIMINATOR: no single flat base exists and the
def offsets are per-cluster (SEQREAD/GEO/PRESET4/PRIM/SPU/...; the
0651 anchor is SEQREAD's second cluster +0x10ea) - the per-cluster
derivation is the OPEN item. Banked anchors: _svm_damper file 0x12464
= 0x10668+0x1dfc (full-body compare, cron-20261101-0536) and
_svm_envx_hist store-run 0x1533c = 0x10668+0x4cd4.

A-ORDINAL LAW (0806, corrects the SPU slot-counter reading): every row's
a field is a per-row UNIQUE ordinal, not a definition-order counter
(SPU's a=10..20 run is the consecutive case, not the law; VMANAGER's
38 b=2 defs carry 38 DISTINCT a values in row order 49,17,11,48,...).
The record-zone fixup stream references this namespace: the 2c0 u32
payload values (6/2/14/23/26/... small ordinals) and the short
[02][u8][00] 3-byte forms (0x47/0x48 next to 0x46..0x4a data rows) are
row-ordinal targets for the 0a [t][u16 site] fixup records; the 2c4
[u16 w][u32 v] form carries the CLASS w (2 code / 6 data, the same b
classes as the def rows) + a class-relative v - the def offsets and
the 2c4 targets share one per-class address space rooted at the base.
Real 06 [seg] 00 markers sit at grammar positions (pre-chunk
0xf6af/0xf6b2/0xf6bc, mid-zone re-selections 0x114d6 seg3/0x1165e
seg2, pre-table 0x18cef seg6/0x18cf7 seg2 on VMANAGER); 06 bytes
inside code words are coincidence, not markers.

OBSERVED SEMANTICS (empirical, not spec-verified - raw fields are always
reported so nothing is lost):
  - kind 0x0c (a, b, off): for a module's own publics b+off behave like a
    section class + offset (SPU: the 11-symbol b=3 data cluster is a
    consecutive a=10..20 run at offsets 0x04..0x40; functions sit at
    b=2 offsets into the code). Kernel externs (ResetCallback,
    EnableEvent, ExitCriticalSection, DeliverEvent, TestEvent) also
    appear as 0x0c rows - psyq allocates call thunks for them, so an
    0x0c row is evidence of storage ONLY when the name is the module's
    own public. The a field is a per-module SLOT counter (10, 11, 12...
    in definition order: ADSR _SsUtBuildADSR a=10, _SsUtResolveADSR a=11).
  - kind 0x30 (a, b, off): def rows in the DATA class (b=6 observed,
    off=2 constant in LIBSND 3.3 - VM_G is all-0x30 for its 19 svm
    statics). Adding this kind fixed the VMANAGER truncation: the old
    3-kind walk broke at the first 0x30 row and the longest-chain law
    fell back to the 2-row tail fragment (only _svm_okon2/SpuVmFlush
    of 44 publics). 80 rows now parse, 22 public defs included.
  - kind 0x0e: reference to a symbol defined in ANOTHER module of the
    same lib (_spu_init is 0x0e in SPU's table and a 0x0c definition in
    S_INI's; _spu_FsetRXX the reverse). The payload indexes a lib-wide
    slot dictionary (VBLANK_MINUS=11 in TEMPO/SEPINIT/SEQINIT alike;
    SsSeqOpen and SsSepOpen share slot 13 - header-alias pair).
  - kind 0x12: (w, value) pairs - w=2 rows carry a code-class offset
    (SpuVmNoiseOff v=0x27c, SpuVmSetSeqVol v=0x1380), w=6 rows a data-
    class one (_svm_pg v=0x61c); printf stays the extern shape.

CURATION VERDICT this extraction proves (banked in docs/TASKS.md): the
SPU module's data cluster places _spu_transMode BETWEEN _spu_tsa (0x30)
and _spu_RXX (0x38), while the game's retail block has the tsa-role slot
(0x800AB0B4) ADJACENT below the RXX-role slot (0x800AB0B8); no single
base satisfies both curated anchors (RXX-anchored base 0x800AB080 puts
inTransfer at 0x800AB0A4 vs its mainmenu_jp-sig-matched 0x800AB0E8;
inTransfer-anchored base 0x800AB0C4 puts RXX at 0x800AB0FC). The game's
libspu is therefore NOT this archive's layout - consistent with the
banked code-level finding (src/func_800642A0.c PROVENANCE: "NOT
byte-identical (different frame)") - so the numeric statics stay D_
(contra-evidenced HOLD; wrong names are worse than placeholders).

Usage:
  python3 tools/omf_pubsyms.py <lib> [--module REGEX] [--tsv] [--raw] [--check]
"""
import argparse
import re
import struct
import sys

MAGIC = b"LIB\x01"
MOD_MAGIC = b"\x4c\x1f"
LNK_MAGIC = b"LNK"
KIND_PAYLOAD = {0x0C: 8, 0x0E: 2, 0x12: 6, 0x30: 8}


# --- row classification (the cron-20261101-0151 quirk pin) -----------------
#
# The PUBLICS region ([len][name] pairs before LNK) is byte-clean - verified
# raw on LIBSND.LIB SSCALL ([0f]'SsSeqCalledTbyT' 00) and TEMPO
# ([09]'Snd_tempo' 00): no cross-module name bleed there. The misattribution
# class lives in the SYMBOL TABLE reading, three concrete shapes:
#
#   THUNK  kind 0x0c for a name that is NOT the module's public AND carries
#          off=0 - the extern/call-thunk shape (SSCALL 'Snd_tempo', SSADD
#          '_ss_score', PAUSE 'SpuVmSeqKeyOff', SSCLOSE 'SpuVmSetSeqVol',
#          LIBSPU's kernel externs). psyq allocates call thunks for externs;
#          the storage resolves at link time, so off=0 is the tell.
#          The banked cron-20261031-1525/ITEM-4 text read SSCALL's
#          'Snd_tempo' 0x0c row as "SSCALL's own definition row" - WRONG
#          under this law (Snd_tempo is TEMPO's public); SSCALL CALLS
#          Snd_tempo. The _snd_seq_t_max verdict SURVIVES on stronger
#          evidence: SSCALL's public IS SsSeqCalledTbyT (the per-tick
#          callback) and SSCALL refs _snd_seq_t_max directly.
#   LOCAL  kind 0x0c for a non-public with a REAL offset - the module's
#          own static function/data (VMANAGER note2pitch a=49 b=2
#          off=0x4684, SpuVmKeyOnNow a=11 off=0x1370 - both prologue-
#          verified under the measured section base). The old 2-row
#          parses never saw this class; the banked '0x0c non-public =
#          thunk' law needs the off=0 qualifier from now on.
#   TAIL   a public absent from the table entirely: the module tail's
#          [len][name] 0x00 is the missing row (SSADD 'SsSetTempo', SSCLOSE
#          'SsSeqClose' - both verified tail = the absent last public).
#   ALIAS? an OWN public appearing as a 0x0e ref (TEMPO's 'Snd_tempo',
#          SSADD's 'SsSetLoop'/'SsIsEos'). RESOLVED (cron-20261101-0536):
#          the publics list is the COMPILATION GROUP's exports; a public
#          with a ref-only row is defined in a sibling module of the same
#          group (VMANAGER's SpuVmKeyOff ref idx=85 -> def in SEQREAD;
#          SsSeqOpen/SsSepOpen share lib slot 13 as a header alias pair).
#          The def-side map (--defs / xrefs) is authoritative for storage.

VERDICT_DEF = "def"      # 0x0c, name is the module's own public
VERDICT_THUNK = "thunk"  # 0x0c, name is NOT the module's public, off=0
VERDICT_LOCAL = "local"  # 0x0c, non-public with a real offset: own static
VERDICT_REF = "ref"      # 0x0e
VERDICT_REF2 = "ref2"    # 0x12
VERDICT_DEF30 = "def30"  # 0x30 data-class def row (public or local)


def classify(mod):
    """Return {name: [verdicts]} for a module's symbol rows."""
    out = {}
    for s in mod.symbols:
        if s.kind == 0x0C:
            if s.name in mod.publics:
                v = VERDICT_DEF
            elif s.offset == 0:
                v = VERDICT_THUNK
            else:
                v = VERDICT_LOCAL
        elif s.kind == 0x30:
            v = VERDICT_DEF30
        elif s.kind == 0x0E:
            v = VERDICT_REF
        elif s.kind == 0x12:
            v = VERDICT_REF2
        else:
            v = "unk"
        out.setdefault(s.name, []).append(v)
    return out


def def_map(mod):
    """The module's def rows: [(name, kind, a, b, offset)] in stream order.

    The storage-side map the curation pass uses (the publics list alone
    is the GROUP's exports and may name symbols defined in sibling
    modules)."""
    return [(s.name, s.kind, s.a, s.b, s.offset) for s in mod.symbols
            if s.kind in (0x0C, 0x30)]


def lib_def_index(lib):
    """{name: [(module, kind, b, offset)]} over every module's def rows."""
    idx = {}
    for m in lib.modules:
        for name, kind, _a, b, off in def_map(m):
            idx.setdefault(name, []).append((m.name, kind, b, off))
    return idx


def prologue_positions(data, lo, hi):
    """File offsets of 0x27bd.... (addiu $sp) words in [lo, hi), step 2."""
    out = []
    if hi > len(data) - 4:
        hi = len(data) - 4
    for p in range(lo, hi, 2):
        if (struct.unpack_from("<I", data, p)[0] >> 16) == 0x27BD:
            out.append(p)
    return out


def first_code_chunk(data, mod):
    """File offset of the first 02-chunk's DATA (the post-LNK blob start).

    Walks publics -> LNK -> path records -> leading 06 xx 00 markers;
    returns (first_chunk_data_offset, paths_end, n_paths) or (None, ...)."""
    end = mod.offset + mod.size
    d = data
    o = mod.offset + 20
    while o < end and d[o] != 0x00:
        o += 1 + d[o]
    if o >= end or d[o] != 0x00:
        return None, None, 0
    o += 1
    if d[o:o + 3] != LNK_MAGIC:
        return None, None, 0
    o += 3
    while o < end:
        ln = d[o]
        p = o + 1 + ln
        if p >= end:
            return None, None, 0
        if d[p] == 0x1C:
            o = p  # the 0x1c doubles as the first path record's kind byte
            break
        o = p + 6
    else:
        return None, None, 0
    n_paths = 0
    while o + 4 <= end and d[o] == 0x1C and d[o + 2] == 0x00 \
            and 0x08 <= d[o + 3] <= 0x40:
        ln = d[o + 3]
        path = d[o + 4:o + 4 + ln]
        if o + 4 + ln > end or not all(32 <= c < 127 for c in path):
            break
        n_paths += 1
        o += 4 + ln
    while o + 3 <= end and d[o] == 0x06 and d[o + 2] == 0x00 \
            and d[o + 1] != 0x00:
        o += 3
    if o + 3 <= end and d[o] == 0x02:
        size = struct.unpack_from("<H", d, o + 1)[0]
        if size:
            return o + 3, o, n_paths
    return None, None, n_paths


def solve_def_base(data, mod):
    """Solve the module's def base by prologue-vote maximization.

    Every addiu-sp word p in [first_code_chunk, table_start) votes for the
    candidate base p - off of every b=2 0x0c def row; the top-voted base
    wins. Votes from EPILOGUE words are refused: an addiu $sp immediately
    followed by jr $ra (0x03e00008) is the previous function's frame
    restore, not a head - refusing those is what separates VMANAGER's true
    base 0x10668 (23 strict head votes) from the epilogue ghost 0x1065c
    (26 votes, cron-20261101-0651). Returns
    (base, strict_hits, defs, n_prologues) or None when the module has no
    code def rows or no discoverable blob."""
    blob, _pe, _np = first_code_chunk(data, mod)
    if blob is None:
        return None
    defs = [(n, off) for n, k, a, b, off in def_map(mod)
            if k == 0x0C and b == 2]
    if not defs:
        return None
    ts = mod.table_start or (mod.offset + mod.size)
    pros = prologue_positions(data, blob, ts)
    votes = {}
    for p in pros:
        if p + 8 <= len(data) - 4 and \
                struct.unpack_from("<I", data, p + 4)[0] == 0x03E00008:
            continue  # epilogue addiu: [restore][jr $ra][delay]
        for _n, off in defs:
            c = p - off
            if c >= blob:
                votes[c] = votes.get(c, 0) + 1
    if not votes:
        return (blob, 0, len(defs), len(pros))
    base = max(votes, key=lambda c: (votes[c], -c))
    return (base, votes[base], len(defs), len(pros))


# --- the all-landings-valid base law (cron-20261101-0806) ----------------
HEAD_SPECIAL_FUNCTS = frozenset((0x08, 0x09, 0x10, 0x12, 0x21, 0x23, 0x25,
                                 0x27, 0x2a, 0x2b, 0x04, 0x06, 0x07))
HEAD_OPS = frozenset((0x02, 0x03, 0x09, 0x0c, 0x0d, 0x0f, 0x20, 0x21, 0x23,
                      0x24, 0x25, 0x28, 0x29, 0x2b))


def head_ok(word):
    """Def-landing head-word validity predicate (cron-20261101-0806).

    A gcc 2.8.x function head is one of: the addiu-sp prologue (op 0x09,
    rs=29), a jr $ra veneer (funct 0x08), jal/j, a lui/ori/andi
    scheduled-preamble first compute, a SPECIAL arithmetic/move first
    compute (addu/subu/or/nor/slt/sltu/sllv/srlv/srav/mfhi/mflo), or a
    load/store first word (lw/lb/lbu/lhu/sb/sh/sw). A nop (0x00000000)
    is NEVER a head - it is a delay-slot or alignment pad."""
    if word == 0x00000000:
        return False
    opc = word >> 26
    if opc == 0x00:
        return (word & 0x3f) in HEAD_SPECIAL_FUNCTS
    return opc in HEAD_OPS


def solve_def_base_valid(data, mod):
    """The ALL-LANDINGS-VALID base constraint (cron-20261101-0806).

    Enumerates candidate bases c = p - off (every non-epilogue prologue
    p x every b=2 0x0c def off, c in [first_blob, span)) and keeps ONLY
    those landing EVERY def row on a head_ok word. Kills the epilogue
    ghost mechanically (the ghost lands prologue-first defs 12 bytes
    early, inside the previous function's [restore][jr][delay] tail -
    on the delay nop or a mid-tail word) and makes VMANAGER's base a
    UNIQUE solution (0x10668, 23/38 strict). Returns [(base,
    strict_hits, ndefs)] sorted by strict_hits desc; [] = no base
    satisfies the constraint - the MULTI-CLUSTER DISCRIMINATOR (the
    def offsets are per-cluster, base law OPEN, SEQREAD second cluster
    +0x10ea the 0651 anchor); None = no code def rows or no blob."""
    blob, _pe, _np = first_code_chunk(data, mod)
    if blob is None:
        return None
    defs = [(n, off) for n, k, a, b, off in def_map(mod)
            if k == 0x0C and b == 2]
    if not defs:
        return None
    ts = mod.table_start or (mod.offset + mod.size)
    lim = min(ts, len(data) - 4)
    if lim - blob > 0x40000:
        lim = blob + 0x40000
    cands = set()
    for p in prologue_positions(data, blob, lim):
        if p + 8 <= len(data) - 4 and \
                struct.unpack_from("<I", data, p + 4)[0] == 0x03E00008:
            continue
        for _n, off in defs:
            c = p - off
            if blob <= c < lim:
                cands.add(c)
    out = []
    for c in sorted(cands):
        strict = 0
        ok = True
        for _n, off in defs:
            p = c + off
            if p < 0 or p > len(data) - 4:
                ok = False
                break
            w = struct.unpack_from("<I", data, p)[0]
            if not head_ok(w):
                ok = False
                break
            if (w >> 16) == 0x27BD:
                strict += 1
        if ok:
            out.append((c, strict, len(defs)))
    out.sort(key=lambda t: (-t[1], t[0]))
    return out


def lib_xrefs(lib):
    """Resolve every 0x0e ref against the lib-wide def index.

    Returns [(module, name, idx, resolved-or-None)] for all ref rows."""
    defs = lib_def_index(lib)
    out = []
    for m in lib.modules:
        for s in m.symbols:
            if s.kind == 0x0E:
                out.append((m.name, s.name, s.a, defs.get(s.name)))
    return out


def check_module(mod):
    """Consistency findings for one module (the quirk classes above).

    Returns a list of human-readable strings; empty means the module's
    publics and table agree under the group model."""
    findings = []
    cls = classify(mod)
    table_names = set(cls)
    for pub in mod.publics:
        if pub not in table_names:
            role = "tail" if pub == mod.tail_name else "ABSENT"
            findings.append(
                f"public {pub!r} has no table row ({role})")
        elif VERDICT_REF in cls[pub] and VERDICT_DEF not in cls[pub] \
                and VERDICT_DEF30 not in cls[pub]:
            findings.append(
                f"public {pub!r} appears as 0x0e ref (group-internal "
                f"cross-object ref - the def lives in a sibling module)")
    for s in mod.symbols:
        if s.kind == 0x0C and s.name not in mod.publics:
            if s.offset == 0:
                findings.append(
                    f"0x0c row for non-public {s.name!r} (thunk, a={s.a} "
                    f"b={s.b} off={s.offset:#x}) - NOT a definition")
            else:
                findings.append(
                    f"0x0c row for non-public {s.name!r} (local static, "
                    f"a={s.a} b={s.b} off={s.offset:#x}) - own storage")
    return findings


class PsyqSymbol:
    __slots__ = ("name", "kind", "a", "b", "offset", "raw")

    def __init__(self, name, kind, payload):
        self.name = name
        self.kind = kind
        self.raw = payload
        if kind in (0x0C, 0x30) and len(payload) == 8:
            self.a, self.b, self.offset = struct.unpack("<HHI", payload)
        elif kind == 0x0E and len(payload) == 2:
            self.a = struct.unpack("<H", payload)[0]
            self.b = self.offset = None
        elif kind == 0x12 and len(payload) == 6:
            self.a, self.offset = struct.unpack("<HI", payload)
            self.b = None
        else:  # unknown kind reached only via manual construction
            self.a = self.b = self.offset = None

    def __repr__(self):
        if self.kind in (0x0C, 0x30):
            return f"{self.name!r} kind=0x{self.kind:02x} a={self.a} b={self.b} off={self.offset:#x}"
        if self.kind == 0x0E:
            return f"{self.name!r} kind=0x0e idx={self.a}"
        if self.kind == 0x12:
            return f"{self.name!r} kind=0x12 w={self.a} val={self.offset:#x}"
        return f"{self.name!r} kind=0x{self.kind:02x} raw={self.raw.hex(' ')}"


class PsyqModule:
    def __init__(self, name, offset, size):
        self.name = name      # rstripped
        self.raw_name = name  # kept verbatim for provenance
        self.offset = offset  # module name offset in file
        self.size = size
        self.hdr_x = None     # per-module header word, meaning unknown
        self.publics = []     # [str]
        self.sections = {}    # {index: name}
        self.symbols = []     # [PsyqSymbol]
        self.tail_name = None
        self.table_start = None

    def symbol(self, name):
        for s in self.symbols:
            if s.name == name:
                return s
        return None


class PsyqLib:
    def __init__(self, path):
        self.path = path
        with open(path, "rb") as f:
            self.data = f.read()
        if self.data[:4] != MAGIC:
            raise ValueError(f"{path}: not a PSYLIB container (magic {self.data[:4]!r})")
        self.name = self.data[4:12].decode("latin1").rstrip()
        self.modules = []
        self._walk()

    def _name_at(self, off):
        ln = self.data[off]
        nm = self.data[off + 1:off + 1 + ln]
        if not (1 <= ln <= 128) or len(nm) != ln:
            return None
        if not all(32 <= c < 127 for c in nm):
            return None
        return nm.decode("ascii")

    def _raw_name_at(self, off, cap=64):
        """Length-prefixed name without the printability gate (the LNK
        table's first section name is the raw pair 2e 07 on every module)."""
        ln = self.data[off]
        nm = self.data[off + 1:off + 1 + ln]
        if not (1 <= ln <= cap) or len(nm) != ln:
            return None
        return nm.decode("latin1")

    def _walk(self):
        data = self.data
        n = len(data)
        pos = 4
        while pos + 20 <= n:
            # module magic: the second byte is a constant 0x1f across libs;
            # the first byte is lib-constant (4c LIBSPU/LIBAPI, 51 LIBSND,
            # 52 LIBGPU) and unchecked here
            nm8 = data[pos:pos + 8]
            if data[pos + 9] != 0x1F or not all(32 <= c < 127 for c in nm8):
                break
            hdr_x = struct.unpack_from("<I", data, pos + 12)[0]  # per-module, meaning unknown (304 on SPU, 32 on SPU_IO, 0xfe on S_INI)
            size = struct.unpack_from("<I", data, pos + 16)[0]
            if size <= 20 or pos + size > n:
                break
            mod = PsyqModule(data[pos:pos + 8].decode("latin1").rstrip(), pos, size)
            mod.hdr_x = hdr_x
            self._parse_module(mod)
            self.modules.append(mod)
            pos += size

    def _parse_module(self, mod):
        data = self.data
        end = mod.offset + mod.size
        o = mod.offset + 20  # past name8 + 12-byte header
        # publics
        while o < end and data[o] != 0x00:
            nm = self._name_at(o)
            if nm is None:
                break
            mod.publics.append(nm)
            o += 1 + len(nm)
        if o < end and data[o] == 0x00:
            o += 1
        # LNK section table
        if data[o:o + 3] == LNK_MAGIC:
            o += 3
            while o < end:
                nm = self._raw_name_at(o)
                if nm is None:
                    break
                p = o + 1 + len(nm)
                if p >= end:
                    break
                if data[p] == 0x1C:
                    # last entry carries no index; the debug-path region
                    # follows. Key it as max+1 and mark the name inferred.
                    nxt = (max(mod.sections) + 1) if mod.sections else 1
                    mod.sections[nxt] = nm + " (?)"
                    break
                if data[p] != 0x10:
                    break
                idx = struct.unpack_from("<I", data, p + 1)[0]
                mod.sections[idx] = nm
                o = p + 6  # 0x10 + u32 + 0x08
        # symbol table discovery: the longest kind-chain that ends at a
        # [len][name] 0x00 tail reaching exactly module end
        best = None
        for s in range(o, end - 4):
            ents = []
            q = s
            while q < end:
                nm = self._name_at(q)
                if nm is None:
                    break
                p = q + 1 + len(nm)
                if p >= end:
                    break
                kind = data[p]
                psz = KIND_PAYLOAD.get(kind)
                if psz is None or p + 1 + psz > end:
                    break
                ents.append((nm, kind, data[p + 1:p + 1 + psz]))
                q = p + 1 + psz
            tail = None
            if q < end and data[q] != 0x00:
                nm = self._name_at(q)
                if nm is not None and q + 1 + len(nm) + 1 == end and data[q + 1 + len(nm)] == 0x00:
                    tail = nm
            if (tail is not None or q == end) and (best is None or len(ents) > len(best[0])):
                best = (ents, s, tail)
        if best is None:
            return
        ents, start, tail = best
        mod.table_start = start
        mod.tail_name = tail
        mod.symbols = [PsyqSymbol(nm, k, pl) for nm, k, pl in ents]


def _fmt_table(mod, verdicts=False):
    lines = []
    lines.append(f"module {mod.name!r} @{mod.offset:#x} size={mod.size:#x} hdr_x={mod.hdr_x} "
                 f"publics={len(mod.publics)} sections={len(mod.sections)}")
    if mod.publics:
        lines.append("  publics: " + ", ".join(mod.publics))
    if mod.sections:
        lines.append("  sections: " + ", ".join(f"{i}={nm!r}" for i, nm in sorted(mod.sections.items())))
    if mod.symbols:
        cls = classify(mod) if verdicts else None
        lines.append(f"  symbols @{mod.table_start:#x} (tail {mod.tail_name!r}):")
        for s in mod.symbols:
            if cls is not None:
                lines.append(f"    {s!r}  [{','.join(cls.get(s.name, ['?']))}]")
            else:
                lines.append(f"    {s!r}")
    for f in check_module(mod):
        lines.append(f"  CHECK: {f}")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("lib", help="path to the psyq .LIB file")
    ap.add_argument("--module", help="regex filter on module names")
    ap.add_argument("--tsv", action="store_true",
                    help="one row per symbol: module, name, kind, a, b, offset, raw")
    ap.add_argument("--check", action="store_true",
                    help="classify every row (def/thunk/ref) and print the "
                         "quirk findings per module (public-as-tail, "
                         "public-as-0x0e-ref, thunk rows for non-publics)")
    ap.add_argument("--defs", action="store_true",
                    help="print the storage-side def map (name, kind, a, b, "
                         "offset) per module - the public-offset map")
    ap.add_argument("--xref", action="store_true",
                    help="resolve every 0x0e ref against the lib-wide def "
                         "index and print the defining module")
    ap.add_argument("--file-offsets", action="store_true",
                    help="emit the b=2 code def rows with ARCHIVE FILE "
                         "offsets: solve the per-module base by prologue-"
                         "vote maximization (banked cron-20261101-0651, "
                         "empirical - see the DEF-BASE LAW note); strict "
                         "addiu-sp hits and the -12 scheduled-preamble "
                         "family are reported per module")
    args = ap.parse_args(argv)

    try:
        lib = PsyqLib(args.lib)
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    rx = re.compile(args.module) if args.module else None
    mods = [m for m in lib.modules if not rx or rx.search(m.name)]
    if args.tsv:
        print("module\tname\tkind\ta\tb\toffset\traw")
        for m in mods:
            for s in m.symbols:
                print(f"{m.name}\t{s.name}\t{s.kind:#04x}\t"
                      f"{s.a if s.a is not None else ''}\t{s.b if s.b is not None else ''}\t"
                      f"{s.offset if s.offset is not None else ''}\t{s.raw.hex()}")
    elif args.defs:
        for m in mods:
            print(f"module {m.name!r} @{m.offset:#x} size={m.size:#x} "
                  f"publics={len(m.publics)}")
            for name, kind, a, b, off in def_map(m):
                tag = "pub" if name in m.publics else "loc"
                print(f"  {name}\tkind={kind:#04x}\ta={a}\tb={b}\toff={off:#x}\t[{tag}]")
    elif args.file_offsets:
        for m in mods:
            sol = solve_def_base(lib.data, m)
            if sol is None:
                continue
            base, hits, ndefs, npros = sol
            val = solve_def_base_valid(lib.data, m)
            if val:
                base, hits, _n = val[0]
                law = ("valid-unique" if len(val) == 1
                       else f"valid-ambiguous x{len(val)}")
            else:
                law = "vote-max (no all-valid base: multi-cluster)"
            nonpro = 0
            for _n, _k, _a, _b, off in def_map(m):
                if _k != 0x0C or _b != 2:
                    continue
                p = base + off
                if p + 4 <= len(lib.data) and \
                        (struct.unpack_from("<I", lib.data, p)[0] >> 16) != 0x27BD:
                    nonpro += 1
            print(f"module {m.name!r} base={base:#x} law={law} "
                  f"blob_delta={base - (first_code_chunk(lib.data, m)[0] or base):+#x} "
                  f"strict={hits}/{ndefs} nonprologue_heads={nonpro} "
                  f"prologues={npros}")
            for name, kind, a, b, off in def_map(m):
                if kind != 0x0C or b != 2:
                    continue
                fo = base + off
                tag = "pub" if name in m.publics else "loc"
                print(f"  {name}\toff={off:#x}\tfile={fo:#x}\t[{tag}]")
    elif args.xref:
        defs = lib_def_index(lib)
        n_res = n_unres = 0
        for mname, name, idx, where in lib_xrefs(lib):
            if where:
                n_res += 1
                sites = ", ".join(f"{mn} kind={k:#04x} b={b} off={off:#x}"
                                  for mn, k, b, off in where)
                print(f"{mname}\t{name}\tidx={idx}\t-> {sites}")
            else:
                n_unres += 1
                print(f"{mname}\t{name}\tidx={idx}\t-> UNRESOLVED")
        print(f"# {n_res} resolved, {n_unres} unresolved 0x0e ref(s)")
    else:
        for m in mods:
            print(_fmt_table(m, verdicts=args.check))
    nsym = sum(len(m.symbols) for m in mods)
    print(f"# {len(mods)}/{len(lib.modules)} module(s), {nsym} symbol row(s), lib {lib.name!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

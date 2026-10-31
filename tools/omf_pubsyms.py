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
                 entry is followed by 0x1c (debug source-path region)
               then section blobs (06 xx 00 / 02 yy 00 chunk headers -
               NOT parsed by this tool), then the symbol table:
                 [u8 len][name][kind][payload] entries, kinds
                   0x0c -> (u16 a, u16 b, u32 off)  # defined/thunk entry
                   0x0e -> u16 index                # cross-module lib ref
                   0x12 -> (u16 w, u32 v)           # second ref class
               (the table walk stops at any other kind byte)
          module tail: [u8 len][name] 0x00 ending exactly at the next
          module (observed tail name = the module's last public)

OBSERVED SEMANTICS (empirical, not spec-verified - raw fields are always
reported so nothing is lost):
  - kind 0x0c (a, b, off): for a module's own publics b+off behave like a
    section class + offset (SPU: the 11-symbol b=3 data cluster is a
    consecutive a=10..20 run at offsets 0x04..0x40; functions sit at
    b=2 offsets into the code). Kernel externs (ResetCallback,
    EnableEvent, ExitCriticalSection, DeliverEvent, TestEvent) also
    appear as 0x0c rows - psyq allocates call thunks for them, so an
    0x0c row is evidence of storage ONLY when the name is the module's
    own public.
  - kind 0x0e: reference to a symbol defined in ANOTHER module of the
    same lib (_spu_init is 0x0e in SPU's table and a 0x0c definition in
    S_INI's; _spu_FsetRXX the reverse).
  - kind 0x12: (2, value) pairs observed on printf (extern) and _spu_r_.

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
KIND_PAYLOAD = {0x0C: 8, 0x0E: 2, 0x12: 6}


# --- row classification (the cron-20261101-0151 quirk pin) -----------------
#
# The PUBLICS region ([len][name] pairs before LNK) is byte-clean - verified
# raw on LIBSND.LIB SSCALL ([0f]'SsSeqCalledTbyT' 00) and TEMPO
# ([09]'Snd_tempo' 00): no cross-module name bleed there. The misattribution
# class lives in the SYMBOL TABLE reading, three concrete shapes:
#
#   THUNK  kind 0x0c for a name that is NOT the module's public. psyq
#          allocates call thunks for externs; the a=10 b=2 off=0 shape is
#          the common single-thunk case (SSCALL 'Snd_tempo', SSADD
#          '_ss_score', PAUSE 'SpuVmSeqKeyOff', SSCLOSE 'SpuVmSetSeqVol').
#          The banked cron-20261031-1525/ITEM-4 text read SSCALL's
#          'Snd_tempo' 0x0c row as "SSCALL's own definition row" - WRONG
#          under this law (Snd_tempo is TEMPO's public); SSCALL CALLS
#          Snd_tempo. The _snd_seq_t_max verdict SURVIVES on stronger
#          evidence: SSCALL's public IS SsSeqCalledTbyT (the per-tick
#          callback) and SSCALL refs _snd_seq_t_max directly.
#   TAIL   a public absent from the table entirely: the module tail's
#          [len][name] 0x00 is the missing row (SSADD 'SsSetTempo', SSCLOSE
#          'SsSeqClose' - both verified tail = the absent last public).
#   ALIAS? an OWN public appearing as a 0x0e ref (TEMPO's 'Snd_tempo',
#          SSADD's 'SsSetLoop'/'SsIsEos'). UNRESOLVED - candidate readings:
#          def rows behind a kind the walk truncates on, or alias publics
#          resolving to another module's def. Flag, never guess.

VERDICT_DEF = "def"      # 0x0c, name is the module's own public
VERDICT_THUNK = "thunk"  # 0x0c, name is NOT the module's public
VERDICT_REF = "ref"      # 0x0e
VERDICT_REF2 = "ref2"    # 0x12


def classify(mod):
    """Return {name: [verdicts]} for a module's symbol rows."""
    out = {}
    for s in mod.symbols:
        if s.kind == 0x0C:
            v = VERDICT_DEF if s.name in mod.publics else VERDICT_THUNK
        elif s.kind == 0x0E:
            v = VERDICT_REF
        elif s.kind == 0x12:
            v = VERDICT_REF2
        else:
            v = "unk"
        out.setdefault(s.name, []).append(v)
    return out


def check_module(mod):
    """Consistency findings for one module (the quirk classes above).

    Returns a list of human-readable strings; empty means the module's
    publics and table agree under the three-row model."""
    findings = []
    cls = classify(mod)
    table_names = set(cls)
    for pub in mod.publics:
        if pub not in table_names:
            role = "tail" if pub == mod.tail_name else "ABSENT"
            findings.append(
                f"public {pub!r} has no table row ({role})")
        elif VERDICT_REF in cls[pub]:
            findings.append(
                f"public {pub!r} appears as 0x0e ref (alias? class)")
    for s in mod.symbols:
        if s.kind == 0x0C and s.name not in mod.publics:
            findings.append(
                f"0x0c row for non-public {s.name!r} (thunk, a={s.a} "
                f"b={s.b} off={s.offset:#x}) - NOT a definition")
    return findings


class PsyqSymbol:
    __slots__ = ("name", "kind", "a", "b", "offset", "raw")

    def __init__(self, name, kind, payload):
        self.name = name
        self.kind = kind
        self.raw = payload
        if kind == 0x0C and len(payload) == 8:
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
        if self.kind == 0x0C:
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
    else:
        for m in mods:
            print(_fmt_table(m, verdicts=args.check))
    nsym = sum(len(m.symbols) for m in mods)
    print(f"# {len(mods)}/{len(lib.modules)} module(s), {nsym} symbol row(s), lib {lib.name!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

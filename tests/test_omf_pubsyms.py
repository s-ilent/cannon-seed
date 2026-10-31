#!/usr/bin/env python3
"""Tests for tools/omf_pubsyms.py - the psyq PSYLIB (LIB\\x01) extractor.

The parser was reverse-engineered 2026-10-31 (window cron-20261031-1251) off
psyq 3.3 LIBSPU.LIB and verified against eight libs of the same SDK. These
tests pin the container grammar with a hand-assembled fixture so a future
format surprise fails loudly instead of silently reordering fields:

  * lib header (LIB\\x01 + 8-byte name) and the module size chain;
  * the module header word pair (hdr_x is NOT a constant - the first
    regression candidate);
  * publics list with its 0x00 terminator;
  * the LNK section table including the raw first name (2e 07) and the
    index-less last entry (0x1c marker);
  * the four symbol kinds (0x0c def, 0x0e cross-module ref, 0x12 second
    ref class, 0x30 data-class def) and the chain stop at an unknown kind;
  * the [len][name] 0x00 tail reaching exactly the module end.

Run: python3 -m unittest tests/test_omf_pubsyms.py -v
"""
import os
import struct
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "tools"))
import omf_pubsyms as op  # noqa: E402


def name_entry(s):
    b = s.encode("ascii")
    return bytes([len(b)]) + b


def build_lib():
    """Hand-assembled two-module lib mirroring the observed grammar.

    The first module's name8 doubles as the lib name (the walk starts at
    offset 4 - that is how LIBSPU's 'SPU' and LIBAPI's 'C57' read)."""
    out = bytearray(b"LIB\x01")
    # ---- module MOD1 at 0x0c ----
    m1 = bytearray()
    m1 += b"M1      " + b"\x4c\x1f" + b"\x00\xa1"   # name8 + magic + u8 + a1
    m1 += struct.pack("<I", 0x20)                # hdr_x = 32
    m1 += struct.pack("<I", 0)                   # size, patched below
    m1 += name_entry("pub_one")                  # publics
    m1 += name_entry("pub_two")
    m1 += b"\x00"
    m1 += b"LNK"                                 # section table
    m1 += b"\x02.\x07" + b"\x10" + struct.pack("<I", 1) + b"\x08"
    m1 += name_entry(".text") + b"\x10" + struct.pack("<I", 2) + b"\x08"
    m1 += name_entry(".sbss") + b"\x10" + struct.pack("<I", 3) + b"\x08"
    m1 += name_entry(".dtors") + b"\x1c"         # index-less last entry
    m1 += b"\x00" * 8                            # blob-region stand-in
    m1 += name_entry("pub_one") + b"\x0c" + struct.pack("<HHI", 5, 2, 0x40)
    m1 += name_entry("pub_two") + b"\x0c" + struct.pack("<HHI", 6, 3, 0x04)
    m1 += name_entry("sibling") + b"\x0e" + struct.pack("<H", 9)
    m1 += name_entry("printf") + b"\x12" + struct.pack("<HI", 2, 0x7d0)
    m1 += name_entry("pub_two") + b"\x00"        # tail = last public
    struct.pack_into("<I", m1, 16, len(m1))      # patch the size field
    out += m1
    # ---- module MOD2 ----
    m2 = bytearray()
    m2 += b"MOD2    " + b"\x4c\x1f" + b"\x00\xa1"
    m2 += struct.pack("<I", 0x18)
    m2 += struct.pack("<I", 0)
    m2 += name_entry("sibling")
    m2 += b"\x00"
    m2 += b"LNK"
    m2 += b"\x02.\x07" + b"\x10" + struct.pack("<I", 1) + b"\x08"
    m2 += name_entry(".text") + b"\x10" + struct.pack("<I", 2) + b"\x08"
    m2 += name_entry(".dtors") + b"\x1c"
    m2 += b"\x00" * 8
    m2 += name_entry("sibling") + b"\x0c" + struct.pack("<HHI", 9, 2, 0x00)
    m2 += name_entry("sibling") + b"\x00"
    struct.pack_into("<I", m2, 16, len(m2))
    out += m2
    return bytes(out)


class TestPsyqLib(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = "/tmp/omf_pubsyms_test.lib"
        with open(cls.path, "wb") as f:
            f.write(build_lib())
        cls.lib = op.PsyqLib(cls.path)

    def test_lib_name(self):
        # the first module's name doubles as the lib name
        self.assertEqual(self.lib.name, "M1")

    def test_module_chain(self):
        names = [m.name for m in self.lib.modules]
        self.assertEqual(names, ["M1", "MOD2"])
        m1 = self.lib.modules[0]
        self.assertEqual(m1.offset, 0x04)
        self.assertEqual(m1.hdr_x, 0x20)
        # size field = the byte distance to the next module name
        self.assertEqual(m1.size, self.lib.modules[1].offset - m1.offset)

    def test_publics(self):
        self.assertEqual(self.lib.modules[0].publics, ["pub_one", "pub_two"])
        self.assertEqual(self.lib.modules[1].publics, ["sibling"])

    def test_sections(self):
        secs = self.lib.modules[0].sections
        self.assertEqual(secs[1], ".\x07")  # the raw non-printable first name
        self.assertEqual(secs[2], ".text")
        self.assertEqual(secs[3], ".sbss")
        self.assertTrue(secs[4].startswith(".dtors"))  # index-less last entry

    def test_symbol_kinds(self):
        syms = {s.name: s for s in self.lib.modules[0].symbols}
        d = syms["pub_one"]
        self.assertEqual(d.kind, 0x0C)
        self.assertEqual((d.a, d.b, d.offset), (5, 2, 0x40))
        r = syms["sibling"]
        self.assertEqual(r.kind, 0x0E)
        self.assertEqual(r.a, 9)
        self.assertIsNone(r.offset)
        p = syms["printf"]
        self.assertEqual(p.kind, 0x12)
        self.assertEqual((p.a, p.offset), (2, 0x7D0))

    def test_tail_and_order(self):
        m1 = self.lib.modules[0]
        self.assertEqual(m1.tail_name, "pub_two")
        # the defined data cluster keeps file order (extraction, not sorting)
        self.assertEqual([s.name for s in m1.symbols],
                         ["pub_one", "pub_two", "sibling", "printf"])

    def test_lookup_helper(self):
        self.assertEqual(self.lib.modules[0].symbol("pub_two").offset, 0x04)
        self.assertIsNone(self.lib.modules[0].symbol("nope"))

    def test_bad_magic_raises(self):
        bad = "/tmp/omf_pubsyms_bad.lib"
        with open(bad, "wb") as f:
            f.write(b"AR!\x00" + b"\x00" * 32)
        with self.assertRaises(ValueError):
            op.PsyqLib(bad)

    def test_cli_tsv(self):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = op.main([self.path, "--tsv"])
        self.assertEqual(rc, 0)
        rows = [ln.split("\t") for ln in buf.getvalue().strip().splitlines()
                if not ln.startswith("#")]
        self.assertEqual(rows[0][:3], ["module", "name", "kind"])
        self.assertIn("pub_one", [r[1] for r in rows[1:]])


PSYQ_DIRS = (
    "/home/z/psyq/3.3/PSX/LIB",
    "/home/z/my-project/psyq/3.3/PSX/LIB",
)
PSYQ_DIR = next((d for d in PSYQ_DIRS if os.path.isdir(d)), None)


@unittest.skipUnless(PSYQ_DIR, "psyq archive not provisioned")
class TestRealArchive(unittest.TestCase):
    """Live-archive sanity: the grammar holds across the SDK's libs."""

    def test_libspu_anchors(self):
        lib = op.PsyqLib(os.path.join(PSYQ_DIR, "LIBSPU.LIB"))
        self.assertEqual(lib.name, "SPU")
        spu = next(m for m in lib.modules if m.name == "SPU")
        rxx = spu.symbol("_spu_RXX")
        self.assertEqual((rxx.kind, rxx.b, rxx.offset), (0x0C, 3, 0x38))
        tsa = spu.symbol("_spu_tsa")
        self.assertEqual(tsa.offset, 0x30)
        trans = spu.symbol("_spu_transMode")
        self.assertEqual(trans.offset, 0x34)  # BETWEEN tsa and RXX: the
        # contra-evidence that pins the curation HOLD (docs/TASKS.md)
        # _spu_init/_spu_t are cross-module refs in SPU, defined in S_INI
        self.assertEqual(spu.symbol("_spu_init").kind, 0x0E)
        s_ini = next(m for m in lib.modules if m.name == "S_INI")
        init = s_ini.symbol("_spu_init")
        self.assertEqual((init.kind, init.b, init.offset), (0x0C, 3, 0x64))
        self.assertEqual(len(lib.modules), 67)

    def test_s_sca_no_longer_truncated(self):
        # the old 3-kind walk found 0 rows in S_SCA; the 0x30 kind
        # recovers its 2-row stream (cron-20261101-0536 audit)
        lib = op.PsyqLib(os.path.join(PSYQ_DIR, "LIBSPU.LIB"))
        sca = next(m for m in lib.modules if m.name == "S_SCA")
        self.assertEqual(len(sca.symbols), 2)

    def test_libsnd_vmanager_full_stream(self):
        # the truncation witness: 44 publics now yield 80 rows incl. the
        # SpuVmInit + _svm_damper def rows the svm-init identity needs
        lib = op.PsyqLib(os.path.join(PSYQ_DIR, "LIBSND.LIB"))
        vm = next(m for m in lib.modules if m.name == "VMANAGER")
        self.assertEqual(len(vm.publics), 44)
        self.assertEqual(len(vm.symbols), 80)
        init = vm.symbol("SpuVmInit")
        self.assertEqual((init.kind, init.b, init.offset), (0x0C, 2, 0x314c))
        damper = vm.symbol("_svm_damper")
        self.assertEqual((damper.kind, damper.b, damper.offset),
                         (0x0C, 2, 0x1dfc))
        # the svm-init identity: _svm_damper's def bounds [0x1dfc, 0x21fc)
        # = the game func_80067690 twin (prologue + store-run delta 0x26c)
        kmax = vm.symbol("kMaxPrograms")
        self.assertEqual((kmax.kind, kmax.b, kmax.offset), (0x0C, 2, 0x21fc))

    def test_libsnd_group_xref(self):
        # the ALIAS? resolution: VMANAGER's publics include names whose
        # defs live in sibling modules of the same compilation group
        lib = op.PsyqLib(os.path.join(PSYQ_DIR, "LIBSND.LIB"))
        idx = op.lib_def_index(lib)
        self.assertIn("SpuVmKeyOff", idx)
        self.assertTrue(any(mn == "SEQREAD" for mn, _k, _b, _o
                            in idx["SpuVmKeyOff"]))
        xrefs = op.lib_xrefs(lib)
        keyoff = [(mn, where) for mn, nm, _i, where in xrefs
                  if nm == "SpuVmKeyOff" and mn == "VMANAGER"]
        self.assertTrue(keyoff and keyoff[0][1], "VMANAGER's SpuVmKeyOff "
                        "ref must resolve to a defining module")


def build_quirk_lib():
    """Hand-assembled one-module lib reproducing the LIBSND SSCALL/TEMPO
    row shapes (cron-20261101-0151): an own public as a 0x0e ref, a 0x0c
    row for a non-public (thunk), and a public carried only by the tail."""
    out = bytearray(b"LIB\x01")
    m = bytearray()
    m += b"QK      " + b"\x4c\x1f" + b"\x00\xa1"
    m += struct.pack("<I", 0x20)
    m += struct.pack("<I", 0)
    m += name_entry("tick_cb")     # publics: one, shown below as a 0x0e ref
    m += b"\x00"
    m += b"LNK"
    m += b"\x02.\x07" + b"\x10" + struct.pack("<I", 1) + b"\x08"
    m += name_entry(".text") + b"\x10" + struct.pack("<I", 2) + b"\x08"
    m += name_entry(".dtors") + b"\x1c"
    m += b"\x00" * 8
    m += name_entry("Snd_x") + b"\x0c" + struct.pack("<HHI", 10, 2, 0)  # thunk
    m += name_entry("tick_cb") + b"\x0e" + struct.pack("<H", 14)        # alias?
    m += name_entry("helper") + b"\x00"   # tail, NOT in publics on purpose:
    # the SSCALL shape's tail is a FOREIGN name (SpuVmFlush), so the module's
    # public tick_cb is table-present (as ref) and the tail is foreign.
    struct.pack_into("<I", m, 16, len(m))
    out += m
    return bytes(out)


def build_group_lib():
    """The VMANAGER truncation regression (cron-20261101-0536): a row
    stream whose SECOND row is kind 0x30. The old 3-kind walk broke there
    and the longest-chain law fell back to the 2-row tail fragment; the
    0x30 kind must keep the whole stream parseable to the tail."""
    out = bytearray(b"LIB\x01")
    m = bytearray()
    m += b"GRP     " + b"\x4c\x1f" + b"\x00\xa1"
    m += struct.pack("<I", 0x20)
    m += struct.pack("<I", 0)
    m += name_entry("vm_init")
    m += name_entry("key_off")
    m += b"\x00"
    m += b"LNK"
    m += b"\x02.\x07" + b"\x10" + struct.pack("<I", 1) + b"\x08"
    m += name_entry(".text") + b"\x10" + struct.pack("<I", 2) + b"\x08"
    m += name_entry(".dtors") + b"\x1c"
    m += b"\x00" * 8
    m += name_entry("vm_init") + b"\x0c" + struct.pack("<HHI", 27, 2, 0x314c)
    m += name_entry("stat_one") + b"\x30" + struct.pack("<HHI", 67, 6, 2)
    m += name_entry("key_off") + b"\x0c" + struct.pack("<HHI", 21, 2, 0x25e0)
    m += name_entry("key_off") + b"\x00"   # tail = the absent last public
    struct.pack_into("<I", m, 16, len(m))
    out += m
    return bytes(out)


class TestQuirkClassification(unittest.TestCase):
    """The row-classification pin: defs vs thunks vs the alias class."""

    @classmethod
    def setUpClass(cls):
        cls.path = "/tmp/omf_pubsyms_quirk_test.lib"
        with open(cls.path, "wb") as f:
            f.write(build_quirk_lib())
        cls.lib = op.PsyqLib(cls.path)

    def test_thunk_row_is_not_a_definition(self):
        mod = self.lib.modules[0]
        s = mod.symbol("Snd_x")
        self.assertEqual(s.kind, 0x0C)
        cls = op.classify(mod)
        self.assertEqual(cls["Snd_x"], [op.VERDICT_THUNK])

    def test_def_row_for_own_public(self):
        mod = self.lib.modules[0]
        # add a def row check via a second module built on the fly is
        # overkill; assert the classification law with MOD2 of build_lib
        lib2 = op.PsyqLib("/tmp/omf_pubsyms_test.lib")
        m2 = lib2.modules[1]
        self.assertEqual(op.classify(m2)["sibling"], [op.VERDICT_DEF])

    def test_own_public_as_ref_is_flagged(self):
        mod = self.lib.modules[0]
        self.assertEqual(op.classify(mod)["tick_cb"], [op.VERDICT_REF])
        findings = op.check_module(mod)
        self.assertTrue(any("tick_cb" in f and "0x0e ref" in f
                            for f in findings), findings)

    def test_thunk_finding_names_the_law(self):
        mod = self.lib.modules[0]
        findings = op.check_module(mod)
        self.assertTrue(any("NOT a definition" in f and "Snd_x" in f
                            for f in findings), findings)

    def test_foreign_tail_is_not_reported_as_public(self):
        # the tail 'helper' is not a public - check_module must NOT invent
        # a finding for it (findings only cover real publics)
        mod = self.lib.modules[0]
        findings = op.check_module(mod)
        self.assertFalse(any("helper" in f for f in findings), findings)

    def test_cli_check_prints_findings(self):
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = op.main([self.path, "--check"])
        self.assertEqual(rc, 0)
        out = buf.getvalue()
        self.assertIn("[thunk]", out)
        self.assertIn("[ref]", out)
        self.assertIn("CHECK:", out)


class TestGroupModel(unittest.TestCase):
    """The 0x30 kind + the group-internal ref law (cron-20261101-0536)."""

    @classmethod
    def setUpClass(cls):
        cls.path = "/tmp/omf_pubsyms_group_test.lib"
        with open(cls.path, "wb") as f:
            f.write(build_group_lib())
        cls.lib = op.PsyqLib(cls.path)

    def test_kind30_row_parses(self):
        mod = self.lib.modules[0]
        s = mod.symbol("stat_one")
        self.assertIsNotNone(s)
        self.assertEqual(s.kind, 0x30)
        self.assertEqual((s.a, s.b, s.offset), (67, 6, 2))
        self.assertEqual(op.classify(mod)["stat_one"], [op.VERDICT_DEF30])

    def test_stream_survives_leading_30_kind(self):
        # the VMANAGER law: a 0x30 row early in the stream must NOT
        # truncate the walk - all three named rows parse to the tail
        mod = self.lib.modules[0]
        self.assertEqual([s.name for s in mod.symbols],
                         ["vm_init", "stat_one", "key_off"])
        self.assertEqual(mod.tail_name, "key_off")

    def test_def_map_and_index(self):
        mod = self.lib.modules[0]
        dmap = op.def_map(mod)
        self.assertIn(("vm_init", 0x0C, 27, 2, 0x314c), dmap)
        self.assertIn(("stat_one", 0x30, 67, 6, 2), dmap)
        idx = op.lib_def_index(self.lib)
        self.assertEqual(idx["vm_init"], [("GRP", 0x0C, 2, 0x314c)])

    def test_tail_public_needs_no_finding(self):
        mod = self.lib.modules[0]
        findings = op.check_module(mod)
        self.assertFalse(any("key_off" in f for f in findings), findings)


def build_base_lib():
    """One-module lib carrying a code chunk with an epilogue trap.

    Code layout (blob starts at first_chunk_data):
      +0x00 27bd0010  prologue A            -> def pub_a off=0x00 (strict)
      +0x10 27bd0020  epilogue restore A
      +0x14 03e00008  jr $ra                -> the +0x10 word MUST be refused
      +0x18 00000000  delay
      +0x1c 27bdffd8  prologue B            -> def pub_b off=0x1c (strict)
      +0x20..         nops, jr/nop tail

    The LNK last entry's 0x1c doubles as the first debug-path record's kind
    byte, exactly as measured on LIBSND VMANAGER (cron-20261101-0651)."""
    out = bytearray(b"LIB\x01")
    m = bytearray()
    m += b"BASEMOD " + b"\x4c\x1f" + b"\x00\xa1"
    m += struct.pack("<I", 0x20)
    m += struct.pack("<I", 0)
    m += name_entry("pub_a") + name_entry("pub_b") + b"\x00"
    m += b"LNK"
    m += b"\x02.\x07" + b"\x10" + struct.pack("<I", 1) + b"\x08"
    m += name_entry(".text") + b"\x10" + struct.pack("<I", 2) + b"\x08"
    m += name_entry(".dtors") + b"\x1c"          # doubles as path kind byte
    m += b"\x40\x00" + bytes([0x0a]) + b"C:\\src\\a.c"
    m += b"\x06\x02\x00"                          # section marker
    code = (struct.pack("<I", 0x27BD0010) + b"\x00" * 12
            + struct.pack("<I", 0x27BD0020)       # epilogue restore
            + struct.pack("<I", 0x03E00008)       # jr $ra
            + struct.pack("<I", 0x00000000)       # delay
            + struct.pack("<I", 0x27BDFFD8)       # prologue B
            + b"\x00" * 16
            + struct.pack("<I", 0x03E00008) + struct.pack("<I", 0))
    m += b"\x02" + struct.pack("<H", len(code)) + code
    m += name_entry("pub_a") + b"\x0c" + struct.pack("<HHI", 10, 2, 0x00)
    m += name_entry("pub_b") + b"\x0c" + struct.pack("<HHI", 11, 2, 0x1c)
    m += name_entry("pub_b") + b"\x00"
    struct.pack_into("<I", m, 16, len(m))
    out += m
    return bytes(out)


class TestDefBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = "/tmp/omf_pubsyms_base_test.lib"
        with open(cls.path, "wb") as f:
            f.write(build_base_lib())
        cls.lib = op.PsyqLib(cls.path)

    def test_first_code_chunk_walks_paths_and_marker(self):
        mod = self.lib.modules[0]
        blob, paths_end, n_paths = op.first_code_chunk(self.lib.data, mod)
        self.assertEqual(n_paths, 1)
        self.assertIsNotNone(blob)
        self.assertEqual(
            self.lib.data[blob:blob + 4], struct.pack("<I", 0x27BD0010))

    def test_epilogue_votes_are_refused(self):
        mod = self.lib.modules[0]
        sol = op.solve_def_base(self.lib.data, mod)
        self.assertIsNotNone(sol)
        base, hits, ndefs, _npros = sol
        blob, _pe, _np = op.first_code_chunk(self.lib.data, mod)
        self.assertEqual(base, blob)       # true base = blob start
        self.assertEqual((hits, ndefs), (2, 2))
        # the epilogue-implied ghost base (blob+0x10) must NOT win
        self.assertNotEqual(base, blob + 0x10)


@unittest.skipUnless(PSYQ_DIR, "psyq archive not provisioned")
class TestDefBaseReal(unittest.TestCase):
    def test_vmanager_base_and_banked_anchors(self):
        lib = op.PsyqLib(os.path.join(PSYQ_DIR, "LIBSND.LIB"))
        m = next(x for x in lib.modules if x.name == "VMANAGER")
        base, hits, ndefs, _npros = op.solve_def_base(lib.data, m)
        self.assertEqual(base, 0x10668)
        self.assertEqual((hits, ndefs), (23, 38))
        self.assertEqual(base + 0x1dfc, 0x12464)   # _svm_damper (banked)
        self.assertEqual(base + 0x4cd4, 0x1533c)   # _svm_envx_hist (banked)

    def test_single_object_modules_sit_at_delta_zero(self):
        lib = op.PsyqLib(os.path.join(PSYQ_DIR, "LIBSND.LIB"))
        for name in ("SSCLOSE", "SSPLAY"):
            m = next(x for x in lib.modules if x.name == name)
            base, _hits, _ndefs, _npros = op.solve_def_base(lib.data, m)
            blob, _pe, _np = op.first_code_chunk(lib.data, m)
            self.assertIsNotNone(blob)
            self.assertEqual(base, blob, name)


if __name__ == "__main__":
    unittest.main()

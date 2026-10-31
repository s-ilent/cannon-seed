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
  * the three symbol kinds (0x0c def, 0x0e cross-module ref, 0x12 second
    ref class) and the chain stop at an unknown kind;
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


PSYQ_DIR = "/home/z/psyq/3.3/PSX/LIB"


@unittest.skipUnless(os.path.isdir(PSYQ_DIR), "psyq archive not provisioned")
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


if __name__ == "__main__":
    unittest.main()

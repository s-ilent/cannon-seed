#!/usr/bin/env python3
"""Tests for tools/sdk_members.py symbol-window scanning (--windows).

Whole-member sliding assumes the game SDK grouped functions into archive
members like the local drop. The cron-20261024 review proved it does not:
mainmenu_eu's data_8006FCF8 island carries LightColor/DpqColorLight/
DpqColor3 verbatim, but the local member continues with OuterProduct*/
Lzc, so the whole-member slide saw nothing and the functions were
hand-derived across targets (commit 68f0df80).

Run: python3 -m unittest tests/test_sdk_windows.py -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "tools"))
import sdk_members as sm  # noqa: E402


class FakeMember:
    """Minimal Member stand-in for locate_windows()."""

    def __init__(self, text, syms):
        self._text = text
        self._syms = syms

    def text(self):
        return self._text

    def text_syms(self):
        return self._syms


def member():
    # 14 function slots of 0x28 bytes, none of it zero: relocated fields
    # are wildcards for the whole-member slide but NOT here, so a zero
    # byte would end a verbatim span by construction. The mix must not be
    # periodic (a stride-0x100 pattern would match its own tail).
    text = bytes((((i * 7 + 3) ^ (i >> 3)) & 0xFF) or 1 for i in range(0x280))
    syms = [(o, "fn_%02x" % o) for o in range(0, 0x280, 0x28)]
    return FakeMember(text, syms)


class TestLocateWindows(unittest.TestCase):
    def test_whole_text_present(self):
        m = member()
        payload = b"\x00" * 0x40 + m.text() + b"\xff" * 0x40
        spans = sm.locate_windows(payload, m)
        self.assertEqual(len(spans), 1)
        off, size, names, mark = spans[0]
        self.assertEqual(off, 0x40)
        self.assertEqual(size, 0x280)
        self.assertEqual(mark, "verbatim")
        self.assertEqual(len(names), 0x280 // 0x28)

    def test_prefix_present_only(self):
        # the game SDK's member ends at fn_0e0: the tail (OuterProduct*/Lzc
        # in the real case) is absent, so whole-member matching fails
        m = member()
        payload = b"\xaa" * 0x20 + m.text()[:0x100] + b"\x00" * 0x40
        spans = sm.locate_windows(payload, m)
        self.assertEqual(len(spans), 1)
        off, size, names, mark = spans[0]
        self.assertEqual((off, size), (0x20, 0x100))
        self.assertEqual(mark, "verbatim")
        # symbol names inside the span only, offsets relative to span start
        self.assertEqual([n for _d, n in names],
                         ["fn_%02x" % o for o in range(0, 0x100, 0x28)])
        self.assertEqual([d for d, _n in names],
                         list(range(0, 0x100, 0x28)))

    def test_relocated_fields_are_wildcards(self):
        # link-time constants: the object carries zeroes where the image
        # carries patched addresses - same code, 'fixed' not 'verbatim'
        base = member().text()
        text = bytearray(base)
        for off in (0x0C, 0x44, 0x94):        # lo16/hi16-ish patched words
            text[off:off + 2] = b"\x00\x00"
        m = FakeMember(bytes(text), member().text_syms())
        payload = bytes(base) + b"\x00" * 0x40
        spans = sm.locate_windows(payload, m)
        self.assertEqual(len(spans), 1)
        _off, size, _names, mark = spans[0]
        self.assertEqual(size, 0x280)
        self.assertEqual(mark, "fixed")

    def test_wildcard_run_cannot_wander(self):
        # 0x14 consecutive zero bytes in the object: past the 0x10 cap the
        # span must break, not swallow whatever follows
        m = member()
        text = bytearray(m.text())
        text[0x100:0x114] = b"\x00" * 0x14
        m2 = FakeMember(bytes(text), m.text_syms())
        payload = bytes(text[:0x110]) + b"\xff" * 0x40 + b"\x00" * 0x40
        for off, size, names, mark in sm.locate_windows(payload, m2):
            self.assertLessEqual(size, 0x110)

    def test_interior_run_stops_at_divergence(self):
        m = member()
        cut = bytearray(m.text())
        cut[0x60] ^= 0xFF          # divergence inside fn_60
        payload = bytes(cut) + b"\x00" * 0x40
        spans = sm.locate_windows(payload, m)
        # two honest facts: the run before the divergence, and the
        # verbatim run from the next clean symbol boundary onward
        self.assertEqual(len(spans), 2)
        off0, size0, names0, mark0 = spans[0]
        self.assertEqual((off0, size0), (0, 0x60))
        self.assertEqual(mark0, "verbatim")   # the flip is at 0x60, outside
        # fn_50's first 0x10 bytes are inside the span; >= 8 bytes counts
        self.assertEqual([n for _d, n in names0], ["fn_00", "fn_28", "fn_50"])
        off1, size1, names1, mark1 = spans[1]
        self.assertEqual(off1, 0x78)               # first symbol past 0x60
        self.assertEqual(size1, 0x280 - 0x78)
        self.assertEqual(mark1, "verbatim")
        # deltas are relative to the span start (report computes addr+d)
        self.assertEqual([d for d, _n in names1],
                         list(range(0, 0x280 - 0x78, 0x28)))
        self.assertEqual(names1[0][1], "fn_78")

    def test_absent_member_yields_nothing(self):
        m = member()
        payload = b"\x01\x02\x03\x04" * 0x100
        self.assertEqual(sm.locate_windows(payload, m), [])

    def test_word_alignment_enforced(self):
        m = member()
        payload = b"\x00" * 0x41 + m.text()
        self.assertEqual(sm.locate_windows(payload, m), [])

    def test_single_short_symbol_not_reported(self):
        text = bytes((((i * 11 + 5) & 0xFF) or 2) for i in range(0x28))
        m = FakeMember(text, [(0, "tiny"), (0x28 - 4, "shrt")])
        payload = text + b"\x00" * 0x40
        # only one full symbol inside -> needs size >= 0x100 to stand alone
        self.assertEqual(sm.locate_windows(payload, m), [])


class TestYamlAnchors(unittest.TestCase):
    """The yaml is a scatter list: names carry the true vram, and it is
    not linear in file offset. Cron-20261024: a single linear map put a
    query 0xa510 away from its real bytes in mainmenu_eu."""

    ANCHORS = [(0x800, 0x80020000), (0x1c70, 0x80021800),
               (0x45FE8, 0x8006FCF8), (0x46850, 0x80070650)]

    def test_raw_to_name_inside_subsegment(self):
        a = self.ANCHORS
        self.assertEqual(sm.raw_to_name(0x45FEC, a), 0x8006FCFC)
        self.assertEqual(sm.raw_to_name(0x804, a), 0x80020004)

    def test_raw_to_name_before_first_anchor(self):
        self.assertIsNone(sm.raw_to_name(0x100, self.ANCHORS))

    def test_name_to_raw_roundtrip(self):
        a = self.ANCHORS
        off = sm.name_to_raw(0x8006FCFC, a)
        self.assertEqual(off, 0x45FEC)
        self.assertEqual(sm.raw_to_name(off, a), 0x8006FCFC)

    def test_real_yaml_carves_the_scatter(self):
        # mainmenu_eu: the 68f0df80 island sits at raw 0x45FE8 and its
        # yaml name says 0x8006FCF8 - a linear map says 0x800657E8
        a = sm.yaml_anchors("mainmenu_eu")
        self.assertEqual(sm.raw_to_name(0x45FE8, a), 0x8006FCF8)
        # landed c rows carry real names (no _XXXXXXXX): they must be
        # present in with_kind but not anchor positions
        kinds = sm.yaml_anchors("mainmenu_eu", with_kind=True)
        self.assertIn("c", [k for _o, k, _n, _v in kinds])


if __name__ == "__main__":
    unittest.main()

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
        off, size, names = spans[0]
        self.assertEqual(off, 0x40)
        self.assertEqual(size, 0x280)
        self.assertEqual(len(names), 0x280 // 0x28)

    def test_prefix_present_only(self):
        # the game SDK's member ends at fn_0e0: the tail (OuterProduct*/Lzc
        # in the real case) is absent, so whole-member matching fails
        m = member()
        payload = b"\xaa" * 0x20 + m.text()[:0x100] + b"\x00" * 0x40
        spans = sm.locate_windows(payload, m)
        self.assertEqual(len(spans), 1)
        off, size, names = spans[0]
        self.assertEqual((off, size), (0x20, 0x100))
        # symbol names inside the span only, offsets relative to span start
        self.assertEqual([n for _d, n in names],
                         ["fn_%02x" % o for o in range(0, 0x100, 0x28)])
        self.assertEqual([d for d, _n in names],
                         list(range(0, 0x100, 0x28)))

    def test_interior_run_stops_at_divergence(self):
        m = member()
        cut = bytearray(m.text())
        cut[0x60] ^= 0xFF          # divergence inside fn_60
        payload = bytes(cut) + b"\x00" * 0x40
        spans = sm.locate_windows(payload, m)
        # two honest facts: the run before the divergence, and the
        # verbatim run from the next clean symbol boundary onward
        self.assertEqual(len(spans), 2)
        off0, size0, names0 = spans[0]
        self.assertEqual((off0, size0), (0, 0x60))
        # fn_50's first 0x10 bytes are inside the span; >= 8 bytes counts
        self.assertEqual([n for _d, n in names0], ["fn_00", "fn_28", "fn_50"])
        off1, size1, names1 = spans[1]
        self.assertEqual(off1, 0x78)               # first symbol past 0x60
        self.assertEqual(size1, 0x280 - 0x78)
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
        text = bytes(((i * 11 + 5) & 0xFF) or 2 for i in range(0x28))
        m = FakeMember(text, [(0, "tiny"), (0x28 - 4, "shrt")])
        payload = text + b"\x00" * 0x40
        # only one full symbol inside -> needs size >= 0x100 to stand alone
        self.assertEqual(sm.locate_windows(payload, m), [])


if __name__ == "__main__":
    unittest.main()

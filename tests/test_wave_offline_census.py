#!/usr/bin/env python3
"""tests/test_wave_offline_census.py - the witness-free wave universe must
include every real asm row, including the duplicate-name-disambiguated
dotted rows (func_XXXXXXXX.2).

The 2026-11-01 re-rank found the f3e0fb2d 0x34 wave listing 6 members
while the tree carries SEVEN byte-identical own-row copies: g3_jp's row is
named func_800629A0.2 (the scan's duplicate-name disambiguation over the
landed c row func_800629A0), and ROW_RE's `\\w+` name group stopped at the
dot - 14 dotted asm rows across the eight configs silently fell out of
the census universe. The fix widens the name group to `[\\w.]+`; these
tests pin the row-line parse end to end at the regex level (no fixtures,
no build, fully offline):

  * a plain row parses (offset, type, name, extent comment);
  * a dotted row parses WITH the dot and the full extent;
  * non-asm rows (c/data) and non-row lines never match.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import wave_offline_census as woc  # noqa: E402


class RowRegexTest(unittest.TestCase):
    def test_plain_row_parses_with_extent(self):
        m = woc.ROW_RE.match(
            "      - [0x43B30, asm, func_80063330]   # 0x34 sdk")
        self.assertIsNotNone(m)
        self.assertEqual(m.groups(), ("43B30", "asm", "func_80063330"))

    def test_dotted_row_parses_with_dot(self):
        m = woc.ROW_RE.match(
            "      - [0x431A0, asm, func_800629A0.2]   # 0x34 sdk")
        self.assertIsNotNone(m)
        self.assertEqual(m.groups(), ("431A0", "asm", "func_800629A0.2"))

    def test_non_asm_rows_match_regex_but_filter_is_asms(self):
        # the type filter lives in asm_rows (group(2) == "asm"), not in
        # ROW_RE - the regex must simply capture the type faithfully
        m = woc.ROW_RE.match("      - [0x3A7E0, c, func_800629A0]   # 0x8")
        self.assertIsNotNone(m)
        self.assertEqual(m.group(2), "c")
        m = woc.ROW_RE.match(
            "      - [0x57B6C, data, data_8008433C]   # 0x4b8")
        self.assertIsNotNone(m)
        self.assertEqual(m.group(2), "data")
        self.assertIsNone(woc.ROW_RE.match("  .L80077B04:"))
        self.assertIsNone(woc.ROW_RE.match(
            "      - [0x431A0, asm, ]   # nameless"))

    def test_dotted_rows_exist_in_the_real_configs(self):
        # read-only real-repo pin: the universe gap was real - at least one
        # dotted asm row exists, and every dotted row's listing file exists
        # on disk (the census can actually read what it now includes)
        dotted = []
        for t in woc.TARGETS:
            for off, name, ext in woc.asm_rows(t):
                if "." in name:
                    dotted.append((t, name))
                    self.assertTrue(
                        woc.listing_path(t, name).exists(),
                        f"{t}: dotted row {name} has no committed listing")
        self.assertGreaterEqual(len(dotted), 14)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Tests for tools/invariant_census.py ranking helpers.

The two comparisons fixed in the cron-20261023 review:
  * scan_member keyed on votes instead of the eq fraction;
  * main() dedupe kept the LOWEST eq fraction per (tgt, start) key,
    opposite its "keep best eq" comment. The misattribution feeds
    split_classifier.py's fn-size lookup, so it changes class assignment.

Live-tree effect measured on the cron-20261023 window: 167 multi-vote
keys across the five gate-passing targets; 70 of ~417 candidate rows
change under the fixed rule (e.g. mainmenu_eu 0x80081EF4 keeps
word-eq 8/8 instead of 87/88).

Run: python3 -m unittest tests/test_invariant_census.py -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "tools"))
import invariant_census as ic  # noqa: E402


def row(src_t, name, tgt, start, cls, encl, eq, n, votes):
    """main()-shape row; size is fixed at 0x40 (never ranked)."""
    return (src_t, name, 0x40, tgt, start, cls, encl, eq, n, votes)


class TestBetterEq(unittest.TestCase):
    def test_beats_by_fraction(self):
        # 22/22 beats 21/22: cross-mult 22*22=484 > 21*22=462.
        self.assertTrue(ic.better_eq(22, 22, 21, 22))

    def test_tie_keeps_first_seen(self):
        # Strict: equal fractions never beat.
        self.assertFalse(ic.better_eq(21, 22, 21, 22))

    def test_low_fraction_does_not_beat(self):
        # 8/8 (fraction 1.0) beats 87/88 even though its counts are lower;
        # the old inverted rule kept 87/88 instead.
        self.assertTrue(ic.better_eq(8, 8, 87, 88))

    def test_no_floats(self):
        # Equal fractions written differently are decided exactly:
        # 1/3 vs 2/6 tie, strict tie keeps first-seen.
        self.assertFalse(ic.better_eq(1, 3, 2, 6))


class TestDedupeBest(unittest.TestCase):
    def test_disagreeing_members_keep_best_eq(self):
        # Two members vote the same key mainmenu_eu 0x80081EF4.
        a = row("mainmenu_eu", "SsSetSerialVol", "mainmenu_eu", 0x80081EF4,
                "func-row", "-", 87, 88, 20)
        b = row("mainmenu_eu", "OtherMember", "mainmenu_eu", 0x80081EF4,
                "func-row", "-", 8, 8, 5)
        kept = ic.dedupe_best([a, b])
        self.assertEqual(len(kept), 1)
        # Best fraction is 8/8: the fixed rule keeps it, the old rule
        # kept a (the lower fraction).
        self.assertIs(kept[0], b)

    def test_tie_keeps_first_seen(self):
        a = row("g3_jp", "A", "g3_jp", 0x80059EB0, "func-row", "-", 6, 6, 2)
        b = row("g3_jp", "B", "g3_jp", 0x80059EB0, "func-row", "-", 6, 6, 3)
        kept = ic.dedupe_best([a, b])
        self.assertIs(kept[0], a)

    def test_distinct_keys_all_survive(self):
        rows = [row("g3_jp", "A", "g3_jp", 0x80059EB0, "func-row", "-", 6, 6, 2),
                row("g3org_jp", "C", "g3org_jp", 0x8004EFB4, "DATA-ROW", "-", 22, 22, 4)]
        kept = ic.dedupe_best(rows)
        self.assertEqual(len(kept), 2)

    def test_single_row_passes_through(self):
        r = row("mainmenu_eu", "OuterProduct12", "mainmenu_eu", 0x80065930,
                "func-row", "-", 22, 22, 3)
        self.assertEqual(ic.dedupe_best([r]), [r])


if __name__ == "__main__":
    unittest.main()

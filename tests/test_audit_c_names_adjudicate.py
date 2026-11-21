#!/usr/bin/env python3
"""Tests for audit_c_names.py's --adjudicate evidence overlay.

The census's target-unique mismatch class overcounts the fair-game set:
the memclr family and the other sdk-anchor rows carry their identity in
config/sdk_anchors.txt / config/symbols.curated.txt, and cross-target
shared names are the owner-gated naming call.  The 2026-11-21 windows
adjudicated these by hand and corrected the queue twice; --adjudicate
codifies the classification so the recount is mechanical.

Run: python3 -m unittest tests/test_audit_c_names_adjudicate.py -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "tools"))
import audit_c_names as ac  # noqa: E402


class TestParseSdkAnchors(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "fixtures_adjudicate", "sdk_anchors.txt")
        self.anchors = ac.parse_sdk_anchors(self.path)

    def test_membership_fields(self):
        a = self.anchors[0x8004AB24][0]
        self.assertEqual(a["symbol"], "memclr")
        self.assertEqual(a["member"], "INTR_VB")
        self.assertEqual(a["library"], "LIBETC")
        self.assertIn("unique", a["tags"])

    def test_unique_placement_keying(self):
        # Two anchors at DIFFERENT placements never merge; the dict is
        # keyed by the placement int, not the text.
        self.assertIn(0x8004AB24, self.anchors)
        self.assertIn(0x800447A0, self.anchors)
        self.assertIsNot(self.anchors[0x8004AB24][0],
                         self.anchors[0x800447A0][0])

    def test_skips_comments_and_blanks(self):
        # The fixture's header comment and blank lines produced no keys.
        self.assertEqual(len(self.anchors), 3)


class TestParseCurated(unittest.TestCase):
    def setUp(self):
        self.path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "fixtures_adjudicate", "curated.txt")
        self.curated = ac.parse_curated(self.path)

    def test_named_and_bare_lines(self):
        # `name = 0x...; // comment` and bare `0x...; // comment` both parse.
        self.assertIn(0x8002EDB0, self.curated)
        self.assertEqual(self.curated[0x8002EDB0][0]["name"], "setjmp")
        self.assertIn(0x8002F168, self.curated)
        self.assertEqual(self.curated[0x8002F168][0]["name"], "")

    def test_comment_roundtrip(self):
        cmt = self.curated[0x8002F168][0]["comment"]
        self.assertIn("C-DEFINITION SITE", cmt)
        self.assertIn("emclr-placement conflict class", cmt)


class TestClassifyMismatch(unittest.TestCase):
    def setUp(self):
        fx = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "fixtures_adjudicate")
        self.anchors = ac.parse_sdk_anchors(
            os.path.join(fx, "sdk_anchors.txt"))
        self.curated = ac.parse_curated(os.path.join(fx, "curated.txt"))

    @staticmethod
    def row(name, placement):
        return {"name": name, "placement": placement, "status": "mismatch"}

    def test_shared_name_is_owner_gated(self):
        cls, ev = ac.classify_mismatch(self.row("func_800492F8", 0x0),
                                       {"func_800492F8"}, self.anchors,
                                       self.curated)
        self.assertEqual(cls, "SHARED")
        self.assertIn("owner-gated", ev)

    def test_memclr_anchor_parks(self):
        cls, ev = ac.classify_mismatch(self.row("func_80051144", 0x8004AB24),
                                       set(), self.anchors, self.curated)
        self.assertEqual(cls, "PARKED-MEMCLR")
        self.assertIn("sdk_anchors", ev)
        self.assertIn("memclr INTR_VB", ev)

    def test_real_member_anchor_is_carve_candidate(self):
        cls, ev = ac.classify_mismatch(self.row("func_80049E50", 0x800447A0),
                                       set(), self.anchors, self.curated)
        self.assertEqual(cls, "CARVE-CANDIDATE")
        self.assertIn("SpuVmDamperOn", ev)

    def test_curated_parking_language_parks(self):
        cls, ev = ac.classify_mismatch(self.row("func_80031638", 0x8002F168),
                                       set(), self.anchors, self.curated)
        self.assertEqual(cls, "PARKED-CURATED")
        self.assertIn("C-DEFINITION SITE", ev)

    def test_curated_supportive_is_note(self):
        cls, _ = ac.classify_mismatch(self.row("func_8002EDB0", 0x8002EDB0),
                                      set(), self.anchors, self.curated)
        self.assertEqual(cls, "CURATED-NOTE")

    def test_open_when_no_evidence(self):
        cls, ev = ac.classify_mismatch(self.row("func_8004C4CC", 0x8004682C),
                                       set(), self.anchors, self.curated)
        self.assertEqual(cls, "OPEN")
        self.assertIn("3ccee159", ev)

    def test_anchor_wins_over_curated(self):
        # A placement anchored AND curated classifies by the anchor (the
        # stronger evidence); the curated text rides the evidence string.
        cls, ev = ac.classify_mismatch(self.row("func_80031940", 0x8004AB24),
                                       set(), self.anchors, self.curated)
        self.assertEqual(cls, "PARKED-MEMCLR")
        self.assertIn("sdk_anchors", ev)


if __name__ == "__main__":
    unittest.main()

"""Offline tests for evidence-separated byte-level decompilation coverage."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import coverage_report as cv


class CoverageFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "config").mkdir()
        (self.root / "src").mkdir()
        yaml = """segments:
  - name: payload
    type: code
    start: 0x800
    vram: 0x80020000
    subsegments:
      - [0x800, asm, Unmatched]
      - [0x840, c, Foo]
      - [0x880, c, Bar]
      - [0x900, data, D]
  - [0x1100]
"""
        (self.root / "config/splat.g3_jp.yaml").write_text(yaml)
        self.anchors = self.root / "config/sdk_anchors.txt"
        self.anchors.write_text(
            "// target: g3_jp (2 anchors)\n"
            "0x80020030 0x40 SDK1 LIB LIBSND unique\n"
            "0x80020040 0x30 SDK2 LIB LIBSND window-fixed\n"
        )
        (self.root / "src/Foo.c").write_text(
            '/* __asm__ volatile("wrong"); */\n'
            "int Foo(void) { return 1; }\n"
        )
        (self.root / "src/Bar.c").write_text(
            'void Bar(void) { __asm__ volatile("nop"); }\n'
        )
        self.reviews = self.root / "config/coverage_reviews.json"

    def set_reviews(self, *entries):
        self.reviews.write_text(json.dumps({"schema": 1, "reviews": list(entries)}))

    @staticmethod
    def review(name, tier, source=None):
        return {
            "target": "g3_jp", "name": name,
            "source": source or f"src/{name}.c", "tier": tier,
            "evidence": "Reviewed the bounded function's source and calls.",
        }

    def single(self, *, strict=False, rows=False):
        return cv.report(self.root, target="g3_jp", rows=rows, strict=strict)


class TestEvidenceIntervals(CoverageFixture):
    def test_union_does_not_double_count_overlapping_anchors(self):
        intervals = [(10, 25), (15, 35), (2, 5)]
        self.assertEqual(cv.overlap_union(0, 50, intervals), 28)

    def test_exact_mapped_byte_denominators(self):
        t = self.single()["targets"][0]
        self.assertEqual(t["payload_bytes"], 0x900)
        self.assertEqual(t["c_bytes"], 0xC0)
        self.assertEqual(t["asm_bytes"], 0x40)
        self.assertEqual(t["mapped_code_bytes"], 0x100)
        self.assertEqual(t["mapped_data_bytes"], 0x800)
        self.assertEqual(t["c_share_of_mapped_code_pct"], 75.0)

    def test_sdk_provenance_not_confused_with_game(self):
        t = self.single()["targets"][0]
        self.assertEqual(t["sdk_evidenced_code_bytes"], 0x40)
        self.assertEqual(t["sdk_evidenced_asm_bytes"], 0x10)
        self.assertEqual(t["sdk_evidenced_c_bytes"], 0x30)
        self.assertEqual(t["origin_unattributed_code_bytes"], 0xC0)
        self.assertEqual(t["origin_unattributed_c_bytes"], 0x90)
        self.assertEqual(t["origin_unattributed_c_share_pct"], 75.0)

    def test_source_unit_flags_not_semantic_claims(self):
        t = self.single()["targets"][0]
        self.assertEqual(t["c_source_flags_bytes"]["no_inline_asm_detected"], 0x40)
        self.assertEqual(t["c_source_flags_bytes"]["inline_asm"], 0x80)
        self.assertEqual(t["c_review_bytes"]["unreviewed"], 0xC0)
        self.assertEqual(t["c_review_bytes"]["semantic_c"], 0)

    def test_reviewed_bytes_are_only_explicit_reviews(self):
        self.set_reviews(self.review("Foo", "semantic_c"),
                         self.review("Bar", "hybrid"))
        t = self.single()["targets"][0]
        self.assertEqual(t["c_review_bytes"]["semantic_c"], 0x40)
        self.assertEqual(t["c_review_bytes"]["hybrid"], 0x80)
        self.assertEqual(t["c_review_bytes"]["unreviewed"], 0)
        self.assertEqual(t["reviewed_rows"]["hybrid"], 1)

    def test_per_row_audit_shows_exact_sources_and_evidence(self):
        t = self.single(rows=True)["targets"][0]
        rows = [r for r in t["rows"] if r["kind"] == "c"]
        self.assertEqual([r["offset"] for r in rows], [0x840, 0x880])
        self.assertEqual(rows[0]["source"], "src/Foo.c")
        self.assertEqual(rows[0]["sdk_evidenced_bytes"], 0x30)

    def test_no_retail_claims(self):
        r = self.single()
        self.assertFalse(r["retail_verified"])
        self.assertIn("not proven game", r["origin_warning"])


class TestRefusals(CoverageFixture):
    def test_malformed_missing_end_fails(self):
        path = self.root / "config/splat.g3_jp.yaml"
        path.write_text(path.read_text().replace("  - [0x1100]\n", ""))
        with self.assertRaisesRegex(cv.CoverageError, "end boundary"):
            self.single()

    def test_noncontiguous_row_fails(self):
        path = self.root / "config/splat.g3_jp.yaml"
        path.write_text(path.read_text().replace("0x840, c", "0x830, c"))
        # The new row is still contiguous, but one row is 0x30 bytes long.
        # Make an actual invalid ordering instead.
        path.write_text(path.read_text().replace("0x880, c", "0x810, c"))
        with self.assertRaisesRegex(cv.CoverageError, "noncontiguous"):
            self.single()

    def test_malformed_sdk_evidence_fails(self):
        self.anchors.write_text("// target: g3_jp\n0x80020030 BAD\n")
        with self.assertRaisesRegex(cv.CoverageError, "invalid SDK anchor"):
            self.single()

    def test_missing_source_is_visible_and_strictly_refused(self):
        (self.root / "src/Bar.c").unlink()
        t = self.single()["targets"][0]
        self.assertEqual(t["source_missing_rows"], 1)
        self.assertEqual(t["c_source_flags_bytes"]["source_missing"], 0x80)
        with self.assertRaisesRegex(cv.CoverageError, "no resolved source"):
            self.single(strict=True)

    def test_missing_sdk_evidence_refused_only_by_strict(self):
        self.anchors.write_text("// target: other\n")
        t = self.single()["targets"][0]
        self.assertEqual(t["sdk_evidenced_code_bytes"], 0)
        with self.assertRaisesRegex(cv.CoverageError, "no committed SDK anchors"):
            self.single(strict=True)

    def test_semantic_review_with_inline_asm_is_refused(self):
        self.set_reviews(self.review("Bar", "semantic_c"))
        with self.assertRaisesRegex(cv.CoverageError, "contradicts source flags"):
            self.single()

    def test_stale_review_name_is_refused(self):
        self.set_reviews(self.review("Unmatched", "hybrid"))
        with self.assertRaisesRegex(cv.CoverageError, "orphaned review"):
            self.single()

    def test_stale_review_source_is_refused(self):
        self.set_reviews(self.review("Foo", "semantic_c", "src/Renamed.c"))
        with self.assertRaisesRegex(cv.CoverageError, "source differs"):
            self.single()

    def test_duplicate_review_is_refused(self):
        self.set_reviews(self.review("Foo", "semantic_c"),
                         self.review("Foo", "semantic_c"))
        with self.assertRaisesRegex(cv.CoverageError, "duplicate review"):
            self.single()

    def test_invalid_review_tier_is_refused(self):
        self.set_reviews(self.review("Foo", "fully_decompiled"))
        with self.assertRaisesRegex(cv.CoverageError, "invalid review entry"):
            self.single()

    def test_per_target_source_overrides_shared_source(self):
        d = self.root / "src/g3_jp"
        d.mkdir()
        (d / "Foo.c").write_text('void Foo(void) { __asm__("nop"); }\n')
        t = self.single(rows=True)["targets"][0]
        foo = next(r for r in t["rows"] if r["name"] == "Foo")
        self.assertEqual(foo["source"], "src/g3_jp/Foo.c")
        self.assertEqual(foo["source_style"], "inline_asm")

    def test_reviewed_target_instance_not_double_counted_within_target(self):
        self.set_reviews(self.review("Foo", "semantic_c"))
        t = self.single()["targets"][0]
        self.assertEqual(t["reviewed_rows"]["semantic_c"], 1)


if __name__ == "__main__":
    unittest.main()

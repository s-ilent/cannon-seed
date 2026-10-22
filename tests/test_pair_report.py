#!/usr/bin/env python3
"""tests/test_pair_report.py - the cron-20261022-0313b instrument gaps.

Offline unit tests for the two pair_report fixes (no baselines, no build
ELFs - fixtures are synthetic bytes and temp-dir yamls):

1. is_matched target-scoping: the matched decision is the target's own
   yaml c-row map (structured parse, spans to the next subsegment row).
   The old bare src/<name>.c existence test was not target-scoped and
   false-matched cross-exe name collisions (src/func_80037CAC.c belongs
   to mainmenu_eu while g3_eu's yaml covers the VA with an asm rowdef).
2. is_fragment over-0x10 mid-body detection via the out-of-symbol branch
   signal (func_8002E3D0: sz 0x28, closing bne 0x4c past the symbol end
   - the over-0x10 slice the old unconditional False let through to the
   compiler class).

Run:  python3 -m unittest tests/test_pair_report.py -v
"""
import os
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "tools"))
import pair_report as pr  # noqa: E402


class Fixture(unittest.TestCase):
    """Swap the module's REPO / caches / byte source for synthetic ones."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.makedirs(os.path.join(self._tmp.name, "src"))
        os.makedirs(os.path.join(self._tmp.name, "config"))
        self._save = (pr.REPO, dict(pr._C_ROWS), pr.baseline_bytes)
        pr.REPO = self._tmp.name
        pr._C_ROWS = {}
        self.addCleanup(self._restore)

    def _restore(self):
        pr.REPO, rows, bb = self._save
        pr._C_ROWS = rows
        pr.baseline_bytes = bb
        self._tmp.cleanup()

    def put_src(self, name):
        with open(os.path.join(self._tmp.name, "src", f"{name}.c"), "w") as f:
            f.write("/* fixture */\n")

    def put_yaml(self, target, text):
        with open(os.path.join(self._tmp.name, "config",
                               f"splat.{target}.yaml"), "w") as f:
            f.write(text)

    def put_bytes(self, words):
        blob = b"".join(struct.pack("<I", w) for w in words)

        def fake_bytes(target, va, size, _blob=blob):
            return _blob[:size]
        pr.baseline_bytes = fake_bytes


# --- is_matched: target-scoped c-row map -------------------------------------

class TestIsMatchedScoped(Fixture):
    ROWS_MM_EU = [(0x80037CAC, 0x80037CD8, "func_80037CAC")]

    def test_cross_exe_collision_fixed(self):
        """The 0313b artifact: the src file exists but belongs to
        mainmenu_eu; g3_eu has no c row at the VA -> NOT matched."""
        pr._C_ROWS = {"mainmenu_eu": list(self.ROWS_MM_EU), "g3_eu": []}
        self.put_src("func_80037CAC")
        self.assertFalse(pr.is_matched("g3_eu", "func_80037CAC",
                                       0x80037CAC))
        self.assertTrue(pr.is_matched("mainmenu_eu", "func_80037CAC",
                                      0x80037CAC))

    def test_span_covers_merged_parent_member(self):
        """A member split out of a merged parent is matched by the
        parent row's span, no own row, no own file needed."""
        pr._C_ROWS = {"t": [(0x80010000, 0x80010100, "func_80010000")]}
        self.assertTrue(pr.is_matched("t", "func_80010040", 0x80010040))

    def test_span_boundaries(self):
        pr._C_ROWS = {"t": [(0x80010000, 0x80010010, "row")]}
        self.assertTrue(pr.is_matched("t", "x", 0x80010000))    # lo
        self.assertFalse(pr.is_matched("t", "x", 0x80010010))   # hi exclusive
        self.assertFalse(pr.is_matched("t", "x", 0x8000FFFC))   # below

    def test_name_only_call(self):
        pr._C_ROWS = {"t": [(0x80010000, 0x80010100, "GsCurated")],
                      "u": []}
        self.assertTrue(pr.is_matched("t", "GsCurated"))
        self.assertFalse(pr.is_matched("u", "GsCurated"))

    def test_asm_row_va_not_matched_even_with_file(self):
        """A VA the target serves as asm is unmatched even though some
        other target lands a c row of the same name elsewhere."""
        pr._C_ROWS = {"t": [], "u": [(0x80020000, 0x80020048, "func_x")]}
        self.put_src("func_x")
        self.assertFalse(pr.is_matched("t", "func_x", 0x80020000))
        self.assertTrue(pr.is_matched("u", "func_x", 0x80020000))


class TestCRowsParse(Fixture):
    def test_structured_parse_matches_build_sh_universe(self):
        """Only code-segment 3+-element `c` rows; VA = vram + rom -
        0x800; spans run to the next subsegment row (any type)."""
        self.put_yaml("t", """\
options:
  asm_path: asm/nonmatchings
segments:
  - type: header
    start: 0x0
  - type: code
    vram: 0x80020000
    start: 0x800
    subsegments:
      - [0x800, data, data_80020000]
      - [0x900, c, func_80020100]      # spans to the NEXT row (0x948)
      - [0x948, asm, func_80020148]
      - [0x960, c, func_80020160]      # last row: unbounded tail
  - type: data
    start: 0x1000
    subsegments:
      - [0x1000, c, not_code_segment]  # must be ignored
""")
        rows = pr.c_rows("t")
        # the code segment's last c row is bounded by the NEXT segment's
        # start (0x1000 -> VA 0x80020800), not an unbounded tail
        self.assertEqual(rows, [
            (0x80020100, 0x80020148, "func_80020100"),
            (0x80020160, 0x80020800, "func_80020160"),
        ])
        self.assertTrue(pr.is_matched("t", "q", 0x80020120))
        self.assertFalse(pr.is_matched("t", "q", 0x80020148))  # the asm row
        self.assertFalse(pr.is_matched("t", "q", 0x80021000))  # data segment

    def test_piece_rows_get_own_spans(self):
        self.put_yaml("t", """\
segments:
  - type: code
    vram: 0x80020000
    start: 0x800
    subsegments:
      - [0x800, c, base]
      - [0x840, c, base.p2]
      - [0x880, data, tail]
""")
        rows = pr.c_rows("t")
        self.assertEqual(rows, [
            (0x80020000, 0x80020040, "base"),
            (0x80020040, 0x80020080, "base.p2"),
        ])


# --- is_fragment: over-0x10 out-of-symbol branch signal ----------------------

VA = 0x80010000


def bne(rs, rt, off):
    return (0x05 << 26) | (rs << 21) | (rt << 16) | (off & 0xFFFF)


def bgezal(off):
    return (0x01 << 26) | (0 << 21) | (0x11 << 16) | (off & 0xFFFF)


NOP = 0


class TestIsFragmentOver16(Fixture):
    def test_branch_past_symbol_end_is_fragment(self):
        """The 0313b class: sz 0x28, closing bne 0x4c past the end.
        Branch at word 9 (PC = VA+0x24): target = PC+4+off*4 =
        VA+0x28+0x4c -> off = 0x4c/4 = 19."""
        w = [NOP] * 9 + [bne(8, 9, 19)]
        self.put_bytes(w)
        self.assertTrue(pr.is_fragment("t", VA, 0x28))

    def test_all_branches_inside_is_not_fragment(self):
        """A real small function: loop branch back to its own head,
        jr $ra tail - every target inside [VA, VA+0x20)."""
        w = [bne(8, 9, -1),           # word 0 -> target = VA (loop head)
             NOP, NOP, NOP, NOP, NOP, NOP,
             0x03E00008]              # jr $ra
        self.put_bytes(w)
        self.assertFalse(pr.is_fragment("t", VA, 0x20))

    def test_bal_outside_is_a_call_not_a_branch_out(self):
        """bgezal with rs=0 is bal - a call; a real function calls out."""
        w = [NOP] * 5 + [bgezal(0x20)] + [NOP] * 2
        self.put_bytes(w)
        self.assertFalse(pr.is_fragment("t", VA, 0x20))

    def test_backward_branch_before_start_is_fragment(self):
        w = [bne(8, 9, 0x10000 - 2)]    # -> VA+4-8 = below VA
        self.put_bytes(w + [NOP] * 7)
        self.assertTrue(pr.is_fragment("t", VA, 0x20))

    def test_small_symbols_keep_the_banked_path(self):
        self.put_bytes([NOP] * 4)
        self.assertTrue(pr.is_fragment("t", VA, 0x10))      # no return
        self.put_bytes([0x03E00008, NOP, NOP, NOP])
        self.assertTrue(pr.is_fragment("t", VA, 0x10))      # jr $ra head
        self.put_bytes([0x8FBF0020, NOP, NOP, NOP])
        self.assertTrue(pr.is_fragment("t", VA, 0x10))      # epilogue restore

    def test_missing_baseline_is_not_fragment(self):
        pr.baseline_bytes = lambda t, va, size: None
        self.assertFalse(pr.is_fragment("t", VA, 0x28))


if __name__ == "__main__":
    unittest.main(verbosity=2)

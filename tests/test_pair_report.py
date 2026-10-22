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
3. The input gates (cron-20261022-0928): baseline_witness (the local
   baseline must BE the committed oracle - the woven-set class slices
   garbage into every byte comparison) and stale_symbols (a yaml c-row
   label the build ELF links outside its own row span proves the ELF
   predates the committed yaml - the 0658 audit's 57 stale-ELF-VA
   relocations).
4. The pinned-class decisions (cron-20261022-1043): is_veneer's 3-word
   BIOS-dispatch shape (A0/B0/C0 vector, jr $t2, ordinal, banked pad) and
   fn_class precedence (veneer > fragment > sdk by name or span >
   compiler) - the classification that orders every pick list.

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


# --- input gates: baseline witness + stale-build detection -------------------

class TestBaselineWitness(Fixture):
    def setUp(self):
        super().setUp()
        os.makedirs(os.path.join(self._tmp.name, "baselines"))
        os.makedirs(os.path.join(self._tmp.name, "config", "sha1"))

    def put_oracle(self, target, blob):
        import hashlib
        with open(os.path.join(self._tmp.name, "baselines",
                               f"{target}.bin"), "wb") as f:
            f.write(blob)
        h = hashlib.sha1(blob).hexdigest()
        # the real files' shape: comment lines, then the sha1sum row
        with open(os.path.join(self._tmp.name, "config", "sha1",
                               f"{target}.sha1"), "w") as f:
            f.write(f"# config/sha1/{target}.sha1 - THE ORACLE\n")
            f.write(f"{h}  {target}.bin\n")

    def test_witnessed_baseline_passes(self):
        self.put_oracle("t", b"\x01\x02\x03\x04")
        ok, why = pr.baseline_witness("t")
        self.assertTrue(ok)
        self.assertEqual(why, "")

    def test_wrong_bytes_fail_with_the_woven_class_message(self):
        self.put_oracle("t", b"\x01\x02\x03\x04")
        with open(os.path.join(self._tmp.name, "baselines", "t.bin"),
                  "wb") as f:
            f.write(b"\xff" * 4)          # the all-woven set re-extracted
        ok, why = pr.baseline_witness("t")
        self.assertFalse(ok)
        self.assertIn("!= committed oracle", why)
        self.assertIn("woven-set class", why)

    def test_missing_baseline_fails(self):
        ok, why = pr.baseline_witness("t")
        self.assertFalse(ok)
        self.assertIn("missing", why)

    def test_sha1_file_without_hash_field_fails(self):
        with open(os.path.join(self._tmp.name, "baselines", "t.bin"),
                  "wb") as f:
            f.write(b"\x01")
        with open(os.path.join(self._tmp.name, "config", "sha1",
                               "t.sha1"), "w") as f:
            f.write("# comments only - no hash row\n")
        ok, why = pr.baseline_witness("t")
        self.assertFalse(ok)
        self.assertIn("no hash field", why)


class TestStaleSymbols(Fixture):
    """The cron-20261022-0658 stale-build signature: a yaml c-row label
    the build ELF links outside its own row span."""

    ROWS = [(0x80020000, 0x80020040, "func_80020000"),
            (0x80020040, 0x80020080, "GsSetLightMode")]

    def setUp(self):
        super().setUp()
        pr._C_ROWS = {"t": list(self.ROWS)}

    def test_consistent_tree_has_no_violations(self):
        funcs = {"func_80020000": (0x80020000, 0x40),
                 "GsSetLightMode": (0x80020040, 0x2C),
                 "asm_only_unit": (0x80030000, 0x20)}   # no row: unchecked
        self.assertEqual(pr.stale_symbols("t", funcs), [])

    def test_label_outside_its_row_span_is_the_signature(self):
        # the 0658 class: GsSetLightMode linked at its woven VA while the
        # committed true row sits elsewhere
        funcs = {"GsSetLightMode": (0x800678BC, 0x2C)}
        bad = pr.stale_symbols("t", funcs)
        self.assertEqual([(b[0], b[1]) for b in bad],
                         [("GsSetLightMode", 0x800678BC)])
        self.assertEqual(bad[0][2], [self.ROWS[1][:2]])   # spans reported

    def test_label_hit_in_one_of_its_spans_is_consistent(self):
        pr._C_ROWS = {"t": [(0x80020000, 0x80020040, "dup"),
                            (0x80030000, 0x80030040, "dup")]}
        funcs = {"dup": (0x80030000, 0x10)}
        self.assertEqual(pr.stale_symbols("t", funcs), [])

    def test_label_absent_from_elf_is_skipped(self):
        funcs = {"other": (0x80020000, 0x10)}
        self.assertEqual(pr.stale_symbols("t", funcs), [])

    def test_row_hi_is_exclusive(self):
        funcs = {"func_80020000": (0x80020040, 0x10)}   # == row hi
        self.assertTrue(pr.stale_symbols("t", funcs))
        funcs = {"func_80020000": (0x8002003C, 0x4)}    # last word inside
        self.assertEqual(pr.stale_symbols("t", funcs), [])


class TestInputGates(Fixture):
    def setUp(self):
        super().setUp()
        os.makedirs(os.path.join(self._tmp.name, "baselines"))
        os.makedirs(os.path.join(self._tmp.name, "config", "sha1"))

    def test_aggregates_both_problem_classes(self):
        import hashlib
        # baseline present but unwitnessed (wrong bytes)
        with open(os.path.join(self._tmp.name, "baselines", "t.bin"),
                  "wb") as f:
            f.write(b"\xff")
        with open(os.path.join(self._tmp.name, "config", "sha1",
                               "t.sha1"), "w") as f:
            f.write(f"{hashlib.sha1(b'good').hexdigest()}  t.bin\n")
        pr._C_ROWS = {"t": [(0x80020000, 0x80020040, "GsSetLightMode")]}
        funcs = {"GsSetLightMode": (0x800678BC, 0x2C)}   # the stale class
        ok, problems = pr.input_gates("t", funcs)
        self.assertFalse(ok)
        self.assertEqual(len(problems), 2)
        self.assertIn("witness:", problems[0])
        self.assertIn("stale vs committed yaml", problems[1])

    def test_clean_inputs_pass(self):
        import hashlib
        blob = b"\x01\x02\x03\x04"
        with open(os.path.join(self._tmp.name, "baselines", "t.bin"),
                  "wb") as f:
            f.write(blob)
        with open(os.path.join(self._tmp.name, "config", "sha1",
                               "t.sha1"), "w") as f:
            f.write(f"{hashlib.sha1(blob).hexdigest()}  t.bin\n")
        pr._C_ROWS = {"t": [(0x80020000, 0x80020040, "func_80020000")]}
        funcs = {"func_80020000": (0x80020000, 0x40)}
        ok, problems = pr.input_gates("t", funcs)
        self.assertTrue(ok)
        self.assertEqual(problems, [])


# --- is_veneer + fn_class: the pinned-class decisions ------------------------

A0_VEC = [0x240A00A0,        # addiu $t2, $zero, 0xA0  (the A0 vector)
          0x01400008,        # jr $t2
          0x24090005,        # addiu $t1, $zero, 5      (the stub ordinal)
          0x00000000]        # the banked pad word


class TestIsVeneer(Fixture):
    """The 3-word dispatch stub over the 0xA0/0xB0/0xC0 BIOS tables; the
    row may pad one zero word past the stub (the banked pad law)."""

    def test_a0_stub_with_pad_is_veneer(self):
        self.put_bytes(A0_VEC)
        self.assertTrue(pr.is_veneer("t", VA, 0x10))

    def test_b0_and_c0_vectors_are_veneers(self):
        self.put_bytes([0x240A00B0, 0x01400008, 0x2409000C])
        self.assertTrue(pr.is_veneer("t", VA, 0xC))    # no pad word yet
        self.put_bytes([0x240A00C0, 0x01400008, 0x24090038])
        self.assertTrue(pr.is_veneer("t", VA, 0xC))

    def test_unknown_vector_is_not_veneer(self):
        self.put_bytes([0x240A0090, 0x01400008, 0x24090005, 0])
        self.assertFalse(pr.is_veneer("t", VA, 0x10))

    def test_nonzero_pad_word_is_not_veneer(self):
        self.put_bytes([0x240A00A0, 0x01400008, 0x24090005, 0x0000000D])
        self.assertFalse(pr.is_veneer("t", VA, 0x10))

    def test_wrong_jr_target_is_not_veneer(self):
        # jr $t1 would jump to the ordinal, not the vector
        self.put_bytes([0x240A00A0, 0x01200008, 0x24090005, 0])
        self.assertFalse(pr.is_veneer("t", VA, 0x10))

    def test_other_sizes_are_not_veneer(self):
        self.put_bytes(A0_VEC)
        self.assertFalse(pr.is_veneer("t", VA, 0x14))
        self.assertFalse(pr.is_veneer("t", VA, 0x8))


class TestFnClass(Fixture):
    """fn_class precedence: veneer > fragment > sdk (name, then span) >
    compiler - the classification that orders every pick list."""

    def setUp(self):
        super().setUp()
        self._save_sdk = (pr._ANCHORS, pr._LIBNAMES)
        self.addCleanup(self._restore_sdk)
        pr._ANCHORS = None
        pr._LIBNAMES = None
        with open(os.path.join(self._tmp.name, "config",
                               "sdk_anchors.txt"), "w") as f:
            f.write("// target: t\n")
            f.write("0x80030000 0x40 LibFn a b c\n")
        with open(os.path.join(self._tmp.name, "config",
                               "sdk_members.txt"), "w") as f:
            f.write("")                      # no member rows in this fixture

    def _restore_sdk(self):
        pr._ANCHORS, pr._LIBNAMES = self._save_sdk

    def test_veneer_beats_everything(self):
        self.put_bytes(A0_VEC)               # a veneer-shaped stub...
        self.assertEqual(pr.fn_class("t", 0x80030000, 0x10, "LibFn"),
                         "veneer")           # ...even inside an sdk span

    def test_fragment_beats_sdk(self):
        self.put_bytes([NOP] * 4)            # 0x10, no return -> fragment
        self.assertEqual(pr.fn_class("t", 0x80030010, 0x10, "LibFn"),
                         "fragment")

    def test_sdk_by_name(self):
        self.put_bytes([NOP, NOP, NOP, 0x03E00008])   # not a fragment
        self.assertEqual(pr.fn_class("t", 0x80020000, 0x10, "LibFn"), "sdk")

    def test_sdk_by_span(self):
        self.put_bytes([NOP, NOP, NOP, 0x03E00008])
        self.assertEqual(pr.fn_class("t", 0x80030020, 0x10, "random"), "sdk")
        # last full-size slot inside the span (0x80030030+0x10 == span hi)
        self.assertEqual(pr.fn_class("t", 0x80030030, 0x10, "random"), "sdk")

    def test_compiler_when_nothing_pinned(self):
        self.put_bytes([NOP, NOP, NOP, 0x03E00008])
        self.assertEqual(pr.fn_class("t", 0x80020000, 0x10, "random"),
                         "compiler")
        # span hi is exclusive: 0x80030040 is outside the anchor
        self.assertEqual(pr.fn_class("t", 0x80030040, 0x10, "random"),
                         "compiler")


if __name__ == "__main__":
    unittest.main(verbosity=2)

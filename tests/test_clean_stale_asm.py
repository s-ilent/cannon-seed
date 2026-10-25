#!/usr/bin/env python3
"""tests/test_clean_stale_asm.py - the row-type law (cron-202610251904).

Offline unit tests for clean_stale_asm's type-aware union rule (no
deletions, no git - fixtures are temp-dir yamls and empty .s files):

1. The landed-flip class: a plain .s whose name is referenced ONLY by a
   c row is STALE (g3_eu func_8004D704 flipped to src/ while its
   whole-row disassembly stayed behind - the file the
   glabel_collision_pass renamed on every extract, the standing
   restore-to-HEAD dance the old type-blind union rule kept alive).
2. An asm-row-named .s is ALIVE; an unreferenced .s is stale.
3. A data-row-named .data.s is ALIVE; an unreferenced .data.s is stale
   (the label-shifted re-scan leftovers - 702 files by the sweep).
4. The union rule across targets sharing an asm_path survives.

Run:  python3 -m unittest tests/test_clean_stale_asm.py -v
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "tools"))
import clean_stale_asm as csa  # noqa: E402


class Fixture(unittest.TestCase):
    """Swap the module's REPO for a synthetic temp-dir one."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.makedirs(os.path.join(self._tmp.name, "config"))
        self._save = csa.REPO
        csa.REPO = Path(self._tmp.name)
        self.addCleanup(self._restore)

    def _restore(self):
        csa.REPO = self._save
        self._tmp.cleanup()

    def put_yaml(self, target, text):
        with open(os.path.join(self._tmp.name, "config",
                               f"splat.{target}.yaml"), "w") as f:
            f.write(text)

    def put_s(self, rel):
        p = os.path.join(self._tmp.name, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            f.write("/* fixture */\n")

    YAML = """\
options:
  asm_path: {asm_path}
segments:
  - type: code
    vram: 0x80020000
    start: 0x800
    subsegments:
      - [0x800, data, data_80020000]
      - [0x900, c, func_80020100]
      - [0x948, asm, func_80020148]
      - [0x960, data, data_80020160]
"""


class TestRowTypeLaw(Fixture):
    def test_c_row_named_s_is_stale(self):
        """The banked class: the flip's leftover .s dies with the sweep.

        The old type-blind union rule kept it alive because the c row
        references the name - the file could never link again (the yaml
        row compiles src/<name>.c) yet sat in the assembled tree, and
        the glabel_collision_pass renamed it on every extract.
        """
        self.put_yaml("t", self.YAML.format(asm_path="asm/t/nonmatchings"))
        self.put_s("asm/t/nonmatchings/func_80020100.s")   # c-row name only
        self.assertIn("asm/t/nonmatchings/func_80020100.s",
                      csa.stale_names())

    def test_asm_row_named_s_is_alive(self):
        self.put_yaml("t", self.YAML.format(asm_path="asm/t/nonmatchings"))
        self.put_s("asm/t/nonmatchings/func_80020148.s")   # asm row
        self.assertNotIn("asm/t/nonmatchings/func_80020148.s",
                         csa.stale_names())

    def test_unreferenced_s_is_stale(self):
        self.put_yaml("t", self.YAML.format(asm_path="asm/t/nonmatchings"))
        self.put_s("asm/t/nonmatchings/func_800DEAD.s")    # old scan label
        self.assertIn("asm/t/nonmatchings/func_800DEAD.s",
                      csa.stale_names())

    def test_data_row_named_data_s_is_alive(self):
        self.put_yaml("t", self.YAML.format(asm_path="asm/t/nonmatchings"))
        self.put_s("asm/t/nonmatchings/data/data_80020160.data.s")
        self.assertNotIn("asm/t/nonmatchings/data/data_80020160.data.s",
                         csa.stale_names())

    def test_unreferenced_data_s_is_stale(self):
        """The sweep's biggest class: the label-shifted re-scan
        leftovers (702 stale .data.s files by the 2026-10-25 sweep)."""
        self.put_yaml("t", self.YAML.format(asm_path="asm/t/nonmatchings"))
        self.put_s("asm/t/nonmatchings/data/data_800227F8.data.s")
        self.assertIn("asm/t/nonmatchings/data/data_800227F8.data.s",
                      csa.stale_names())

    def test_cross_type_reference_does_not_keep_a_file(self):
        """An asm row keeps a plain .s alive but NOT a .data.s, and a
        data row keeps a .data.s alive but NOT a plain .s."""
        self.put_yaml("t", self.YAML.format(asm_path="asm/t/nonmatchings"))
        self.put_s("asm/t/nonmatchings/func_80020148.data.s")  # asm name
        self.put_s("asm/t/nonmatchings/data/data_80020160.s")  # data name
        stale = csa.stale_names()
        self.assertIn("asm/t/nonmatchings/func_80020148.data.s", stale)
        self.assertIn("asm/t/nonmatchings/data/data_80020160.s", stale)


class TestUnionRule(Fixture):
    def test_shared_dir_name_from_either_yaml_survives(self):
        """Two targets sharing an asm_path: a name either yaml lists
        (with the consuming type) keeps the file."""
        shared = "options:\n  asm_path: asm/shared/nonmatchings\n"
        self.put_yaml("a", shared + """\
segments:
  - type: code
    vram: 0x80020000
    start: 0x800
    subsegments:
      - [0x800, asm, func_80020000]
""")
        self.put_yaml("b", shared + """\
segments:
  - type: code
    vram: 0x80020000
    start: 0x800
    subsegments:
      - [0x800, c, func_80020100]
""")
        self.put_s("asm/shared/nonmatchings/func_80020000.s")
        self.put_s("asm/shared/nonmatchings/func_80020100.s")
        stale = csa.stale_names()
        self.assertNotIn("asm/shared/nonmatchings/func_80020000.s", stale)
        self.assertIn("asm/shared/nonmatchings/func_80020100.s", stale)


class TestFilterStatus(Fixture):
    def test_stale_deletions_dropped_live_kept(self):
        self.put_yaml("t", self.YAML.format(asm_path="asm/t/nonmatchings"))
        stdin = "\n".join([
            "D\tasm/t/nonmatchings/func_80020100.s",   # c-row name: stale
            "D\tasm/t/nonmatchings/func_80020148.s",   # asm row: LIVE
            "M\tasm/t/nonmatchings/func_80020148.s",   # modification stays
        ]) + "\n"
        import io
        import contextlib
        old = sys.stdin
        sys.stdin = io.StringIO(stdin)
        try:
            with contextlib.redirect_stdout(io.StringIO()) as out:
                rc = csa.filter_status()
        finally:
            sys.stdin = old
        self.assertEqual(rc, 0)
        self.assertEqual(out.getvalue().splitlines(), [
            "D\tasm/t/nonmatchings/func_80020148.s",
            "M\tasm/t/nonmatchings/func_80020148.s",
        ])


if __name__ == "__main__":
    unittest.main()

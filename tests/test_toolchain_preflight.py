"""Offline regression tests for the full-image toolchain integrity gate."""
from __future__ import annotations

import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import toolchain_preflight as tc


class ToolchainFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / "repo"
        (self.repo / "tools").mkdir(parents=True)
        (self.repo / "tools/patch_cc1_263.sh").write_text("rebuild recipe v1")
        (self.repo / "tools/maspsx_delay_slot.patch").write_text("patch data")
        self.patch_repo = mock.patch.object(tc, "REPO", self.repo)
        self.patch_repo.start()
        self.addCleanup(self.patch_repo.stop)
        self.toolroot = self.root / "toolroot"
        self.gcc = self.toolroot / "gcc-2.6.3-src/gcc-2.6.3"
        self.gcc.mkdir(parents=True)
        for source, markers in tc.GUARD_MARKERS.items():
            (self.gcc / source).write_text("\n".join(markers))
        for name in tc.BINARIES:
            f = self.gcc / name
            f.write_text(f"fake {name} binary")
            f.chmod(f.stat().st_mode | stat.S_IXUSR)

    def attest(self):
        return tc.record_guarded_cc1(self.gcc)


class TestGuardedCompiler(ToolchainFixture):
    def test_fresh_attestation_matches(self):
        stamp = self.attest()
        self.assertTrue(stamp.exists())
        self.assertEqual(json.loads(stamp.read_text())["schema"], 1)
        tc.check_guarded_cc1(self.gcc)

    def test_missing_attestation_fails(self):
        with self.assertRaisesRegex(tc.PreflightError, "no rebuild attestation"):
            tc.check_guarded_cc1(self.gcc)

    def test_changed_compiler_binary_fails(self):
        self.attest()
        (self.gcc / "cc1").write_text("old prebuilt restored by sandbox")
        with self.assertRaisesRegex(tc.PreflightError, "differ from"):
            tc.check_guarded_cc1(self.gcc)

    def test_changed_cpp_binary_fails(self):
        self.attest()
        (self.gcc / "cpp").write_text("different cpp")
        with self.assertRaises(tc.PreflightError):
            tc.check_guarded_cc1(self.gcc)

    def test_guard_removed_fails(self):
        self.attest()
        (self.gcc / "loop.c").write_text("stock upstream loop")
        with self.assertRaisesRegex(tc.PreflightError, "guard missing"):
            tc.check_guarded_cc1(self.gcc)

    def test_patch_script_changed_fails(self):
        self.attest()
        (self.repo / "tools/patch_cc1_263.sh").write_text("rebuild recipe v2")
        with self.assertRaisesRegex(tc.PreflightError, "differ from"):
            tc.check_guarded_cc1(self.gcc)

    def test_tampered_stamp_fails(self):
        stamp = self.attest()
        stamp.write_text("{not-json")
        with self.assertRaisesRegex(tc.PreflightError, "invalid guarded"):
            tc.check_guarded_cc1(self.gcc)


class TestEffectiveCompiler(ToolchainFixture):
    def test_legacy_fallback_is_refused_before_other_checks(self):
        env = {"TOOLROOT": str(self.toolroot)}
        with self.assertRaisesRegex(tc.PreflightError, "no rebuild attestation"):
            tc.check_environment(env)

    def test_explicit_prebuilt_compiler_is_refused(self):
        env = {
            "TOOLROOT": str(self.toolroot),
            "GCCDIR": str(self.toolroot / "gcc-2.6.3-psx"),
        }
        with self.assertRaisesRegex(tc.PreflightError, "not the guarded compiler"):
            tc.check_environment(env)

    def test_wrong_qemu_for_guarded_compiler_is_refused(self):
        env = {"TOOLROOT": str(self.toolroot), "QEMU": "/path/to/qemu-i386"}
        with self.assertRaisesRegex(tc.PreflightError, "QEMU must be"):
            tc.check_environment(env)

    def test_explicit_guarded_path_is_allowed(self):
        self.attest()
        env = {"TOOLROOT": str(self.toolroot), "GCCDIR": str(self.gcc),
               "QEMU": "/usr/bin/env"}
        with mock.patch.object(tc, "check_maspsx") as maspsx, \
             mock.patch.object(tc, "check_binutils") as binutils, \
             mock.patch.object(tc, "check_python") as py:
            tc.check_environment(env)
        maspsx.assert_called_once()
        binutils.assert_called_once()
        py.assert_called_once()


class TestMaspsx(ToolchainFixture):
    def setUp(self):
        super().setUp()
        self.maspsx = self.root / "maspsx/maspsx.py"
        self.maspsx.parent.mkdir()
        self.maspsx.write_text("# patched entrypoint")

    def test_wrong_revision_refused(self):
        with mock.patch.object(tc, "command_output", return_value="not-pinned"):
            with self.assertRaisesRegex(tc.PreflightError, "pinned"):
                tc.check_maspsx(self.maspsx)

    def test_pinned_revision_must_also_have_full_reverse_applicable_patch(self):
        def command(args, env=None):
            if "rev-parse" in args:
                return tc.MASPSX_REV
            raise tc.PreflightError("patch does not reverse-apply")
        with mock.patch.object(tc, "command_output", side_effect=command):
            with self.assertRaisesRegex(tc.PreflightError, "patch does not"):
                tc.check_maspsx(self.maspsx)

    def test_valid_revision_and_patch_are_accepted(self):
        with mock.patch.object(tc, "command_output",
                               side_effect=[tc.MASPSX_REV, ""] ) as run:
            tc.check_maspsx(self.maspsx)
        self.assertEqual(run.call_count, 2)
        args = run.call_args_list[-1].args[0]
        self.assertEqual(args[-3:-1], ["--reverse", "--check"])

    def test_wrong_entrypoint_refused(self):
        file = self.root / "maspsx/other.py"
        file.write_text("x")
        with self.assertRaisesRegex(tc.PreflightError, "patched maspsx.py"):
            tc.check_maspsx(file)


class TestOtherComponents(ToolchainFixture):
    def test_missing_binutils_refused(self):
        with self.assertRaisesRegex(tc.PreflightError, "missing executable"):
            tc.check_binutils(self.toolroot)

    def test_wrong_binutils_version_refused(self):
        with mock.patch.object(tc, "command_output", return_value="GNU assembler 2.41"):
            bindir = self.toolroot / "mipsel-root/usr/bin"
            bindir.mkdir(parents=True)
            for name in ("as", "ld", "objcopy"):
                f = bindir / f"mipsel-linux-gnu-{name}"
                f.write_text("stub")
                f.chmod(0o755)
            with self.assertRaisesRegex(tc.PreflightError, "expected GNU binutils"):
                tc.check_binutils(self.toolroot)

    def test_python_dependency_mismatch_refused(self):
        with mock.patch.object(tc.metadata, "version", return_value="9.0"):
            with self.assertRaisesRegex(tc.PreflightError, "expected"):
                tc.check_python()


if __name__ == "__main__":
    unittest.main()

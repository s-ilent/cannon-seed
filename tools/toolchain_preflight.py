#!/usr/bin/env python3
"""Fail-closed, stdlib-only preflight for byte-exact PS-X image builds.

This is an environment-integrity check, not evidence of retail matching.
Run at the start of tools/build.sh. Individual cc.sh compiler experiments
are deliberately outside this gate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from importlib import metadata
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MASPSX_REV = "e85ecb373828aabea96d7e6400974d4f91ce8c74"
ATTESTATION = ".cannon-seed-guarded-cc1.json"
GUARD_MARKERS = {
    "fold-const.c": ("MODIFIED-CC1 (GUARD 1",),
    "cse.c": ("MODIFIED-CC1 (GUARD 2", "MODIFIED-CC1 (GUARD 3"),
    "loop.c": ("MODIFIED-CC1 (GUARD 4",),
}
BINARIES = ("cpp", "cc1")
PYTHON_DEPS = {
    "splat64": "0.50.0",
    "spimdisasm": "1.42.4",
    "PyYAML": "6.0.3",
}


class PreflightError(RuntimeError):
    pass


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def require_file(path: Path, executable: bool = False) -> None:
    if not path.is_file() or (executable and not os.access(path, os.X_OK)):
        raise PreflightError(f"missing {'executable' if executable else 'file'}: {path}")


def guarded_fingerprint(gccdir: Path) -> dict:
    """Tie the compiler binaries to the four marked guard source sites."""
    sources = {}
    binaries = {}
    for name, markers in GUARD_MARKERS.items():
        path = gccdir / name
        require_file(path)
        src = path.read_text(errors="replace")
        for marker in markers:
            if marker not in src:
                raise PreflightError(f"guard missing in {path}: {marker}")
        sources[name] = file_hash(path)
    for name in BINARIES:
        path = gccdir / name
        require_file(path, executable=True)
        binaries[name] = file_hash(path)
    patch = REPO / "tools/patch_cc1_263.sh"
    require_file(patch)
    return {
        "schema": 1,
        "kind": "cannon-seed-guarded-gcc-2.6.3",
        "guard_source_sha256": sources,
        "compiler_sha256": binaries,
        "patch_script_sha256": file_hash(patch),
    }


def record_guarded_cc1(gccdir: Path) -> Path:
    """Called only after patch_cc1_263.sh finishes rebuilding cpp/cc1."""
    fingerprint = guarded_fingerprint(gccdir)
    destination = gccdir / ATTESTATION
    pending = destination.with_suffix(".tmp")
    pending.write_text(json.dumps(fingerprint, indent=2, sort_keys=True) + "\n")
    pending.replace(destination)
    return destination


def check_guarded_cc1(gccdir: Path) -> None:
    expected = guarded_fingerprint(gccdir)
    stamp = gccdir / ATTESTATION
    if not stamp.is_file():
        raise PreflightError(
            "guarded cc1 has no rebuild attestation; run "
            "sh tools/build_cc1_263.sh && sh tools/patch_cc1_263.sh"
        )
    try:
        actual = json.loads(stamp.read_text())
    except (ValueError, OSError) as exc:
        raise PreflightError(f"invalid guarded cc1 attestation: {exc}") from exc
    if actual != expected:
        raise PreflightError(
            "guarded cc1 sources/binaries or patch script differ from the "
            "rebuild attestation; rerun sh tools/patch_cc1_263.sh"
        )


def command_output(args: list[str], env: dict | None = None) -> str:
    try:
        p = subprocess.run(args, capture_output=True, text=True, check=False,
                           env=env, timeout=15)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PreflightError(f"cannot run {args[0]}: {exc}") from exc
    if p.returncode != 0:
        raise PreflightError(
            f"command failed ({p.returncode}): {' '.join(args)}: "
            f"{p.stderr.strip()[:240]}"
        )
    return p.stdout.strip()


def check_maspsx(path: Path) -> None:
    require_file(path)
    directory = path.parent
    if path.name != "maspsx.py":
        raise PreflightError(f"MASPSX must name the patched maspsx.py: {path}")
    head = command_output(["git", "-C", str(directory), "rev-parse", "HEAD"])
    if head != MASPSX_REV:
        raise PreflightError(
            f"maspsx revision {head} != pinned {MASPSX_REV}; "
            "rerun sh tools/rehydrate.sh"
        )
    patch = REPO / "tools/maspsx_delay_slot.patch"
    require_file(patch)
    command_output(["git", "-C", str(directory), "apply",
                    "--reverse", "--check", str(patch)])


def check_binutils(toolroot: Path) -> None:
    root = toolroot / "mipsel-root"
    env = dict(os.environ)
    lib = str(root / "usr/lib/x86_64-linux-gnu")
    env["LD_LIBRARY_PATH"] = lib + (":" + env["LD_LIBRARY_PATH"]
                                   if env.get("LD_LIBRARY_PATH") else "")
    for name in ("as", "ld", "objcopy"):
        path = root / "usr/bin" / f"mipsel-linux-gnu-{name}"
        require_file(path, executable=True)
        version = command_output([str(path), "--version"], env=env).splitlines()[0]
        if "2.31.1" not in version:
            raise PreflightError(
                f"{path} is {version!r}, expected GNU binutils 2.31.1"
            )


def check_python() -> None:
    for package, expected in PYTHON_DEPS.items():
        try:
            actual = metadata.version(package)
        except metadata.PackageNotFoundError as exc:
            raise PreflightError(f"missing Python dependency {package}=={expected}") from exc
        if actual != expected:
            raise PreflightError(
                f"Python dependency {package}=={actual}, expected {expected}"
            )


def check_environment(env: dict[str, str] | None = None) -> None:
    env = os.environ if env is None else env
    toolroot = Path(env.get("TOOLROOT") or "/home/z/my-project/tools-local")
    guarded = toolroot / "gcc-2.6.3-src/gcc-2.6.3"
    effective = Path(env.get("GCCDIR") or guarded)
    if effective.resolve() != guarded.resolve():
        raise PreflightError(
            f"effective GCCDIR={effective} is not the guarded compiler {guarded}; "
            "prebuilt/experimental compilers are not permitted in full-image builds"
        )
    if env.get("QEMU") not in (None, "", "/usr/bin/env"):
        raise PreflightError(
            "guarded cc1 is native x86-64: QEMU must be /usr/bin/env "
            "(or unset) during a full-image build"
        )
    check_guarded_cc1(guarded)
    maspsx = Path(env.get("MASPSX") or REPO / "tools-src/maspsx/maspsx.py")
    check_maspsx(maspsx)
    check_binutils(toolroot)
    check_python()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--record-guarded-cc1", metavar="GCCDIR", type=Path,
                    help="record hashes after the guarded cc1 build completes")
    args = ap.parse_args()
    try:
        if args.record_guarded_cc1 is not None:
            dest = record_guarded_cc1(args.record_guarded_cc1)
            print(f"toolchain: guarded cc1 rebuild attested at {dest}")
        else:
            check_environment()
            print("toolchain: guarded cc1, patched pinned maspsx, "
                  "GNU binutils 2.31.1 and Python dependencies OK")
    except PreflightError as exc:
        print(f"toolchain: REFUSED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

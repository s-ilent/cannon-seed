# Continuous integration and retail verification

GitHub Actions runs **source-only checks** on pushes and pull requests. A green
CI run means the checked-in Python tooling and project metadata passed those
checks. **It does not mean any PS-X executable was rebuilt or matched retail.**

## Required GitHub-hosted jobs

| Job | Gate |
| --- | --- |
| Source hygiene | Existing whitespace/conflict checks; Python syntax across `tools/`, `scripts/`, and `tests/` |
| Offline Python unit tests | Disc-free tests, including the `cc_post` rule suite; at least 200 tests must be discovered; failures are fatal |
| Placeholder/debt ratchets | `tools/check_ratchets.py`; the current tree must match `config/ratchets.json` |
| Function census | `tools/progress.py --json` runs and publishes `progress-report`; counts are approximate, not binary-match evidence |
| Code-span coverage | `tools/coverage_report.py --strict --json --rows` adds `coverage.json` to the same artifact, with mapped C vs ASM bytes, SDK-evidenced vs unattributed origin, and explicit semantic reviews. **Not executable code coverage, semantic completion, or retail verification.** |

The offline suite deliberately does not require CHDs, PlayStation executables,
the Psy-Q archives, a working MIPS linker, or the patched GCC compiler. Tests
that explicitly require a local Psy-Q archive may be skipped; review the
unittest output and its skip count.

The previous workflow's `oracle-gate` checked for
`baselines/main.bin`, which is not one of this project's eight target
baseline names. It exited successfully when the file was absent, without
building or verifying any target. That check was removed, not represented as
a successful or verified oracle. Do not require an `oracle-gate` status from
that old workflow.

## Actual matching verification

Only a witnessed, complete-image `make verify` against the immutable SHA-1
oracle is authoritative. `tools/build.sh` now refuses full-image builds
unless `tools/toolchain_preflight.py` verifies the guarded compiler
attestation, pinned and patched maspsx, binutils and Python dependencies.
This preflight runs **locally**, not in the source-only GitHub Actions jobs.
In a separately provisioned build environment:

```sh
sh tools/witness_check.sh
for target in slps_00270 sces_00269 mainmenu_jp mainmenu_eu \
              g3_jp g3_eu g3org_jp g3org_eu; do
    make clean
    make verify TARGET="$target" || exit 1
done
```

This requires the correct baseline for each target and the *effective* pinned
toolchain, including the guarded compiler and applicable maspsx/cc_post
patches. An agent's report of 8/8 matches is useful evidence but cannot
substitute for reproducible local output or a successful full-oracle job.

**Do not silently fall back to a green status when baselines or tools are
missing.** Any future full-oracle CI job must either:

1. be explicitly disabled/skipped until a designated runner and legal,
   independently provisioned inputs exist, or
2. run all eight targets and fail on missing inputs, toolchain mismatch,
   baseline-witness failure, or any output mismatch.

Keep the oracle job's name and result distinct from source-only checks.
Do not fetch copyrighted input binaries from the public source repository
as an incidental CI setup step.

## Run source checks locally

```sh
python3 -m compileall -q tools scripts tests
PYTHONPATH=tools python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 tools/check_ratchets.py
python3 tools/progress.py --json
python3 tools/coverage_report.py --strict --json --rows > coverage.json
```

The unit suite needs PyYAML 6.0.3 and optionally Capstone 5.0.7, both
already present in `requirements-lock.txt`. No retail artifacts are needed.

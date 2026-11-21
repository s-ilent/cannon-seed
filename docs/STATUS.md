# Project status

**Reviewed 2026-11-22** against the source-only CI/toolchain cleanup
(`dfd10e79`, `2d5e0673`) and subsequent mapped-code coverage research.
This document is the **current orientation page**, not a running log;
recompute live metrics on HEAD before making a matching claim. For actionable work see
[WORK_QUEUE.md](WORK_QUEUE.md); for historical evidence and experiment
notes see [TASKS.md](TASKS.md) and [RESEARCH_LOG_INDEX.md](RESEARCH_LOG_INDEX.md).

## Purpose and targets

Galaxian³: Project Dragoon (PlayStation), matching decompilation of eight
PS-X executables: `slps_00270`, `sces_00269`, `mainmenu_jp`,
`mainmenu_eu`, `g3_jp`, `g3_eu`, `g3org_jp`, `g3org_eu`.
Japan is the primary semantic-recovery target; Europe is a critical
cross-region comparison and remains a separate binary oracle.

## Evidence and verification levels

| Signal | Last grounded status | What it establishes |
| --- | --- | --- |
| Source-only GitHub Actions | Green on `2d5e0673`, 2026-11-21 UTC | Python suite, syntax, debt ratchets, source census; **not** retail matching |
| Full retail SHA-1 image verification | **Reported 8/8 GREEN** in [TASKS.md, 2026-11-21, cron-202611211415](TASKS.md), at `a13c6f92` | Historical environment-specific evidence; **not rerun** after the CI/toolchain merges |
| Baseline witness | **Reported 8/8 STRICT** in the same historical run | Historical copies matched `config/sha1/*.sha1`; current host must re-witness |
| Current effective build preflight | Merged `2d5e0673` | Refuses missing/unattested guarded GCC, wrong maspsx patch/revision, binutils or Python versions; needs exercise in provisioned build host |
| Function progress | ~873/26,078 counted target-specific function instances (~3.35%) in the 2026-11-22 source-only census | **Heuristic**: C definitions vs assembly glabels, counts shared sources per target; not semantic-C completion |
| **Mapped byte coverage (source-only)** | **4.71%** of YAML-mapped C+ASM bytes belong to C rows across eight target instances (first 2026-11-22 coverage run) | Distinct from function counts; the segmentation may hide executable code in data rows |
| **SDK vs unattributed origins** | C share **9.18%** of SDK-evidenced mapped code vs **1.60%** of origin-unattributed mapped code | SDK evidence comes from committed member anchors; unassigned code is **not yet proven game code** |
| **Assembly involvement / reviewed C** | ~66.2 KiB of C-mapped rows have detected inline asm; only ~3.6 KiB have explicit semantic-C source reviews | Source-unit syntax flag vs manually inspected bounded sample, neither a new retail hash witness |
| Identifier debt | `unknown_function=959`, `unknown_data=831`, from November 21 matching log | Token counts in ratchets, **not distinct unknown functions/data** |
| Carve-name census | 75 address-name mismatches, 144 placement matches at `a13c6f92` | **Historical** name/VA-placement census; mismatches include intentional shared names and parked exceptions |

**Check a live checkout rather than trusting a frozen number:**

```sh
python3 tools/progress.py
python3 tools/coverage_report.py
python3 tools/check_ratchets.py
python3 tools/audit_c_names.py --cross --adjudicate
python3 tools/baseline_audit.py
python3 tools/toolchain_preflight.py
# Full-image verification only on a witnessed, fully provisioned host:
sh tools/witness_check.sh
make verify TARGET=g3_jp
```

A passing progress or ratchet report **never** substitutes for complete
retail-image matching. Conversely, an exact binary match does not establish
that a function has been semantically reconstructed into understandable C.

## Recovered capabilities

- Eight target SHA-1 oracles and per-target linker/segment layouts.
- Working source/asm round-trip pipeline (as last reported on November 21),
  including guarded GCC 2.6.3, patched maspsx, deterministic cc_post rules,
  MIPS binutils 2.31.1 and named Psy-Q SDK member identification.
- Cross-region matching tools, function/window detection, carve-name
  adjudication, byte/word diff tooling and source-only CI unit tests.
- Significant SDK, glue-code and short-wrapper reconstruction. The **game
  proper remains overwhelmingly assembly-backed** despite the successful
  round-trip builds.

See [COVERAGE.md](COVERAGE.md) for the byte-span denominator, SDK evidence and curated source-quality review schema. The total C-mapped byte share remains primarily SDK-heavy: **do not interpret the 1.60% unattributed C share as a validated gameplay completion figure**.

Do not interpret the 3.35% metric as a percentage of gameplay logic understood.
Some C rows contain assembly or special compiler fixups. Work should distinguish
**binary-exact**, **asm-preserved**, **hybrid C/asm**, **semantic C**,
and **named/typed semantic C**; these are separate dimensions.

## Current boundaries and unresolved decisions

1. **Owner decision — cross-target names.** The last log records 13
   shared-name cases; some names intentionally denote functions at different
   regional addresses. Do not mechanically rename the whole class. Recompute
   `--cross --adjudicate`, present a canonical-name/per-target-alias proposal,
   and request the owner's naming rule before changing shared identifiers.
2. **mainmenu_jp naming lane.** Twenty tool-fair C-row name/placement cases
   were explicitly reserved for that lane as of the last log. Do not
   treat them as unattended mechanical cleanup.
3. **Parked name/VA conflicts.** Memclr/INTR family and two hand-adjudicated
   cases (`g3_jp func_800629A0` scan duplicate-name holder and
   `slps_00270 func_80036CFC` cross-target adopted name) are intentionally
   not generic repair candidates.
4. **Remaining historical owner/technical gates.** The
   `func_8006AF70`/`SsSetTickMode` choice, setIntr family, 
   `GsSetDrawBuffOffset` round-5, 43 size-wrong candidates, and certain
   SDK/OMF attribution questions remain parked. The large historical task
   file is **not** an instruction to reopen completed campaigns.
5. **Provenance/publishing cleanup deferred.** The intended source-only
   policy conflicts with legacy tracked files under `extract/jp` and
   `extract/eu`. Removing them safely from distributed Git history requires
   a separate owner-approved migration; no such rewrite is part of this
   documentation work.

## Working rules

A scheduled or human research pass starts from `git rev-parse HEAD`,
checks the [current queue](WORK_QUEUE.md), searches the
[historical evidence](RESEARCH_LOG_INDEX.md), and independently validates
the target addresses against current configs and source. If the retail
oracle or guarded toolchain is missing, perform bounded **read-only static
research**; do not call a speculative source edit "matched" or commit a
matching change without the witnessed whole-image verifier.

See [CI.md](CI.md) and [TOOLCHAIN.md](TOOLCHAIN.md) for the verification
contract, [RULES.md](RULES.md) for policy, and [GUIDELINES.md](GUIDELINES.md)
for source organization.

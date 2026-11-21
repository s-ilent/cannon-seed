# Current work queue

**Reconciled 2026-11-22** using the **latest** November 21 entry in
[TASKS.md](TASKS.md) (cron-202611211415, close-out at `a13c6f92`) and the
subsequent source-only CI/toolchain commits. This file, **not the October
"## Queued" section at the top of TASKS.md**, is the task entry point.
Use [STATUS.md](STATUS.md) for verification confidence and
[RESEARCH_LOG_INDEX.md](RESEARCH_LOG_INDEX.md) to find older experiments.

**Always start by refreshing evidence:** record HEAD, the relevant yaml
rows/source files, existing branch/PR work, and current
`python3 tools/audit_c_names.py --cross --adjudicate` output. The
numbers below are the last historical snapshot, not a promise about a
newer tree.

## Ready: bounded read-only research

### R1 — Game-code recovery atlas (first independent research track)

**Target:** `g3_jp` first; `g3_eu` for comparison.

**Why:** Current C coverage includes abundant SDK members and wrappers,
while the meaningful main-game code remains poorly classified. A
game-specific map gives the next matching campaign high-value targets
rather than another pass over identical glue functions.

**One-run scope:** choose exactly one coherent contiguous game-code
region or function family **not already settled** in TASKS.md, and:

1. Establish row/ROM/VA extent with `config/splat.g3_jp.yaml`, asm
   labels, any nearby data pointers, call targets and candidate function
   entry/exit boundaries.
2. Check ownership: SDK member/window evidence
   (`config/sdk_anchors.txt`, `tools/sdk_members.py` outputs) vs
   game-owned code; report ambiguities.
3. Cross-check EU offsets/call graph when possible; distinguish exact
   byte twins, address-shifted siblings, and inferred analogues.
4. Explain **gameplay or state responsibility** in terms of observable
   writes/reads/dispatch; avoid invented names and interpretative leaps.
5. Produce an evidence table (address/extent, backing path, xrefs,
   verified vs inferred) and rank one or two feasible future semantic-C
   conversion candidates. Record a negative result when evidence rules out
   a candidate.

**Deliverable:** a short source-linked investigation, appended to a
*focused* durable subsystem document or a standalone research note;
cross-link from [RESEARCH_LOG_INDEX.md](RESEARCH_LOG_INDEX.md). No source
changes unless the full oracle is available and a separate landing
decision was made.

**Done for a run:** at least one NEW conclusion or clearly demonstrated
negative/blocked finding, with source/offset evidence and the next
specific question. Do not reopen a previously measured region merely to
repeat its summary.

### R2 — Cross-target source reuse and semantic-quality classification

**Target:** a bounded sample of current `src/` C rows and their actual
target yaml consumers.

**Question:** Which C rows reconstruct behavior, and which are
assembly-preserved, register-pinned, special-rule hybrids or thin wrappers?
What game structures are still opaque?

**Method:** classify no more than 10–20 functions in one pass; verify
which targets **actually compile** the source rather than deducing target
ownership from the filename. Keep binary-match evidence separate from C
semantic quality. Include samples from `g3_jp` where possible.

**Deliverable:** a small reusable evidence-backed classification table,
with links to source/yaml rows, not an unverified global percentage.

### R3 — Read-only status of the retained naming exceptions

**Target:** the last recorded 13 cross-target shared-name cases,
mainmenu_jp's 20 reserved name/placement rows, and the known parked
memclr/INTR and `func_800629A0`/`func_80036CFC` exceptions.

**Method:** rerun the census/adjudicator and check live YAML ownership,
definitions, curated names and C references. Report changed membership,
owner conflicts, and exact affected targets. **Do not rename, repartition
or automatically "fix" intentional shared-name mismatches.**

**Deliverable:** a decision brief with options for shared canonical name
vs region-local alias, with proposed collision policy and complete impact
surface. This can be worked on without the retail baseline.

## Ready only with full retail oracle

### L1 — Guarded toolchain roll-out verification

After pulling commit `2d5e0673` or later, on a host with the legally
provisioned baseline and exact historical tools:

```sh
# Guarded compiler rebuild/attestation on an existing checkout:
sh tools/patch_cc1_263.sh
sh tools/rehydrate.sh
python3 tools/toolchain_preflight.py
sh tools/witness_check.sh
for target in slps_00270 sces_00269 mainmenu_jp mainmenu_eu \
              g3_jp g3_eu g3org_jp g3org_eu; do
    make clean
    make verify TARGET="$target" || exit 1
done
```

If the guarded compiler source build is absent, run
`sh tools/build_cc1_263.sh` before the patch script. A clean
`make verify` must **never** fall back to a prebuilt unguarded compiler.
Save exact command/output hashes and record success or the first precise
failure (environment vs source vs oracle).

**Acceptance:** witnessed baseline 8/8 and full-image 8/8 matching
at the **same HEAD**, with the preflight passing; source-only green CI
is not acceptable substitute evidence.

### L2 — Candidate gameplay C conversions

Only after R1/R2 establish boundaries, owners and source hypotheses:
make one bounded C conversion on a dedicated branch, then
`make clean verify TARGET=<target>`. If shared headers, common
translation units or shared source resolution changed, verify **all
eight** executables before merge. A unit-level judge or a good
partial-diff score is not a substitute for image SHA-1.

## Owner-gated or parked; do not schedule as self-directed landings

| Subject | Current rule / unblock condition |
| --- | --- |
| 13 cross-target shared names | Owner chooses naming convention after R3 decision brief |
| mainmenu_jp 20 tool-fair rows | Reserved naming lane; obtain lane handoff/owner direction |
| `func_8006AF70` / `SsSetTickMode` | Owner choice for round-7 4-word mismatch, see DISC_RETURN_RUNBOOK phase C |
| `setIntr` / `GsSetDrawBuffOffset` / 43 size-wrong units | Previously parked, investigate only a **new** mechanism or explicit assigned scope |
| SDK memclr/OMF def-base cases | Require member/ownership evidence; not generic rename or asm-to-C work |
| Tracked extracted retail files and Git-history rewrite | Owner has deferred remediation; preserve history, do not force-push |

## Run protocol for scheduled research

- **One bounded, substantive investigation per execution.** Do not
  default to repeated sweeps, status recaps, mass edits or speculative
  "matching" work.
- **Reconcile first.** Check HEAD, current branches/PRs, focused docs
  and the relevant previous TASKS.md entries. Retire completed work;
  don't restage old tasks based on stale top-of-file queue text.
- **Always provide evidence.** State target, addresses, byte extents,
  source paths, method, verified facts, inferences, negative results
  and unresolved requirements.
- **No-oracle mode:** read-only static research and documentation.
  Do not modify C, assembly, YAML or oracles merely to show activity.
- **Oracle mode:** require a baseline witness, guarded toolchain
  preflight and per-target full-image hashes before any match claim.
- **Progress is not a claim.** `tools/progress.py` is a heuristic
  function-instance census, not a percentage of recovered gameplay.
- **Finish with an exact next step** and mark any decision blocked on
  owner input as **owner-gated**.

New research evidence should live in focused documents where
possible, indexed from [RESEARCH_LOG_INDEX.md](RESEARCH_LOG_INDEX.md).
Keep [TASKS.md](TASKS.md) as historical source, not as an ever-growing
new task queue.

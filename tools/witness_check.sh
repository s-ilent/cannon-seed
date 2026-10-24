#!/usr/bin/env bash
# =============================================================================
# tools/witness_check.sh — the 15-second fresh-session oracle triage.
#
# Runs verify.sh's step-2 comparison (baseline vs the committed oracle) for
# every target WITHOUT building anything. Answers, right after a sandbox
# rollback or a fresh clone: is the oracle UP (witness 8/8) or DOWN, and
# when it is DOWN, WHY.
#
# The trap this closes (witnessed live 2026-10-24): a fresh-session check
# that greps "the 40-hex field" of config/sha1/<t>.sha1 compares the
# baseline against WHATEVER config the current HEAD carries. On a rolled-
# back tree that is the PRE-FLIP config, so woven-era baselines pass 8/8
# and the window plans around an oracle that verify.sh then refuses
# (expected d637286a..., actual ec26c696...). The committed oracle of the
# CURRENT HEAD is the only witness; this tool reads it exactly the way
# verify.sh does (awk '!/^#/ && NF {print tolower($1); exit}').
#
# Diagnosis, per mismatched target:
#   - matches the PRE-FLIP oracle (2270376d, the pre-de-frame baseline
#     commit): "woven-era baseline" -> the flip re-baselined the oracles;
#     re-run the disc-return (chd_extract + iso9660 --per-sector) to
#     regenerate the TRUE per-sector baselines. Do not re-download the
#     discs unless they are also gone.
#   - matches nothing on record: unknown dump -> same remedy, but check
#     provenance first (retail sha256 gate on the CHDs).
#
# Exit codes: 0 = witness 8/8 (oracle UP), 1 = any target refused or
# missing (oracle DOWN for at least one target), 2 = usage/setup error.
# =============================================================================
set -euo pipefail

TARGETS=(slps_00270 sces_00269 mainmenu_jp mainmenu_eu g3_jp g3_eu g3org_jp g3org_eu)
PREFLIP_COMMIT=2270376d

cd "$(dirname "$0")/.."

say() { printf '%s\n' "$*"; }

if [[ ! -d .git ]]; then
    say "witness_check: run from inside the repository." >&2
    exit 2
fi

# Optional subset: witness_check.sh [target ...]
if [[ $# -gt 0 ]]; then
    TARGETS=("$@")
fi

ok=0
down=0
for t in "${TARGETS[@]}"; do
    baseline="baselines/${t}.bin"
    sha1_file="config/sha1/${t}.sha1"
    if [[ ! -f "${sha1_file}" ]]; then
        say "${t}: REFUSED - no committed oracle at ${sha1_file}"
        down=$((down + 1))
        continue
    fi
    if [[ ! -f "${baseline}" ]]; then
        say "${t}: MISSING - ${baseline} (sandbox rollback eats these; re-run the disc-return)"
        down=$((down + 1))
        continue
    fi
    expected="$(awk '!/^#/ && NF {print tolower($1); exit}' "${sha1_file}")"
    actual="$(sha1sum "${baseline}" | awk '{print $1}')"
    if [[ "${expected}" == "${actual}" ]]; then
        say "${t}: OK ${actual}"
        ok=$((ok + 1))
        continue
    fi
    preflip="$(git show "${PREFLIP_COMMIT}:config/sha1/${t}.sha1" 2>/dev/null \
        | awk '!/^#/ && NF {print tolower($1); exit}' || true)"
    if [[ -n "${preflip}" && "${actual}" == "${preflip}" ]]; then
        say "${t}: REFUSED ${actual}"
        say "        woven-era baseline: matches the PRE-FLIP oracle, not HEAD's."
        say "        HEAD ${sha1_file} expects ${expected}."
        say "        -> the disc-return must regenerate the TRUE per-sector baseline"
        say "           (chd_extract + iso9660_extract --per-sector; mandatory flag)."
    else
        say "${t}: REFUSED ${actual}"
        say "        expected ${expected}; matches no committed oracle on record."
        say "        Unknown dump - check provenance (retail sha256 gate) and re-extract."
    fi
    down=$((down + 1))
done

say "witness: ${ok}/${#TARGETS[@]}"
if [[ ${down} -eq 0 ]]; then
    say "oracle UP - make verify TARGET=<t> may run for every target."
    exit 0
fi
say "oracle DOWN for ${down} target(s) - baseline/ELF consumers will refuse;"
say "report tools stay gated until the disc-return restores witness ${#TARGETS[@]}/${#TARGETS[@]}."
exit 1

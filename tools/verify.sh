#!/usr/bin/env bash
# =============================================================================
# tools/verify.sh — the single build entrance (the oracle gate).
#
# Distilled from lsddecomp's build-and-verify.sh and parasite-eve-decomp's
# `make verify`: build, then compare the whole linked image with the retail
# executable. Ends with "OK: build matches retail ..." on success.
#
# Exit codes:
#   0  build matches retail (the only green there is)
#   1  the baseline is missing or is the wrong dump (oracle disagreement)
#   2  the build did not compile / produced no image, or setup is incomplete
#
# A per-function diff may say MATCH, but only the linked image promotes the
# result. Stale builds and leftover INCLUDE_ASM stubs have scored full
# matches against themselves; the whole-image SHA-1 cannot be fooled.
# =============================================================================
set -euo pipefail

TARGET="${1:-main}"
BASELINE="baselines/${TARGET}.bin"
SHA1_FILE="config/sha1/${TARGET}.sha1"
# FILL: path of the image your pipeline produces, e.g. build/${TARGET}.bin
IMAGE="build/${TARGET}.bin"

cd "$(dirname "$0")/.."

say() { printf '%s\n' "$*"; }
die() { printf 'verify: %s\n' "$*" >&2; exit 2; }

# 1. The baseline must exist. ------------------------------------------------
if [[ ! -f "${BASELINE}" ]]; then
    say "verify: no baseline at ${BASELINE}."
    say ""
    say "Setup (see docs/CHECKLIST.md):"
    say "  1. Put your legally obtained retail executable at ${BASELINE}"
    say "     (one revision only — every config address is wrong for any other)."
    say "  2. Record its SHA-1 in ${SHA1_FILE}:"
    say "        sha1sum ${BASELINE}   # then edit the placeholder line"
    say "     Editing that file is a one-time setup act; commit it with"
    say "     'git commit --no-verify' after triple-checking the hash."
    say "  3. Fill in the splat config and the build pipeline (grep -rn 'FILL:')."
    exit 2
fi

# 2. The baseline must match the committed oracle. ----------------------------
# Wrong dump = wrong build = every address in config/ is wrong for it.
# (Comment lines starting with '#' are allowed in the sha1 file; skip them.)
expected="$(awk '!/^#/ && NF {print tolower($1); exit}' "${SHA1_FILE}")"
actual="$(sha1sum "${BASELINE}" | awk '{print $1}')"
if [[ "${expected}" != "${actual}" ]]; then
    say "verify: ${BASELINE} does not match the committed oracle ${SHA1_FILE}."
    say "  expected sha1: ${expected}"
    say "  actual   sha1: ${actual}"
    say "A different hash is a different build. Never edit ${SHA1_FILE} to pass."
    exit 1
fi
say "verify: baseline matches oracle (${expected})."

# 3. Build. -------------------------------------------------------------------
# FILL: point this at your real pipeline. The template's stub fails on
# purpose until you configure the pinned toolchain.
if ! make build; then
    die "build failed (see above)"
fi

# 4. Compare the whole image with retail. -------------------------------------
if [[ ! -f "${IMAGE}" ]]; then
    die "build produced no image at ${IMAGE} (check the FILL markers in tools/verify.sh)"
fi
image_sha1="$(sha1sum "${IMAGE}" | awk '{print $1}')"
if [[ "${image_sha1}" == "${expected}" ]]; then
    say "OK: build matches retail ${BASELINE}"
    exit 0
fi

say "verify: image differs from retail."
say "  retail sha1: ${expected}"
say "  image  sha1: ${image_sha1}"
say ""
say "Localise the first differing byte (PS-X EXE, VRAM base 0x80010000):"
say "  cmp -l ${IMAGE} ${BASELINE} | head"
say "  vram = (offset - 1) - 0x800 + 0x80010000"
say "  then grep that address in your linker map to name the function."
exit 2

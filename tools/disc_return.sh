#!/bin/sh
# tools/disc_return.sh — one-command Phase A of docs/DISC_RETURN_RUNBOOK.md.
#
# Banked cron-20261027-0219 after 35+ manual disc-returns. Implements the
# full disc -> witnessed-baseline sequence with every gate inline, so the
# known failure modes are structurally impossible:
#   - backgrounded curls killed mid-download (curl error 23): both
#     downloads run FOREGROUND, sequential, in this one script;
#   - sha-gate skipped: the byte-size + sha256 gates refuse to proceed;
#   - the woven-corruption trap: --per-sector is hardcoded on both ISO
#     extracts (contiguous read cannot be reached from this script);
#   - sector-count drift: both raw bins are asserted before extraction;
#   - disk-full mid-extract (cron-20261027-1748: chd_extract died on
#     Errno 28 at ~200k sectors after a full ~2.2GB of pipeline files):
#     a pre-flight free-space gate fail-fasts BEFORE the first download.
#
# Space budget: both CHDs (~765MB) + both raw bins (~1.26GB) + ISO
# extracts (~100MB) ~= 2.15GB; the gate demands 2.5GB free.
#
# Usage:
#   sh tools/disc_return.sh '<EU .chd url>' '<JP .chd url>'
# (~9 min: ~2m40s per chd_extract; run under a >=600s shell timeout.)
# URLs come from Silent's fresh Discord links; the sha256 gates below are
# the retail provenance (unchanged across refreshes).
#
# Exits 0 only when tools/witness_check.sh reports 8/8 STRICT. Never
# prints or commits token material; never commits the discs or baselines
# (both are git-ignored).

set -eu

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

EU_URL="${1:-}"
JP_URL="${2:-}"
if [ -z "$EU_URL" ] || [ -z "$JP_URL" ]; then
    echo "usage: sh tools/disc_return.sh '<EU .chd url>' '<JP .chd url>'" >&2
    exit 2
fi

EU_CHD=disk/Galaxian3_Europe.chd
JP_CHD=disk/Galaxian3_Japan.chd
EU_BIN=build/Galaxian3_Europe.bin
JP_BIN=build/Galaxian3_Japan.bin
EU_SECTORS=267752
JP_SECTORS=267504
SEC=2352

say() { printf '[disc-return] %s\n' "$*"; }

# --- 0. already witnessed? ----------------------------------------------------
if bash tools/witness_check.sh >/dev/null 2>&1; then
    say "witness already 8/8 STRICT - nothing to do"
    exit 0
fi
say "witness down -> running the disc-return sequence"

# --- 0b. pre-flight free-space gate (fail-fast BEFORE downloading) ------
# cron-20261027-1748 lost a full download+extract cycle to Errno 28 when
# the sandbox rootfs hit 100%. 2.5GB covers the whole pipeline (~2.15GB)
# with headroom. df -Pk: portable, 1K blocks, 'available' = field 4.
avail_kb=$(df -Pk "$REPO" | awk 'NR==2{print $4}')
if [ "$avail_kb" -lt 2500000 ]; then
    say "FATAL: only ${avail_kb}KB free below $REPO - the pipeline needs ~2.15GB"
    say "(CHDs 765MB + raw bins 1.26GB + iso extracts ~100MB)."
    say "Evict stale disc dumps outside the repo (old manual-era *.bin /"
    say "disc_* / work dirs are all regenerable from the sha256-gated CHDs)"
    say "and re-run. NOT downloading anything."
    exit 7
fi
say "pre-flight space OK (${avail_kb}KB free, need >= 2500000KB)"

mkdir -p disk build

# --- 1. download both discs, FOREGROUND ---------------------------------------
say "downloading EU + JP CHDs (foreground, sequential)"
curl -fsSL --retry 2 -o "$EU_CHD" "$EU_URL"
curl -fsSL --retry 2 -o "$JP_CHD" "$JP_URL"

# --- 2. retail-provenance gate -------------------------------------------------
say "sha256 + byte-size gate"
eu_size=$(wc -c < "$EU_CHD" | tr -d ' ')
jp_size=$(wc -c < "$JP_CHD" | tr -d ' ')
[ "$eu_size" = "382613010" ] || { say "FATAL: EU size $eu_size != 382613010"; exit 1; }
[ "$jp_size" = "382607234" ] || { say "FATAL: JP size $jp_size != 382607234"; exit 1; }
echo "98ccd87749918a3ac2e072f1ab9c7649eae567627c3edd62f8154c4b98cf165c  $EU_CHD" | sha256sum -c -
echo "a6025267f57392e178a2feace611a28e5ffd8ee2819358596f0879130fc73d08  $JP_CHD" | sha256sum -c -

# --- 3. CHD -> raw bin (assert sector counts) ----------------------------------
say "chd_extract EU (~2m40s)"
python3 tools/chd_extract.py "$EU_CHD" "$EU_BIN"
eu_sectors=$(( $(wc -c < "$EU_BIN" | tr -d ' ') / SEC ))
[ "$eu_sectors" = "$EU_SECTORS" ] || { say "FATAL: EU bin $eu_sectors sectors != $EU_SECTORS"; exit 1; }
say "chd_extract JP (~2m40s)"
python3 tools/chd_extract.py "$JP_CHD" "$JP_BIN"
jp_sectors=$(( $(wc -c < "$JP_BIN" | tr -d ' ') / SEC ))
[ "$jp_sectors" = "$JP_SECTORS" ] || { say "FATAL: JP bin $jp_sectors sectors != $JP_SECTORS"; exit 1; }

# --- 4. ISO extract, --per-sector MANDATORY -------------------------------------
say "iso9660_extract --per-sector x2 (the true content join)"
rm -rf build/iso_eu build/iso_jp
python3 tools/iso9660_extract.py "$EU_BIN" build/iso_eu --per-sector \
    'SCES_002.69;1' 'MAINMENU.EXE;1' 'DRAGOON/G3.EXE;1' 'GOURB/G3ORG.EXE;1'
python3 tools/iso9660_extract.py "$JP_BIN" build/iso_jp --per-sector \
    'SLPS_002.70;1' 'MAINMENU.EXE;1' 'DRAGOON/G3.EXE;1' 'GOURB/G3ORG.EXE;1'

# --- 5. copy the eight baselines -------------------------------------------------
say "copying eight baselines"
cp 'build/iso_eu/SCES_002.69;1'    baselines/sces_00269.bin
cp 'build/iso_eu/MAINMENU.EXE;1'   baselines/mainmenu_eu.bin
cp 'build/iso_eu/DRAGOON_G3.EXE;1' baselines/g3_eu.bin
cp 'build/iso_eu/GOURB_G3ORG.EXE;1' baselines/g3org_eu.bin
cp 'build/iso_jp/SLPS_002.70;1'    baselines/slps_00270.bin
cp 'build/iso_jp/MAINMENU.EXE;1'   baselines/mainmenu_jp.bin
cp 'build/iso_jp/DRAGOON_G3.EXE;1' baselines/g3_jp.bin
cp 'build/iso_jp/GOURB_G3ORG.EXE;1' baselines/g3org_jp.bin

# --- 6. the honest gate ------------------------------------------------------------
say "witness check"
if bash tools/witness_check.sh; then
    say "witness 8/8 STRICT - Phase A complete; continue with runbook Phase B"
    exit 0
fi
say "FATAL: witness refused the fresh baselines - STOP and report (do not edit sha1 files)"
exit 1

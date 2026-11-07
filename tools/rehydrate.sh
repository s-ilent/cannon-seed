#!/bin/sh
# tools/rehydrate.sh — one-command sandbox recovery after a re-provision.
#
# What a re-provision does to us (observed 2026-10-10 twice):
#   1. flips every tracked file's mode (644 <-> 755)  -> git status noise
#   2. wipes /home/z dotfiles (PAT locations, credentials)
#   3. reverts /home/z/.venv to the base image (toolchain gone)
#   4. keeps /home/z/my-project intact (repo, .secrets, wheelhouse, .venv)
#
# What this script does (idempotent, offline, ~seconds):
#   1. core.filemode=false  -> mode-flip noise stops mattering
#   2. re-marks executable entry points explicitly
#   3. restores the 3 /home/z PAT locations from the surviving .secrets copies
#   4. re-asserts git identity (Super Z / bot email)
#   4b. audits the baseline oracles (tools/baseline_audit.py, read-only,
#       always exit 0) - catches the retired-woven-dump rollback state
#       before a window burns minutes on verify's by-design exit 1
#   5. rebuilds the persistent venv at /home/z/my-project/.venv from the
#      offline wheelhouse if the toolchain is missing (no network needed)
#   6. verifies splat/spimdisasm/capstone import; re-clones maspsx if lost
#
# --smoke  additionally runs `make verify TARGET=slps_00270` (the slow proof).
#
# NEVER prints or commits token material.

set -u
START=$(date +%s)
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

PERSISTENT_VENV=/home/z/my-project/.venv
WHEELHOUSE=/home/z/my-project/wheelhouse
SECRETS=/home/z/my-project/.secrets
PYBIN="${PERSISTENT_VENV}/bin/python3"

say() { printf '[rehydrate] %s\n' "$*"; }

# --- 1. stop mode-flip noise -------------------------------------------------
git config core.filemode false
say "core.filemode=false (mode flips no longer pollute git status)"

# --- 2. executable entry points ---------------------------------------------
chmod +x tools/*.sh tools/gen_ld .githooks/pre-commit 2>/dev/null || true
say "exec bits re-marked (build.sh, verify.sh, gen_ld, pre-commit)"

# --- 3. PAT locations --------------------------------------------------------
PAT="$(grep -oh 'github_pat_[A-Za-z0-9_]*' "$SECRETS/github_token" "$SECRETS/env.sh" 2>/dev/null | head -1 || true)"
if [ -n "$PAT" ]; then
    printf '%s' "$PAT" > /home/z/.github_token
    printf '%s' "$PAT" > /home/z/.github_token2
    printf 'machine github.com\nlogin x-access-token\npassword %s\n' "$PAT" > /home/z/.git-credentials
    chmod 600 /home/z/.github_token /home/z/.github_token2 /home/z/.git-credentials 2>/dev/null || true
    say "PAT locations restored (3/5: token, token2, git-credentials; .secrets copies were the survivors)"
else
    say "WARNING: no PAT found under $SECRETS — recover from the cron task book manually"
fi

# --- 4. git identity + push auth ---------------------------------------------
git config user.name  "Super Z"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git config credential.helper store
say "git identity + credential helper asserted"

# --- 4a. baselines from the extract intermediates (the 2026-11-07 restore) ---
# The disc-return's extraction intermediates at extract/<region>/<file>;1 ARE
# the TRUE oracle bytes (sha1-identical to the eight committed oracles,
# proven 2026-11-07 when a rollback ate baselines/ while the disc links were
# dead - the window restored witness 8/8 from these files alone). If a
# baseline is missing or disagrees with its extract twin, restore it; the
# committed config/sha1 gate stays the only authority (the 4b audit below
# then reports the truth).
if [ -d extract/jp ] || [ -d extract/eu ]; then
    restore_one() {
        # $1 = baseline name, $2 = extract/<region>/<file>;1 (may be absent)
        [ -f "extract/$2" ] || return 0
        if [ ! -f "baselines/$1" ] || \
           [ "$(sha1sum < "baselines/$1" | cut -d" " -f1)" != \
             "$(sha1sum < "extract/$2" | cut -d" " -f1)" ]; then
            mkdir -p baselines
            cp "extract/$2" "baselines/$1"
            say "baselines/$1 restored from extract/$2"
        fi
    }
    restore_one slps_00270   "jp/SLPS_002.70;1"
    restore_one sces_00269   "eu/SCES_002.69;1"
    restore_one mainmenu_jp  "jp/MAINMENU.EXE;1"
    restore_one mainmenu_eu  "eu/MAINMENU.EXE;1"
    restore_one g3_jp        "jp/DRAGOON_G3.EXE;1"
    restore_one g3_eu        "eu/DRAGOON_G3.EXE;1"
    restore_one g3org_jp     "jp/GOURB_G3ORG.EXE;1"
    restore_one g3org_eu     "eu/GOURB_G3ORG.EXE;1"
fi

# --- 4b. baseline oracle audit (read-only guard, NEVER fails the session) ----
# cron-20261101-0237: a rollback can park the retired woven-era dumps at
# baselines/ while the committed oracles pin the true de-framed retail -
# verify then exits 1 by design on EVERY target and the window burns its
# minutes proving the sandbox state instead of working. The audit prints the
# expected/actual table in seconds. `|| true` by design: a blocked baseline
# is a Law Zero work-around-it state, not a crash. Runs on the system python
# (stdlib-only) because the persistent venv may not exist yet at this point.
if [ -f tools/baseline_audit.py ]; then
    /usr/bin/python3 tools/baseline_audit.py || true
else
    say "baseline audit skipped (tools/baseline_audit.py missing)"
fi

# --- 5. persistent venv (offline first, network fallback) --------------------
if [ ! -x "$PYBIN" ] || ! "$PYBIN" -c "import splat, spimdisasm, capstone" >/dev/null 2>&1; then
    say "persistent venv missing/incomplete -> rebuilding"
    rm -rf "$PERSISTENT_VENV"
    /usr/bin/python3 -m venv --without-pip "$PERSISTENT_VENV"
    if [ -d "$WHEELHOUSE" ] && ls "$WHEELHOUSE"/*.whl >/dev/null 2>&1; then
        /usr/bin/pip3 -q --python "$PYBIN" install --no-index \
            --find-links "$WHEELHOUSE" -r requirements-lock.txt \
            && say "toolchain installed OFFLINE from wheelhouse" \
            || say "wheelhouse install failed -> trying network"
    fi
    "$PYBIN" -c "import splat" >/dev/null 2>&1 || {
        say "falling back to network install"
        /usr/bin/pip3 -q --python "$PYBIN" install -r requirements-lock.txt
    }
else
    say "persistent venv intact ($PERSISTENT_VENV)"
fi

# --- 6. maspsx clone ---------------------------------------------------------
if [ ! -d tools-src/maspsx ]; then
    say "maspsx clone missing -> re-cloning mkst/maspsx"
    git clone -q https://github.com/mkst/maspsx tools-src/maspsx
else
    say "maspsx clone intact"
fi

# --- 6b. maspsx delay-slot patch (in-repo, idempotent) ------------------------
# The func_800642A0 landing (window 33) needs two nop-materialization classes
# upstream maspsx does not emit: nop_lw_lw load-load padding and the
# redefine-dest hazard. The clone is git-ignored, so the patch lives in-repo
# and is re-applied after every (re)clone or rollback.
# TWO clone locations exist and BOTH must be patched (cron-20261030-2336
# lesson: cc.sh/build.sh default to the OUT-OF-REPO absolute path
# /home/z/my-project/tools-src/maspsx while step 6 clones in-repo; the
# rollback ate the out-of-repo patch state and func_800642A0 silently
# dropped its load-load nops - g3_eu verify failed with a 953-byte diff
# until the out-of-repo clone was patched too).
MASPSX_PATCH="$(pwd)/tools/maspsx_delay_slot.patch"
if [ ! -f "$MASPSX_PATCH" ]; then
    # Stale-HEAD guard (cron-20261101-1414 incident): rehydrate runs BEFORE
    # the session's origin sync, so a tree parked on a HEAD that predates
    # 8ff08f1c has no patch file and 6b used to skip SILENTLY - the clones
    # stayed unpatched and every later build of the patch-dependent C rows
    # (func_80052038/func_800642A0/func_80067690, then the sdk-body set)
    # drifted until a verify caught it 3273 bytes in. The clones are
    # git-ignored but the patch is in-repo, so patch from the origin/main
    # blob when the local checkout does not carry the file yet; the next
    # rehydrate after the reset re-applies from the identical working-tree
    # copy (idempotent by the checkout-first loop below).
    git fetch -q origin main 2>/dev/null || true
    if git cat-file -e origin/main:tools/maspsx_delay_slot.patch 2>/dev/null; then
        MASPSX_TMP="$(pwd)/build/maspsx_delay_slot.origin.patch"
        mkdir -p "$(pwd)/build"
        git show origin/main:tools/maspsx_delay_slot.patch > "$MASPSX_TMP" 2>/dev/null
        if [ -s "$MASPSX_TMP" ]; then
            MASPSX_PATCH="$MASPSX_TMP"
            say "patch file absent at HEAD ($(git rev-parse --short HEAD 2>/dev/null || echo '?')) - using origin/main's copy (stale-HEAD guard)"
        fi
    else
        say "WARN: tools/maspsx_delay_slot.patch absent at HEAD and origin/main - skipping 6b (pre-patch tree)"
    fi
fi
if [ -f "$MASPSX_PATCH" ]; then
    for MASPSX_DIR in tools-src/maspsx /home/z/my-project/tools-src/maspsx; do
        if [ ! -d "$MASPSX_DIR" ]; then
            continue
        fi
        # reset first: the patch regrows (cron-20261030-2151 added the addiu_at
        # flip), so an already-old-patched clone must not skip the new hunks.
        git -C "$MASPSX_DIR" checkout -- . 2>/dev/null
        if git -C "$MASPSX_DIR" apply --check "$MASPSX_PATCH" 2>/dev/null; then
            git -C "$MASPSX_DIR" apply "$MASPSX_PATCH" 2>/dev/null
            say "maspsx delay-slot patch applied ($MASPSX_DIR)"
        elif grep -q "line_redefines_reg" "$MASPSX_DIR/maspsx/__init__.py" 2>/dev/null && grep -q "args.addiu_at is not None" "$MASPSX_DIR/maspsx.py" 2>/dev/null; then
            say "maspsx delay-slot patch already present ($MASPSX_DIR)"
        else
            say "WARN: maspsx delay-slot patch failed to apply in $MASPSX_DIR - the landed load-load-nop C rows will not build"
        fi
    done
fi

# --- 7. mipsel binutils (tools-local, git-ignored) ---------------------------
TOOLROOT=/home/z/my-project/tools-local/mipsel-root
AS="$TOOLROOT/usr/bin/mipsel-linux-gnu-as"
export LD_LIBRARY_PATH="$TOOLROOT/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
if [ ! -x "$AS" ] || ! "$AS" --version 2>/dev/null | grep -q 2.31.1; then
    say "mipsel binutils missing -> running tools/get_binutils.sh (network)"
    sh tools/get_binutils.sh >/dev/null 2>&1 \
        && say "binutils 2.31.1 restored into tools-local/mipsel-root" \
        || say "WARNING: binutils restore failed — run tools/get_binutils.sh manually"
else
    say "mipsel binutils intact"
fi

# --- 7.5 guarded-cc1 witness (the twenty-fifth-rollback lesson, 2026-11-07) --
# The pipeline's cc1 is NOT the decompals prebuilt at gcc-2.6.3-psx/cc1:
# since cron-20261022 it is the SOURCE build at gcc-2.6.3-src with the
# MODIFIED-CC1 guards 1-4 applied (build_cc1_263.sh + patch_cc1_263.sh),
# wired at build time via QEMU=/usr/bin/env GCCDIR=<source tree> (the source
# binaries are x86-64; the decompals ones are i386-under-qemu). A rollback
# restores the prebuilt i386 cc1 and the -x checks above cannot tell the
# difference: 100+ units stay byte-exact but the three ISO9660 rows in
# mainmenu_jp (func_8007796C/77678/77A18) drift and ALL image hashes break.
# slps_00270 --smoke does NOT catch it (that target has no guard-sensitive
# row) - hence this explicit check and the mainmenu_jp canary in --smoke.
CC1SRC=/home/z/my-project/tools-local/gcc-2.6.3-src/gcc-2.6.3
if [ -x /home/z/my-project/tools-local/gcc-2.6.3-psx/cc1 ] && [ ! -x "$CC1SRC/cc1" ]; then
    say "WARN: guarded cc1 MISSING (rollback ate the source build)"
    say "      the ISO9660 rows WILL drift - remedy (about 6 min):"
    say "        sh tools/build_cc1_263.sh && sh tools/patch_cc1_263.sh"
    say "        then build with: QEMU=/usr/bin/env GCCDIR=$CC1SRC make build TARGET=<t>"
elif [ -x "$CC1SRC/cc1" ]; then
    if grep -q "MODIFIED-CC1 (GUARD 4" "$CC1SRC/loop.c" 2>/dev/null && \
       grep -q "MODIFIED-CC1 (GUARD 3" "$CC1SRC/cse.c" 2>/dev/null; then
        say "guarded cc1 intact (source tree carries guards 1-4)"
    else
        say "WARN: cc1 source tree lost the guards - run: sh tools/patch_cc1_263.sh"
    fi
fi

# --- 8. Psy-Q compiler (GCC 2.6.3-psx + qemu-i386, tools-local) ---------------
# Needed for C matches (tools/cc.sh). get_gcc.sh is idempotent and only
# hits the network when something is actually missing.
if [ -x /home/z/my-project/tools-local/gcc-2.6.3-psx/cc1 ] \
   && [ -x /home/z/my-project/tools-local/qemu-root/usr/bin/qemu-i386-static ]; then
    say "gcc-2.6.3-psx + qemu-i386 intact"
else
    say "Psy-Q compiler missing -> running tools/get_gcc.sh (network)"
    sh tools/get_gcc.sh >/dev/null 2>&1 \
        && say "gcc-2.6.3-psx + qemu-i386 restored into tools-local/" \
        || say "WARNING: compiler restore failed — run tools/get_gcc.sh manually"
fi

# --- smoke -------------------------------------------------------------------
"$PYBIN" -c "import splat, spimdisasm, capstone; print('import smoke: OK')" || {
    say "FATAL: toolchain still broken"; exit 1; }

# witness status line (bash-only tool; informational, never fails rehydrate)
if command -v bash >/dev/null 2>&1 && [ -f tools/witness_check.sh ]; then
    bash tools/witness_check.sh 2>&1 | tail -1
fi

END=$(date +%s)
say "done in $((END - START))s — tree ready (run with --smoke for the full oracle proof)"
# the full oracle proof: slps_00270 is the fast whole-image gate, and
# mainmenu_jp is the guarded-cc1 CANARY (its three ISO9660 rows are the only
# units in the repo that drift under the unguarded prebuilt cc1 - witnessed
# live 2026-11-07). Both must pass for a truly green session start.
if [ "${1:-}" = "--smoke" ]; then
    make verify TARGET=slps_00270 || exit 1
    make verify TARGET=mainmenu_jp || exit 1
fi
exit 0

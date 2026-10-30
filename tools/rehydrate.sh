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
        elif grep -q "line_redefines_reg" "$MASPSX_DIR/maspsx/__init__.py" 2>/dev/null && grep -q "addiu_at: bool = True" "$MASPSX_DIR/maspsx.py" 2>/dev/null; then
            say "maspsx delay-slot patch already present ($MASPSX_DIR)"
        else
            say "WARN: maspsx delay-slot patch failed to apply in $MASPSX_DIR - func_800642A0 will not build"
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

END=$(date +%s)
say "done in $((END - START))s — tree ready (run with --smoke for the full oracle proof)"
[ "${1:-}" = "--smoke" ] && make verify TARGET=slps_00270
exit 0

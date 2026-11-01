#!/bin/sh
# tools/provision_psyq.sh - one-command re-provision of the repo-external
# psyq 3.3 evidence assets that the sandbox rollbacks repeatedly reap.
#
# Recurring cost made into a tool: every psyq-curation / sdk-evidence window
# re-clones these by hand ("this is now the standard window-opening cost",
# cron-20261031-1251; the recipes are docs/MATCHING.md and the TASKS.md
# windows 6715/12740/12886/12980). Idempotent: existing provisioned trees
# are kept unless --force is given.
#
# What it provisions (BOTH repo-external, never inside the repo):
#   /home/z/psyq       sozud/psy-q sparse clone:
#                      3.3/PSX/LIB + 3.3/PSX/INCLUDE + 3.3/PSX/DOC
#                      (the LIBs are the omf_pubsyms/sdk_members evidence;
#                      INCLUDE holds the psyq headers - LIBSND.H's SS_* tick
#                      constants were the 1406 window's strongest source;
#                      DOC holds FUNCTION.TXT, Shift-JIS, the SsSetTickMode
#                      spec and the SsInit/SsInitHot polarity wording)
#   /home/z/psyq-sigs  lab313ru/psx_psyq_signatures sparse clone: 330
#                      (sdk_members.py --sigs corroboration DB)
#
# Usage: sh tools/provision_psyq.sh [--force] [--psyq-only] [--sigs-only]
# Network needed (~seconds each with --depth 1 --filter=blob:none --sparse;
# the 2026-10-12 note "the psyq re-clone stalled twice at ~116K" is the
# full-clone trap this recipe avoids). No tokens involved, nothing committed.

set -e

FORCE=0
DO_PSYQ=1
DO_SIGS=1
for arg in "$@"; do
    case "$arg" in
        --force)     FORCE=1 ;;
        --psyq-only) DO_SIGS=0 ;;
        --sigs-only) DO_PSYQ=0 ;;
        *) echo "usage: $0 [--force] [--psyq-only] [--sigs-only]" >&2; exit 2 ;;
    esac
done

say() { echo "[provision_psyq] $*"; }

clone_sparse() {
    # clone_sparse <url> <dest> <shift...> - depth-1 blob-filtered sparse clone
    url="$1"; dest="$2"; shift 2
    if [ "$FORCE" = 1 ] && [ -e "$dest" ]; then
        say "removing $dest (--force)"
        rm -rf "$dest"
    fi
    if [ -d "$dest/.git" ]; then
        say "kept existing $dest (no --force)"
        return 0
    fi
    say "cloning $url -> $dest"
    git clone --depth 1 --filter=blob:none --sparse "$url" "$dest"
    git -C "$dest" sparse-checkout set "$@"
}

# 1. the psyq 3.3 SDK (LIB + INCLUDE + DOC - DOC added cron-20261031-1525)
if [ "$DO_PSYQ" = 1 ]; then
    clone_sparse https://github.com/sozud/psy-q /home/z/psyq \
        3.3/PSX/LIB 3.3/PSX/INCLUDE 3.3/PSX/DOC
    for d in /home/z/psyq/3.3/PSX/LIB /home/z/psyq/3.3/PSX/INCLUDE \
             /home/z/psyq/3.3/PSX/DOC; do
        if [ ! -d "$d" ]; then
            say "MISSING $d after checkout - inspect $dest manually"; exit 1
        fi
    done
    say "psyq 3.3 ok: $(ls /home/z/psyq/3.3/PSX/LIB/*.LIB 2>/dev/null | wc -l) LIBs, INCLUDE+DOC present"
fi

# 2. the signature-DB corroboration dir (sdk_members.py --sigs)
if [ "$DO_SIGS" = 1 ]; then
    clone_sparse https://github.com/lab313ru/psx_psyq_signatures \
        /home/z/psyq-sigs 330
    if [ ! -d /home/z/psyq-sigs/330 ]; then
        say "MISSING /home/z/psyq-sigs/330 after checkout - inspect manually"; exit 1
    fi
    say "sigs ok: 330 checkout present"
fi

say "done"

#!/bin/sh
# tools/make_wheelhouse.sh — rebuild the offline wheel cache.
#
# The wheelhouse lives OUTSIDE the repo (survives sandbox re-provisions):
#     /home/z/my-project/wheelhouse   (~5 MB, 14 wheels)
#
# Uses `pip wheel`, NOT `pip download`: packages without cp313 wheels on
# PyPI (pylibyaml, intervaltree) must be compiled into local binary wheels;
# a download-only cache fails later under --no-index when pip tries to
# build those sdists offline.
#
# Run whenever requirements-lock.txt changes.

set -eu
WHEELHOUSE="${WHEELHOUSE:-/home/z/my-project/wheelhouse}"
LOCK="$(cd "$(dirname "$0")/.." && pwd)/requirements-lock.txt"

# system pip (the persistent venv is created --without-pip on purpose)
/usr/bin/pip3 wheel -w "$WHEELHOUSE" -r "$LOCK"

echo "wheelhouse: $WHEELHOUSE ($(ls "$WHEELHOUSE" | wc -l) wheels)"

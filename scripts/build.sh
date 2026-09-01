#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"

cd "$ROOT"

echo "========================================"
echo "temperans: build"
echo "========================================"

"$ROOT/scripts/check.sh"

echo
echo "[1/3] Clean previous builds"

rm -rf \
    "$ROOT/build" \
    "$ROOT/dist" \
    "$ROOT/temperans.egg-info"

echo "PASS"

echo
echo "[2/3] Build wheel + source distribution"

"$PYTHON" -m build

echo
echo "[3/3] Validate distributions"

"$PYTHON" -m twine check "$ROOT"/dist/*

echo
echo "Artifacts:"
ls -lh "$ROOT"/dist/

echo
echo "========================================"
echo "TEMPERANS BUILD PASSED"
echo "========================================"

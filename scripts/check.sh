#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"

cd "$ROOT"

if [ ! -x "$PYTHON" ]; then
    echo "ERROR: Python environment not found:"
    echo "$PYTHON"
    echo
    echo "Create it with:"
    echo "python3 -m venv .venv"
    echo ".venv/bin/python -m pip install -e '.[dev]'"
    exit 1
fi

echo "========================================"
echo "temperans: validation"
echo "========================================"

echo
echo "[1/5] Compile package"
"$PYTHON" -m compileall -q temperans
echo "PASS"

echo
echo "[2/5] Run tests"
"$PYTHON" -m pytest -q
echo "PASS"

echo
echo "[3/5] Validate package metadata"
"$PYTHON" - <<'PY'
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib

root = Path.cwd()

with open(root / "pyproject.toml", "rb") as f:
    data = tomllib.load(f)

project = data["project"]

print("name:", project["name"])
print("version:", project["version"])
print("homepage:", project["urls"]["Homepage"])

assert project["name"] == "temperans"
assert project["version"]
assert project["urls"]["Homepage"]

print("PASS")
PY

echo
echo "[4/5] Verify model artifacts"

test -f \
"$ROOT/temperans/models/temperans_v1_primitive_head.pkl"

test -f \
"$ROOT/temperans/models/temperans_v1_match_head.pkl"

echo "PASS"

echo
echo "[5/5] Git status"
git status --short

echo
echo "========================================"
echo "TEMPERANS CHECKS PASSED"
echo "========================================"

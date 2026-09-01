#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT"

echo "========================================"
echo "temperans: development setup"
echo "========================================"

if [ ! -d "$ROOT/.venv" ]; then
    echo
    echo "[1/3] Creating virtual environment"
    python3 -m venv "$ROOT/.venv"
else
    echo
    echo "[1/3] Virtual environment already exists"
fi

echo
echo "[2/3] Upgrading pip"

"$ROOT/.venv/bin/python" -m pip install --upgrade pip

echo
echo "[3/3] Installing temperans development environment"

"$ROOT/.venv/bin/python" -m pip install -e "$ROOT[dev]"

echo
echo "========================================"
echo "TEMPERANS SETUP COMPLETE"
echo "========================================"
echo
echo "Activate with:"
echo "source \"$ROOT/.venv/bin/activate\""
echo
echo "Then validate with:"
echo "./scripts/check.sh"

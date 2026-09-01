#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"

cd "$ROOT"

if [ "$#" -ne 1 ]; then
    echo "Usage:"
    echo "  ./scripts/release.sh VERSION"
    echo
    echo "Example:"
    echo "  ./scripts/release.sh 0.1.0a2"
    exit 1
fi

VERSION="$1"
TAG="v$VERSION"

echo "========================================"
echo "temperans release: $VERSION"
echo "========================================"

echo
echo "[1/7] Verify package versions"

PROJECT_VERSION="$("$PYTHON" - <<'PY'
try:
    import tomllib
except ImportError:
    import tomli as tomllib

with open("pyproject.toml", "rb") as f:
    print(tomllib.load(f)["project"]["version"])
PY
)"

INIT_VERSION="$("$PYTHON" - <<'PY'
import re
from pathlib import Path

text = Path("temperans/__init__.py").read_text()

m = re.search(
    r'__version__\s*=\s*["\']([^"\']+)["\']',
    text,
)

if not m:
    raise SystemExit("Could not find __version__")

print(m.group(1))
PY
)"

echo "pyproject.toml: $PROJECT_VERSION"
echo "temperans:      $INIT_VERSION"
echo "requested:      $VERSION"

if [ "$PROJECT_VERSION" != "$VERSION" ]; then
    echo "ERROR: pyproject.toml version mismatch"
    exit 1
fi

if [ "$INIT_VERSION" != "$VERSION" ]; then
    echo "ERROR: temperans.__version__ mismatch"
    exit 1
fi

echo "PASS"

echo
echo "[2/7] Verify Git working tree"

if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
    echo "ERROR: tracked files have uncommitted changes."
    git status --short
    exit 1
fi

echo "PASS"

echo
echo "[3/7] Verify tag does not already exist"

if git rev-parse "$TAG" >/dev/null 2>&1; then
    echo "ERROR: tag already exists: $TAG"
    exit 1
fi

echo "PASS"

echo
echo "[4/7] Run build pipeline"

"$ROOT/scripts/build.sh"

echo
echo "[5/7] Run clean-wheel smoke test"

"$ROOT/scripts/smoke-test.sh"

echo
echo "[6/7] Create release tag"

git tag -a "$TAG" -m "temperans $VERSION"

echo "Created: $TAG"

echo
echo "[7/7] Push branch and tag"

git push origin main
git push origin "$TAG"

echo
echo "========================================"
echo "TEMPERANS RELEASE VALIDATED"
echo "========================================"
echo
echo "Version: $VERSION"
echo "Tag:     $TAG"
echo
echo "Artifacts:"
ls -lh "$ROOT"/dist/
echo
echo "PyPI upload is intentionally NOT automatic."
echo
echo "After reviewing the artifacts, publish with:"
echo
echo "  $PYTHON -m twine upload $ROOT/dist/*"

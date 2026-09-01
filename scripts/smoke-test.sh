#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

TMP_DIR="$(mktemp -d /tmp/temperans-smoke.XXXXXX)"
VENV="$TMP_DIR/venv"
DB="$TMP_DIR/temperans.db"

cleanup() {
    rm -rf "$TMP_DIR"
}

trap cleanup EXIT

WHEEL="$(find "$ROOT/dist" -maxdepth 1 -name 'temperans-*.whl' | head -1)"

if [ -z "$WHEEL" ]; then
    echo "ERROR: No wheel found in $ROOT/dist"
    echo "Run ./scripts/build.sh first."
    exit 1
fi

echo "========================================"
echo "temperans: clean wheel smoke test"
echo "========================================"

echo
echo "Wheel:"
echo "$WHEEL"

echo
echo "[1/3] Create clean environment"

python3 -m venv "$VENV"

echo "PASS"

echo
echo "[2/3] Install wheel"

"$VENV/bin/python" -m pip install --quiet "$WHEEL"

echo "PASS"

echo
echo "[3/3] Test public SDK"

cd "$TMP_DIR"

"$VENV/bin/python" - <<PY
import temperans

from temperans import TrajectoryStore
from temperans.threading import SemanticThreadResolver
from temperans.analytics import ThreadAnalytics

print("temperans version:", temperans.__version__)

store = TrajectoryStore("$DB")

trace = store.trace(
    user_id="smoke_user",
    trajectory_id="smoke_project",
    conversation_id="chat_1",
    thread_resolver=SemanticThreadResolver(),
)

event = trace.human(
    "How should we benchmark trajectory understanding?"
)

trace.agent(
    "Compare correct history with shuffled history.",
    actor_id="agent_1",
    thread_id=event.thread_id,
)

summary = trace.summary()
analytics = ThreadAnalytics(trace).analyze()

assert summary["events"] == 2
assert summary["conversations"] == 1
assert summary["agents"] == 1
assert summary["threads"] == 1
assert event.thread_id
assert event.thread_id in analytics

print("thread:", event.thread_id)
print("summary:", summary)
print("analytics:", analytics)

store.close()

print()
print("PUBLIC SDK SMOKE TEST: PASS")
PY

echo
echo "========================================"
echo "TEMPERANS SMOKE TEST PASSED"
echo "========================================"

# temperans

Trajectory intelligence for human–agent–tool interactions.

`temperans` maintains persistent trajectories across conversations, agents, and
tools, and computes structural signals over them — duplicated tool calls, tool
thrash, failure and recovery runs, and agent handoffs.

Copyright 2026 Temperans AI. Licensed under the Apache License, Version 2.0.

> **Alpha.** The public API covers event ingestion and trajectory assembly.
> Behavioral perception (classifying turns as repair, resistance, and similar) is
> under active research and is **not** part of the public API.

---

## Contents

- [Install](#install)
- [Quickstart](#quickstart)
- [What it computes](#what-it-computes)
- [Status](#status)
- [Engineering notes](#engineering-notes)
  - [1. What is actually shipped](#1-what-is-actually-shipped)
  - [2. Correctness defects](#2-correctness-defects)
  - [3. Complexity and latency](#3-complexity-and-latency)
  - [4. Naming and packaging hazards](#4-naming-and-packaging-hazards)
  - [5. Experimental artifacts in the distribution](#5-experimental-artifacts-in-the-distribution)
  - [6. Testing](#6-testing)
  - [7. Remediation sequence](#7-remediation-sequence)
  - [8. Invariants](#8-invariants)
- [License](#license)

---

## Install

```bash
pip install temperans
```

Requires Python 3.10 or later.

## Quickstart

```python
from temperans import TrajectoryStore

store = TrajectoryStore("temperans.db")
trace = store.trace(user_id="u_1", trajectory_id="t_1")

trace.human("the refund still hasn't arrived")
trace.agent("let me check that", actor_id="support-agent")
trace.tool("lookup_refund", status="failed")
trace.tool("lookup_refund", status="failed")

print(trace.state().to_dict())
# {'event_count': 4, 'tool_failures': 2, 'duplicate_tool_calls': 1, ...}
```

## What it computes

All signals below are deterministic counts over the event sequence. No model, no
labels, no inference.

| Signal | Meaning |
|---|---|
| `duplicate_tool_calls` | Same tool invoked with the same arguments again |
| `cross_agent_duplicate_actions` | Duplicate work across different agents |
| `tool_switches` | Consecutive calls to different tools |
| `tool_failures` | Failed tool events |
| `consecutive_tool_failures` | Failure run length since the last success |
| `recovery_count` | Recoveries from an unresolved state |
| `agent_handoffs` | Changes of acting agent |

## Status

| Area | State |
|---|---|
| Event model, trajectory assembly, SQLite store | Working, alpha |
| Structural signals | Working, deterministic |
| Thread resolution | Alpha; see §2.5 |
| Behavioral perception | Research; not exported |

---

# Engineering notes

Status: `0.1.0a1` (alpha). Audit date: 2026-09-01.

This section records the engineering state of the package, the defects found in
the current implementation, and the sequence in which they should be fixed. It is
a working document, not marketing material. Claims about model quality belong in
`experiments_wildchat_v1.json`, not here.

## 1. What is actually shipped

The public API surface is deliberately narrow:

```python
from temperans import Event, Trace, TrajectoryState, TrajectoryStore
```

That is the ingestion and trajectory-assembly layer. It is deterministic and
carries no learned components.

`PerceptionEngine.update()` computes structural signals by counting observable
facts in the event stream:

| Signal | Definition |
|---|---|
| `duplicate_tool_calls` | Same `tool_name` and `metadata` as a prior tool event |
| `cross_agent_duplicate_actions` | A duplicate where the issuing agents differ |
| `tool_switches` | Consecutive tool events with different `tool_name` |
| `tool_failures` | `status == "failed"` |
| `consecutive_tool_failures` | Run length of failures since last success |
| `recovery_count` | Transitions from unresolved to `status == "success"` |
| `agent_handoffs` | Change in `actor_id` between agent events |

None of these require a model, labels, or ground truth. They are countable and
therefore cannot be wrong in the way a classifier can be wrong. This is the layer
that is safe to put in front of a design partner.

**Not exported, and intentionally so:** `PerceptionEngine`, `BehavioralPerception`,
`TemperansV1BehavioralPerception`. The behavioral counters on `TrajectoryState`
(`repair_count`, `resistance_count`, and siblings) are populated only by
`Trace._apply_behavior_dict()`, which runs only when an event carries a
`metadata["behavior"]` payload — i.e. only when a behavior model is explicitly
attached. Without one they remain zero, which is the correct default.

## 2. Correctness defects

Ordered by likelihood of producing a wrong answer on real traffic.

### 2.1 `duplicate_tool_calls` compares only the immediately preceding tool event

`temperans/perception.py:41-47`

```python
previous_tools = [e for e in events[:-1] if e.actor_type == "tool"]
if previous_tools:
    previous = previous_tools[-1]
```

Only `previous_tools[-1]` is examined. A trajectory of `search → fetch → search`
records zero duplicates, because the second `search` is compared against `fetch`.

Real tool thrash is usually interleaved rather than immediately repeated, so the
flagship structural signal under-reports on exactly the pattern it exists to
detect.

**Fix.** Maintain a bounded set of recent tool-call fingerprints on
`TrajectoryState` and test membership:

```python
fingerprint = (event.tool_name, canonical_hash(event.metadata))
if fingerprint in state.recent_tool_calls:
    state.duplicate_tool_calls += 1
state.recent_tool_calls.append(fingerprint)   # deque(maxlen=N)
```

Window size `N` should be configurable; 20 is a reasonable default. Record the
chosen `N` in the emitted state so results are interpretable.

### 2.2 Metadata equality is compared post-serialization

`temperans/perception.py:52-54` compares `previous.metadata == event.metadata`.
Metadata round-trips through `json.dumps`/`json.loads` in `TrajectoryStore`, which
coerces tuples to lists and may alter numeric types. Two logically identical tool
calls can therefore compare unequal depending on whether they were loaded from
SQLite or observed in-process.

**Fix.** Canonicalize before comparison — sorted keys, normalized numerics, stable
digest. Store the digest rather than comparing dicts.

### 2.3 Trajectory ordering depends on ISO-8601 string sort

`temperans/store.py` orders by `ORDER BY timestamp, rowid`, where `timestamp` is
TEXT produced by `datetime.now(timezone.utc).isoformat()`.

Lexicographic ordering matches chronological ordering only when every timestamp
shares the same UTC offset and formatting. A single event carrying `+05:30`, or a
caller supplying its own `timestamp` in a different form, silently reorders the
trajectory. Every sequential signal downstream — consecutive failures, recovery,
handoffs, thread resolution — is then computed over the wrong sequence, with no
error raised.

**Fix.** Store an integer epoch-milliseconds column and sort on it. Keep the ISO
string as a display field. Normalize on ingest; reject or coerce naive datetimes
explicitly rather than accepting them.

### 2.4 `save_event` is not idempotent

`event_id` is `PRIMARY KEY` and the insert is a plain `INSERT`. A retried delivery
— the normal case in agent frameworks and any at-least-once transport — raises
`sqlite3.IntegrityError` and takes down the caller.

**Fix.** `INSERT OR IGNORE`, or an upsert on `event_id`. Ingestion must be safe to
replay.

### 2.5 `SemanticThreadResolver` refits its vectorizer on every call

`temperans/threading.py` constructs a fresh `TfidfVectorizer` per `resolve()` and
fits it on `documents + [text]`.

The vocabulary and IDF weights are therefore derived from a corpus that changes on
every turn. Cosine scores are not comparable across calls, and the same input text
can resolve to different threads depending on what else happens to be in the
trajectory at that moment. A fixed `threshold=0.15` against a moving representation
is not a stable decision boundary.

This is a correctness problem, not a performance problem: thread assignment is
non-deterministic with respect to trajectory history.

**Fix (alpha).** Use `HashingVectorizer`, which has no fitted state, so scores are
stable across calls. **Fix (later).** Persist a fitted vectorizer per store, or move
to a fixed sentence-embedding model. Either way, calibrate the threshold against
labeled thread boundaries rather than picking a constant.

## 3. Complexity and latency

### 3.1 Trace construction is O(n²)

Two compounding issues:

`temperans/trace.py:33-46` — `Trace.__init__` loads every persisted event and
replays `PerceptionEngine.update()` and `_replay_behavior()` over the full history
on every construction.

`temperans/perception.py:41` — each `update()` call itself scans `events[:-1]` to
find prior tool events.

Opening a trajectory with `n` events therefore costs O(n²) work before the first
new event is observed. With a behavior model attached, `_replay_behavior` adds a
model forward pass per historical event.

This is the reason a sub-100 ms per-turn budget is not currently reachable, and no
amount of hardware fixes an asymptotic problem.

**Fix — state snapshotting.** Persist `TrajectoryState` alongside events with the
`event_id` of the last event folded into it. On construction, load the snapshot and
apply only events after that watermark. Combined with §2.1's bounded deque,
per-event cost becomes O(1) and trace open becomes O(new events).

Snapshots must carry a `state_schema_version`; on mismatch, discard and recompute
from the event log. The event log stays the source of truth.

### 3.2 Storage

- No index on `trajectory_id`, so `load_events` is a full table scan.
  Add `CREATE INDEX IF NOT EXISTS idx_events_trajectory ON events(trajectory_id, timestamp_ms, rowid)`.
- `commit()` per insert. Provide a batch path for backfill.
- No WAL mode. `PRAGMA journal_mode=WAL` for concurrent readers.

### 3.3 Concurrency

A single `sqlite3.connect()` with default `check_same_thread=True` is held for the
store's lifetime. Any threaded or async ingestion path fails. Either adopt a
connection-per-thread pool or document the store as single-threaded and enforce it.

## 4. Naming and packaging hazards

- **`temperans/threading.py` shadows the stdlib `threading` module.** Any absolute
  import of `threading` from within the package is at risk. Rename to `threads.py`
  before external code depends on the current path.
- **No `py.typed` marker.** The codebase is annotated, but type information is not
  exported to consumers. Add the marker and declare it in `package-data`.
- **`scikit-learn==1.5.2` is an exact pin on a core dependency.** It is load-bearing
  because the shipped `.pkl` heads unpickle with version warnings on anything else.
  Exact pins on a widely used library will conflict in real environments. Persist
  model coefficients as `.npz` with an explicit schema and reconstruct the estimator
  at load; then the pin can be relaxed to a range.
- **`print()` in `temperans/models/v1.py`.** Library code should use `logging`.
- **`TrajectoryState.to_dict()` hand-copies 25 fields.** It will drift from the
  dataclass. Use `dataclasses.asdict` with an explicit set-to-count adapter.
- **Schema migration is ad-hoc.** `_migrate_schema` performs `PRAGMA table_info`
  checks per column. Introduce a `schema_version` table and ordered migrations.

## 5. Experimental artifacts in the distribution

`temperans/models/temperans_v1_primitive_head.pkl` is a 3-class
`LogisticRegression` over 3584-dimensional trajectory features
(`[current, history, current−history, current×history]`), classes
`continue / new_topic / repair`.

This corresponds to the n=94 benchmark, whose measured performance was **below**
both the current-turn-only condition and a TF-IDF bag-of-words baseline. It did not
replicate the earlier n=36 result.

It is not reachable from the public API, which is correct. But it ships inside the
wheel and is one import away for anyone reading the source.

**Required before the next release:**

- Move experimental heads behind an explicit `temperans.experimental` namespace, or
  exclude them from the distribution entirely.
- Remove `confidence` from `BehaviorResult`, or rename it. It is currently
  `float(np.max(predict_proba(...)))` — an uncalibrated softmax maximum from a model
  fit on fewer than 100 examples. Presenting it as "confidence" invites readers to
  treat it as a probability. If a score is retained, name it `raw_score` and document
  that it is uncalibrated.
- `history_conditioned=True` is hardcoded in `models/v1.py` and is returned even when
  `previous_text` is empty. Derive it from the input.
- `classes.index(1.0)` raises `ValueError` if the match head has no positive class.
  Guard it.

## 6. Testing

Current coverage: `tests/test_trace.py`, 124 lines. CI runs `compileall`, `pytest`,
`build`, and `twine check` on Python 3.10 and 3.11.

Gaps, in priority order:

1. **Structural signal unit tests.** One test per counter, with a hand-built event
   sequence and an asserted expected value. These are the signals shown to customers;
   they need golden fixtures.
2. **Adversarial ordering tests.** Out-of-order timestamps, mixed offsets, duplicate
   `event_id`, missing `tool_name`, empty text.
3. **Snapshot equivalence property.** For any event sequence, state resumed from a
   snapshot must equal state computed by full replay. This is the invariant that
   makes §3.1 safe.
4. **Idempotency property.** Observing the same event twice must not change state.
5. **Round-trip property.** `Event → store → load → Event` preserves all fields
   including metadata types.

Add `ruff` and `mypy` to CI. Add coverage reporting.

## 7. Remediation sequence

Ordered by ratio of risk removed to effort.

| # | Work | Rough effort | Unblocks |
|---|---|---|---|
| 1 | Idempotent insert; epoch-ms timestamp column; trajectory index | half a day | Safe ingestion of real traffic |
| 2 | Bounded tool-call fingerprint window; canonical metadata hash | half a day | Correct thrash detection |
| 3 | State snapshotting; O(1) per-event update | 1–2 days | Latency budget; long trajectories |
| 4 | `HashingVectorizer` in thread resolver | 2 hours | Deterministic threading |
| 5 | Rename `threading.py`; `py.typed`; `logging`; `asdict` | 2 hours | Packaging hygiene |
| 6 | Experimental namespace; drop `confidence` | 2 hours | Removes the overclaim surface |
| 7 | Test suite per §6 | 2 days | Everything above stays fixed |
| 8 | Coefficients as `.npz`; relax sklearn pin | half a day | Installability |
| 9 | WAL + connection handling; batch insert path | 1 day | Concurrent ingestion |

Items 1–6 are the `0.1.0a2` scope. Note that `0.1.0a1` cannot be overwritten on
PyPI; all fixes ship as a new version.

## 8. Invariants

Properties that should never regress, stated so tests can enforce them:

1. The event log is the source of truth. Any derived state must be reconstructible
   from it alone.
2. Ingestion is idempotent. Observing an event twice is a no-op.
3. Trajectory order is defined by a monotonic numeric field, never by string
   comparison.
4. Structural signals are pure functions of the event sequence — no model, no
   randomness, no wall-clock dependence.
5. Learned components are opt-in, namespaced as experimental, and never reachable
   from the top-level import.
6. Any emitted score carries its model version and a statement of whether it is
   calibrated.

---

## License

Copyright 2026 Temperans AI.

Licensed under the Apache License, Version 2.0 (the "License"); you may not use
this file except in compliance with the License. You may obtain a copy of the
License at <http://www.apache.org/licenses/LICENSE-2.0>.

Unless required by applicable law or agreed to in writing, software distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, either express or implied. See the [LICENSE](LICENSE) file
for the specific language governing permissions and limitations.

"Temperans" and the Temperans logo are trademarks of Temperans AI. Trademark rights
are not granted under the Apache License.

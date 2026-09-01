from pathlib import Path

from temperans import TrajectoryStore
from temperans.threading import SemanticThreadResolver


db = Path("temperans_auto_threads.db")

if db.exists():
    db.unlink()

store = TrajectoryStore(str(db))
resolver = SemanticThreadResolver(threshold=0.15)

trajectory = "user_workspace"


# --------------------------------------------------
# Seed thread 1: benchmark
# --------------------------------------------------

c1 = store.trace(
    user_id="user_123",
    trajectory_id=trajectory,
    conversation_id="chat_1",
    thread_id="temperans_benchmark",
)

c1.human(
    "How should we benchmark trajectory understanding?"
)

c1.agent(
    "Compare current-only, correct-history, "
    "and shuffled-history conditions.",
    actor_id="chat_agent",
)


# --------------------------------------------------
# Seed thread 2: SDK
# --------------------------------------------------

c2 = store.trace(
    user_id="user_123",
    trajectory_id=trajectory,
    conversation_id="chat_2",
    thread_id="temperans_sdk",
)

c2.human(
    "How should pip install temperans expose traces?"
)

c2.agent(
    "Use a Trace API for human, agent, and tool events.",
    actor_id="coding_agent",
)


# --------------------------------------------------
# AUTO: should resolve to benchmark
# --------------------------------------------------

c3 = store.trace(
    user_id="user_123",
    trajectory_id=trajectory,
    conversation_id="chat_3",
    thread_resolver=resolver,
)

e3 = c3.human(
    "The shuffled-history benchmark needs more examples."
)

print()
print("AUTO CASE 1")
print("thread:", e3.thread_id)
print(
    "resolution:",
    e3.metadata.get("thread_resolution"),
)


# --------------------------------------------------
# AUTO: should resolve to SDK
# --------------------------------------------------

c4 = store.trace(
    user_id="user_123",
    trajectory_id=trajectory,
    conversation_id="chat_4",
    thread_resolver=resolver,
)

e4 = c4.human(
    "How should the Temperans Trace API expose agent events?"
)

print()
print("AUTO CASE 2")
print("thread:", e4.thread_id)
print(
    "resolution:",
    e4.metadata.get("thread_resolution"),
)


# --------------------------------------------------
# AUTO: should create new thread
# --------------------------------------------------

c5 = store.trace(
    user_id="user_123",
    trajectory_id=trajectory,
    conversation_id="chat_5",
    thread_resolver=resolver,
)

e5 = c5.human(
    "Tell me a joke about penguins."
)

print()
print("AUTO CASE 3")
print("thread:", e5.thread_id)
print(
    "resolution:",
    e5.metadata.get("thread_resolution"),
)


# --------------------------------------------------
# Reconstruct entire trajectory
# --------------------------------------------------

trace = store.trace(
    user_id="user_123",
    trajectory_id=trajectory,
    conversation_id="analysis",
)

print()
print("=" * 70)
print("THREADS AFTER AUTOMATIC ROUTING")
print("=" * 70)

for thread_id, info in trace.threads().items():
    print()
    print(thread_id)
    print(info)


print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)

print(trace.summary())

store.close()

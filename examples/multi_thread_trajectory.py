from pathlib import Path

from temperans import TrajectoryStore


db = Path("temperans_threads_demo.db")

if db.exists():
    db.unlink()

store = TrajectoryStore(str(db))

trajectory = "user_123_workspace"


# --------------------------------------------------
# Chat 1 — Benchmark thread
# --------------------------------------------------

c1 = store.trace(
    user_id="user_123",
    trajectory_id=trajectory,
    conversation_id="chat_1",
    thread_id="temperans_benchmark",
    goal_id="publish_benchmark",
)

c1.human(
    "How should we benchmark trajectory understanding?"
)

c1.agent(
    "We should compare current-only, correct-history, "
    "and shuffled-history conditions.",
    actor_id="chat_agent",
)


# --------------------------------------------------
# Chat 2 — SDK thread
# --------------------------------------------------

c2 = store.trace(
    user_id="user_123",
    trajectory_id=trajectory,
    conversation_id="chat_2",
    thread_id="temperans_sdk",
    goal_id="ship_alpha",
)

c2.human(
    "How should pip install temperans expose traces?"
)

c2.agent(
    "Start with a Trace API for human, agent, "
    "and tool events.",
    actor_id="coding_agent",
)


# --------------------------------------------------
# Chat 3 — return to benchmark
# --------------------------------------------------

c3 = store.trace(
    user_id="user_123",
    trajectory_id=trajectory,
    conversation_id="chat_3",
    thread_id="temperans_benchmark",
    goal_id="publish_benchmark",
)

c3.human(
    "The shuffled-history control performed unexpectedly well."
)

c3.agent(
    "Freeze the benchmark and train a trajectory-sensitive "
    "model without changing the test set.",
    actor_id="chat_agent",
)


# --------------------------------------------------
# Chat 4 — return to SDK
# --------------------------------------------------

c4 = store.trace(
    user_id="user_123",
    trajectory_id=trajectory,
    conversation_id="chat_4",
    thread_id="temperans_sdk",
    goal_id="ship_alpha",
)

c4.human(
    "Now add persistent cross-agent trajectories."
)

c4.agent(
    "Use SQLite-backed trajectory storage and preserve "
    "conversation and agent identity.",
    actor_id="coding_agent",
)


# --------------------------------------------------
# Re-open whole trajectory
# --------------------------------------------------

trace = store.trace(
    user_id="user_123",
    trajectory_id=trajectory,
    conversation_id="analysis",
)


print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print(trace.summary())


print()
print("=" * 70)
print("THREADS")
print("=" * 70)

for thread_id, info in trace.threads().items():
    print()
    print(thread_id)
    print(info)


print()
print("=" * 70)
print("GOALS")
print("=" * 70)

for goal_id, info in trace.goals().items():
    print()
    print(goal_id)
    print(info)


print()
print("=" * 70)
print("BENCHMARK THREAD")
print("=" * 70)

for event in trace.timeline(
    thread_id="temperans_benchmark"
):
    print(
        event["conversation_id"],
        event["actor_type"],
        "->",
        event["text"],
    )


print()
print("=" * 70)
print("SDK THREAD")
print("=" * 70)

for event in trace.timeline(
    thread_id="temperans_sdk"
):
    print(
        event["conversation_id"],
        event["actor_type"],
        "->",
        event["text"],
    )


store.close()

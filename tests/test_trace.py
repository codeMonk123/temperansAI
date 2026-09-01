from pathlib import Path

from temperans import TrajectoryStore
from temperans.analytics import ThreadAnalytics
from temperans.threading import SemanticThreadResolver


def test_basic_trace(tmp_path):
    db = tmp_path / "basic.db"

    store = TrajectoryStore(str(db))

    trace = store.trace(
        user_id="test_user",
        trajectory_id="project",
        conversation_id="chat_1",
    )

    trace.human("Deployment is failing.")
    trace.agent(
        "I'll inspect it.",
        actor_id="agent_a",
    )
    trace.tool(
        "deploy",
        status="failed",
    )

    state = trace.state()

    assert state["event_count"] == 3
    assert state["human_events"] == 1
    assert state["agent_events"] == 1
    assert state["tool_events"] == 1
    assert state["tool_failures"] == 1
    assert state["unresolved"] is True

    store.close()


def test_persistent_trajectory(tmp_path):
    db = tmp_path / "persistent.db"

    store = TrajectoryStore(str(db))

    first = store.trace(
        user_id="test_user",
        trajectory_id="project",
        conversation_id="chat_1",
    )

    first.human("Deployment failed.")

    second = store.trace(
        user_id="test_user",
        trajectory_id="project",
        conversation_id="chat_2",
    )

    assert second.state()["event_count"] == 1

    second.agent(
        "I'll try another approach.",
        actor_id="agent_b",
    )

    assert second.state()["event_count"] == 2
    assert second.state()["conversation_count"] == 2

    store.close()


def test_thread_resolution_and_analytics(tmp_path):
    db = tmp_path / "threads.db"

    store = TrajectoryStore(str(db))
    resolver = SemanticThreadResolver(
        threshold=0.15
    )

    seed = store.trace(
        user_id="test_user",
        trajectory_id="workspace",
        conversation_id="chat_1",
        thread_id="benchmark",
    )

    seed.human(
        "How should we benchmark trajectory understanding?"
    )

    seed.agent(
        "Compare correct history and shuffled history.",
        actor_id="agent_a",
    )

    followup = store.trace(
        user_id="test_user",
        trajectory_id="workspace",
        conversation_id="chat_2",
        thread_resolver=resolver,
    )

    event = followup.human(
        "The shuffled-history benchmark needs more examples."
    )

    assert event.thread_id == "benchmark"

    trace = store.trace(
        user_id="test_user",
        trajectory_id="workspace",
        conversation_id="analysis",
    )

    analytics = ThreadAnalytics(
        trace
    ).analyze()

    assert "benchmark" in analytics
    assert analytics["benchmark"]["revisited"] is True
    assert analytics["benchmark"]["one_off"] is False

    store.close()

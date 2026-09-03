import json
import pytest

from temperans.platform import TemperansPlatform
from temperans.sqlite_store import ConcurrentTrajectoryUpdate


def make_org(platform):
    return platform.create_organization(
        organization_id="a",
        name="a",
    )


def payload(event_id, message, conversation_id="c1"):
    return {
        "event_id": event_id,
        "workspace_id": "w",
        "external_user_id": "U1",
        "surface": "generic_chatbot",
        "conversation_id": conversation_id,
        "message": message,
    }


def test_new_persists_version1_and_creation_delta(tmp_path):
    platform = TemperansPlatform(tmp_path / "platform")
    created = make_org(platform)

    result = platform.observe_with_key(
        api_key=created["api_key"],
        payload=payload("e1", "Investigate PROD-218"),
    )

    runtime = platform.runtime("a")
    trajectory = runtime.sqlite.get_trajectory(
        organization_id="a",
        trajectory_id=result["trajectory_id"],
    )

    assert trajectory["trajectory_version"] == 1

    row = runtime.sqlite.conn.execute(
        "SELECT state_delta_json FROM decisions WHERE decision_id=?",
        (result["decision_record_id"],),
    ).fetchone()

    delta = json.loads(row["state_delta_json"])
    assert delta["trajectory_created"] is True
    assert "current_state" in delta["fields"]
    assert not (runtime.root / "trajectories.json").exists()


def test_restart_loads_trajectory_from_sqlite(tmp_path):
    root = tmp_path / "platform"
    first = TemperansPlatform(root)
    created = make_org(first)

    result = first.observe_with_key(
        api_key=created["api_key"],
        payload=payload("e1", "Investigate PROD-218"),
    )

    trajectory_id = result["trajectory_id"]
    api_key = created["api_key"]

    second = TemperansPlatform(root)

    assert second.authenticate(api_key).organization_id == "a"

    trajectory = second.runtime("a").service.trajectory(
        trajectory_id
    )

    assert trajectory is not None
    assert trajectory["trajectory_id"] == trajectory_id


def test_duplicate_does_not_increment_version_or_decision_count(tmp_path):
    platform = TemperansPlatform(tmp_path / "platform")
    created = make_org(platform)
    event = payload("e1", "Investigate PROD-218")

    first = platform.observe_with_key(
        api_key=created["api_key"],
        payload=event,
    )

    runtime = platform.runtime("a")
    trajectory_id = first["trajectory_id"]

    version_before = runtime.sqlite.get_trajectory(
        organization_id="a",
        trajectory_id=trajectory_id,
    )["trajectory_version"]

    decisions_before = runtime.sqlite.conn.execute(
        "SELECT COUNT(*) FROM decisions WHERE organization_id='a'"
    ).fetchone()[0]

    second = platform.observe_with_key(
        api_key=created["api_key"],
        payload=event,
    )

    version_after = runtime.sqlite.get_trajectory(
        organization_id="a",
        trajectory_id=trajectory_id,
    )["trajectory_version"]

    decisions_after = runtime.sqlite.conn.execute(
        "SELECT COUNT(*) FROM decisions WHERE organization_id='a'"
    ).fetchone()[0]

    assert second == first
    assert version_after == version_before
    assert decisions_after == decisions_before


def test_stale_writer_is_rejected(tmp_path):
    platform = TemperansPlatform(tmp_path / "platform")
    make_org(platform)
    runtime = platform.runtime("a")

    state = {
        "trajectory_id": "t",
        "workspace_id": "w",
        "person_id": "p",
        "durable_goal": "g",
        "current_state": "x",
        "lifecycle": "active",
        "entities": [],
        "artifacts": [],
        "anchors": [],
        "open_questions": [],
        "resolved_questions": [],
        "decisions": [],
        "attempts": [],
        "failures": [],
        "outcomes": [],
        "surfaces": [],
        "conversation_ids": [],
        "recent_context": [],
    }

    runtime.sqlite.create_trajectory(
        organization_id="a",
        trajectory_id="t",
        workspace_id="w",
        person_id="p",
        state=state,
    )

    runtime.sqlite.update_trajectory(
        organization_id="a",
        trajectory_id="t",
        expected_version=1,
        state={**state, "current_state": "y"},
    )

    with pytest.raises(ConcurrentTrajectoryUpdate):
        runtime.sqlite.update_trajectory(
            organization_id="a",
            trajectory_id="t",
            expected_version=1,
            state={**state, "current_state": "z"},
        )

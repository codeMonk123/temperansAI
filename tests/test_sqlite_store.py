import sqlite3
import pytest
from temperans.sqlite_store import SQLiteStore, EventConflict, ConcurrentTrajectoryUpdate


def org(store, oid):
    return store.create_organization(
        organization_id=oid, name=oid, config={"organization_id": oid}
    )


def test_auth_persists(tmp_path):
    p = tmp_path / "temperans.db"
    s = SQLiteStore(p)
    x = org(s, "a")
    key = x["api_key"]
    s.close()
    s = SQLiteStore(p)
    assert s.authenticate(key)["organization_id"] == "a"
    s.close()


def test_event_uniqueness_is_tenant_scoped(tmp_path):
    s = SQLiteStore(tmp_path / "t.db")
    org(s, "a"); org(s, "b")
    a = s.insert_event(organization_id="a", event_id="evt1", payload={"x": 1})
    b = s.insert_event(organization_id="b", event_id="evt1", payload={"x": 2})
    assert a["organization_id"] == "a"
    assert b["organization_id"] == "b"
    assert s.count_events("a") == 1
    assert s.count_events("b") == 1


def test_event_idempotent_and_conflict(tmp_path):
    s = SQLiteStore(tmp_path / "t.db")
    org(s, "a")
    first = s.insert_event(organization_id="a", event_id="evt1", payload={"x": 1})
    second = s.insert_event(organization_id="a", event_id="evt1", payload={"x": 1})
    assert first["record_id"] == second["record_id"]
    assert s.count_events("a") == 1
    with pytest.raises(EventConflict):
        s.insert_event(organization_id="a", event_id="evt1", payload={"x": 2})


def test_identity_isolation(tmp_path):
    s = SQLiteStore(tmp_path / "t.db")
    org(s, "a"); org(s, "b")
    s.link_identity(organization_id="a", workspace_id="w", surface="slack",
                    external_user_id="U1", person_id="person_a")
    s.link_identity(organization_id="b", workspace_id="w", surface="slack",
                    external_user_id="U1", person_id="person_b")
    assert s.resolve_identity(organization_id="a", workspace_id="w", surface="slack",
                              external_user_id="U1") == "person_a"
    assert s.resolve_identity(organization_id="b", workspace_id="w", surface="slack",
                              external_user_id="U1") == "person_b"


def test_trajectory_optimistic_concurrency(tmp_path):
    s = SQLiteStore(tmp_path / "t.db")
    org(s, "a")
    t = s.create_trajectory(
        organization_id="a", trajectory_id="traj1", workspace_id="w",
        person_id="p", state={"durable_goal": "goal", "lifecycle": "active"}
    )
    assert t["trajectory_version"] == 1
    t2 = s.update_trajectory(
        organization_id="a", trajectory_id="traj1", expected_version=1,
        state={"durable_goal": "goal", "lifecycle": "active", "current_state": "next"}
    )
    assert t2["trajectory_version"] == 2
    with pytest.raises(ConcurrentTrajectoryUpdate):
        s.update_trajectory(
            organization_id="a", trajectory_id="traj1", expected_version=1,
            state={"durable_goal": "stale", "lifecycle": "active"}
        )


def test_decision_requires_existing_event_same_org(tmp_path):
    s = SQLiteStore(tmp_path / "t.db")
    org(s, "a"); org(s, "b")
    s.insert_event(organization_id="a", event_id="evt1", payload={"x": 1})
    s.insert_decision(
        organization_id="a", event_id="evt1", trajectory_id=None,
        decision="new", trace={"reason": "test"}, state_delta={"lifecycle": {"to": "active"}}
    )
    with pytest.raises(sqlite3.IntegrityError):
        s.insert_decision(
            organization_id="b", event_id="evt1", trajectory_id=None,
            decision="new", trace={}
        )


def test_foreign_keys_enabled(tmp_path):
    s = SQLiteStore(tmp_path / "t.db")
    assert s.conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1

import pytest

from temperans.platform import TemperansPlatform
from temperans.sqlite_store import EventConflict


def make_org(platform, oid):
    return platform.create_organization(organization_id=oid, name=oid)


def payload(event_id, message="Investigate PROD-218"):
    return {
        "event_id": event_id,
        "workspace_id": "w",
        "external_user_id": "U1",
        "surface": "generic_chatbot",
        "conversation_id": "c1",
        "message": message,
    }


def test_observe_event_is_sqlite_authoritative(tmp_path):
    p = TemperansPlatform(tmp_path / "platform")
    created = make_org(p, "a")
    result = p.observe_with_key(api_key=created["api_key"], payload=payload("evt1"))
    r = p.runtime("a")
    row = r.sqlite.get_event(organization_id="a", event_id="evt1")
    assert row is not None
    assert row["result"] == result
    assert not (r.root / "idempotency.json").exists()


def test_duplicate_returns_completed_result_without_mutation(tmp_path):
    p = TemperansPlatform(tmp_path / "platform")
    created = make_org(p, "a")
    x = payload("evt1")
    first = p.observe_with_key(api_key=created["api_key"], payload=x)
    r = p.runtime("a")
    before_events = len(r.service.store.read("events.jsonl"))
    before_decisions = len(r.service.store.read("decisions.jsonl"))
    before_traj = {k: v.to_dict() for k, v in r.service.runtime.trajectories.items()}

    second = p.observe_with_key(api_key=created["api_key"], payload=x)

    assert second == first
    assert len(r.service.store.read("events.jsonl")) == before_events
    assert len(r.service.store.read("decisions.jsonl")) == before_decisions
    assert {k: v.to_dict() for k, v in r.service.runtime.trajectories.items()} == before_traj


def test_conflicting_duplicate_fails(tmp_path):
    p = TemperansPlatform(tmp_path / "platform")
    created = make_org(p, "a")
    p.observe_with_key(api_key=created["api_key"], payload=payload("evt1", "one"))
    with pytest.raises(EventConflict):
        p.observe_with_key(api_key=created["api_key"], payload=payload("evt1", "two"))


def test_same_event_id_across_orgs_is_legal(tmp_path):
    p = TemperansPlatform(tmp_path / "platform")
    a = make_org(p, "a")
    b = make_org(p, "b")
    ra = p.observe_with_key(api_key=a["api_key"], payload=payload("evt1", "A"))
    rb = p.observe_with_key(api_key=b["api_key"], payload=payload("evt1", "B"))
    assert ra["organization_id"] == "a"
    assert rb["organization_id"] == "b"
    assert p.runtime("a").sqlite.count_events("a") == 1
    assert p.runtime("b").sqlite.count_events("b") == 1


def test_completed_result_survives_platform_restart(tmp_path):
    root = tmp_path / "platform"
    p1 = TemperansPlatform(root)
    created = make_org(p1, "a")
    key = created["api_key"]
    x = payload("evt1")
    first = p1.observe_with_key(api_key=key, payload=x)

    p2 = TemperansPlatform(root)
    second = p2.observe_with_key(api_key=key, payload=x)
    assert second == first

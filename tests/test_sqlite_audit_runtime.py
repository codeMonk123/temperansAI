import json
from temperans.platform import TemperansPlatform


def make_org(p, oid="a"):
    return p.create_organization(organization_id=oid, name=oid)


def payload(event_id="evt1"):
    return {
        "event_id": event_id,
        "workspace_id": "w",
        "external_user_id": "U1",
        "surface": "generic_chatbot",
        "conversation_id": "c1",
        "message": "Investigate PROD-218",
    }


def test_runtime_decision_is_persisted_in_sqlite(tmp_path):
    p = TemperansPlatform(tmp_path / "platform")
    c = make_org(p)
    result = p.observe_with_key(api_key=c["api_key"], payload=payload())
    r = p.runtime("a")

    row = r.sqlite.conn.execute(
        "SELECT * FROM decisions WHERE organization_id=? AND event_id=?",
        ("a", "evt1"),
    ).fetchone()

    assert row is not None
    assert row["decision_id"] == result["decision_record_id"]
    assert row["decision"] == result["decision"]
    assert json.loads(row["trace_json"]) == result["trace"]
    delta = json.loads(row["state_delta_json"])
    assert delta["trajectory_created"] is True
    assert "current_state" in delta["fields"]
    assert not (r.root / "decisions.jsonl").exists()


def test_duplicate_event_does_not_duplicate_sqlite_decision(tmp_path):
    p = TemperansPlatform(tmp_path / "platform")
    c = make_org(p)
    x = payload()
    first = p.observe_with_key(api_key=c["api_key"], payload=x)
    second = p.observe_with_key(api_key=c["api_key"], payload=x)
    r = p.runtime("a")

    n = r.sqlite.conn.execute(
        "SELECT COUNT(*) FROM decisions WHERE organization_id=? AND event_id=?",
        ("a", "evt1"),
    ).fetchone()[0]

    assert second == first
    assert n == 1


def test_runtime_correction_is_sqlite_authoritative(tmp_path):
    p = TemperansPlatform(tmp_path / "platform")
    c = make_org(p)
    result = p.observe_with_key(api_key=c["api_key"], payload=payload())
    r = p.runtime("a")

    correction = r.service.correct({
        "decision_record_id": result["decision_record_id"],
        "event_id": "evt1",
        "action": "confirm",
        "reason_code": "human_verified",
    })

    assert correction["correction_id"].startswith("cor_")
    rows = r.service.corrections()
    assert len(rows) == 1
    assert rows[0]["event_id"] == "evt1"
    assert rows[0]["decision_id"] == result["decision_record_id"]
    assert rows[0]["correction"]["decision"] == "confirm"
    assert not (r.root / "corrections.jsonl").exists()

from temperans.platform import TemperansPlatform
from temperans.sqlite_audit_store import SQLitePilotAuditStore

def make_org(p, oid="a"):
    return p.create_organization(organization_id=oid, name=oid)

def test_decision_adapter_persists_trace_and_empty_state_delta(tmp_path):
    p=TemperansPlatform(tmp_path/"platform"); c=make_org(p); r=p.runtime("a")
    r.sqlite.insert_event(organization_id="a",event_id="evt1",payload={"x":1})
    a=SQLitePilotAuditStore(r.sqlite,"a")
    x=a.decision({"event_id":"evt1","trajectory_id":None,"decision":"new",
                  "trace":{"source":"test"},"state_delta":{}})
    assert x["record_id"].startswith("dec_")
    row=r.sqlite.conn.execute("SELECT * FROM decisions WHERE decision_id=?",(x["record_id"],)).fetchone()
    assert row is not None
    assert row["state_delta_json"]=="{}"

def test_correction_adapter_persists_structured_assertion(tmp_path):
    p=TemperansPlatform(tmp_path/"platform"); make_org(p); r=p.runtime("a")
    a=SQLitePilotAuditStore(r.sqlite,"a")
    x=a.correction({"event_id":"evt1","decision_id":"dec1",
                    "correction":{"source":"user","decision":"branch","reason_code":"wrong_relationship"},
                    "diagnosis":{"source":"system","linkage":"wrong_relationship"}})
    assert x["correction_id"].startswith("cor_")
    row=r.sqlite.conn.execute("SELECT * FROM corrections WHERE correction_id=?",(x["correction_id"],)).fetchone()
    assert row is not None
    assert "wrong_relationship" in row["correction_json"]

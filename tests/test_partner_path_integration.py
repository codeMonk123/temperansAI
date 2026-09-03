from temperans.platform import TemperansPlatform

def create_org(p, oid):
    return p.create_organization(organization_id=oid,name=oid)

def event(eid,message,user="U1",conversation_id="c1"):
    return {"event_id":eid,"workspace_id":"production","external_user_id":user,
            "surface":"generic_chatbot","conversation_id":conversation_id,
            "message":message}

def test_runtime_accepts_authenticated_config(tmp_path):
    p=TemperansPlatform(tmp_path/"platform"); c=create_org(p,"xyzabc321")
    cfg=p.authenticate(c["api_key"])
    assert p.runtime(cfg) is p.runtime(cfg.organization_id)

def test_live_partner_path_strong_anchor_attaches(tmp_path):
    p=TemperansPlatform(tmp_path/"platform"); c=create_org(p,"xyzabc321"); key=c["api_key"]
    a=p.observe_with_key(api_key=key,payload=event(
        "evt1","Ticket PROD-218 deployment is failing during startup",conversation_id="c1"))
    b=p.observe_with_key(api_key=key,payload=event(
        "evt2","PROD-218 now shows a certificate mismatch after restart",conversation_id="c2"))
    assert b["source"] not in {"no_candidates","candidate_retrieval"}
    assert b["trajectory_id"]==a["trajectory_id"]
    assert b["decision"]=="attach"

def test_anchor_never_crosses_org_boundary(tmp_path):
    p=TemperansPlatform(tmp_path/"platform"); a=create_org(p,"xyzabc321"); b=create_org(p,"xyzabc322")
    ra=p.observe_with_key(api_key=a["api_key"],payload=event("shared","Ticket PROD-218 deployment is failing"))
    rb=p.observe_with_key(api_key=b["api_key"],payload=event("shared","Ticket PROD-218 deployment is failing"))
    assert ra["organization_id"]=="xyzabc321"
    assert rb["organization_id"]=="xyzabc322"
    assert ra["trajectory_id"]!=rb["trajectory_id"]
    assert ra["person_id"]!=rb["person_id"]

def test_sqlite_trajectory_version_exists(tmp_path):
    p=TemperansPlatform(tmp_path/"platform"); c=create_org(p,"xyzabc321")
    r=p.observe_with_key(api_key=c["api_key"],payload=event("evt1","Investigate PROD-218"))
    stored=p.runtime("xyzabc321").sqlite.get_trajectory(
        organization_id="xyzabc321",trajectory_id=r["trajectory_id"])
    assert stored is not None
    assert stored["trajectory_version"]>=1

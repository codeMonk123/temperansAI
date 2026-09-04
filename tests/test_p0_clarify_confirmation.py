import pytest
from temperans.platform import TemperansPlatform

def payload(e,text="Investigate PROD-218"):
    return {"event_id":e,"workspace_id":"w","external_user_id":"u","surface":"generic_chatbot","conversation_id":e+"_c","content":{"text":text}}

def count_traj(rt):
    return rt.sqlite.conn.execute("SELECT COUNT(*) FROM trajectories WHERE organization_id=?",(rt.config.organization_id,)).fetchone()[0]

def test_confirm_new_exactly_once(tmp_path):
    p=TemperansPlatform(tmp_path/"p");c=p.create_organization(organization_id="o",name="o",routing_mode="clarify_only");rt=p.runtime("o")
    r=p.observe_with_key(api_key=c["api_key"],payload=payload("e1"));assert count_traj(rt)==0
    x=p.confirm_proposal_with_key(api_key=c["api_key"],proposal_id=r["proposal_id"]);assert x["status"]=="confirmed" and count_traj(rt)==1
    x=p.confirm_proposal_with_key(api_key=c["api_key"],proposal_id=r["proposal_id"]);assert x["status"]=="confirmed" and count_traj(rt)==1

def test_reject_never_mutates(tmp_path):
    p=TemperansPlatform(tmp_path/"p");c=p.create_organization(organization_id="o",name="o",routing_mode="clarify_only");rt=p.runtime("o")
    r=p.observe_with_key(api_key=c["api_key"],payload=payload("e1"))
    x=p.reject_proposal_with_key(api_key=c["api_key"],proposal_id=r["proposal_id"]);assert x["status"]=="rejected" and count_traj(rt)==0
    with pytest.raises(ValueError):p.confirm_proposal_with_key(api_key=c["api_key"],proposal_id=r["proposal_id"])

def test_cross_org_confirm_forbidden(tmp_path):
    p=TemperansPlatform(tmp_path/"p");a=p.create_organization(organization_id="a",name="a",routing_mode="clarify_only");b=p.create_organization(organization_id="b",name="b",routing_mode="clarify_only")
    r=p.observe_with_key(api_key=a["api_key"],payload=payload("e1"))
    with pytest.raises(KeyError):p.confirm_proposal_with_key(api_key=b["api_key"],proposal_id=r["proposal_id"])
    assert count_traj(p.runtime("a"))==0 and count_traj(p.runtime("b"))==0

def test_confirm_survives_restart(tmp_path):
    root=tmp_path/"p";p=TemperansPlatform(root);c=p.create_organization(organization_id="o",name="o",routing_mode="clarify_only")
    r=p.observe_with_key(api_key=c["api_key"],payload=payload("e1"))
    p2=TemperansPlatform(root);x=p2.confirm_proposal_with_key(api_key=c["api_key"],proposal_id=r["proposal_id"])
    assert x["status"]=="confirmed" and count_traj(p2.runtime("o"))==1

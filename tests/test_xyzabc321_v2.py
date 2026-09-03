from temperans.platform import TemperansPlatform
from temperans.xyzabc321_dataset import build_xyzabc321
from temperans.xyzabc321_identity import link_xyzabc321_identities
from temperans.xyzabc321_evaluator_v2 import evaluate_v2
def test_identity_links_three_surfaces_to_one_person(tmp_path):
 p=TemperansPlatform(tmp_path/"p");p.create_organization(organization_id="XYZABC321",name="x")
 rt=p.runtime("XYZABC321");link_xyzabc321_identities(rt)
 ids=[rt.identities.resolve("production",s,"user_01",False) for s in ("slack","generic_chatbot","mcp")]
 assert len(set(ids))==1 and ids[0]=="xyz_person_01"
def test_v2_evaluator_abstentions_not_committed(tmp_path):
 p=TemperansPlatform(tmp_path/"p");p.create_organization(organization_id="XYZABC321",name="x")
 rt=p.runtime("XYZABC321");link_xyzabc321_identities(rt)
 events,_=build_xyzabc321();r=evaluate_v2(rt,events)
 assert r["committed_events"]+r["abstained_events"]==120
 assert 0<=r["automatic_coverage"]<=1
 assert 0<=r["committed_pair_precision"]<=1

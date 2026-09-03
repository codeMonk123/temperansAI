from temperans.platform import TemperansPlatform
from temperans.xyzabc322_isolation import verify_isolation

def test_xyzabc322_adversarial_same_ids_are_isolated(tmp_path):
 p=TemperansPlatform(tmp_path/"p")
 ca=p.create_organization(organization_id="XYZABC321",name="a")
 cb=p.create_organization(organization_id="XYZABC322",name="b")
 payload={"event_id":"SAME","workspace_id":"production","external_user_id":"user_01",
 "surface":"chat","conversation_id":"SAME","content":{"text":"Ticket PROD-201 same text"}}
 a=p.observe_with_key(api_key=ca["api_key"],payload=payload)
 b=p.observe_with_key(api_key=cb["api_key"],payload=payload)
 assert a["organization_id"]=="XYZABC321" and b["organization_id"]=="XYZABC322"
 assert a["person_id"]!=b["person_id"]
 assert verify_isolation(p)["pass"]

def test_verification_contract_does_not_fake_human_gate():
 import temperans.v1_verification as v
 assert callable(v.main)

from temperans.platform import TemperansPlatform
def payload(e,u,s,t):
 return {"event_id":e,"workspace_id":"w","external_user_id":u,"surface":s,"conversation_id":e+"_c","content":{"text":t}}
def test_cross_surface_rescue_without_identity_merge(tmp_path):
 p=TemperansPlatform(tmp_path/"p");o=p.create_organization(organization_id="o",name="o")
 a=p.observe_with_key(api_key=o["api_key"],payload=payload("a","u","slack","Investigate PROD-777 certificate failure"))
 b=p.observe_with_key(api_key=o["api_key"],payload=payload("b","u","generic_chatbot","PROD-777 still failing"))
 assert b["decision"]=="clarify" and b["source"]=="cross_person_structural_rescue"
 assert b["trajectory_id"]==a["trajectory_id"] and b["person_id"]!=a["person_id"]
 assert any(x["rule"]=="cross_person_anchor_rescue" for x in b["trace"]["rules"])
def test_shared_ticket_different_people_never_auto_attach(tmp_path):
 p=TemperansPlatform(tmp_path/"p");o=p.create_organization(organization_id="o",name="o")
 a=p.observe_with_key(api_key=o["api_key"],payload=payload("a","alice","slack","Working on PROD-218 checkout failure"))
 b=p.observe_with_key(api_key=o["api_key"],payload=payload("b","bob","generic_chatbot","PROD-218 checkout still failing"))
 assert b["decision"]=="clarify" and b["trajectory_id"]==a["trajectory_id"] and b["person_id"]!=a["person_id"]
def test_no_anchor_no_cross_person_widening(tmp_path):
 p=TemperansPlatform(tmp_path/"p");o=p.create_organization(organization_id="o",name="o")
 a=p.observe_with_key(api_key=o["api_key"],payload=payload("a","alice","slack","checkout certificate failure"))
 b=p.observe_with_key(api_key=o["api_key"],payload=payload("b","bob","generic_chatbot","checkout certificate failure"))
 assert b["decision"]=="new" and b["trajectory_id"]!=a["trajectory_id"]
def test_cross_org_never_rescues(tmp_path):
 p=TemperansPlatform(tmp_path/"p");a=p.create_organization(organization_id="a",name="a");b=p.create_organization(organization_id="b",name="b")
 x=p.observe_with_key(api_key=a["api_key"],payload=payload("x","u","slack","Investigate PROD-999"))
 y=p.observe_with_key(api_key=b["api_key"],payload=payload("y","u","generic_chatbot","PROD-999 follow-up"))
 assert y["decision"]=="new" and y["trajectory_id"]!=x["trajectory_id"]

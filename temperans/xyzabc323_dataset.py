def build_xyzabc323():
 rows=[]
 def add(e,p,w,s,t,q,r):
  rows.append({"event_id":e,"workspace_id":"heldout-production","external_user_id":p,"surface":s,"conversation_id":e+"_conv","source_sequence":str(q),"content":{"text":t},"_gold_work":w,"_gold_relation":r})
 for i in range(1,11):
  p=f"huser_{i:02d}";w=f"INC-{700+i}"
  add(f"{p}_1",p,w,"slack",f"Investigate incident {w}: checkout certificate rejected",1,"new")
  add(f"{p}_2",p,w,"mcp",f"{w} is still blocking checkout after certificate rotation",2,"attach")
 for i in range(11,21):
  p=f"huser_{i:02d}";w=f"OPS-{800+i}"
  add(f"{p}_1",p,w,"generic_chatbot",f"Open {w}: nightly inventory export is missing records",1,"new")
  add(f"{p}_2",p,w,"slack","the inventory export is still missing rows after the backfill",2,"attach")
 for i in range(1,6):
  p=f"similar_{i:02d}"
  add(f"{p}_a",p,f"AUTH-A-{i}","slack","employee SSO login redirects forever in production",1,"new")
  add(f"{p}_b",p,f"AUTH-B-{i}","generic_chatbot","customer portal login redirects forever in production; separate incident",1,"new")
 for i in range(1,6):
  w=f"CASE-{900+i}"
  add(f"shared_{i}_a",f"agent_{i:02d}",w,"slack",f"Working on {w}; payment service returns certificate warning",1,"new")
  add(f"shared_{i}_b",f"owner_{i:02d}",w,"generic_chatbot",f"{w} still has the payment certificate warning",2,"ambiguous_cross_person")
 for i in range(1,6):
  p=f"sparse_{i:02d}"
  add(f"{p}_base1",p,f"DEP-{i}","slack","production deployment is failing certificate validation",1,"new")
  add(f"{p}_base2",p,f"LOGIN-{i}","generic_chatbot","employee login is failing after the identity provider change",1,"new")
  add(f"{p}_amb",p,f"AMB-{i}","mcp","same thing is broken again after that change",2,"clarify")
 return rows

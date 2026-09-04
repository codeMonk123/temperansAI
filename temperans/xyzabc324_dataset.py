def build_xyzabc324():
 rows=[]
 def add(e,p,w,s,text,seq,rel):
  rows.append({"event_id":e,"workspace_id":"validation-prod","external_user_id":p,"surface":s,"conversation_id":e+"_thread","source_sequence":str(seq),"content":{"text":text},"_gold_work":w,"_gold_relation":rel})
 for i in range(1,11):
  p=f"vuser_{i:02d}";w=f"BUG-{1100+i}";add(f"{p}_a",p,w,"generic_chatbot",f"Please investigate {w}; invoice generation times out",1,"new");add(f"{p}_b",p,w,"slack",f"After the worker restart, {w} continues to block invoices",2,"attach")
 for i in range(11,21):
  p=f"vuser_{i:02d}";w=f"JOB-{1200+i}";add(f"{p}_a",p,w,"slack",f"Track {w}: catalog synchronization skips recently edited products",1,"new");add(f"{p}_b",p,w,"mcp","the catalog sync still skips edited products after the retry",2,"attach")
 for i in range(1,11):
  p=f"sep_{i:02d}";add(f"{p}_a",p,f"PAY-A-{i}","slack","payment authorization fails for subscription renewals",1,"new");add(f"{p}_b",p,f"PAY-B-{i}","generic_chatbot","payment authorization fails for marketplace orders; separate issue",1,"new")
 for i in range(1,6):
  w=f"SUP-{1300+i}";add(f"cp_{i}_a",f"support_{i}",w,"slack",f"Investigating {w}: export endpoint returns 502",1,"new");add(f"cp_{i}_b",f"owner_{i}",w,"generic_chatbot",f"{w} export endpoint still returns 502",2,"ambiguous_cross_person")
 for i in range(1,6):
  p=f"amb_{i:02d}";add(f"{p}_a",p,f"SEARCH-{i}","slack","search indexing is delayed after ingestion",1,"new");add(f"{p}_b",p,f"MAIL-{i}","generic_chatbot","email delivery is delayed after queue ingestion",1,"new");add(f"{p}_c",p,f"AMB-{i}","mcp","it is delayed again after that change",2,"clarify")
 return rows

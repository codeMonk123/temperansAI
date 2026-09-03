def build_xyzabc321():
 events=[]; gold={}; surfaces=["slack","generic_chatbot","mcp"]
 for u in range(1,21):
  user=f"user_{u:02d}"
  for w,ticket in enumerate((f"PROD-{200+u}",f"DATA-{300+u}",f"AUTH-{400+u}"),1):
   gid=f"{user}_work_{w}"; gold[gid]=[]
   for n,text in [(1,f"Ticket {ticket} is failing; investigate the initial problem"),(2,f"{ticket} follow-up after restart; continue investigating")]:
    e={"event_id":f"{gid}_{n}","workspace_id":"production","external_user_id":user,
       "surface":surfaces[(u+w+n)%3],"conversation_id":f"{gid}_c{n}",
       "occurred_at":f"2026-08-{10+w:02d}T{9+n:02d}:00:00+00:00","source_sequence":str(n),
       "content":{"text":text},"_gold_trajectory":gid}
    events.append(e); gold[gid].append(e["event_id"])
 return events,gold

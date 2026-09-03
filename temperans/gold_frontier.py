"""Gold-state frontier benchmark independent of prior Temperans mistakes."""
from temperans.anchors import AnchorExtractor

def _ticket(text):
 anchors=AnchorExtractor().extract(text)
 for a in anchors:
  if a.type=="ticket":return a.value
 return None

def build_gold_frontier(events,max_users=None):
 by_work={}
 for e in events:by_work.setdefault(e["_gold_trajectory"],[]).append(e)
 cases=[]
 works=sorted(by_work)
 users=sorted({w.split("_work_")[0] for w in works})
 if max_users:users=users[:max_users]
 for user in users:
  user_works=[w for w in works if w.startswith(user+"_work_")]
  # synthetic candidate IDs are stable evaluation IDs, not production IDs.
  candidates=[]
  for w in user_works:
   first=sorted(by_work[w],key=lambda e:e["source_sequence"])[0]
   ticket=_ticket(first["content"]["text"])
   candidates.append({"trajectory_id":"gold_"+w,"gold_work":w,
    "durable_goal":first["content"]["text"],"current_state":first["content"]["text"],
    "anchors":[{"type":"ticket","value":ticket,"strength":"strong"}] if ticket else [],
    "recent_context":[first["content"]["text"]]})
  for w in user_works:
   seq=sorted(by_work[w],key=lambda e:e["source_sequence"])
   first,follow=seq[0],seq[1]
   # NEW case: candidate set excludes the target work.
   cases.append({"case_id":first["event_id"]+"_gold_new","kind":"new",
    "event":{k:v for k,v in first.items() if k!="_gold_trajectory"},
    "candidate_views":[c for c in candidates if c["gold_work"]!=w],
    "gold_action":"new","gold_candidate_id":None})
   # ATTACH case: includes target + distractors.
   cases.append({"case_id":follow["event_id"]+"_gold_attach","kind":"attach",
    "event":{k:v for k,v in follow.items() if k!="_gold_trajectory"},
    "candidate_views":candidates,"gold_action":"attach",
    "gold_candidate_id":"gold_"+w})
 return cases

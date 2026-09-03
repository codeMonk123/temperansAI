def extract_frontier_v2(runtime,events):
 cases=[];gold_runtime={}
 for e in events:
  clean=dict(e);gold=clean.pop("_gold_trajectory")
  person=runtime.identities.resolve(clean.get("workspace_id","default"),
   clean.get("surface","generic_chatbot"),clean["external_user_id"],True)
  candidates=[]
  for t in runtime.service.runtime.trajectories.values():
   if t.workspace_id==clean.get("workspace_id","default") and t.person_id==person:
    x=t.to_dict();x["anchors"]=[a.to_dict() for a in t.anchors];candidates.append(x)
  result=runtime.observe(clean)
  if result["decision"]!="clarify":
   if result["decision"] in {"new","branch"}:gold_runtime[gold]=result["trajectory_id"]
   elif result["decision"]=="attach" and gold not in gold_runtime:gold_runtime[gold]=result["trajectory_id"]
   continue
  expected_id=gold_runtime.get(gold)
  gold_action="attach" if expected_id else "new"
  cases.append({"case_id":clean["event_id"],"gold_work":gold,"gold_action":gold_action,
   "gold_candidate_id":expected_id,"event":clean,"candidate_views":candidates})
 return cases

def extract_frontier(runtime,events):
 cases=[]
 for e in events:
  clean=dict(e);gold=clean.pop("_gold_trajectory")
  # Candidate views must be captured BEFORE processing the ambiguous event.
  person=runtime.identities.resolve(clean.get("workspace_id","default"),
    clean.get("surface","generic_chatbot"),clean["external_user_id"],True)
  candidates=runtime.service.trajectories(clean.get("workspace_id","default"),person)
  result=runtime.observe(clean)
  if result["decision"]=="clarify":
   cases.append({"case_id":clean["event_id"],"gold_trajectory":gold,
    "event":clean,"candidate_views":candidates})
 return cases

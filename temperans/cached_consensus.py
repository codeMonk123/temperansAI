from temperans.frontier_assessment import FrontierAssessment
from temperans.semantic_new_recovery import decide_new
def assessment(d):
 if not d:return None
 x=d["assessment"];return FrontierAssessment(x["action"],x.get("candidate_id"),
  x["confidence"],x.get("evidence",[]),x.get("maturity","L2"))
def cached_new_consensus(primary_row,verifier_row):
 d=decide_new(assessment(primary_row),assessment(verifier_row))
 return {"accepted":d.accepted,"action":d.action,"reason":d.reason}
